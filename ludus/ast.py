from .lexer import Lexer
from .nodes import *
from .parser import parse
from .runtime.symbol_table import SymbolTableError, SymbolTable
from .runtime.interpreter import SemanticError, evaluate 
import re
from typing import Union

class ParserError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"

class Semantic:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        self.current_token = self.get_next_token()
        self.symbol_table = SymbolTable()
        self.globalstruct = []

    TYPE_MAP = {
        int: "hp",
        float: "xp",
        str: "comms",
        bool: "flag"
    }

    def get_next_token(self):
        if self.current_token_index < len(self.tokens):
            token = self.tokens[self.current_token_index]
            self.current_token_index += 1
            return token
        return None
    
    def skip_whitespace(self):
        while self.current_token and self.current_token.token in {"newline", "space"}:
            self.current_token = self.get_next_token()

    def skip_spaces(self):
        while self.current_token and self.current_token.token == "space":
            self.current_token = self.get_next_token()

    def expect(self, token_type, error_message):
        prev_token = self.current_token
        self.current_token = self.get_next_token()
        if not prev_token or prev_token.token != token_type:
            raise ParserError(f"Parser Error: {error_message}")
        
    def look_ahead(self):
        la_token_index = self.current_token_index 
        while la_token_index < len(self.tokens):
            la_token = self.tokens[la_token_index]
            if la_token.token != "space": 
                return la_token
            la_token_index += 1  

        return None  

    def produce_ast(self) -> Program:
        program = Program(body=[])

        try:
            while self.current_token and self.current_token.token != 'gameOver':
                self.skip_whitespace()
                if self.current_token and re.match(r'^id\d+$', self.current_token.token):
                    la_token = self.look_ahead()
                    if la_token is not None and la_token.token in [':',',']:  
                        program.body.append(self.parse_var_init("global"))
                    elif la_token is not None and la_token.token == '[':  
                        program.body.append(self.parse_array("global"))
                    else:
                        raise ParserError(f"Unexpected token found during parsing: {la_token.token}")
                elif self.current_token and self.current_token.token in ['hp','xp','comms','flag']:
                    program.body.append(self.var_or_arr("global"))
                elif self.current_token and self.current_token.token == 'immo':
                    program.body.append(self.parse_immo("global"))
                    self.current_token = self.get_next_token()
                elif self.current_token and self.current_token.token == 'generate':
                    program.body.append(self.parse_func())
                    self.current_token = self.get_next_token()
                elif self.current_token and self.current_token.token == 'build':
                    program.body.append(self.parse_globalstruct())
                elif self.current_token and self.current_token.token == 'play':
                    program.body.append(self.parse_func())
                    self.current_token = self.get_next_token()
                else:
                    raise ParserError(f"Unexpected token found during parsing: {self.current_token.token}")
                
            if self.globalstruct:
                raise ParserError(f"StructError: Global struct '{self.globalstruct[0]}' was declared but not initialized.")
                
        except ParserError as e:
            return e, self.symbol_table
        except SemanticError as e:
            return e, self.symbol_table
        except SymbolTableError as e:
            return e, self.symbol_table
        
        return program, self.symbol_table
    
    def parse_func(self) -> PlayFunc:
        self.skip_whitespace()

        if not self.current_token or self.current_token.token != "play":
            raise ParserError("Expected function declaration keyword 'play'.")

        if self.current_token and self.current_token.token == 'play':
            self.current_token = self.get_next_token() # eat play
            self.current_token = self.get_next_token() # eat (
            self.skip_whitespace()
            self.current_token = self.get_next_token() # eat )
            self.skip_whitespace()
            self.current_token = self.get_next_token() # eat {

        body = []
        while self.current_token and self.current_token.token != "}":
            stmt = self.parse_stmt('play')
            body.append(stmt)
            self.skip_whitespace()

        self.expect("}", "Expected '}' to close function body.")

        return PlayFunc(body=BlockStmt(statements=body))

    def parse_stmt(self, scope) -> Stmt:
        self.skip_whitespace()

        if self.current_token and re.match(r'^id\d+$', self.current_token.token):
            la_token = self.look_ahead()
            if la_token is not None and la_token.token in [':',',']:  
                return self.parse_var_init(scope)
            elif la_token is not None and la_token.token == '[':  
                return self.parse_array(scope)
            elif la_token is not None and la_token.token == '.':  
                return self.parse_inst_ass(scope)
            else:
                raise ParserError(f"Unexpected token found during parsing: {la_token.token}")
        elif self.current_token and self.current_token.token in ['hp','xp','comms','flag']:
            return self.var_or_arr(scope)
        elif self.current_token and self.current_token.token == 'build':
            return self.parse_struct(scope)
        elif self.current_token and self.current_token.token == 'access':
            return self.parse_struct_inst(scope)
        elif self.current_token and self.current_token.token == 'immo':
            return self.parse_immo(scope)
        else:
            raise ParserError(f"Unexpected token found during parsing: {self.current_token.token}")
    
    ######### ARRAYS AND VARIABLES #########
    
    def var_or_arr(self, scope):
        datatype = self.current_token.token  

        self.current_token = self.get_next_token()
        self.skip_whitespace()

        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise ParserError("Expected variable name.")
        
        la_token = self.look_ahead()
        if la_token is not None and la_token.token == '[':  
            return self.parse_empty_array(datatype, scope)
        else:
            return self.parse_var_dec(datatype, scope)

    def parse_var_init(self, scope) -> Union[VarDec, BatchVarDec, VarAssignment]:
        self.skip_whitespace()

        var_names = [Identifier(symbol=self.current_token.lexeme)]  
        name = self.current_token.lexeme
        self.current_token = self.get_next_token() # eat id
        self.skip_whitespace()

        while self.current_token and self.current_token.token == ",":
            self.current_token = self.get_next_token()  # eat ,
            self.skip_whitespace()

            if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise ParserError("Expected variable name after ','.")

            var_names.append(Identifier(symbol=self.current_token.lexeme))
            self.current_token = self.get_next_token() # eat id
            self.skip_whitespace()
            
            if self.current_token and self.current_token.token == ":":
                self.current_token = self.get_next_token() # eat :
                self.skip_whitespace()

                value = self.parse_expr()
                evaluated_val = evaluate(value, self.symbol_table, scope)

                for var in var_names:
                    self.symbol_table.define_def_variable(var.symbol, evaluated_val)

                self.skip_whitespace()
                return BatchVarDec(declarations=[VarDec(name=var, value=value) for var in var_names])
        
        self.current_token = self.get_next_token() # eat :
        self.skip_whitespace() 

        value = self.parse_expr()
        evaluated_val = evaluate(value, self.symbol_table, scope)
        expected_type = type(evaluated_val)  

        values_table={name: {"values": value, "eval_values": evaluated_val}}

        while self.current_token and self.current_token.token == ",":
            self.current_token = self.get_next_token()  
            self.skip_whitespace()

            if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise ParserError("Expected variable name after ','.")

            var_names.append(Identifier(symbol=self.current_token.lexeme))
            variable_name = self.current_token.lexeme
            self.current_token = self.get_next_token()
            self.skip_whitespace()

            if not self.current_token or self.current_token.token != ":":
                raise ParserError("Expected ':' in variable initialization.")
            
            self.current_token = self.get_next_token()
            self.skip_whitespace()

            value = self.parse_expr()
            evaluated_val = evaluate(value, self.symbol_table, scope)
            values_table[variable_name] = {"values": value, "eval_values": evaluated_val}

            if type(evaluated_val) != expected_type:
                raise SemanticError(f"TypeMismatchError: Expected {expected_type.__name__}, but got {type(evaluated_val).__name__} in '{variable_name}'.")

        self.skip_whitespace()
        if len(var_names) > 1:
            for var in var_names:
                self.symbol_table.define_def_variable(var.symbol, values_table[var.symbol]["eval_values"],scope)
            return BatchVarDec(declarations=[VarDec(name=var, value=values_table[var.symbol]["values"]) for var in var_names])
        else:
            var = var_names[0]
            if self.symbol_table.check_var(var.symbol,scope):
                if scope == "global":
                    raise ParserError(f"AssignmentError: Assignment statement cannot be done globally for global variable: '{var.symbol}'.")
                self.symbol_table.define_variable(var.symbol, evaluated_val, scope)
                return VarAssignment(var, ':', value)
            else:
                self.symbol_table.define_variable(var.symbol, evaluated_val, scope)
                return VarDec(var, value)  

    def parse_var_dec(self, datatype, scope) -> Union[VarDec, BatchVarDec]:
        var_names = []
        
        while True:
            var_names.append(Identifier(symbol=self.current_token.lexeme))
            self.current_token = self.get_next_token()
        
            while self.current_token and self.current_token.token == 'space':
                self.current_token = self.get_next_token()

            if self.current_token and self.current_token.token == ",":
                self.current_token = self.get_next_token()
                self.skip_whitespace()
            else:
                break  
        value = None 
       
        if self.current_token and self.current_token.token == 'newline':
            if datatype == 'hp':
                value = 0
            elif datatype == 'xp':
                value = 0.0
            elif datatype == 'comms':
                value = ''
            elif datatype == 'flag':
                value = False
            else:
                raise ParserError(f"Unknown data type '{datatype}'.")
            
            for var in var_names:
                self.symbol_table.define_def_variable(var.symbol, value, scope)

        elif self.current_token and self.current_token.token == ':':
            self.current_token = self.get_next_token()
            self.skip_whitespace()

            if not self.current_token or self.current_token.token != 'dead':
                raise ParserError("Expected 'dead' after ':'.")

            value = None  
            self.current_token = self.get_next_token()  
            for var in var_names:
                self.symbol_table.define_dead_variable(var.symbol, datatype, scope)

        self.skip_whitespace()

        if len(var_names) > 1:
            var_declarations = [VarDec(name=var, value=value) for var in var_names]
            return BatchVarDec(declarations=var_declarations)
        else:
            return VarDec(name=var_names[0], value=value)
 
    def parse_empty_array(self, datatype,scope) -> ArrayDec:
        arr_name = Identifier(symbol=self.current_token.lexeme)
        self.current_token = self.get_next_token()
        self.skip_whitespace()
        dimensions = []
        values = []

        while self.current_token and self.current_token.token == '[':
            self.current_token = self.get_next_token() #eat [
            self.skip_whitespace()
            if self.current_token and self.current_token.token == 'hp_ltr':
                dimensions.append(int(self.current_token.lexeme))
                self.current_token = self.get_next_token()
            else:
                dimensions.append(None)
            self.skip_whitespace()
            self.expect("]", "Expected ']' to close array dimension declaration.")
            self.skip_spaces()

        if self.current_token and self.current_token.token == 'newline':
            default_value = {
                'hp': HpLiteral(0),
                'xp': XpLiteral(0.0),
                'comms': CommsLiteral(''),
                'flag': FlagLiteral(False)
            }.get(datatype, None)

            if default_value is None:
                raise ParserError(f"Unknown data type '{datatype}'.")
            
            if len(dimensions) == 2:
                if dimensions[0] is None and dimensions[1] is None:
                    values = []  # arr[][]
                    eval_values = []

                elif dimensions[0] is None and dimensions[1] is not None:
                    values = [default_value] * dimensions[1]  # arr[][int]
                    eval_values = [default_value.value] * dimensions[1]

                elif dimensions[0] is not None and dimensions[1] is None:
                    values = [[] for _ in range(dimensions[0])]  # arr[int][]
                    eval_values = [[] for _ in range(dimensions[0])]

                elif dimensions[0] is not None and dimensions[1] is not None:
                    values = [[default_value] * dimensions[1] for _ in range(dimensions[0])]  # arr[int][int]
                    eval_values = [[default_value.value] * dimensions[1] for _ in range(dimensions[0])] 
            else:
                if dimensions[0] is None:
                    values = []  # arr[]
                    eval_values = []
                else:
                    values = [default_value] * dimensions[0]
                    eval_values = [default_value.value] * dimensions[0]
            
            self.symbol_table.define_dead_array(arr_name.symbol, dimensions, eval_values, datatype, scope)

        elif self.current_token and self.current_token.token == ':':
            self.current_token = self.get_next_token() #eat :
            self.skip_spaces()

            self.expect("dead", "Expected 'dead' after ':'.")

            if len(dimensions) == 2:
                if dimensions[0] is None and dimensions[1] is None:
                    values = None  # arr[][]
                else:
                    raise ParserError("NullPointerError: Null arrays cannot be initialized with specific size.")
            else:
                if dimensions[0] is None:
                    values = None  # arr[]
                else:
                    raise ParserError("NullPointerError: Null arrays cannot be initialized with specific size.")
            
            self.symbol_table.define_dead_array(arr_name.symbol, dimensions, values, datatype, scope)
        
        
        return ArrayDec(arr_name, dimensions, values)

    def parse_array(self, scope) -> Union[ArrayDec, ArrAssignment]:
        self.skip_whitespace()

        arr_name = Identifier(symbol=self.current_token.lexeme)
        self.current_token = self.get_next_token() # eat id
        self.skip_whitespace()
        dimensions = []

        while self.current_token and self.current_token.token == '[':
            self.current_token = self.get_next_token() #eat [
            self.skip_whitespace()
            if self.current_token and self.current_token.token == 'hp_ltr':
                dimensions.append(int(self.current_token.lexeme))
                self.current_token = self.get_next_token()
            else:
                dimensions.append(None)
            self.skip_whitespace()
            self.expect("]", "Expected ']' to close array dimension declaration.")
            self.skip_whitespace()

        is_modification, scope = self.symbol_table.check_array(arr_name.symbol, scope)

        self.expect(":", "Expected ':' in array initialization or modification.")
        self.skip_whitespace()

        if is_modification:
            if self.symbol_table.check_dead_array(arr_name.symbol, scope):
                existing_dimensions = self.symbol_table.get_array_dimensions(arr_name.symbol,scope)
                if len(existing_dimensions) != len(dimensions):
                    raise ParserError(f"ArrayIndexError: Incorrect number of dimensions for '{arr_name.symbol}'.")
                
                values, eval_values = self.parse_array_values(expected_dims=dimensions, depth=0, scope=scope)
                if all(dim is None for dim in dimensions):
                    if isinstance(values[0], list):  
                        dimensions = [len(values), len(values[0])]
                    else:  
                        dimensions = [len(values)]
                self.symbol_table.define_array(arr_name.symbol, dimensions, eval_values, scope, True)
                return ArrayDec(arr_name, dimensions, values)
            else: 
                if all(dim is not None for dim in dimensions):
                    existing_dimensions = self.symbol_table.get_array_dimensions(arr_name.symbol, scope)
                    if len(existing_dimensions) != len(dimensions):
                        raise ParserError(f"ArrayIndexError: Incorrect number of dimensions for '{arr_name.symbol}'.")
                    for i, dim in enumerate(dimensions):
                        if dim is not None and dim >= existing_dimensions[i]:
                            raise SemanticError(f"ArrayIndexError: Index {dim} is out of bounds for dimension {i} in '{arr_name.symbol}'.")
                    
                    value = self.parse_expr()
                    evaluated_val = evaluate(value, self.symbol_table, scope)
                    self.symbol_table.modify_array(arr_name.symbol, dimensions, evaluated_val, scope)
                    return ArrAssignment(arr_name, ':', value)
                else:
                    raise ParserError(f"DeclarationError: Array '{arr_name.symbol}' is already defined.")
        else:
            values, eval_values = self.parse_array_values(expected_dims=dimensions, depth=0, scope=scope)
            if all(dim is None for dim in dimensions):
                if isinstance(values[0], list):  
                    dimensions = [len(values), len(values[0])]
                else:  
                    dimensions = [len(values)]
            
            self.symbol_table.define_array(arr_name.symbol, dimensions, eval_values, scope=scope)
            return ArrayDec(arr_name, dimensions, values)

    def parse_array_values(self, expected_dims, depth, scope):
        values = []
        eval_values = []
        
        if expected_dims[depth] is None or isinstance(expected_dims[depth], int):
            while self.current_token and self.current_token.token != 'newline':
                if depth + 1 < len(expected_dims):  # 2d array
                    self.expect("[", "Expected '[' for nested array values.")
                    self.skip_whitespace()
                    res_val, res_eval = self.parse_array_values(expected_dims, depth + 1, scope)
                    values.append(res_val)
                    eval_values.append(res_eval)
                    self.expect("]", "Expected ']' to close nested array values.")
                else:  
                    value = self.parse_expr()
                    eval_value = evaluate(value, self.symbol_table, scope)
                    if value.kind not in ["HpLiteral", "XpLiteral", "CommsLiteral", "FlagLiteral"]:
                        raise ParserError("Arrays can only be initialied with literal values.")
                    values.append(value)
                    eval_values.append(eval_value)

                
                self.skip_whitespace()
                if self.current_token.token == ',':
                    self.current_token = self.get_next_token()  # eat ,
                    self.skip_whitespace()
                else:
                    break
        
        if expected_dims[depth] is not None and len(values) != expected_dims[depth]:
            raise SemanticError(
                f"ArraySizeError: Expected {expected_dims[depth]} elements, but got {len(values)}."
            )

        return values, eval_values
  
    ############ STRUCTS ###############

    def parse_globalstruct(self) -> Union[StructDec, GlobalStructDec]:
        self.current_token = self.get_next_token() # eat build
        self.skip_whitespace()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise ParserError("Expected struct name after 'build'.")
        struct_name = Identifier(self.current_token.lexeme)
        self.current_token = self.get_next_token() # eat id
        self.skip_whitespace()
        if self.current_token.token == '{':
            for item in self.globalstruct:
                if item == struct_name.symbol:
                    self.globalstruct.remove(item)
                    return self.create_struct(struct_name, "global")
                
            raise ParserError(f"StructError: Global struct '{struct_name.symbol}' was not declared.")
        else:
            if struct_name.symbol in self.globalstruct:
                raise ParserError(f"StructError: Global struct '{struct_name.symbol}' was already declared.")
            self.globalstruct.append(struct_name.symbol)
            return GlobalStructDec(struct_name)
    
    def parse_struct(self, scope) -> StructDec:
        self.current_token = self.get_next_token() # eat build
        self.skip_whitespace()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise ParserError("Expected struct name after 'build'.")
        struct_name = Identifier(self.current_token.lexeme)
        self.current_token = self.get_next_token() # eat id
        self.skip_whitespace()
        return self.create_struct(struct_name, scope)
    
    def create_struct(self, struct_name, scope) -> StructDec:
        fields_table = {}
        fields = []
        self.expect("{","StructDeclarationError: Struct fields must be enclosed in curly braces.")
        self.skip_whitespace()
        while self.current_token and self.current_token.token != '}':
            datatype = self.current_token.token  
            self.current_token = self.get_next_token()  # eat datatype
            self.skip_whitespace()
            field_name = Identifier(self.current_token.lexeme)  
            self.current_token = self.get_next_token()  # eat id
            self.skip_whitespace()
            value = None  
            if self.current_token.token == ':':  
                self.current_token = self.get_next_token()  # eat :
                self.skip_whitespace()
                value = self.parse_expr()  
                eval_val = evaluate(value, self.symbol_table, scope)  
                fields.append(StructFields(field_name, value))  
                if field_name.symbol in fields_table:
                    raise ParserError(f"FieldError: Duplicate field name detected: '{field_name.symbol}'.")
                fields_table[field_name.symbol] = {
                    "datatype": datatype,
                    "value": eval_val
                }
                self.skip_whitespace()
            else:
                fields.append(StructFields(field_name, None))
                if field_name.symbol in fields_table:
                    raise ParserError(f"FieldError: Duplicate field name detected: '{field_name.symbol}'.")
                fields_table[field_name.symbol] = {
                    "datatype": datatype,
                    "value": None
                }
            if self.current_token and self.current_token.token == ',':
                self.current_token = self.get_next_token()  # eat ,
                self.skip_whitespace()
        self.current_token = self.get_next_token() # eat }
        self.skip_whitespace()

        self.symbol_table.define_struct(struct_name.symbol, fields_table, scope)
        return StructDec(struct_name, fields)
    
    def parse_struct_inst(self, scope) -> StructInst:
        self.current_token = self.get_next_token()  # eat 'access'
        self.skip_whitespace()
        
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise ParserError("Expected struct name after 'access'.")

        struct_parent = self.current_token.lexeme

        result, parent_scope = self.symbol_table.check_struct(struct_parent, scope)
        if not result:
            raise ParserError(f"Struct '{struct_parent}' is not defined.")
        
        field_table = self.symbol_table.get_fieldtable(struct_parent, parent_scope)

        self.current_token = self.get_next_token()  # eat id
        self.skip_spaces()
        
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise ParserError("Expected struct instance name after struct name.")
        
        inst_name = Identifier(self.current_token.lexeme)
        self.current_token = self.get_next_token()  # eat id
        self.skip_spaces()

        values, eval_values = [], []
        if self.current_token.token == ':':
            self.current_token = self.get_next_token()  # eat ':'
            self.skip_spaces()
   
            while self.current_token.token != ',':
                value = self.parse_expr()
                eval_val = evaluate(value, self.symbol_table, scope)
                values.append(value)
                eval_values.append(eval_val)
                self.skip_spaces()
                if self.current_token.token == ',':
                    self.current_token = self.get_next_token()  # eat ','
                    self.skip_spaces()
                    if self.current_token.token == 'newline':
                        raise ParserError("Unexpected newline found after struct instance value.")
                elif self.current_token.token == 'newline':
                    break
        return self.create_struct_instance(inst_name, struct_parent, field_table, values, eval_values, scope)

    def create_struct_instance(self, inst_name, struct_parent, field_table, values, eval_values, scope):
        struct_fields = []
        new_field_table = {}
        field_names = list(field_table.keys())

        if len(eval_values) > len(field_names):
            raise ParserError(f"Too many values provided for struct '{struct_parent}'. Expected {len(field_names)}, got {len(eval_values)}.")

        for i, field in enumerate(field_names):
            expected_type = field_table[field]["datatype"]
            default_value = field_table[field]["value"]

            if i < len(eval_values):  
                actual_type_name = self.TYPE_MAP.get(type(eval_values[i]), None)
                if actual_type_name != expected_type:
                    raise ParserError(f"FieldTypeError: Type mismatch for field '{field}'. Expected '{expected_type}', but got '{actual_type_name}'.")
                
                value_to_use = eval_values[i]
                struct_fields.append(StructFields(field, values[i]))  
            else:  
                value_to_use = default_value if default_value is not None else None
                struct_fields.append(StructFields(field, self.get_default_literal(default_value)))

            new_field_table[field] = {"datatype": expected_type, "value": value_to_use}

        self.symbol_table.define_structinst(inst_name.symbol, new_field_table, scope)
        return StructInst(inst_name, struct_parent, struct_fields)

    def get_default_literal(self, value):
        type_literals = {str: CommsLiteral, int: HpLiteral, float: XpLiteral, bool: FlagLiteral}
        return type_literals.get(type(value), lambda x: x)(value) if value is not None else None
        
    def parse_inst_ass(self, scope) -> InstAssignment:
        struct_inst_name = Identifier(self.current_token.lexeme)
        self.symbol_table.check_structinst(self.current_token.lexeme, scope)
        self.current_token = self.get_next_token() # eat id
        if self.current_token.token != '.':
            raise ParserError("Expected '.' after struct instance name.")
        self.current_token = self.get_next_token() # eat .
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise ParserError("Expected struct instance field name after struct instance name.")
        inst_field_name = Identifier(self.current_token.lexeme)
        self.symbol_table.check_structinst_field(struct_inst_name.symbol, self.current_token.lexeme, scope)
        left = StructInstField(struct_inst_name, inst_field_name)
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        self.expect(":","Expected ':' after struct instance field name.")
        self.skip_spaces()
        value = self.parse_expr()
        eval = evaluate(value, self.symbol_table, scope)
        self.symbol_table.modify_structinst_field(struct_inst_name.symbol, inst_field_name.symbol, eval, scope)
        
        return InstAssignment(left, ':', value)
    
    ############ IMMO ##############

    def parse_immo(self, scope):
        self.current_token = self.get_next_token() # eat immo
        self.skip_spaces()
        if self.current_token.token == 'access':
            immo_inst = self.parse_immo_inst(scope)
            return immo_inst
        else:
            if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise ParserError("Expected identifier or 'access' after 'immo'.")
            la_token = self.look_ahead()
            if la_token is not None and la_token.token in [':',',']:  
                immo_var = self.parse_immo_var(scope)  
                return immo_var
            elif la_token is not None and la_token.token == '[':  
                immo_arr = self.parse_immo_arr(scope)
                return immo_arr
            else:
                raise ParserError(f"bruh")  
            
    def parse_immo_var(self, scope) -> Union[ImmoVarDec, BatchImmoVarDec]:
        immo_declarations = [] 
        first_type = None
        while True:
            identifiers = [Identifier(self.current_token.lexeme)]
            if self.symbol_table.check_var(identifiers[0].symbol, scope):
                raise ParserError(f"DeclarationError: Variable '{identifiers[0].symbol}' is already defined.")
            self.current_token = self.get_next_token()  # eat id
            self.skip_spaces()

            while self.current_token.token == ',':
                self.current_token = self.get_next_token()  # eat ,
                self.skip_spaces()
                if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                    raise ParserError("Expected identifier after ',' in immutable variable declaration.")
                if self.symbol_table.check_var(self.current_token.lexeme, scope):
                    raise ParserError(f"DeclarationError: Variable '{self.current_token.lexeme}' is already defined.")
                identifiers.append(Identifier(self.current_token.lexeme))
                self.current_token = self.get_next_token()  # eat id
                self.skip_spaces()

            self.expect(":", "Expected ':' after immutable variable name.")
            self.skip_spaces()
            value = self.parse_expr()
            evaluated_val = evaluate(value, self.symbol_table, scope)
            value_type = self.TYPE_MAP.get(type(evaluated_val), None)
            self.skip_spaces()

            if len(identifiers) > 1:
                for immo_name in identifiers:
                    self.symbol_table.define_immo_variable(immo_name.symbol, evaluated_val, scope)
                    immo_declarations.append(ImmoVarDec(immo_name, value))
                break
            else:
                if first_type is None:
                    first_type = value_type
                elif first_type != value_type:
                    raise ParserError(f"TypeMismatchError: Expected all values to be '{first_type}', but got '{value_type}'.")

                self.symbol_table.define_immo_variable(identifiers[0].symbol, evaluated_val, scope)
                immo_declarations.append(ImmoVarDec(identifiers[0], value))  
                self.skip_spaces()
                if self.current_token.token == ',':  
                    self.current_token = self.get_next_token()  # eat ,
                    self.skip_spaces()
                else:
                    break
        
        if len(immo_declarations) > 1:
            return BatchImmoVarDec(declarations=immo_declarations)
        else:
            return immo_declarations[0]
    
    def parse_immo_arr(self, scope) -> ImmoArrayDec:
        arr_name = Identifier(self.current_token.lexeme)
        res, scope = self.symbol_table.check_array(arr_name.symbol, scope)
        if res:
            raise ParserError(f"DeclarationError: Array '{arr_name.symbol}' is already defined.")
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        dimensions, values, eval_values = [], [], []
        self.expect("[","Expected '[' to start immutable array declaration.")
        self.skip_spaces()
        dim = int(self.current_token.lexeme)
        if dim < 2:
            raise ParserError(f"ArraySizeError: Expected array size to be greater than 1, but got {dim}.")
        dimensions.append(dim)
        self.current_token = self.get_next_token() # eat hp_ltr
        self.skip_spaces()
        self.expect("]","Expected ']' to close immutable array declaration.")
        self.skip_spaces()
        if self.current_token.token == '[':
            self.current_token = self.get_next_token()
            self.skip_spaces()
            dim = int(self.current_token.lexeme)
            if dim < 2:
                raise ParserError(f"ArraySizeError: Expected array size to be greater than 1, but got {dim}.")
            dimensions.append(dim)
            self.current_token = self.get_next_token() # eat hp_ltr
            self.skip_spaces()
            self.expect("]","Expected ']' to close immutable array declaration.")
            self.skip_spaces()
        self.expect(":","Expected ':' after immutable array declaration.")
        self.skip_spaces()
        first_type = None
        if len(dimensions) == 1:
            while self.current_token.token != "]":
                value = self.parse_expr()
                evaluated_val = evaluate(value, self.symbol_table, scope)
                value_type = self.TYPE_MAP.get(type(evaluated_val), None)
                if first_type is None:
                    first_type = value_type
                elif first_type != value_type:
                    raise ParserError(f"TypeMismatchError: Expected all elements to be '{first_type}', but got '{value_type}'.")
                values.append(value)
                eval_values.append(evaluated_val)
                self.skip_spaces()
                if self.current_token.token == ",":
                    self.current_token = self.get_next_token()  # eat ,
                    self.skip_spaces()
                else:
                    break
            if len(eval_values) != dimensions[0]:
                    raise ParserError(f"ArraySizeError: Expected {dimensions[0]} elements, but got {len(eval_values)}.")
        elif len(dimensions) == 2:
            while True:  
                row_values, row_eval_values = [], []
                self.expect("[", "Expected '[' to start a row in the immutable array.")
                self.skip_spaces()
                while self.current_token.token != "]":
                    value = self.parse_expr()
                    evaluated_val = evaluate(value, self.symbol_table)
                    value_type = self.TYPE_MAP.get(type(evaluated_val), None)
                    if first_type is None:
                        first_type = value_type
                    elif first_type != value_type:
                        raise ParserError(f"TypeMismatchError: Expected all elements to be '{first_type}', but got '{value_type}'.")
                    row_values.append(value)
                    row_eval_values.append(evaluated_val)
                    self.skip_spaces()
                    
                    if self.current_token.token == ",":
                        self.current_token = self.get_next_token()  # eat ,
                        self.skip_spaces()
                    else:
                        break  
                self.expect("]", "Expected ']' to close a row in the immutable array.")
                self.skip_spaces()
                if len(row_eval_values) != dimensions[1]:
                    raise ParserError(f"ArraySizeError: Expected {dimensions[1]} elements per row, but got {len(row_eval_values)}.")
                values.append(row_values)
                eval_values.append(row_eval_values)
                if self.current_token.token == ",":
                    self.current_token = self.get_next_token()  # eat ,
                    self.skip_spaces()
                else:
                    break  

            if len(eval_values) != dimensions[0]:
                raise ParserError(f"ArraySizeError: Expected {dimensions[0]} rows, but got {len(eval_values)}.")
        self.symbol_table.define_immo_array(arr_name.symbol, dimensions, eval_values, scope)
        return ImmoArrayDec(arr_name, dimensions, values)
    
    def parse_immo_inst(self, scope) -> ImmoInstDec:
        self.current_token = self.get_next_token()  # eat 'access'
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise ParserError("Expected struct name after 'access'.")
        struct_parent = self.current_token.lexeme
        res, parent_scope = self.symbol_table.check_struct(struct_parent, scope)
        if not res:
            raise ParserError(f"Struct '{struct_parent}' is not defined.")
        field_table = self.symbol_table.get_fieldtable(struct_parent, parent_scope)
        self.current_token = self.get_next_token()  # eat id
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise ParserError("Expected struct instance name after struct name.")
        inst_name = Identifier(self.current_token.lexeme)
        self.current_token = self.get_next_token()  # eat id
        self.skip_spaces()
        values, eval_values = [], []
        self.expect(":","Expected ':' after struct instance name.")
        self.skip_spaces()
        while self.current_token.token != ",":  
            value = self.parse_expr()
            eval_val = evaluate(value, self.symbol_table, scope)
            values.append(value)
            eval_values.append(eval_val)
            self.skip_spaces()
            if self.current_token.token == ",":
                self.current_token = self.get_next_token()  # eat ','
                self.skip_spaces()
                if self.current_token.token == 'newline':
                    raise ParserError("Unexpected newline found after struct instance value.")
            elif self.current_token.token == 'newline':
                break
        struct_fields = []
        new_field_table = {}
        field_names = list(field_table.keys())

        if len(eval_values) != len(field_names):
            raise ParserError(f"Wrong number of values provided for struct '{struct_parent}'. Expected {len(field_names)}, got {len(eval_values)}.")
        
        for i, field in enumerate(field_names):
            expected_type = field_table[field]["datatype"]

            actual_type_name = self.TYPE_MAP.get(type(eval_values[i]), None)
            if actual_type_name != expected_type:
                raise ParserError(f"FieldTypeError: Type mismatch for field '{field}'. Expected '{expected_type}', but got '{actual_type_name}'.")
                
            value_to_use = eval_values[i]
            struct_fields.append(StructFields(field, values[i]))  
            new_field_table[field] = {"datatype": expected_type, "value": value_to_use}

        self.symbol_table.define_immo_structinst(inst_name.symbol, new_field_table, scope)
        return ImmoInstDec(inst_name, struct_parent, struct_fields) 
    
    ############ EXPRESSIONS ##############

    def parse_expr(self) -> Expr:
        self.skip_spaces()
        return self.parse_additive_expr()

    def parse_additive_expr(self) -> Expr:
        self.skip_spaces()
        left = self.parse_multiplicative_expr()

        while self.current_token and self.current_token.token in '+-':
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            right = self.parse_multiplicative_expr()
            left = BinaryExpr(left=left, right=right, operator=operator)
        return left

    def parse_multiplicative_expr(self) -> Expr:
        self.skip_spaces()
        left = self.parse_primary_expr()

        while self.current_token and self.current_token.token in ["/", "*", "%"]:
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            right = self.parse_primary_expr()
            left = BinaryExpr(left=left, right=right, operator=operator)  

        return left  

    def parse_primary_expr(self) -> Expr:
        self.skip_spaces()
        if not self.current_token:
            raise ParserError("Unexpected end of input during parsing!")
        
        tk = self.current_token.token

        if re.match(r'^id\d+$', tk):
            tk= 'id'

        if tk == 'id':
            identifier = Identifier(symbol=self.current_token.lexeme)
            self.current_token = self.get_next_token()
            self.skip_spaces()
            return identifier
        elif tk == 'hp_ltr' or tk == 'nhp_ltr':
            literal = HpLiteral(value=self.current_token.lexeme)
            self.current_token = self.get_next_token()
            self.skip_spaces()
            return literal
        elif tk == 'xp_ltr' or tk == 'nxp_ltr':
            literal = XpLiteral(value=self.current_token.lexeme)
            self.current_token = self.get_next_token()
            self.skip_spaces()
            return literal
        elif tk == 'comms_ltr':
            value = re.sub(r'^"(.*)"$', r'\1', self.current_token.lexeme)
            literal = CommsLiteral(value)
            self.current_token = self.get_next_token()
            self.skip_spaces()
            return literal
        elif tk == 'flag_ltr':
            lexeme = self.current_token.lexeme 
            if lexeme == 'true':
                value = True
            else:
                value = False
            literal = FlagLiteral(value)
            self.current_token = self.get_next_token()
            self.skip_spaces()
            return literal
        elif tk == '(':
            self.current_token = self.get_next_token()
            self.skip_spaces()
            value = self.parse_expr()  
            
            self.expect(')', "Unexpected token found inside parenthesised expression. Expected closing parenthesis.")
            self.skip_spaces()
            return value

        else:
            raise ParserError(f"Unexpected token found during parsing: {tk}")

def check(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()

    if error:
        return 'Lexical errors found, cannot continue with syntax analyzing. Please check lexer tab.', {}

    result = parse(fn, text)

    if result != 'No lexical errors found!Valid syntax.':
        return 'Syntax errors found, cannot continue with semantic analyzing. Please check syntax tab.', {}

    semantic = Semantic(tokens)
    
    result, table = semantic.produce_ast()
    return result, table

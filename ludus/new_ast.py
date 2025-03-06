from .lexer import Lexer
from .nodes import *
from .parser import parse
import re
from typing import Union
from .runtime.traverser import ASTVisitor, SemanticAnalyzer
from .error import SemanticError

class Semantic:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        self.current_token = self.get_next_token()
        self.var_list = {"global": []} 
        self.arr_list = {"global": {}} 
        self.struct_list = {"global": []}
        self.struct_inst_list = {}
        self.globalstruct = []
        self.scope_stack = [{}]
    
    TYPE_MAP = {
        int: "hp",
        float: "xp",
        str: "comms",
        bool: "flag"
    }

    def push_scope(self):
        self.scope_stack.append({})

    def pop_scope(self):
        if len(self.scope_stack) > 1:  
            self.scope_stack.pop()
        else:
            raise SemanticError("Attempted to pop global scope")

    def declare_id(self, name, type, dimensions=0):
        current_scope = self.scope_stack[-1]
        if name in current_scope:
            raise SemanticError(f"NameError: Identifier '{name}' is already defined in this scope.")
        current_scope[name] = {
            "type": type,
            "dimensions": dimensions
        } 
    
    def lookup_identifier(self, name):
        for scope in reversed(self.scope_stack):
            if name  in scope:
                return True
        return False
    
    def lookup_id_type(self, name, id_type):
        for scope in reversed(self.scope_stack):
            if name  in scope:
                info = self.get_identifier_info(name)
                if info["type"] == id_type:
                    return True
                else:
                    raise SemanticError(f"NameError: Identifier '{name}' is already declared as {info["type"]}.")
        return False
    
    def get_identifier_info(self, name):
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]  
        raise SemanticError(f"Identifier '{name}' not declared")
    
    def is_array(self, name):
        if self.lookup_identifier(name):
            info = self.get_identifier_info(name)
            if info["type"] == "an array":
                return True
            else:
                return False
        else:
            return False
    
    def get_dimensions(self, name):
        info = self.get_identifier_info(name)
        if info["type"] != "an array":
            raise SemanticError(f"Identifier '{name}' is not an array")
        return info["dimensions"]

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
            raise SemanticError(f"Parser Error: {error_message}")
        
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
                    name = self.current_token.lexeme
                    if la_token is not None and la_token.token in [':',',']: 
                        if self.lookup_identifier(name):
                            info = self.get_identifier_info(name)
                            raise SemanticError(f"NameError: Identifier {name}' was "
                                                f"already declared as {info["type"]}.")
                        program.body.append(self.parse_var_init("global"))
                    elif la_token is not None and la_token.token == '[':  
                        if self.lookup_identifier(name):
                            info = self.get_identifier_info(name)
                            raise SemanticError(f"NameError: Identifier {name}' was "
                                                f"already declared as {info["type"]}.")
                        program.body.append(self.parse_array("global"))
                    else:
                        raise SemanticError(f"Unexpected token found during parsing: {la_token.token}")
                elif self.current_token and self.current_token.token in ['hp','xp','comms','flag']:
                    program.body.append(self.var_or_arr("global"))
                elif self.current_token and self.current_token.token == 'immo':
                    program.body.append(self.parse_immo("global"))
                    self.current_token = self.get_next_token()
                elif self.current_token and self.current_token.token == 'build':
                    program.body.append(self.parse_globalstruct())
                elif self.current_token and self.current_token.token == 'play':
                    program.body.append(self.parse_func())
                elif self.current_token and self.current_token.token == 'gameOver':
                    break
                else:
                    raise SemanticError(f"Unexpected token found during parsing: {self.current_token.token}")
            if self.globalstruct:
                raise SemanticError(f"StructError: Global struct '{self.globalstruct[0]}' was declared but not initialized.")
        
        except SemanticError as e:
            return e
        return program
                
    def parse_func(self) -> PlayFunc:
        self.skip_whitespace()
        self.push_scope()
        if not self.current_token or self.current_token.token != "play":
            raise SemanticError("Expected function declaration keyword 'play'.")

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
        self.pop_scope()
        return PlayFunc(body=BlockStmt(statements=body))
    
    def parse_stmt(self, scope) -> Stmt:
        self.skip_whitespace()

        if self.current_token and re.match(r'^id\d+$', self.current_token.token):
            la_token = self.look_ahead()
            if la_token is not None and la_token.token in [':',',']:  
                return self.parse_var_init(scope)
            elif la_token is not None and la_token.token in ['+=','-=','*=', '/=', '%=']: 
                return self.parse_var_ass(scope)
            elif la_token is not None and la_token.token == '[':  
                return self.parse_array(scope)
            elif la_token is not None and la_token.token == '.':  
                return self.parse_inst_ass(scope)
            else:
                raise SemanticError(f"Unexpected token found during parsing: {la_token.token}")
        elif self.current_token and self.current_token.token in ['hp','xp','comms','flag']:
            return self.var_or_arr(scope)
        elif self.current_token and self.current_token.token == 'build':
            return self.parse_struct(scope)
        elif self.current_token and self.current_token.token == 'access':
            return self.parse_struct_inst(scope)
        elif self.current_token and self.current_token.token == 'immo':
            return self.parse_immo(scope)
        elif self.current_token and self.current_token.token == 'if':
            return self.parse_if(scope)
        elif self.current_token and self.current_token.token == 'flank':
            return self.parse_flank(scope)
        else:
            raise SemanticError(f"Unexpected token found during parsing: {self.current_token.token}")

    ######### ARRAYS AND VARIABLES #########    
    def var_or_arr(self, scope) -> Union[VarDec, ArrayDec]:
        datatype = self.current_token.token  
        self.current_token = self.get_next_token()
        self.skip_spaces()

        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise SemanticError("Expected variable name.")
    
        la_token = self.look_ahead()
        name = self.current_token.lexeme
        if la_token is not None and la_token.token == '[':  
            if self.lookup_identifier(name):
                info = self.get_identifier_info(name)
                raise SemanticError(f"NameError: Identifier {name}' was "
                                    f"already declared as {info["type"]}.")
            return self.parse_empty_array(datatype, scope)
        else:
            if self.lookup_identifier(name):
                info = self.get_identifier_info(name)
                raise SemanticError(f"NameError: Identifier {name}' was "
                                    f"already declared as {info["type"]}.")
            return self.parse_var_dec(datatype, scope)
    
    def parse_var_init(self, scope) -> Union[VarDec, BatchVarDec, VarAssignment]:
        var_names = [Identifier(symbol=self.current_token.lexeme)]  
        name = self.current_token.lexeme
        if self.is_array(name): 
            return self.parse_arr_redec(name, scope)

        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()

        while self.current_token and self.current_token.token == ",":
            self.current_token = self.get_next_token()  # eat ,
            self.skip_spaces()

            if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("Expected variable name after ','.")

            var_names.append(Identifier(symbol=self.current_token.lexeme))
            self.current_token = self.get_next_token() # eat id
            self.skip_spaces()
            
            if self.current_token and self.current_token.token == ":":
                self.current_token = self.get_next_token() # eat :
                self.skip_spaces()
                value = self.parse_expr(scope)

                for var in var_names:
                    if self.lookup_identifier(name):
                        info = self.get_identifier_info(name)
                        raise SemanticError(f"NameError: Identifier {name}' was "
                                            f"already declared as {info["type"]}.")
                    self.declare_id(var.symbol, "a variable")

                self.skip_spaces()
                return BatchVarDec(declarations=[VarDec(var, value, False, scope) for var in var_names])

        self.current_token = self.get_next_token() # eat :
        self.skip_spaces()
        value = self.parse_expr(scope)
        values_table = {name: {"values": value}}
        self.skip_spaces()

        while self.current_token and self.current_token.token == ",":
            self.current_token = self.get_next_token()  # eat ,
            self.skip_spaces()

            if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("Expected variable name after ','.")
            
            var_names.append(Identifier(symbol=self.current_token.lexeme))
            variable_name = self.current_token.lexeme
            self.current_token = self.get_next_token() # eat id
            self.skip_spaces()

            if not self.current_token or self.current_token.token != ":":
                raise SemanticError("Expected ':' in variable initialization.")
            
            self.current_token = self.get_next_token() # eat :
            self.skip_whitespace()

            value = self.parse_expr(scope)
            values_table[variable_name] = {"values": value}

        self.skip_spaces()
        if len(var_names) > 1:
            for var in var_names:
                if self.lookup_identifier(name):
                    info = self.get_identifier_info(name)
                    raise SemanticError(f"NameError: Identifier {name}' was "
                                        f"already declared as {info["type"]}.")
                self.declare_id(var.symbol, "a variable")
            return BatchVarDec(declarations=[VarDec(var, values_table[var.symbol]['values'], False, scope) for var in var_names])
        else:
            var = var_names[0]
            if self.lookup_identifier(var.symbol):
                return VarAssignment(left=var, operator=':', right=value)
            self.declare_id(var.symbol, "a variable")
            return VarDec(var, value, False, scope) 
        
    def parse_var_dec(self, datatype, scope) -> Union[VarDec, BatchVarDec]:
        var_names = []

        while True:
            var_names.append(Identifier(symbol=self.current_token.lexeme))
            self.current_token = self.get_next_token() # eat id
            self.skip_spaces()

            if self.current_token.token == ",":
                self.current_token = self.get_next_token()
                self.skip_spaces()
            else:
                break
        value = None
        if self.current_token and self.current_token.token == 'newline':
            if datatype == 'hp':
                value = HpLiteral(0)
            elif datatype == 'xp':
                value = XpLiteral(0.0)
            elif datatype == 'comms':
                value = CommsLiteral('')
            elif datatype == 'flag':
                value = FlagLiteral(False)
            else:
                raise SemanticError(f"Unknown data type '{datatype}'.")
        elif self.current_token and self.current_token.token == ':':
            self.current_token = self.get_next_token()
            self.skip_spaces()
            self.expect("dead", "Expected 'dead' keyword.")
            value = None  
        self.skip_whitespace()

        if len(var_names) > 1:
            for var in var_names:
                if self.lookup_identifier(var.symbol):
                    info = self.get_identifier_info(var.symbol)
                    raise SemanticError(f"NameError: Identifier {var.symbol}' was "
                                        f"already declared as {info["type"]}.")  
                self.declare_id(var.symbol, "a variable")
            if value != None:
                return BatchVarDec([VarDec(var, value, False, scope) for var in var_names])
            else:
                return BatchVarDec([VarDec(var, DeadLiteral(value, datatype), False, scope) for var in var_names])
        else:
            var = var_names[0]
            if self.lookup_identifier(var.symbol):
                    info = self.get_identifier_info(var.symbol)
                    raise SemanticError(f"NameError: Identifier {var.symbol}' was "
                                        f"already declared as {info["type"]}.")    
            self.declare_id(var.symbol, "a variable")
            if value != None:
                return VarDec(var, value, False, scope)
            else:
                return VarDec(var, DeadLiteral(value, datatype), False, scope)

    def parse_empty_array(self, datatype, scope) -> ArrayDec:
        arr_name = Identifier(symbol=self.current_token.lexeme)
        name = arr_name.symbol
        self.current_token = self.get_next_token()
        self.skip_spaces()
        dimensions = []
        values = []

        while self.current_token and self.current_token.token == '[':
            self.current_token = self.get_next_token() #eat [
            self.skip_spaces()
            if self.current_token and self.current_token.token == 'hp_ltr':
                dimensions.append(int(self.current_token.lexeme))
                self.current_token = self.get_next_token()
            else:
                dimensions.append(None)
            self.skip_spaces()
            self.expect("]", "Expected ']' to close array dimension declaration.")
            self.skip_spaces()
        
        if self.current_token and self.current_token.token == 'newline':
            default_value = {
                'hp': HpLiteral(0),
                'xp': XpLiteral(0.0),
                'comms': CommsLiteral(''),
                'flag': FlagLiteral(False)
            }.get(datatype, None)   

            if len(dimensions) == 2:
                if dimensions[0] is None and dimensions[1] is None:
                    values = [[],[]]  # arr[][]
                elif dimensions[0] is not None and dimensions[1] is not None:
                    values = [[default_value] * dimensions[1] for _ in range(dimensions[0])]  # arr[int][int]
                else:
                    raise SemanticError("DeclarationError: Row and column sizes must both be empty or specified.")
            else:
                if dimensions[0] is None:
                    values = []  # arr[]
                else:
                    values = [default_value] * dimensions[0]

            self.declare_id(name, "an array", len(dimensions))
            return ArrayDec(arr_name, dimensions, values, False, scope, datatype)
        elif self.current_token and self.current_token.token == ':':
            self.current_token = self.get_next_token() #eat :
            self.skip_spaces()
            self.expect("dead", "Expected 'dead' after ':'.")
            if len(dimensions) == 2:
                if dimensions[0] is None and dimensions[1] is None:
                    values = None  # arr[][]
                else:
                    raise SemanticError("NullPointerError: Null arrays cannot be initialized with specific size.")
            else:
                if dimensions[0] is None:
                    values = None  # arr[]
                else:
                    raise SemanticError("NullPointerError: Null arrays cannot be initialized with specific size.")
                
            self.declare_id(name, "an array", len(dimensions))
            return ArrayDec(arr_name, dimensions, values, False, scope, datatype)      
    
    def parse_array(self, scope) -> Union[ArrayDec, ArrAssignment]:
        arr_name = Identifier(symbol=self.current_token.lexeme)
        name= arr_name.symbol
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        arr_exist = self.is_array(name)
        dimensions = []
        
        while self.current_token and self.current_token.token == '[':
            self.current_token = self.get_next_token() #eat [
            self.skip_spaces
            if self.current_token and self.current_token.token == ']':
                if arr_exist:
                    raise SemanticError("AssignmentError: Index must not be blank for array index assignment.")
                dimensions.append(None)
            else:
                dim = self.parse_expr(scope)
                if arr_exist:
                    dimensions.append(dim)
                else:
                    if isinstance(dim, HpLiteral):
                        dimensions.append(dim.value)
                    else:
                        raise SemanticError("DeclarationError: Array size must be an hp literal only.")
                
            self.skip_spaces()
            self.expect("]", "Expected ']' to close array dimension declaration.")
            self.skip_spaces()
            
        if self.current_token.token == ':':
            self.current_token = self.get_next_token() #eat :
            self.skip_spaces()
            if self.current_token and self.current_token.token == '[':
                if arr_exist:
                    raise SemanticError(f"DeclarationError: Array '{name}' was already declared.")
                else:
                    values = self.parse_array_values(dimensions, scope)
                    self.declare_id(name, "an array", len(dimensions))
                    return ArrayDec(arr_name, dimensions, values, False, scope)
            else:
                if arr_exist:
                    if all(dim is not None for dim in dimensions):
                        value = self.parse_expr(scope)
                        lhs = ArrElement(arr_name, dimensions)
                        return ArrAssignment(lhs, ':', value)
                    else:
                        raise SemanticError(f"AssignmentError: Index must not be blank for array index assignment for array name '{arr_name.symbol}'.")
                else:
                    raise SemanticError(f"AssignmentError: Array '{arr_name.symbol}' does not exist.")
        else:
            operator = self.current_token.token
            self.current_token = self.get_next_token() #eat operator
            self.skip_spaces()
            if arr_exist:
                if all(dim is not None for dim in dimensions):
                    value = self.parse_expr(scope)
                    lhs = ArrElement(arr_name, dimensions)
                    return ArrAssignment(lhs, operator, value)
                else:
                    raise SemanticError(f"AssignmentError: Index must not be blank for array index assignment for array name '{arr_name.symbol}'.")
            else:
                raise SemanticError(f"AssignmentError: Array '{arr_name.symbol}' does not exist.")

    def parse_array_values(self, expected_dims, scope):
        values = []
        self.skip_spaces()
        if len(expected_dims) == 2:
            while self.current_token and self.current_token.token != 'newline':
                self.expect("[", "Expected '[' for array values.")
                self.skip_spaces()
                inner_values = self.parse_inner_arr_values(scope)
                values.append(inner_values)
                self.expect("]", "Expected ']' to close array values.")
                self.skip_spaces()
                if self.current_token.token == ',':
                    self.current_token = self.get_next_token()  # eat ,
                    self.skip_spaces()
                else:
                    break
            if expected_dims[0] is not None and len(values) != expected_dims[0]:     
                raise SemanticError(
                    f"ArraySizeError: Expected {expected_dims[0]} elements, but got {len(values)}."
                )
            for row in values:
                if expected_dims[1] is not None and len(row) != expected_dims[1]:
                    raise SemanticError(
                        f"ArraySizeError: Expected {expected_dims[1]} elements, but got {len(row)}."
                    )
        else:
            self.expect("[", "Expected '[' for array values.")
            self.skip_spaces()
            inner_values = self.parse_inner_arr_values(scope)
            values = inner_values
            self.expect("]", "Expected ']' to close array values.")
            self.skip_spaces()
            if self.current_token.token == ',':
                raise SemanticError(
                    f"ArraySizeError: Redeclaring a one-dimensional array with more than one rows."
                )
            
            if expected_dims[0] is not None and len(values) != expected_dims[0]:
                raise SemanticError(
                    f"ArraySizeError: Expected {expected_dims[0]} elements, but got {len(values)}."
                )
        
        return values

    def parse_inner_arr_values(self, scope):
        inner_values = []
        while self.current_token and self.current_token.token != ']':
            value = self.parse_expr(scope)
            if value.kind not in ["HpLiteral", "XpLiteral", "CommsLiteral", "FlagLiteral"]:
                raise SemanticError("Arrays can only be initialied with literal values.")
            inner_values.append(value)
            self.skip_spaces()
            if self.current_token.token == ',':
                self.current_token = self.get_next_token()  # eat ,
                self.skip_spaces()
        return inner_values
   
    def parse_arr_redec(self, name, scope):
        dimensions=self.get_dimensions(name)
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        self.expect(":", "Expected ':' after array name for array re-decleration.")
        self.skip_spaces()
        if dimensions == 1:
            dimensions = [None]
        elif dimensions == 2:
            dimensions = [None, None]
        if self.current_token and self.current_token.token == '[':
            values = self.parse_array_values(dimensions, scope)
            return ArrayRedec(name, dimensions, values, False, scope)
        else:
            raise SemanticError(f"RedeclarationError: Array '{name}' is being redeclared with"
                                " non-array element.")

    ########## STRUCTS ##########
    def parse_globalstruct(self) -> Union[StructDec, GlobalStructDec]:
        self.current_token = self.get_next_token() # eat build
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("Expected struct name after 'build'.")
        struct_name = Identifier(self.current_token.lexeme)
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        if self.current_token.token == '{':
            for item in self.globalstruct:
                if item == struct_name.symbol:
                    self.globalstruct.remove(item)
                    return self.create_struct(struct_name, "global")
                
            raise SemanticError(f"NameError: Global struct '{struct_name.symbol}' was not declared.")
        else:
            if struct_name.symbol in self.globalstruct:
                raise SemanticError(f"NameError: Global struct '{struct_name.symbol}' was already declared.")
            self.globalstruct.append(struct_name.symbol)
            return GlobalStructDec(struct_name)

    def parse_struct(self, scope) -> StructDec:
        self.current_token = self.get_next_token() # eat build
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("Expected struct name after 'build'.")
        struct_name = Identifier(self.current_token.lexeme)
        self.current_token = self.get_next_token() # eat id
        self.skip_whitespace()
        return self.create_struct(struct_name, scope)
    
    def create_struct(self, struct_name, scope) -> StructDec:
        name = struct_name.symbol
        fields_table = []
        fields = []
        self.expect("{","StructError: Struct fields must be enclosed in curly braces.")
        self.skip_whitespace()
        while self.current_token and self.current_token.token != '}':
            datatype = self.current_token.token
            self.current_token = self.get_next_token()  # eat datatype
            self.skip_spaces()
            field_name = Identifier(self.current_token.lexeme)  
            self.current_token = self.get_next_token()  # eat id
            self.skip_spaces()
            value = None
            if self.current_token.token == ':':
                self.current_token = self.get_next_token()  # eat :
                self.skip_spaces()
                value = self.parse_expr(scope) 
                fields.append(StructFields(field_name, value, datatype))
                if field_name.symbol in fields_table:
                    raise SemanticError(f"FieldError: Duplicate field name detected: '{field_name.symbol}'.")
                fields_table.append(field_name.symbol)
                self.skip_whitespace()
            else:
                fields.append(StructFields(field_name, None, datatype))
                if field_name.symbol in fields_table:
                    raise SemanticError(f"FieldError: Duplicate field name detected: '{field_name.symbol}'.")
                fields_table.append(field_name.symbol)
                self.skip_whitespace()
            if self.current_token and self.current_token.token == ',':
                self.current_token = self.get_next_token()  # eat ,
                self.skip_whitespace()
        self.current_token = self.get_next_token() # eat }
        self.skip_whitespace()
        if name in self.globalstruct:
            raise SemanticError(f"NameError: Global struct '{name}' already exists.")
        if self.lookup_identifier(name):
            info = self.get_identifier_info(name)
            raise SemanticError(f"NameError: Identifier {name}' was "
                                f"already declared as {info["type"]}.") 
        self.declare_id(name, "a struct")
        return StructDec(struct_name, fields, scope)

    def parse_struct_inst(self, scope) -> StructInst:
        self.current_token = self.get_next_token()  # eat 'access'
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise SemanticError("Expected struct name after 'access'.")
        struct_parent = self.current_token.lexeme
        if not self.lookup_identifier(struct_parent):
            if struct_parent in self.globalstruct:
                pass
            else:
                raise SemanticError(f"NameError: Struct '{struct_parent}' is not defined.")
        self.current_token = self.get_next_token()  # eat id
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise SemanticError("Expected struct instance name after struct name.")
        inst_name = Identifier(self.current_token.lexeme)
        self.current_token = self.get_next_token()  # eat id
        self.skip_spaces()
        values = []
        if self.current_token.token == ':':
            self.current_token = self.get_next_token()  # eat ':'
            self.skip_spaces()
            while self.current_token.token != ',':
                value = self.parse_expr(scope)
                values.append(value)
                self.skip_spaces()
                if self.current_token.token == ',':
                    self.current_token = self.get_next_token()  # eat ','
                    self.skip_spaces()
                    if self.current_token.token == 'newline':
                        raise SemanticError("Unexpected newline found after struct instance value.")
                elif self.current_token.token == 'newline':
                    break
        if self.lookup_identifier(inst_name.symbol):
            info = self.get_identifier_info(inst_name.symbol)
            raise SemanticError(f"NameError: Identifier {inst_name.symbol}' was "
                                f"already declared as {info["type"]}.") 
        self.declare_id(inst_name.symbol, "a struct instance")
        return StructInst(inst_name, struct_parent, values, False)

    def parse_inst_ass(self, scope) -> InstAssignment:
        struct_inst_name = Identifier(self.current_token.lexeme)
        if not self.lookup_id_type(struct_inst_name.symbol, "a struct instance"):
            raise SemanticError(f"NameError: Struct instance '{struct_inst_name.symbol}' is not defined.")
        self.current_token = self.get_next_token() # eat id
        if self.current_token.token != '.':
            raise SemanticError("Expected '.' after struct instance name.")
        self.current_token = self.get_next_token() # eat .
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise SemanticError("Expected struct instance field name after struct instance name.")
        inst_field_name = Identifier(self.current_token.lexeme)
        left = StructInstField(struct_inst_name, inst_field_name)
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        operator = self.current_token.token
        self.current_token = self.get_next_token() # eat operator
        self.skip_spaces()
        value = self.parse_expr(scope)
        return InstAssignment(left, operator, value)

    ########## IMMO ############
    def parse_immo(self, scope):
        self.current_token = self.get_next_token() # eat immo
        self.skip_spaces()
        if self.current_token.token == 'access':
            immo_inst = self.parse_immo_inst(scope)
            return immo_inst
        else:
            if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("Expected identifier or 'access' after 'immo'.")
            la_token = self.look_ahead()
            if la_token is not None and la_token.token in [':',',']:  
                immo_var = self.parse_immo_var(scope)  
                return immo_var
            elif la_token is not None and la_token.token == '[':  
                immo_arr = self.parse_immo_arr(scope)
                return immo_arr
            else:
                raise SemanticError(f"Unexpected token found during parsing: {la_token}")  
            
    def parse_immo_var(self, scope) -> Union[VarDec, BatchVarDec]:
        var_names = [Identifier(symbol=self.current_token.lexeme)]  
        name = self.current_token.lexeme
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        while self.current_token and self.current_token.token == ",":
            self.current_token = self.get_next_token()  # eat ,
            self.skip_spaces()

            if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("Expected variable name after ','.")
            
            var_names.append(Identifier(symbol=self.current_token.lexeme))
            self.current_token = self.get_next_token() # eat id
            self.skip_spaces()

            if self.current_token and self.current_token.token == ":":
                self.current_token = self.get_next_token() # eat :
                self.skip_spaces()
                value = self.parse_expr(scope)
                if scope not in self.var_list:
                    self.var_list[scope] = []
                for var in var_names:
                    if self.lookup_identifier(var.symbol):
                        info = self.get_identifier_info(var.symbol)
                        raise SemanticError(f"NameError: Identifier '{var.symbol}' is already declared as {info["type"]}.")  
                    self.declare_id(var.symbol, "a variable")
                self.skip_spaces()
                return BatchVarDec(declarations=[VarDec(var, value, True, scope) for var in var_names])
            
        self.current_token = self.get_next_token() # eat :
        self.skip_spaces()
        value = self.parse_expr(scope)
        values_table = {name: {"values": value}}
        self.skip_spaces()

        while self.current_token and self.current_token.token == ",":
            self.current_token = self.get_next_token()  # eat ,
            self.skip_spaces()

            if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("Expected variable name after ','.")
            
            var_names.append(Identifier(symbol=self.current_token.lexeme))
            variable_name = self.current_token.lexeme
            self.current_token = self.get_next_token() # eat id
            self.skip_spaces()

            if not self.current_token or self.current_token.token != ":":
                raise SemanticError("Expected ':' in variable initialization.")
            
            self.current_token = self.get_next_token() # eat :
            self.skip_spaces()

            value = self.parse_expr(scope)
            values_table[variable_name] = {"values": value}
        
        self.skip_spaces()
        if len(var_names) > 1:
            for var in var_names:
                if self.lookup_identifier(var.symbol):
                    info = self.get_identifier_info(var.symbol)
                    raise SemanticError(f"NameError: Identifier '{var.symbol}' is already declared as {info["type"]}.")  
                self.declare_id(var.symbol, "a variable")
            return BatchVarDec(declarations=[VarDec(var, values_table[var.symbol]['values'], True, scope) for var in var_names])
        else:
            var = var_names[0]
            if self.lookup_identifier(var.symbol):
                info = self.get_identifier_info(var.symbol)
                raise SemanticError(f"NameError: Identifier '{var.symbol}' is already declared as {info["type"]}.")    
            self.declare_id(var.symbol, "a variable")
            return VarDec(var, value, True, scope)

    def parse_immo_arr(self, scope) -> ArrayDec:
        arr_name = Identifier(self.current_token.lexeme)
        name=arr_name.symbol
        if self.lookup_identifier(name):
            info = self.get_identifier_info(name)
            raise SemanticError(f"NameError: Identifier '{name}' is already declared as {info["type"]}.")
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        dimensions = []
        while self.current_token and self.current_token.token == '[':
            self.current_token = self.get_next_token() #eat [
            self.skip_spaces
            dim = int(self.current_token.lexeme)
            if dim < 2:
                raise SemanticError(f"ArraySizeError: Expected array size to be greater than 1, but got {dim}.")
            dimensions.append(dim)
            self.current_token = self.get_next_token() # eat hp_ltr
            self.skip_spaces()
            self.expect("]","Expected ']' to close immutable array declaration.")
            self.skip_spaces()
            
        self.expect(":", "Expected ':' in array initialization or modification.")
        self.skip_spaces()
        values = self.parse_array_values(dimensions, scope)
        self.declare_id(name, "an array", len(dimensions))
        return ArrayDec(arr_name, dimensions, values, True, scope)
    
    def parse_immo_inst(self, scope) -> ImmoInstDec:
        self.current_token = self.get_next_token()  # eat 'access'
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise SemanticError("Expected struct name after 'access'.")
        struct_parent = self.current_token.lexeme
        if not self.lookup_identifier(struct_parent):
            if struct_parent in self.globalstruct:
                pass
            else:
                raise SemanticError(f"NameError: Struct '{struct_parent}' is not defined.")
        self.current_token = self.get_next_token()  # eat id
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise SemanticError("Expected struct instance name after struct name.")
        inst_name = Identifier(self.current_token.lexeme)
        self.current_token = self.get_next_token()  # eat id
        self.skip_spaces()
        values = []
        self.expect(":","Expected ':' after struct instance name.")
        self.skip_spaces()
        while self.current_token.token != ',':
            value = self.parse_expr(scope)
            values.append(value)
            self.skip_spaces()
            if self.current_token.token == ',':
                self.current_token = self.get_next_token()  # eat ','
                self.skip_spaces()
                if self.current_token.token == 'newline':
                    raise SemanticError("Unexpected newline found after struct instance value.")
            elif self.current_token.token == 'newline':
                break
        if self.lookup_identifier(inst_name.symbol):
            info = self.get_identifier_info(inst_name.symbo)
            raise SemanticError(f"NameError: Identifier '{inst_name.symbo}' is already declared as {info["type"]}.")
        self.declare_id(inst_name.symbol, "a struct instance")
        return StructInst(inst_name, struct_parent, values, True)

    ########## ASS #############
    def parse_var_ass(self, scope) -> VarAssignment:
        var_name = Identifier(symbol=self.current_token.lexeme)
        name = self.current_token.lexeme
        if not self.lookup_identifier(name):
            raise SemanticError(f"NameError: Variable '{name}' does not exist.")
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        operator = self.current_token.token
        self.current_token = self.get_next_token() # eat operator
        self.skip_spaces()
        value = self.parse_expr(scope)
        return VarAssignment(var_name, operator, value)

    ########## EXPR ############
    def parse_expr(self, scope) -> Expr:
        self.skip_spaces()
        return self.parse_or_expr(scope)
    
    def parse_or_expr(self, scope) -> Expr:
        self.skip_spaces()
        left = self.parse_and_expr(scope)
        while self.current_token and self.current_token.token in ['OR', '||']:
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            right = self.parse_and_expr(scope)
            left = BinaryExpr(left=left, right=right, operator=operator)
        return left
    
    def parse_and_expr(self, scope) -> Expr:
        self.skip_spaces()
        left = self.parse_relat_expr(scope)
        while self.current_token and self.current_token.token in ['AND', '&&']:
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            right = self.parse_relat_expr(scope)
            left = BinaryExpr(left=left, right=right, operator=operator)
        return left
    
    def parse_relat_expr(self, scope) -> Expr:
        self.skip_spaces()
        left = self.parse_additive_expr(scope)
        if not self.current_token or self.current_token.token not in ['<', '>', '<=', '>=', '==', '!=']:
            return left

        expr = []
        while self.current_token and self.current_token.token in ['<', '>', '<=', '>=', '==', '!=']:
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            right = self.parse_additive_expr(scope)
            expr.append(BinaryExpr(left=left, right=right, operator=operator))
            left = right

        return ChainRelatExpr(expr)
    
    def parse_additive_expr(self, scope) -> Expr:
        self.skip_spaces()
        left = self.parse_multiplicative_expr(scope)

        while self.current_token and self.current_token.token in '+-':
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            right = self.parse_multiplicative_expr(scope)
            left = BinaryExpr(left=left, right=right, operator=operator)
        return left

    def parse_multiplicative_expr(self, scope) -> Expr:
        self.skip_spaces()
        left = self.parse_not_expr(scope)

        while self.current_token and self.current_token.token in "/*%":
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            right = self.parse_not_expr(scope)
            left = BinaryExpr(left=left, right=right, operator=operator)  

        return left  
    
    def parse_not_expr(self, scope) -> Expr:
        self.skip_spaces()

        if self.current_token and self.current_token.token == '!':
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            operand = self.parse_exp_expr()
            return UnaryExpr(operator=operator, operand=operand)

        return self.parse_exp_expr(scope)
    
    def parse_exp_expr(self, scope) -> Expr:
        self.skip_spaces()
        left = self.parse_primary_expr(scope)

        while self.current_token and self.current_token.token == '^':
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            right = self.parse_exp_expr(scope)
            left = BinaryExpr(left=left, right=right, operator=operator)  

        return left 

    def parse_primary_expr(self, scope) -> Expr:
        self.skip_spaces()
        if not self.current_token:
            raise SemanticError("Unexpected end of input during parsing!")
        
        tk = self.current_token.token

        if re.match(r'^id\d+$', tk):
            tk= 'id'

        if tk == 'id':
            identifier = Identifier(symbol=self.current_token.lexeme)
            self.current_token = self.get_next_token()
            self.skip_spaces()
            if self.current_token.token == '.':
                if not self.lookup_id_type(identifier.symbol, "a struct instance"):
                    raise SemanticError(f"NameError: Struct instance '{identifier.symbol}' does not exist.")
                self.current_token = self.get_next_token()
                self.skip_spaces()
                if not re.match(r'^id\d+$', self.current_token.token):
                    raise SemanticError("Expected 'id' after '.' in accessing a struct instance field.")
                field = Identifier(symbol=self.current_token.lexeme)
                identifier = StructInstField(identifier, field)
                self.current_token = self.get_next_token()
                self.skip_spaces()
            elif self.current_token.token == '[':
                dimensions = []
                if not self.lookup_id_type(identifier.symbol, "an array"):
                    raise SemanticError(f"NameError: Array '{identifier.symbol}' does not exist.")
                while self.current_token and self.current_token.token == '[':
                    self.current_token = self.get_next_token() #eat [
                    self.skip_spaces
                    if self.current_token and self.current_token.token == ']':
                        raise SemanticError("IndexError: Index cannot be empty.")
                    else:
                        dim = self.parse_expr(scope)
                        dimensions.append(dim)
                        self.skip_spaces()
                        self.expect("]", "Expected ']' to close array dimension.")
                        self.skip_spaces()
                
                identifier = ArrElement(identifier, dimensions)
            else:
                if not self.lookup_id_type(identifier.symbol, "a variable"):
                    raise SemanticError(f"NameError: Variable '{identifier.symbol}' does not exist.")
            return identifier
        elif tk == 'hp_ltr':
            literal = HpLiteral(value=self.current_token.lexeme)
            self.current_token = self.get_next_token()
            self.skip_spaces()
            return literal
        elif tk == 'xp_ltr':
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
            value = self.parse_expr(scope)  
            
            self.expect(')', "Unexpected token found inside parenthesised expression. Expected closing parenthesis.")
            self.skip_spaces()
            return value
        elif tk == '-':
            self.current_token = self.get_next_token()
            self.skip_spaces()
            if self.current_token and self.current_token.token == '(':
                self.current_token = self.get_next_token()
                self.skip_spaces()
                expr = self.parse_expr(scope)
                self.expect(')', "Unexpected token found inside parenthesized expression. Expected closing parenthesis.")
                self.skip_spaces()
                return UnaryExpr(operator='-', operand=expr)
            elif re.match(r'^id\d+$', self.current_token.token):
                identifier = Identifier(symbol=self.current_token.lexeme)
                self.current_token = self.get_next_token()
                self.skip_spaces()
                return UnaryExpr(operator='-', operand=identifier)
        else:
            raise SemanticError(f"Unexpected token found during parsing: {tk}")
        
    ########### IF #############
    def parse_if(self, scope) -> IfStmt:
        self.current_token = self.get_next_token()  # eat if
        self.skip_spaces()
        condition = self.parse_expr(scope)
        self.skip_whitespace()
        self.expect("{", "Expected '{' to open an if statement's body.")
        self.skip_whitespace()
        then_branch = []
        self.push_scope()
        while self.current_token and self.current_token.token != "}":
            stmt = self.parse_stmt(scope)
            then_branch.append(stmt)
            self.skip_whitespace()

        self.expect("}", "Expected '}' to close an if statement's body.")
        self.skip_whitespace()
        self.pop_scope()
        elif_branches = []
        
        while self.current_token and self.current_token.token == 'elif':
            self.push_scope()
            self.current_token = self.get_next_token()  # eat elif
            self.skip_spaces()
            elif_condition = self.parse_expr(scope)
            self.skip_whitespace()
            self.expect("{", "Expected '{' to open an elif statement's body.")
            self.skip_whitespace()
            elif_body = []

            while self.current_token and self.current_token.token != "}":
                stmt = self.parse_stmt(scope)
                elif_body.append(stmt)
                self.skip_whitespace()

            self.expect("}", "Expected '}' to close an elif statement's body.")
            self.skip_whitespace()
            elif_branches.append(ElifStmt(elif_condition, elif_body))
            self.pop_scope()
        else_branch = None
        if self.current_token and self.current_token.token == 'else':
            self.push_scope()
            self.current_token = self.get_next_token()  # eat else
            self.skip_whitespace()
            self.expect("{", "Expected '{' to open an else statement's body.")
            self.skip_whitespace()
            else_branch = []

            while self.current_token and self.current_token.token != "}":
                stmt = self.parse_stmt(scope)
                else_branch.append(stmt)
                self.skip_whitespace()
            self.pop_scope()
            self.expect("}", "Expected '}' to close an else statement's body.")
            self.skip_whitespace()

        if not elif_branches:
            elif_branches = None
        return IfStmt(condition, then_branch, elif_branches, else_branch)

    def parse_flank(self, scope) -> FlankStmt:
        self.current_token = self.get_next_token()  # eat flank
        self.skip_spaces()
        expression = self.parse_expr(scope)
        self.skip_whitespace()
        self.expect("{", "Expected '{' to open a flank statement's body.")
        self.skip_whitespace()
        choices = []

        if self.current_token.token != 'choice':
            raise SyntaxError("FlankError: There must be at least one choice statement in a flank statement.")
        
        while self.current_token and self.current_token.token == "choice":
            self.current_token = self.get_next_token()  # eat choice
            self.skip_spaces()
            values = [self.parse_expr(scope)]
            self.skip_spaces()

            while self.current_token and self.current_token.token == ',':
                self.current_token = self.get_next_token()  # eat ,
                values.append(self.parse_expr(scope))
                self.skip_spaces()
            
            self.expect(":", "Expected ':' to open a choice statement's body.")
            self.skip_whitespace()

            self.push_scope()
            choice_body = []
            while self.current_token and self.current_token.token not in ["choice", "backup", "}"]:
                stmt = self.parse_stmt(scope)
                choice_body.append(stmt)
                self.skip_whitespace()
            self.pop_scope()
            choices.append(ChoiceStmts(values, choice_body))
        
        if not self.current_token or self.current_token.token != 'backup':
            raise SyntaxError("FlankError: A flank statement must include a backup statement.")

        self.current_token = self.get_next_token()  # eat backup
        self.skip_spaces()
        self.expect(":", "Expected ':' to open backup statement's body.")
        self.skip_whitespace()

        self.push_scope()
        backup_body = []
        while self.current_token and self.current_token.token != "}":
            stmt = self.parse_stmt(scope)
            backup_body.append(stmt)
            self.skip_whitespace()
        self.pop_scope()

        self.expect("}", "Expected '}' to close a flank statement's body.")
        self.skip_whitespace()

        return FlankStmt(expression, choices, backup_body)

def check(fn, text):
    lexer = Lexer(fn, text)
    if text == "":
        return "No code in the module.", {}
    tokens, error = lexer.make_tokens()

    if error:
        return 'Lexical errors found, cannot continue with syntax analyzing. Please check lexer tab.', {}

    result = parse(fn, text)

    if result != 'No lexical errors found!\nValid syntax.':
        return 'Syntax errors found, cannot continue with semantic analyzing. Please check syntax tab.', {}

    semantic = Semantic(tokens)
    result = semantic.produce_ast()

    if isinstance(result, SemanticError):
        return str(result), {}
    
    try:
        visitor = ASTVisitor()
        visitor.visit(result)

        analyzer = SemanticAnalyzer(visitor.symbol_table)
        analyzer.visit(result)
        table = analyzer.symbol_table
    except SemanticError as e:
        return str(e), {}

    return result, table

    return result, {}
        

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
        self.arr_list = {"global": []} 
        self.dead_arr_list = {"global": {}} 
    
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
                if self.current_token and self.current_token.token == 'play':
                    program.body.append(self.parse_func())
                    self.current_token = self.get_next_token()
                else:
                    raise SemanticError(f"Unexpected token found during parsing: {self.current_token.token}")
        except SemanticError as e:
            return e
        return program
                
    def parse_func(self) -> PlayFunc:
        self.skip_whitespace()

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

        return PlayFunc(body=BlockStmt(statements=body))
    
    def parse_stmt(self, scope) -> Stmt:
        self.skip_whitespace()

        if self.current_token and re.match(r'^id\d+$', self.current_token.token):
            la_token = self.look_ahead()
            if la_token is not None and la_token.token in [':',',']:  
                return self.parse_var_init(scope)
            elif la_token is not None and la_token.token == '[':  
                return self.parse_array(scope)
            else:
                raise SemanticError(f"Unexpected token found during parsing: {la_token.token}")
        elif self.current_token and self.current_token.token in ['hp','xp','comms','flag']:
            return self.var_or_arr(scope)
        else:
            raise SemanticError(f"Unexpected token found during parsing: {self.current_token.token}")
        
    def parse_var_init(self, scope) -> Union[VarDec, BatchVarDec, VarAssignment]:
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
                value = self.parse_expr()

                if scope not in self.var_list:
                    self.var_list[scope] = []
                for var in var_names:
                    if var.symbol in self.var_list["global"] or var.symbol in self.var_list[scope]:
                        raise SemanticError(f"Variable '{var.symbol}' is already defined.")   
                    self.var_list[scope].append(var.symbol)

                self.skip_spaces()
                return BatchVarDec(declarations=[VarDec(var, value, scope) for var in var_names])

        self.current_token = self.get_next_token() # eat :
        self.skip_whitespace() 
        value = self.parse_expr()
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

            value = self.parse_expr()
            values_table[variable_name] = {"values": value}

        self.skip_spaces()
        if len(var_names) > 1:
            if scope not in self.var_list:
                self.var_list[scope] = []
            for var in var_names:
                if var.symbol in self.var_list["global"] or var.symbol in self.var_list[scope]:
                    raise SemanticError(f"Variable '{var.symbol}' is already defined.")   
                self.var_list[scope].append(var.symbol)
            return BatchVarDec(declarations=[VarDec(var, values_table[var.symbol]['values'], scope) for var in var_names])
        else:
            var = var_names[0]
            if name in self.var_list["global"]:
                scope = "global"
            if scope not in self.var_list:
                self.var_list[scope] = []
            if name in self.var_list[scope]:
                return VarAssignment(left=var, operator=':', right=value)
            self.var_list[scope].append(name)
            return VarDec(var, value, scope) 
        
    def var_or_arr(self, scope) -> Union[VarDec, ArrayDec]:
        datatype = self.current_token.token  

        self.current_token = self.get_next_token()
        self.skip_spaces()

        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise SemanticError("Expected variable name.")
        
        la_token = self.look_ahead()
        if la_token is not None and la_token.token == '[':  
            return self.parse_empty_array(datatype, scope)
        else:
            return self.parse_var_dec(datatype, scope)
        
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
            if scope not in self.var_list:
                self.var_list[scope] = []
            for var in var_names:
                if var.symbol in self.var_list["global"] or var.symbol in self.var_list[scope]:
                    raise SemanticError(f"Variable '{var.symbol}' is already defined.")   
                self.var_list[scope].append(var.symbol)
            if value != None:
                return BatchVarDec([VarDec(var, value, scope) for var in var_names])
            else:
                return BatchVarDec([VarDec(var, DeadLiteral(value, datatype), scope) for var in var_names])
        else:
            var = var_names[0]
            if var.symbol in self.var_list["global"]:
                scope = "global"
            if scope not in self.var_list:
                self.var_list[scope] = []
            if var.symbol in self.var_list[scope]:
                return VarAssignment(left=var, operator=':', right=value)
            self.var_list[scope].append(var.symbol)
            if value != None:
                return VarDec(var, value, scope)
            else:
                return VarDec(var, DeadLiteral(value, datatype), scope)

    def parse_empty_array(self, datatype,scope) -> ArrayDec:
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

        if name in self.arr_list.get(scope, []) or name in self.arr_list.get("global", []):
            raise SemanticError(f"DeclarationError: Array '{name}' is already defined.")
        
        if name in self.dead_arr_list.get(scope, {}) or name in self.dead_arr_list.get("global", {}):
            raise SemanticError(f"DeclarationError: Array '{name}' is already defined.")
        
        if self.current_token and self.current_token.token == 'newline':
            default_value = {
                'hp': HpLiteral(0),
                'xp': XpLiteral(0.0),
                'comms': CommsLiteral(''),
                'flag': FlagLiteral(False)
            }.get(datatype, None)   

            if len(dimensions) == 2:
                if dimensions[0] is None and dimensions[1] is None:
                    values = []  # arr[][]
                elif dimensions[0] is None and dimensions[1] is not None:
                    values = [default_value] * dimensions[1]  # arr[][int]
                elif dimensions[0] is not None and dimensions[1] is None:
                    values = [[] for _ in range(dimensions[0])]  # arr[int][]
                elif dimensions[0] is not None and dimensions[1] is not None:
                    values = [[default_value] * dimensions[1] for _ in range(dimensions[0])]  # arr[int][int]
            else:
                if dimensions[0] is None:
                    values = []  # arr[]
                else:
                    values = [default_value] * dimensions[0]

            if scope not in self.arr_list:
                self.arr_list[scope] = []
            self.arr_list[scope].append(name)
            return ArrayDec(arr_name, dimensions, values)
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
                
            if scope not in self.dead_arr_list:
                self.dead_arr_list[scope] = {}

            self.dead_arr_list[scope][name] = {
                "type": datatype,
                "dimensions": dimensions
            }
            return ArrayDec(arr_name, dimensions, values)      
    
    def parse_array(self, scope) -> Union[ArrayDec, ArrAssignment]:
        arr_name = Identifier(symbol=self.current_token.lexeme)
        name=arr_name.symbol
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        dimensions = []

        while self.current_token and self.current_token.token == '[':
            self.current_token = self.get_next_token() #eat [
            self.skip_spaces
            if self.current_token and self.current_token.token == 'hp_ltr':
                dimensions.append(int(self.current_token.lexeme))
                self.current_token = self.get_next_token()
            else:
                dimensions.append(None)
            self.skip_spaces()
            self.expect("]", "Expected ']' to close array dimension declaration.")
            self.skip_spaces()
            
        self.expect(":", "Expected ':' in array initialization or modification.")
        self.skip_spaces()
        
        if name in self.dead_arr_list.get(scope, {}) or name in self.dead_arr_list.get("global", {}):
            if name in self.dead_arr_list.get("global", {}):
                scope = "global"
            existing_dimensions = self.dead_arr_list[scope][name]["dimensions"]
            if len(existing_dimensions) != len(dimensions):
                    raise SemanticError(f"ArrayIndexError: Incorrect number of dimensions for '{arr_name.symbol}'.")
            expected_type = self.dead_arr_list[scope][name]["type"]
            values = self.parse_array_values(expected_dims=dimensions, depth=0, scope=scope)
            if all(dim is None for dim in dimensions):
                if isinstance(values[0], list):
                    for row in values:
                        for val in row:
                            val_type = self.TYPE_MAP.get(type(val.value), None)
                            if val_type != expected_type:
                                raise SemanticError(f"TypeMismatchError: Array '{name}' expects '{expected_type}' data type.")
                    dimensions = [len(values), len(values[0])]    
                else:
                    for val in values:
                        val_type = self.TYPE_MAP.get(type(val.value), None)
                        if val_type != expected_type:
                            raise SemanticError(f"TypeMismatchError: Array '{name}' expects '{expected_type}' data type.")
                    dimensions = [len(values)]
            
            self.dead_arr_list[scope].pop(name, None)
            if scope not in self.arr_list:
                self.arr_list[scope] = []
            self.arr_list[scope].append(name)
            return ArrayDec(arr_name, dimensions, values)
        
        if name in self.arr_list["global"]:
            scope = "global"
        if scope not in self.arr_list:
            self.arr_list[scope] = []
        if name in self.arr_list[scope]:
            if all(dim is not None for dim in dimensions):
                value = self.parse_expr()
                return ArrAssignment(arr_name, dimensions, ':', value)
            else:
                raise SemanticError(f"AssignmentError: Index must not be blank for array index assignment for array name '{arr_name.symbol}'.")
        else:
            values = self.parse_array_values(expected_dims=dimensions, depth=0, scope=scope)
            if all(dim is None for dim in dimensions):
                if isinstance(values[0], list):  
                    dimensions = [len(values), len(values[0])]
                else:  
                    dimensions = [len(values)]
            self.arr_list[scope].append(arr_name.symbol)
            return ArrayDec(arr_name, dimensions, values)

    def parse_array_values(self, expected_dims, depth, scope):
        values = []
        if expected_dims[depth] is None or isinstance(expected_dims[depth], int):
            while self.current_token and self.current_token.token != 'newline':
                if depth + 1 < len(expected_dims):  # 2d array
                    self.expect("[", "Expected '[' for nested array values.")
                    self.skip_spaces()
                    res_val = self.parse_array_values(expected_dims, depth + 1, scope)
                    values.append(res_val)
                    self.expect("]", "Expected ']' to close nested array values.")
                else:
                    value = self.parse_expr()
                    if value.kind not in ["HpLiteral", "XpLiteral", "CommsLiteral", "FlagLiteral"]:
                        raise SemanticError("Arrays can only be initialied with literal values.")
                    values.append(value)

                self.skip_spaces()
                if self.current_token.token == ',':
                    self.current_token = self.get_next_token()  # eat ,
                    self.skip_spaces()
                else:
                    break
        if expected_dims[depth] is not None and len(values) != expected_dims[depth]:
            raise SemanticError(
                f"ArraySizeError: Expected {expected_dims[depth]} elements, but got {len(values)}."
            )
        return values

    ########## EXPR ############
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
            raise SemanticError("Unexpected end of input during parsing!")
        
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
            raise SemanticError(f"Unexpected token found during parsing: {tk}")
        
def check(fn, text):
    lexer = Lexer(fn, text)
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
        

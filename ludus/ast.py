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
                program.body.append(self.parse_func())
                self.current_token = self.get_next_token()
        except ParserError as e:
            return e, self.symbol_table
        except SemanticError as e:
            return e, self.symbol_table
        except SymbolTableError as e:
            return e, self.symbol_table
        
        return program, self.symbol_table
    
    def parse_func(self):
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
            stmt = self.parse_stmt()
            body.append(stmt)
            self.skip_whitespace()

        self.expect("}", "Expected '}' to close function body.")

        return PlayFunc(body=BlockStmt(statements=body))

    def parse_stmt(self) -> Stmt:
        self.skip_whitespace()

        if self.current_token and re.match(r'^id\d+$', self.current_token.token):
            la_token = self.look_ahead()
            if la_token is not None and la_token.token in [':',',']:  
                return self.parse_var_init()
            elif la_token is not None and la_token.token == '[':  
                return self.parse_array()
            else:
                raise ParserError(f"Unexpected token found during parsing: {la_token.token}")
    
        elif self.current_token and self.current_token.token in ['hp','xp','comms','flag']:
            return self.var_or_arr()
        else:
            return self.parse_expr()
    
    def var_or_arr(self):
        datatype = self.current_token.token  

        self.current_token = self.get_next_token()
        self.skip_whitespace()

        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise ParserError("Expected variable name.")
        
        la_token = self.look_ahead()
        if la_token is not None and la_token.token == '[':  
            return self.parse_empty_array(datatype)
        else:
            return self.parse_var_dec(datatype)

    def parse_var_init(self) -> Union[VarDec, BatchVarDec]:
        self.skip_whitespace()
        
        var_names = [Identifier(symbol=self.current_token.lexeme)]  
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
                evaluated_val = evaluate(value, self.symbol_table)

                for var in var_names:
                    self.symbol_table.define_variable(var.symbol, evaluated_val)

                self.skip_whitespace()
                return BatchVarDec(declarations=[VarDec(name=var, value=value) for var in var_names])


        
        self.current_token = self.get_next_token() # eat :
        self.skip_whitespace() 

        value = self.parse_expr()
        evaluated_val = evaluate(value, self.symbol_table)
        expected_type = type(evaluated_val)  

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
            evaluated_val = evaluate(value, self.symbol_table)

            if type(evaluated_val) != expected_type:
                raise SemanticError(f"TypeMismatchError: Expected {expected_type.__name__}, but got {type(evaluated_val).__name__} in '{variable_name}'.")

        for var in var_names:
            self.symbol_table.define_variable(var.symbol, evaluated_val)

        self.skip_whitespace()

        if len(var_names) > 1:
            return BatchVarDec(declarations=[VarDec(name=var, value=value) for var in var_names])
        else:
            return VarDec(name=var_names[0], value=value)

    def parse_var_dec(self, datatype) -> Union[VarDec, BatchVarDec]:
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
                self.symbol_table.define_def_variable(var.symbol, value)

        elif self.current_token and self.current_token.token == ':':
            self.current_token = self.get_next_token()
            self.skip_whitespace()

            if not self.current_token or self.current_token.token != 'dead':
                raise ParserError("Expected 'dead' after ':'.")

            value = None  
            self.current_token = self.get_next_token()  
            for var in var_names:
                self.symbol_table.define_dead_variable(var.symbol, datatype)

        self.skip_whitespace()

        if len(var_names) > 1:
            var_declarations = [VarDec(name=var, value=value) for var in var_names]
            return BatchVarDec(declarations=var_declarations)
        else:
            return VarDec(name=var_names[0], value=value)
 
    def parse_empty_array(self, datatype) -> ArrayDec:
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
                'hp': 0,
                'xp': 0.0,
                'comms': '',
                'flag': False
            }.get(datatype, None)

            if default_value is None:
                raise ParserError(f"Unknown data type '{datatype}'.")
            
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
            
            self.symbol_table.define_dead_array(arr_name.symbol, dimensions, values, datatype)

        elif self.current_token and self.current_token.token == ':':
            self.current_token = self.get_next_token() #eat :
            self.skip_spaces()

            self.expect("dead", "Expected 'dead' after ':'.")

            if len(dimensions) == 2:
                if dimensions[0] is None and dimensions[1] is None:
                    values = None  # arr[][]

                elif dimensions[0] is None and dimensions[1] is not None:
                    values = [None] * dimensions[1]  # arr[][int]

                elif dimensions[0] is not None and dimensions[1] is None:
                    values = [[None] for _ in range(dimensions[0])]  # arr[int][]

                elif dimensions[0] is not None and dimensions[1] is not None:
                    values = [[None] * dimensions[1] for _ in range(dimensions[0])]  # arr[int][int]
            else:
                if dimensions[0] is None:
                    values = None  # arr[]
                else:
                    values = [None] * dimensions[0]
            
            self.symbol_table.define_dead_array(arr_name.symbol, dimensions, values, datatype)
        
        
        return ArrayDec(arr_name.symbol, dimensions, values)


    def parse_array(self) -> ArrayDec:
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

        self.expect(":", "Expected ':' in array initialization.")
        self.skip_whitespace()
        
        values = self.parse_array_values(expected_dims=dimensions, depth=0)
        if all(dim is None for dim in dimensions):
            if isinstance(values[0], list):  
                dimensions = [len(values), len(values[0])]
            else:  
                dimensions = [len(values)]
        
        self.symbol_table.define_array(arr_name.symbol, dimensions, values)
        return ArrayDec(arr_name.symbol, dimensions, values)


    def parse_array_values(self, expected_dims, depth):
        values = []
        
        if expected_dims[depth] is None or isinstance(expected_dims[depth], int):
            while self.current_token and self.current_token.token != 'newline':
                if depth + 1 < len(expected_dims):  # 2d array
                    self.expect("[", "Expected '[' for nested array values.")
                    self.skip_whitespace()
                    values.append(self.parse_array_values(expected_dims, depth + 1))
                    self.expect("]", "Expected ']' to close nested array values.")
                else:  
                    value = self.parse_expr()
                    if value.kind not in ["HpLiteral", "XpLiteral", "CommsLiteral", "FlagLiteral"]:
                        raise ParserError("Arrays can only be initialied with literal values.")
                    evaluated_val = evaluate(value, self.symbol_table)  
                    values.append(evaluated_val)
                
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

        return values
  
    def parse_expr(self) -> Expr:
        self.skip_whitespace()
        return self.parse_additive_expr()

    def parse_additive_expr(self) -> Expr:
        self.skip_whitespace()
        left = self.parse_multiplicative_expr()

        while self.current_token and self.current_token.token in '+-':
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            right = self.parse_multiplicative_expr()
            left = BinaryExpr(left=left, right=right, operator=operator)
        return left

    def parse_multiplicative_expr(self) -> Expr:
        self.skip_whitespace()
        left = self.parse_primary_expr()

        while self.current_token and self.current_token.token in ["/", "*", "%"]:
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            right = self.parse_primary_expr()
            left = BinaryExpr(left=left, right=right, operator=operator)  

        return left  

    def parse_primary_expr(self) -> Expr:
        self.skip_whitespace()
        if not self.current_token:
            raise ParserError("Unexpected end of input during parsing!")
        
        tk = self.current_token.token

        if re.match(r'^id\d+$', tk):
            tk= 'id'

        if tk == 'id':
            identifier = Identifier(symbol=self.current_token.lexeme)
            self.current_token = self.get_next_token()
            self.skip_whitespace()
            return identifier
        elif tk == 'hp_ltr' or tk == 'nhp_ltr':
            literal = HpLiteral(value=self.current_token.lexeme)
            self.current_token = self.get_next_token()
            self.skip_whitespace()
            return literal
        elif tk == 'xp_ltr' or tk == 'nxp_ltr':
            literal = XpLiteral(value=self.current_token.lexeme)
            self.current_token = self.get_next_token()
            self.skip_whitespace()
            return literal
        elif tk == 'comms_ltr':
            value = re.sub(r'^"(.*)"$', r'\1', self.current_token.lexeme)
            literal = CommsLiteral(value)
            self.current_token = self.get_next_token()
            self.skip_whitespace()
            return literal
        elif tk == 'flag_ltr':
            lexeme = self.current_token.lexeme 
            if lexeme == 'true':
                value = True
            else:
                value = False
            literal = FlagLiteral(value)
            self.current_token = self.get_next_token()
            self.skip_whitespace()
            return literal
        elif tk == '(':
            self.current_token = self.get_next_token()
            self.skip_whitespace()
            value = self.parse_expr()  
            self.skip_whitespace()
            
            self.expect(')', "Unexpected token found inside parenthesised expression. Expected closing parenthesis.")
            self.skip_whitespace()
            return value

        else:
            raise ParserError(f"Unexpected token found during parsing: {tk}")

def check(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()

    if error:
        return 'Lexical errors found, cannot continue with syntax analyzing. Please check lexer tab.', {}

    result = parse(fn, text)

    if result != 'Valid syntax.':
        return 'Syntax errors found, cannot continue with semantic analyzing. Please check syntax tab.', {}

    semantic = Semantic(tokens)
    result, table = semantic.produce_ast()
    return result, table

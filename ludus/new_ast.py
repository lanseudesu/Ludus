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
        self.var_list = []
    
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

                for var in var_names:
                    if var.symbol in self.var_list:
                        raise SemanticError(f"Variable '{var.symbol}' is already defined.")
                    self.var_list.append(var.symbol)

                self.skip_spaces()
                return BatchVarDec(declarations=[VarDec(name=var, value=value) for var in var_names])

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
            for var in var_names:
                if var.symbol in self.var_list:
                    raise SemanticError(f"Variable '{var.symbol}' is already defined.")
                self.var_list.append(var.symbol)
            return BatchVarDec(declarations=[VarDec(name=var, value=values_table[var.symbol]['values']) for var in var_names])
        else:
            var = var_names[0]
            if name in self.var_list:
                return VarAssignment(left=var, operator=':', right=value)
            self.var_list.append(name)
            return VarDec(var, value) 
        
    def var_or_arr(self, scope) -> Union[VarDec, ArrayDec]:
        datatype = self.current_token.token  

        self.current_token = self.get_next_token()
        self.skip_spaces()

        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise SemanticError("Expected variable name.")
        
        la_token = self.look_ahead()
        if la_token is not None and la_token.token == '[':  
            pass
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
            for var in var_names:
                if var.symbol in self.var_list:
                    raise SemanticError(f"Variable '{var.symbol}' is already defined.")
                self.var_list.append(var.symbol)
            if value != None:
                return BatchVarDec([VarDec(name=var, value=value) for var in var_names])
            else:
                return BatchVarDec([VarDec(var, DeadLiteral(value, datatype)) for var in var_names])
        else:
            var = var_names[0]
            if var.symbol in self.var_list:
                raise SemanticError(f"Variable '{var.symbol}' is already defined.")
            self.var_list.append(var.symbol)
            if value != None:
                return VarDec(var, value)
            else:
                return VarDec(var, DeadLiteral(value, datatype))

    def parse_array(self, scope) -> Union[ArrayDec, ArrAssignment]:
        arr_name = Identifier(symbol=self.current_token.lexeme)
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        dimensions = []

        

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
        

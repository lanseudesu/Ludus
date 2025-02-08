from .lexer import Lexer
from .nodes import *
from .runtime.symbol_table import SymbolTableError, SymbolTable
from .runtime.interpreter import SemanticError, evaluate 
import re

class ParserError(Exception):
    def __init__(self, message, token):
        self.message = message
        self.token = token
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message}"

class Parser:
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

    def expect(self, token_type, error_message):
        prev_token = self.current_token
        self.current_token = self.get_next_token()
        if not prev_token or prev_token.token != token_type:
            raise ParserError(f"Parser Error: {error_message}", prev_token)

    def produce_ast(self) -> Program:
        program = Program(body=[])

        try:
            while self.current_token and self.current_token.token != 'EOF':
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
            raise ParserError("Expected function declaration keyword 'play'.", self.current_token.token)

        if self.current_token and self.current_token.token == 'play':
            self.current_token = self.get_next_token() # eat play
            self.current_token = self.get_next_token() # eat (
            self.current_token = self.get_next_token() # eat )
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
            return self.parse_var_dec()
        else:
            return self.parse_expr()
    
    def parse_var_dec(self) -> VarDec:
        self.skip_whitespace()

        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise ParserError("Expected variable name.", self.current_token.token)
        
        var_name = Identifier(symbol=self.current_token.lexeme)
        variable_name = self.current_token.lexeme
        self.current_token = self.get_next_token() 

        self.skip_whitespace()

        if not self.current_token or self.current_token.token != ":":
            raise ParserError("Expected ':' in variable declaration.", self.current_token)
        
        self.current_token = self.get_next_token()
        self.skip_whitespace()

        value = self.parse_expr()
        evaluated_val = evaluate(value, self.symbol_table)
        
        self.symbol_table.define_variable(variable_name, evaluated_val)
        self.skip_whitespace()

        return VarDec(name=var_name, value=value)


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
            raise ParserError("Unexpected end of input during parsing!", self.current_token)
        
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
            raise ParserError(f"Unexpected token found during parsing: {tk}", self.current_token.token)

def check(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()

    if error:
        return 'Lexical errors found, cannot continue with syntax analyzing. Please check lexer tab.' 

    syntax = Parser(tokens)
    result, table = syntax.produce_ast()
    return result, table

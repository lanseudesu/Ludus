from .error import SemanticError
from .nodes import *
import re

class Helper:
    def __init__(self, tokens, scope_stack, func_flag, start, end):
        self.tokens = tokens
        self.current_token_index = 0
        self.current_token = self.get_next_token()
        self.scope_stack = scope_stack
        self.func_flag = func_flag
        self.start = start
        self.end = end

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
                    raise SemanticError(f"NameError: Identifier '{name}' is already declared as {info["type"]}.", self.start, self.end)
        return False
    
    def get_identifier_info(self, name):
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]  
        raise SemanticError(f"NameError: Identifier '{name}' not declared.", self.start, self.end)
    
    def get_next_token(self):
        if self.current_token_index < len(self.tokens):
            token = self.tokens[self.current_token_index]
            self.current_token_index += 1
            return token
        return None
    
    def skip_spaces(self):
        while self.current_token and self.current_token.token == "space":
            self.current_token = self.get_next_token()
    
    def expect(self, token_type, error_message):
        prev_token = self.current_token
        self.current_token = self.get_next_token()
        if not prev_token or prev_token.token != token_type:
            raise SemanticError(f"ParserError: {error_message}", self.start, self.end)
        
    def look_ahead(self):
        la_token_index = self.current_token_index 
        while la_token_index < len(self.tokens):
            la_token = self.tokens[la_token_index]
            if la_token.token != "space": 
                return la_token
            la_token_index += 1  

        return None  
    
    def parse_expr(self, scope) -> Expr:
        self.skip_spaces()
        expr = self.parse_or_expr(scope)
        if self.current_token and self.current_token.token not in [')', ']']:
            raise SemanticError(f"ParserError: Unexpected token found during parsing: {self.current_token.token}", self.start, self.end)
        print(expr)
        return expr
    
    def parse_or_expr(self, scope) -> Expr:
        self.skip_spaces()
        left = self.parse_and_expr(scope)
        while self.current_token and self.current_token.token in ['OR', '||']:
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            right = self.parse_and_expr(scope)
            left = BinaryExpr(left, operator, right, self.start, self.end)
        return left
    
    def parse_and_expr(self, scope) -> Expr:
        self.skip_spaces()
        left = self.parse_relat_expr(scope)
        while self.current_token and self.current_token.token in ['AND', '&&']:
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            right = self.parse_relat_expr(scope)
            left = BinaryExpr(left, operator, right, self.start, self.end)
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
            expr.append(BinaryExpr(left, operator, right, self.start, self.end))
            left = right

        return ChainRelatExpr(expr, self.start, self.end)
    
    def parse_additive_expr(self, scope) -> Expr:
        self.skip_spaces()
        left = self.parse_multiplicative_expr(scope)

        while self.current_token and self.current_token.token in '+-':
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            right = self.parse_multiplicative_expr(scope)
            left = BinaryExpr(left, operator, right, self.start, self.end)
        return left

    def parse_multiplicative_expr(self, scope) -> Expr:
        self.skip_spaces()
        left = self.parse_not_expr(scope)

        while self.current_token and self.current_token.token in "/*%":
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            right = self.parse_not_expr(scope)
            left = BinaryExpr(left, operator, right, self.start, self.end)  

        return left  
    
    def parse_not_expr(self, scope) -> Expr:
        self.skip_spaces()

        if self.current_token and self.current_token.token == '!':
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            operand = self.parse_exp_expr()
            return UnaryExpr(operator, operand, self.start, self.end)

        return self.parse_exp_expr(scope)
    
    def parse_exp_expr(self, scope) -> Expr:
        self.skip_spaces()
        left = self.parse_primary_expr(scope)

        while self.current_token and self.current_token.token == '^':
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            right = self.parse_exp_expr(scope)
            left = BinaryExpr(left, operator, right, self.start, self.end)  

        return left 

    def parse_primary_expr(self, scope, is_func_call=False) -> Expr:
        self.skip_spaces()
        if not self.current_token:
            raise SemanticError("ParserError: Unexpected end of input during parsing!", self.start, self.end)
        
        tk = self.current_token.token

        if re.match(r'^id\d+$', tk):
            tk= 'id'

        if tk == 'id':
            identifier = Identifier(self.current_token.lexeme, self.start, self.end)
            self.current_token = self.get_next_token()
            self.skip_spaces()
            if self.current_token and self.current_token.token == '.':
                if not self.lookup_identifier(identifier.symbol):
                    raise SemanticError(f"NameError: Struct instance '{identifier.symbol}' does not exist.", self.start, self.end)
                
                info = self.get_identifier_info(identifier.symbol)
                allowed_types = {"a struct instance"}
                if self.func_flag:
                    allowed_types.add("a parameter")
                
                if info["type"] not in allowed_types:
                    raise SemanticError(f"NameError: Identifier '{identifier.symbol}' is already declared as {info['type']}", self.start, self.end)
                
                self.current_token = self.get_next_token()
                self.skip_spaces()
                if self.current_token:
                    if not re.match(r'^id\d+$', self.current_token.token):
                        raise SemanticError("ParserError: Expected 'id' after '.' in accessing a struct instance field.", self.start, self.end)
                field = Identifier(self.current_token.lexeme, self.start, self.end)
                identifier = StructInstField(identifier, field, self.start, self.end)
                self.current_token = self.get_next_token()
                self.skip_spaces()
            elif self.current_token and self.current_token.token == '[':
                dimensions = []
                if not self.lookup_identifier(identifier.symbol):
                    raise SemanticError(f"NameError: Array '{identifier.symbol}' does not exist.", self.start, self.end)
                
                info = self.get_identifier_info(identifier.symbol)
                allowed_types = {"an array"}
                if self.func_flag:
                    allowed_types.add("a parameter")

                if info["type"] not in allowed_types:
                    raise SemanticError(f"NameError: Identifier '{identifier.symbol}' is already declared as {info['type']}", self.start, self.end)

                while self.current_token and self.current_token.token == '[':
                    self.current_token = self.get_next_token() #eat [
                    self.skip_spaces
                    if self.current_token and self.current_token.token == ']':
                        raise SemanticError("IndexError: Index cannot be empty.", self.start, self.end)
                    else:
                        dim = self.parse_expr(scope)
                        dimensions.append(dim)
                        self.skip_spaces()
                        self.expect("]", "Expected ']' to close array dimension.")
                        self.skip_spaces()
                
                identifier = ArrElement(identifier, dimensions, self.start, self.end)
            elif self.current_token and self.current_token.token == '(':
                if not self.lookup_id_type(identifier.symbol, "a function"):
                    raise SemanticError(f"NameError: Function '{identifier.symbol}' does not exist.", self.start, self.end)
                self.current_token = self.get_next_token() # eat ( 
                self.skip_spaces()
                args = []       
                while self.current_token and self.current_token.token != ')':
                    la_token = self.look_ahead()
                    if la_token.token == ',' or la_token.token == ')':
                        arg = self.parse_primary_expr(scope, True)
                    else:
                        arg = self.parse_expr(scope)
                    args.append(arg)
                    self.skip_spaces()
                    if self.current_token and self.current_token.token == ',':
                        self.current_token = self.get_next_token() # eat ,
                        self.skip_spaces()
                self.current_token = self.get_next_token() # eat )
                self.skip_spaces()
                identifier = FuncCallStmt(identifier, args, self.start, self.end)
            elif self.current_token and self.current_token.token == 'xp_formatting':
                if not self.lookup_id_type(identifier.symbol, "a variable"):
                    raise SemanticError(f"NameError: Variable '{identifier.symbol}' does not exist.", self.start, self.end)
                value = re.sub(r'^"(.*)"$', r'\1', self.current_token.lexeme)
                if not re.match(r'^\.\d+f$', value):
                    raise SemanticError(f"FormatError: Invalid format specifier '{value}'.", self.start, self.end)
                digit = int(value[1])
                self.current_token = self.get_next_token() # eat format 
                self.skip_spaces()
                return XpFormatting(identifier, digit, self.start, self.end)
            else:
                if not self.lookup_identifier(identifier.symbol):
                    raise SemanticError(f"NameError: Variable '{identifier.symbol}' does not exist.", self.start, self.end)
                
                info = self.get_identifier_info(identifier.symbol)
                allowed_types = {"a variable"}
                if self.func_flag:
                    allowed_types.add("a parameter")
                    allowed_types.add("an array")
                if is_func_call:
                    allowed_types.add("an array")
                    allowed_types.add("a struct instance")

                if info["type"] not in allowed_types:
                    raise SemanticError(f"NameError: Identifier '{identifier.symbol}' is already declared as {info['type']}", self.start, self.end)

            return identifier
        elif tk == 'hp_ltr':
            literal = HpLiteral(self.current_token.lexeme, self.start, self.end)
            self.current_token = self.get_next_token()
            self.skip_spaces()
            return literal
        elif tk == 'xp_ltr':
            literal = XpLiteral(self.current_token.lexeme, self.start, self.end)
            self.current_token = self.get_next_token()
            self.skip_spaces()
            return literal
        elif re.match(r'^comms_ltr', tk) :
            value = re.sub(r'^"(.*)"$', r'\1', self.current_token.lexeme)
            literal = CommsLiteral(value, self.start, self.end)
            self.current_token = self.get_next_token()
            self.skip_spaces()
            return literal
        elif tk == 'flag_ltr':
            lexeme = self.current_token.lexeme 
            if lexeme == 'true':
                value = True
            else:
                value = False
            literal = FlagLiteral(value, self.start, self.end)
            self.current_token = self.get_next_token()
            self.skip_spaces()
            return literal
        elif tk == '(':
            self.current_token = self.get_next_token()
            self.skip_spaces()
            value = self.parse_expr(scope)  
            #print(value)
            if value.kind == 'XpFormatting':
                raise SemanticError("FormatError: xp formatting cannot be used as a value within a parentheses.", self.start, self.end)
            self.expect(')', "Unexpected token found inside parenthesised expression. Expected closing parenthesis.")
            self.skip_spaces()
            if self.current_token and self.current_token.token == 'xp_formatting':
                format_str = re.sub(r'^"(.*)"$', r'\1', self.current_token.lexeme)
                if not re.match(r'^\.\d+f$', format_str):
                    raise SemanticError(f"FormatError: Invalid format specifier '{format_str}'.", self.start, self.end)
                digit = int(format_str[1])
                self.current_token = self.get_next_token() # eat format 
                self.skip_spaces()
                return XpFormatting(value, digit, self.start, self.end)
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
                return UnaryExpr('-', expr, self.start, self.end)
            elif re.match(r'^id\d+$', self.current_token.token):
                identifier = Identifier(self.current_token.lexeme, self.start, self.end)
                self.current_token = self.get_next_token()
                self.skip_spaces()
                return UnaryExpr('-', identifier, self.start, self.end)
        elif tk == 'dead':
            self.current_token = self.get_next_token()
            self.skip_spaces()
            return DeadLiteral(None, None, self.start, self.end)
        elif tk == 'load' or tk == 'loadNum':
            raise SemanticError(f"ValueError: Cannot use load or loadNum function within string literals.", self.start, self.end)
        else:
            raise SemanticError(f"ParserError: Unexpected token found during parsing: {tk}", self.start, self.end)
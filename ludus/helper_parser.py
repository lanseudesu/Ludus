from .error import SemanticError
from .nodes import *
import re

class Helper:
    def __init__(self, tokens, scope_stack, func_flag):
        self.tokens = tokens
        self.current_token_index = 0
        self.current_token = self.get_next_token()
        self.scope_stack = scope_stack
        self.func_flag = func_flag

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
                    raise SemanticError(f"1 NameError: Identifier '{name}' is already declared as {info["type"]}.")
        return False
    
    def get_identifier_info(self, name):
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]  
        raise SemanticError(f"Identifier '{name}' not declared.")
    
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
            raise SemanticError(f"Parser Error: {error_message}")
        
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
        if self.current_token and self.current_token.token != ')':
            raise SemanticError(f"Unexpected token found during parsing: {self.current_token.token}")
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

    def parse_primary_expr(self, scope, is_func_call=False) -> Expr:
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
            if self.current_token and self.current_token.token == '.':
                if not self.lookup_identifier(identifier.symbol):
                    raise SemanticError(f"NameError: Struct instance '{identifier.symbol}' does not exist.")
                
                info = self.get_identifier_info(identifier.symbol)
                allowed_types = {"a struct instance"}
                if self.func_flag:
                    allowed_types.add("a parameter")
                
                if info["type"] not in allowed_types:
                    raise SemanticError(f"18 NameError: Identifier '{identifier.symbol}' is already declared as {info['type']}")
                
                self.current_token = self.get_next_token()
                self.skip_spaces()
                if self.current_token:
                    if not re.match(r'^id\d+$', self.current_token.token):
                        raise SemanticError("Expected 'id' after '.' in accessing a struct instance field.")
                field = Identifier(symbol=self.current_token.lexeme)
                identifier = StructInstField(identifier, field)
                self.current_token = self.get_next_token()
                self.skip_spaces()
            elif self.current_token and self.current_token.token == '[':
                dimensions = []
                if not self.lookup_identifier(identifier.symbol):
                    raise SemanticError(f"NameError: Array '{identifier.symbol}' does not exist.")
                
                info = self.get_identifier_info(identifier.symbol)
                allowed_types = {"an array"}
                if self.func_flag:
                    allowed_types.add("a parameter")

                if info["type"] not in allowed_types:
                    raise SemanticError(f"19 NameError: Identifier '{identifier.symbol}' is already declared as {info['type']}")

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
            elif self.current_token and self.current_token.token == '(':
                if not self.lookup_id_type(identifier.symbol, "a function"):
                    raise SemanticError(f"NameError: Function '{identifier.symbol}' does not exist.")
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
                identifier = FuncCallStmt(identifier, args)
            elif self.current_token and self.current_token.token == 'xp_formatting':
                if not self.lookup_id_type(identifier.symbol, "a variable"):
                    raise SemanticError(f"NameError: Variable '{identifier.symbol}' does not exist.")
                value = re.sub(r'^"(.*)"$', r'\1', self.current_token.lexeme)
                if not re.match(r'^\.\d+f$', value):
                    raise SemanticError(f"FormatError: Invalid format specifier '{value}'.")
                digit = int(value[1])
                self.current_token = self.get_next_token() # eat format 
                self.skip_spaces()
                return XpFormatting(identifier, digit)
            else:
                if not self.lookup_identifier(identifier.symbol):
                    raise SemanticError(f"NameError: Variable '{identifier.symbol}' does not exist.")
                
                info = self.get_identifier_info(identifier.symbol)
                allowed_types = {"a variable"}
                if self.func_flag:
                    allowed_types.add("a parameter")
                    allowed_types.add("an array")
                if is_func_call:
                    allowed_types.add("an array")
                    allowed_types.add("a struct instance")

                if info["type"] not in allowed_types:
                    raise SemanticError(f"20 NameError: Identifier '{identifier.symbol}' is already declared as {info['type']}")

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
        elif re.match(r'^comms_ltr', tk) :
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
            #print(value)
            if value.kind == 'XpFormatting':
                raise SemanticError("FormatError: xp formatting cannot be used as a value within a parentheses.")
            self.expect(')', "Unexpected token found inside parenthesised expression. Expected closing parenthesis.")
            self.skip_spaces()
            if self.current_token and self.current_token.token == 'xp_formatting':
                format_str = re.sub(r'^"(.*)"$', r'\1', self.current_token.lexeme)
                if not re.match(r'^\.\d+f$', format_str):
                    raise SemanticError(f"FormatError: Invalid format specifier '{format_str}'.")
                digit = int(format_str[1])
                self.current_token = self.get_next_token() # eat format 
                self.skip_spaces()
                return XpFormatting(value, digit)
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
        elif tk == 'dead':
            self.current_token = self.get_next_token()
            self.skip_spaces()
            return DeadLiteral(None, None)
        elif tk == 'load' or tk == 'loadNum':
            raise SemanticError(f"LoadError: Cannot use load or loadNum function within string literals.")
        else:
            raise SemanticError(f"6 Unexpected token found during parsing: {tk}")
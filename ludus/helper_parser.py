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
    
    def is_array(self, name):
        if self.lookup_identifier(name):
            info = self.get_identifier_info(name)
            if info["type"] == "an array":
                return True
            else:
                return False
        else:
            return False
        
    def is_params(self, name):
        if self.lookup_identifier(name):
            info = self.get_identifier_info(name)
            if info["type"] == "a parameter":
                return True
            else:
                return False
        else:
            return False
    
    def get_dimensions(self, name):
        info = self.get_identifier_info(name)
        if info["type"] != "an array":
            raise SemanticError(f"Identifier '{name}' is not an array", self.start, self.end)
        return info["dimensions"]
    
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
    
    def find_token_in_line(self, target_token):
        la_token_index = self.current_token_index

        while la_token_index < len(self.tokens):
            la_token = self.tokens[la_token_index]

            if la_token.token == target_token:
                return la_token

            if la_token.token in {':', 'newline', 'EOF'}:  
                break

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
                
                join_token = self.find_token_in_line('drop')
                if join_token:
                    return self.parse_drop(scope, identifier, self.start)

                join_token = self.find_token_in_line('seek')
                if join_token:
                    return self.parse_seek(scope, identifier, self.start)
                
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
                arr_exist = self.is_array(identifier.symbol) or self.is_params(identifier.symbol)
                if arr_exist:
                    join_token = self.find_token_in_line('drop')
                    if join_token:
                        return self.parse_drop2d(scope, identifier, self.start)
                    
                    join_token = self.find_token_in_line('seek')
                    if join_token:
                        return self.parse_seek2d(scope, identifier, self.start)
                
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
                while self.current_token.token != ')':
                    la_token = self.look_ahead()
                    if la_token.token == ',' or la_token.token == ')':
                        arg = self.parse_primary_expr(scope, 'func_call')
                    else:
                        arg = self.parse_expr(scope)
                    args.append(arg)
                    self.skip_spaces()
                    if self.current_token.token == ',':
                        self.current_token = self.get_next_token() # eat ,
                        self.skip_spaces()
                self.current_token = self.get_next_token() # eat )
                self.skip_spaces()
                identifier = FuncCallStmt(identifier, args, self.start, self.end, self.start, self.end)
           
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
        elif tk == 'rounds':
            self.current_token = self.get_next_token() # eat rounds
            self.expect('(', "Expected '(' after 'rounds'.")
            self.skip_spaces()
            value = self.parse_primary_expr(scope, 'rounds')
            if value.kind not in ['Identifier', 'ArrayElement', 'StructInstField', 'FuncCallStmt',
                                  'CommsLiteral', 'ToCommsStmt']: 
                raise SemanticError("ArgumentError: Invalid rounds argument.", self.start, self.end)
            self.skip_spaces()
            self.expect(')', "Expected ')' after rounds arguments.")
            self.skip_spaces()
            return RoundStmt(value, self.start, self.end)
        elif tk in ('levelUp', 'levelDown'):
            self.current_token = self.get_next_token()  # consume levelUp or levelDown
            self.expect('(', f"Expected '(' after '{tk}'.")
            self.skip_spaces()
            value = self.parse_primary_expr(scope, None)
            valid_kinds = ['Identifier', 'ArrayElement', 'StructInstField', 'FuncCallStmt',
                           'ToCommsStmt']  
            if value.kind not in valid_kinds:
                raise SemanticError(f"ArgumentError: Invalid '{tk}' argument.", self.start, self.end)
            self.skip_spaces()
            self.expect(')', f"Expected ')' after '{tk}' arguments.")
            self.skip_spaces()
            return LevelStmt(value, tk == 'levelUp', self.start, self.end)
        elif tk in ('toHp', 'toXp'):
            self.current_token = self.get_next_token()  # consume toHp or toHp
            self.expect('(', f"Expected '(' after '{tk}'.")
            self.skip_spaces()
            value = self.parse_primary_expr(scope,None)
            valid_kinds = ['Identifier', 'ArrayElement', 'StructInstField'] 
            if value.kind not in valid_kinds:
                raise SemanticError(f"ArgumentError: Invalid '{tk}' argument.", self.start, self.end)
            self.skip_spaces()
            self.expect(')', f"Expected ')' after '{tk}' arguments.")
            self.skip_spaces()
            return ToNumStmt(value, tk == 'toHp', self.start, self.end)
        elif tk == 'toComms':
            self.current_token = self.get_next_token()  # consume toComms
            self.expect('(', f"Expected '(' after '{tk}'.")
            self.skip_spaces()
            value = self.parse_primary_expr(scope, None)
            valid_kinds = ['Identifier', 'ArrayElement', 'StructInstField'] 
            if value.kind not in valid_kinds:
                raise SemanticError(f"ArgumentError: Invalid '{tk}' argument.", self.start, self.end)
            self.skip_spaces()
            self.expect(')', f"Expected ')' after '{tk}' arguments.")
            self.skip_spaces()
            return ToCommsStmt(value, self.start, self.end)
        else:
            raise SemanticError(f"ParserError: Unexpected token found during parsing: {tk}", self.start, self.end)
        
    def parse_drop(self, scope, name, pos_start) -> DropStmt:
        if self.lookup_identifier(name.symbol):
            info = self.get_identifier_info(name.symbol)
            if info["type"] != "an array" and info["type"] != "a parameter":
                raise SemanticError(f"NameError: Array '{name.symbol}' is not defined.", self.start, self.end)
        else:
            raise SemanticError(f"NameError: Array '{name.symbol}' is not defined.", self.start, self.end)
        if info["type"] == "a parameter":
            dimensions = None
        elif info["type"] == "an array":
            dimensions = self.get_dimensions(name.symbol)
        self.expect(".", "Expects '.' in drop function call.")
        self.expect("drop", "Expects 'drop' keyword in drop function call.")
        self.expect("(", "Expects '(' after drop keyword in drop function call.")   
        self.skip_spaces()
        index = None
        if self.current_token.token != ')':
            value = self.parse_expr(scope)
            index = value
            self.skip_spaces()
        self.expect(")", "Expects ')' after to close drop arguments.")
        self.skip_spaces()
        return DropStmt(name, index, dimensions, self.start, self.end)
    
    def parse_drop2d(self, scope, arr_name, pos_start) -> DropStmt:
        self.expect("[", "Expects '[' to specify row index of two-dimensional array.")
        self.skip_spaces()
        if self.current_token.token == ']':
            raise SemanticError("IndexError: Index must not be blank for drop function call.", self.start, self.end)
        dim = self.parse_expr(scope)
        self.skip_spaces()
        self.expect("]", "Expected ']' to close array dimension declaration.")
        self.skip_spaces()
        info = self.get_identifier_info(arr_name.symbol)
        if info["type"] == "an array":
            dimensions = self.get_dimensions(arr_name.symbol)
        else:
            dimensions = None
        if dimensions is None or dimensions == 2:
            pass
        else:
            raise SemanticError("DimensionsError: Trying to drop specific row from a one dimensional array, must be two-dimensional.", self.start, self.end)
        self.expect(".", "Expects '.' in drop function call.")
        self.expect("drop", "Expects 'drop' keyword in drop function call.")
        self.expect("(", "Expects '(' after drop keyword in drop function call.")
        self.skip_spaces()
        index = None
        if self.current_token.token != ')':
            value = self.parse_expr(scope)
            index = value
            self.skip_spaces()
        self.expect(")", "Expects ')' after to close drop arguments.")
        self.skip_spaces()
        return DropStmt(arr_name, index, dimensions, self.start, self.end, dim)

    def parse_seek(self, scope, name, pos_start) -> SeekStmt:
        if self.lookup_identifier(name.symbol):
            info = self.get_identifier_info(name.symbol)
            if info["type"] != "an array" and info["type"] != "a parameter":
                raise SemanticError(f"NameError: Array '{name.symbol}' is not defined.", self.start, self.end)
        else:
            raise SemanticError(f"NameError: Array '{name.symbol}' is not defined.", self.start, self.end)
        if info["type"] == "a parameter":
            dimensions = None
        elif info["type"] == "an array":
            dimensions = self.get_dimensions(name.symbol)
        self.expect(".", "Expects '.' in seek function call.")
        self.expect("seek", "Expects 'seek' keyword in seek function call.")
        self.expect("(", "Expects '(' after seek keyword in seek function call.")
        self.skip_spaces()
        if self.current_token.token == '[':
            if dimensions is None or dimensions == 2:
                pass
            else:
                raise SemanticError("DimensionsError: Trying to seek a specific row in a 1d array, must be a 2d array.", self.start, self.end)
            self.current_token = self.get_next_token() # eat [
            self.skip_spaces()
            values = [self.parse_inner_arr_values(scope)]
            self.expect("]", "Expects ']' to close array row values.")
            self.skip_spaces()
            self.expect(")", "Expects ')' after to close seek arguments.")
            self.skip_spaces()
            return SeekStmt(name, values, 2, self.start, self.end)
        else:
            if dimensions is None or dimensions == 1:
                pass
            else:
                raise SemanticError("DimensionsError: Trying to seek a specific element in a 2d array, must specify row index first.", self.start, self.end)
            if self.current_token.token == ')':
                raise SemanticError("ValueError: Elements inside parentheses must not be empty.", self.start, self.end)
            value = self.parse_expr(scope)
            self.skip_spaces()
            self.expect(")", "Expects ')' after to close seek arguments.")
            self.skip_spaces()
            return SeekStmt(name, value, 1, self.start, self.end)
        
    def parse_seek2d(self, scope, arr_name, pos_start) -> SeekStmt:
        self.expect("[", "Expects '[' to specify row index of two-dimensional array.")
        self.skip_spaces()
        if self.current_token.token == ']':
            raise SemanticError("IndexError: Index must not be blank for seek function call.", self.start, self.end)
        dim = self.parse_expr(scope)
        self.skip_spaces()
        self.expect("]", "Expected ']' to close array dimension declaration.")
        self.skip_spaces()
        info = self.get_identifier_info(arr_name.symbol)
        if info["type"] == "an array":
            dimensions = self.get_dimensions(arr_name.symbol)
        else:
            dimensions = None
        if dimensions is None or dimensions == 2:
            pass
        else:
            raise SemanticError("DimensionsError: Trying to seek a specific row in a 1d array, must be a 2d array.", self.start, self.end)
        self.expect(".", "Expects '.' in seek function call.")
        self.expect("seek", "Expects 'seek' keyword in seek function call.")
        self.expect("(", "Expects '(' after seek keyword in seek function call.")
        self.skip_spaces()
        if self.current_token.token == ')':
            raise SemanticError("ValueError: Elements inside parentheses must not be empty.", self.start, self.end)
        value = self.parse_expr(scope)
        self.skip_spaces()
        self.expect(")", "Expects ')' after to close seek arguments.")
        self.skip_spaces()
        return SeekStmt(arr_name, value, 2, self.start, self.end, dim)
    
    def parse_inner_arr_values(self, scope):
        inner_values = []
        while self.current_token and self.current_token.token != ']':
            value = self.parse_expr(scope)
            if value.kind not in ["HpLiteral", "XpLiteral", "CommsLiteral", "FlagLiteral"]:
                 raise SemanticError("TypeError: Arrays can only be initialied with literal values.", self.start, self.end)
            inner_values.append(value)
            self.skip_spaces()
            if self.current_token.token == ',':
                self.current_token = self.get_next_token()  # eat ,
                self.skip_spaces()
        return inner_values
from .lexer import Lexer
from .nodes import *
from .parser import parse
import re
from typing import Union
from .runtime.traverser import ASTVisitor, SemanticAnalyzer
from .error import SemanticError
from ludus import lexer
from .helper_parser import Helper

class Semantic:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        self.current_token = self.get_next_token()
        self.globalstruct = []
        self.global_func = {}
        self.scope_stack = [{}]
        self.loop_flag = False
        self.flank_flag = False
        self.func_flag = False
        self.func_call_flag = False
        self.recall_stmts = []
    
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
                    raise SemanticError(f"1 NameError: Identifier '{name}' is already declared as {info["type"]}.")
        return False
    
    def get_identifier_info(self, name):
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]  
        raise SemanticError(f"Identifier '{name}' not declared.")
    
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
    
    def find_token_in_line(self, target_token):
        la_token_index = self.current_token_index

        while la_token_index < len(self.tokens):
            la_token = self.tokens[la_token_index]

            if la_token.token == target_token:
                return la_token

            if la_token.token in {'newline', 'EOF'}:  
                break

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
                            raise SemanticError(f"2 NameError: Identifier {name}' was "
                                                f"already declared as {info["type"]}.")
                        program.body.append(self.parse_var_init("global"))
                    elif la_token is not None and la_token.token == '[':  
                        if self.lookup_identifier(name):
                            info = self.get_identifier_info(name)
                            raise SemanticError(f"3 NameError: Identifier {name}' was "
                                                f"already declared as {info["type"]}.")
                        program.body.append(self.parse_array("global"))
                    else:
                        raise SemanticError(f"1 Unexpected token found during parsing: {la_token.token}")
                elif self.current_token and self.current_token.token in ['hp','xp','comms','flag']:
                    program.body.append(self.var_or_arr("global"))
                elif self.current_token and self.current_token.token == 'immo':
                    program.body.append(self.parse_immo("global"))
                    self.current_token = self.get_next_token()
                elif self.current_token and self.current_token.token == 'build':
                    program.body.append(self.parse_globalstruct())
                elif self.current_token and self.current_token.token == 'play':
                    program.body.append(self.parse_play())
                elif self.current_token and self.current_token.token == 'generate':
                    program.body.append(self.parse_func())
                elif self.current_token and self.current_token.token == 'gameOver':
                    break
                else:
                    raise SemanticError(f"2 Unexpected token found during parsing: {self.current_token.token}")
            if self.global_func:
                first_func = next(iter(self.global_func))  
                raise SemanticError(f"FunctionError: Function '{first_func}' was declared but not initialized.")
            if self.globalstruct:
                raise SemanticError(f"StructError: Global struct '{self.globalstruct[0]}' was declared but not initialized.")
        
        except SemanticError as e:
            return e
        return program
                
    def parse_func(self) -> Union[GlobalFuncDec, GlobalFuncBody]: 
        self.current_token = self.get_next_token() # eat generate
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("Expected struct name after 'generate'.")
        func_name = Identifier(self.current_token.lexeme)
        if self.lookup_identifier(func_name.symbol):
            info = self.get_identifier_info(func_name.symbol)
            if info["type"] != "a function":
                raise SemanticError(f"NameError: Function name '{func_name.symbol}' was "
                                    f"already declared as {info["type"]}.")
        self.declare_id(func_name.symbol, "a function")
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        self.expect("(", "Expected '(' after function name.")
        self.skip_spaces()
        param_names = []
        params = []
        while self.current_token.token != ')':
            if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("Expected parameter name after inside parantheses.")
            param_name = self.current_token.lexeme
            if param_name in param_names:
                raise SemanticError(f"ParamError: Duplicate parameter names: '{param_name}'")
            param_names.append(param_name)
            if self.lookup_identifier(param_name):
                raise SemanticError("ParamError: Parameter's name cannot be the same with a global element.")
            self.current_token = self.get_next_token() # eat id
            self.skip_spaces()
            if self.current_token.token == ':':
                self.current_token = self.get_next_token() # eat :
                self.skip_spaces()
                param_val = self.parse_expr(func_name.symbol)
                self.skip_spaces()
                params.append(Params(param_name, param_val))
            else:
                params.append(Params(param_name))

            if self.current_token.token == ',':
                self.current_token = self.get_next_token() # eat ,
                self.skip_spaces()

        self.current_token = self.get_next_token() # eat )
        self.skip_whitespace()

        if self.current_token.token == '{':
            if func_name.symbol in self.global_func:
                existing_params = self.global_func[func_name.symbol]["params"]

                if str(existing_params) != str(params):
                    raise SemanticError(
                        f"Parameter mismatch for function '{func_name.symbol}'. "
                    )
                del self.global_func[func_name.symbol]
                return self.create_func(func_name, params)
            raise SemanticError(f"NameError: User-defined function '{func_name.symbol}' was not declared.")
        else:
            if func_name.symbol in self.global_func:
                raise SemanticError(f"NameError: User-defined function '{func_name.symbol}' was already declared.")
            self.global_func[func_name.symbol] = {
                "params" : params
            }
            return GlobalFuncDec(func_name, params)
    
    def create_func(self, name, params) -> GlobalFuncBody:
        self.push_scope()
        if params:
            for param in params:
                self.declare_id(param.param, "a parameter")
        func_name = name.symbol
        self.current_token = self.get_next_token() # eat {
        self.skip_whitespace()
        body = []
        self.func_flag = True
        self.recall_stmts = []
        while self.current_token and self.current_token.token != '}':
            stmt = self.parse_stmt(func_name)
            body.append(stmt)
            self.skip_whitespace()
            if isinstance(stmt, RecallStmt):
                self.recall_stmts.append(stmt)
        self.expect("}", "Expected '}' to close a function's body.")
        self.skip_whitespace()
        self.pop_scope()
        self.func_flag = False
        return GlobalFuncBody(name, params, body, self.recall_stmts)
    
    def parse_play(self) -> PlayFunc:
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

        ###### decs and ass ######
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
            elif la_token is not None and la_token.token == '(':
                if self.current_token.lexeme in self.global_func:
                    return self.parse_func_call(scope)
                else:
                    raise SemanticError(f"FunctionCallError: Function {self.current_token.lexeme} does not exist.")
            else:
                raise SemanticError(f"3 Unexpected token found during parsing: {la_token.token}")
        elif self.current_token and self.current_token.token in ['hp','xp','comms','flag']:
            return self.var_or_arr(scope)
        elif self.current_token and self.current_token.token == 'build':
            return self.parse_struct(scope)
        elif self.current_token and self.current_token.token == 'access':
            return self.parse_struct_inst(scope)
        elif self.current_token and self.current_token.token == 'immo':
            return self.parse_immo(scope)
        
        ###### conditionals ######
        elif self.current_token and self.current_token.token == 'if':
            return self.parse_if(scope)
        elif self.current_token and self.current_token.token == 'flank':
            return self.parse_flank(scope)
        
        ###### loop control ######
        elif self.current_token and self.current_token.token == 'resume':
            if self.flank_flag or self.loop_flag:
                self.current_token = self.get_next_token()
                self.skip_whitespace()
                return ResumeStmt()
            else:
                raise SemanticError(f"ResumeError: Cannot use resume statement if not within a flank choice body.")
        elif self.current_token and self.current_token.token == 'checkpoint':
            if self.loop_flag:
                self.current_token = self.get_next_token()
                self.skip_whitespace()
                return CheckpointStmt()
            else:
                raise SemanticError(f"ResumeError: Cannot use checkpoint statement if not within a loop body.")
       
       ###### loops ######
        elif self.current_token and self.current_token.token == 'for':
             return self.parse_for(scope)
        elif self.current_token and self.current_token.token == 'grind':
             return self.parse_grind_while(scope)
        elif self.current_token and self.current_token.token == 'while':
             return self.parse_while(scope)
        
        elif self.current_token and self.current_token.token == 'recall':
             if self.func_flag:
                return self.parse_recall(scope)
             else:
                raise SemanticError(f"RecallError: Cannot use recall if not within a user-defined function body.")
        
        ###### built-in funcs ######
        elif self.current_token and self.current_token.token in ['shoot', 'shootNxt']:
            return self.parse_shoot(scope)
        elif self.current_token and self.current_token.token == 'wipe':
            self.current_token = self.get_next_token()
            self.expect("(", "Expects a parentheses after wipe keyword.")
            self.skip_spaces()
            self.expect(")", "Expects a closing parentheses.")
            self.skip_whitespace()
            return WipeStmt()
        else:
            raise SemanticError(f"4 Unexpected token found during parsing: {self.current_token.token}")

    def parse_recall(self, scope) -> RecallStmt:
        self.current_token = self.get_next_token() # eat recall
        self.skip_spaces()
        stmt = []
        while self.current_token.token != 'newline':
            if self.current_token.token == '[':
                self.current_token = self.get_next_token() # eat [
                self.skip_spaces()
                self.expect("]", "Expected '[' after ']'")
                self.skip_spaces()
                stmt.append([])
            elif self.current_token.token == 'void':
                stmt.append('void')
                self.current_token = self.get_next_token() # eat void
                self.skip_spaces()
            else:
                value = self.parse_expr(scope)
                self.skip_spaces()
                stmt.append(value)
            
            if self.current_token.token == ',':
                self.current_token = self.get_next_token() # eat ,
                self.skip_spaces()

        return RecallStmt(stmt)

    def parse_func_call(self, scope) -> FuncCallStmt:
        func_name = Identifier(self.current_token.lexeme)
        if not self.lookup_id_type(func_name.symbol, "a function"):
            raise SemanticError(f"NameError: Function '{func_name.symbol}' does not exist.")
        self.current_token = self.get_next_token() # eat id
        self.expect("(", "Expects '(' after function name.")
        args = []
        self.skip_spaces()

        while self.current_token.token != ')':
            la_token = self.look_ahead()
            if la_token.token == ',' or la_token.token == ')':
                arg = self.parse_primary_expr(scope, True)
            else:
                arg = self.parse_expr(scope)
            args.append(arg)
            self.skip_spaces()
            if self.current_token.token == ',':
                self.current_token = self.get_next_token() # eat ,
                self.skip_spaces()
        self.current_token = self.get_next_token() # eat )
        self.skip_whitespace()
        return FuncCallStmt(func_name, args)
    
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
                raise SemanticError(f"4 NameError: Identifier {name}' was "
                                    f"already declared as {info["type"]}.")
            return self.parse_empty_array(datatype, scope)
        else:
            if self.lookup_identifier(name):
                info = self.get_identifier_info(name)
                raise SemanticError(f"5 NameError: Identifier {name}' was "
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
                is_func = False
                self.current_token = self.get_next_token() # eat :
                self.skip_spaces()
                value = self.parse_expr(scope)
                declarations = []
                for var in var_names:
                    info = self.lookup_identifier(var.symbol)
                    if info:
                        info = self.get_identifier_info(var.symbol)
                        if info["type"] == 'a parameter':
                            self.declare_id(var.symbol, "a variable")
                            declarations.append(VarAssignment(var, ":", value))
                        elif info["type"] != "a variable":
                            raise SemanticError(f"6 NameError: Identifier {var.symbol}' was "
                                                f"already declared as {info["type"]}.")
                        else:
                            declarations.append(VarAssignment(var, ":", value))
                    else:
                        declarations.append(VarDec(var, value, False, scope))
                        self.declare_id(var.symbol, "a variable")

                self.skip_spaces()
                return BatchVarDec(declarations, True)

        self.current_token = self.get_next_token() # eat :
        self.skip_spaces()

        if self.current_token.token == '[' and self.func_flag:
            info = self.lookup_identifier(name)
            if info:
                info = self.get_identifier_info(name)
                if info["type"] != 'a parameter':
                    raise SemanticError(f"21 NameError: Identifier {name}' was "
                                        f"already declared as {info["type"]}.")
                else:
                    values = []
                    while self.current_token and self.current_token.token != 'newline':
                        self.expect("[", "Expected '[' for array values.")
                        self.skip_spaces()
                        inner_values = self.parse_inner_arr_values(scope)
                        self.expect("]", "Expected ']' to close array values.")
                        self.skip_spaces()
                        if self.current_token.token == ',':
                            values.append(inner_values)
                            self.current_token = self.get_next_token()  # eat ,
                            self.skip_spaces()
                        else:
                            values = inner_values
                            break
                    return ArrayRedec(name, None, values, False, scope)
                

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
            declarations = []
            for var in var_names:
                info = self.lookup_identifier(var.symbol)
                if info:
                    info = self.get_identifier_info(var.symbol)
                    if info["type"] == 'a parameter':
                        self.declare_id(var.symbol, "a variable")
                        declarations.append(VarAssignment(var, ":", values_table[var.symbol]['values']))
                    elif info["type"] != "a variable":
                        raise SemanticError(f"7 NameError: Identifier '{var.symbol}' was "
                                            f"already declared as {info["type"]}.")
                    else:
                        declarations.append(VarAssignment(var, ":", values_table[var.symbol]['values']))
                else:
                    declarations.append(VarDec(var, values_table[var.symbol]['values'], False, scope))
                    self.declare_id(var.symbol, "a variable")
           
            return BatchVarDec(declarations)
        else:
            var = var_names[0]
            info = self.lookup_identifier(var.symbol)
            if info:
                info = self.get_identifier_info(var.symbol)
                if info["type"] != "a variable" and info["type"] != "a parameter":
                    raise SemanticError(f"8 NameError: Identifier '{var.symbol}' was "
                                        f"already declared as {info["type"]}.")
                else:
                    if info["type"] == "a parameter" and isinstance(value, Identifier):
                        if self.is_array(value.symbol):
                            return ArrayRedec(var.symbol, None, value.symbol, False, scope)
                        return ArrayOrVar(var.symbol, [VarAssignment(var, ':', value), ArrayRedec(var.symbol, None, value.symbol, False, scope)])
                    return VarAssignment(var, ':', value)
            else:
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
                    raise SemanticError(f"9 NameError: Identifier {var.symbol}' was "
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
                    raise SemanticError(f"10 NameError: Identifier {var.symbol}' was "
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

            self.skip_whitespace()
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
        arr_exist = self.is_array(name) or self.is_params(name)
        if arr_exist:
            join_token = self.find_token_in_line('join')
            if join_token:
                return self.parse_join2d(scope, arr_name)
            
            join_token = self.find_token_in_line('drop')
            if join_token:
                return self.parse_drop2d(scope, arr_name)

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
                    raise SemanticError(f"DeclarationError: Identifier '{name}' was already declared.")
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
        elif re.match(r'^id\d+$', self.current_token.token):
            rhs_name = self.current_token.lexeme
            la_token = self.look_ahead()
            if la_token.token == '(':
                if not self.lookup_id_type(rhs_name, "a function"):
                    raise SemanticError(f"NameError: Function '{rhs_name}' does not exist.")
                values = self.parse_func_call(scope)
                return ArrayRedec(name, dimensions, values, False, scope)
            self.current_token = self.get_next_token() # eat id
            self.skip_whitespace()
            info = self.lookup_identifier(rhs_name)
            if info:
                info = self.get_identifier_info(rhs_name)
                if info["type"] == 'a parameter':
                    self.declare_id(name, "an array")
                    return ArrayRedec(name, dimensions, rhs_name, False, scope)
                elif info["type"] != "an array":
                    raise SemanticError(f"RedeclarationError: Array '{name}' is being redeclared with"
                                        " non-array element.")
                else:
                    return ArrayRedec(name, dimensions, rhs_name, False, scope)
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
        self.skip_whitespace()
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
        if self.lookup_identifier(struct_name.symbol):
            info = self.get_identifier_info(struct_name.symbol)
            raise SemanticError(f"22 NameError: Identifier '{struct_name.symbol}' is already declared as {info["type"]}.")
        
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
                if self.lookup_identifier(field_name.symbol):
                    info = self.get_identifier_info(field_name.symbol)
                    raise SemanticError(f"23 NameError: Field name '{field_name.symbol}' cannot be used since it is already declared as {info["type"]}.")
                if field_name.symbol in fields_table:
                    raise SemanticError(f"FieldError: Duplicate field name detected: '{field_name.symbol}'.")
                fields_table.append(field_name.symbol)
                self.skip_whitespace()
            else:
                fields.append(StructFields(field_name, None, datatype))
                if self.lookup_identifier(field_name.symbol):
                    info = self.get_identifier_info(field_name.symbol)
                    raise SemanticError(f"24 NameError: Field name '{field_name.symbol}' cannot be used since it is already declared as {info["type"]}.")
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
            raise SemanticError(f"11 NameError: Identifier {name}' was "
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
        if self.lookup_identifier(inst_name.symbol):
            info = self.get_identifier_info(inst_name.symbol)
            raise SemanticError(f"23 NameError: Identifier '{inst_name.symbol}' is already declared as {info["type"]}.")
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
            raise SemanticError(f"12 NameError: Identifier {inst_name.symbol}' was "
                                f"already declared as {info["type"]}.") 
        self.declare_id(inst_name.symbol, "a struct instance")
        return StructInst(inst_name, struct_parent, values, False)

    def parse_inst_ass(self, scope) -> InstAssignment:
        struct_inst_name = Identifier(self.current_token.lexeme)
        self.current_token = self.get_next_token() # eat id
        join_token = self.find_token_in_line('join')
        if join_token:
            return self.parse_join(scope, struct_inst_name)
        
        join_token = self.find_token_in_line('drop')
        if join_token:
            return self.parse_drop(scope, struct_inst_name)

        if self.lookup_identifier(struct_inst_name.symbol):
            info = self.get_identifier_info(struct_inst_name.symbol)
            if info["type"] != "a struct instance" and info["type"] != "a parameter":
                raise SemanticError(f"NameError: Struct instance '{struct_inst_name.symbol}' is not defined.")
        else:
            raise SemanticError(f"NameError: Struct instance '{struct_inst_name.symbol}' is not defined.")
        
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
                raise SemanticError(f"5 Unexpected token found during parsing: {la_token}")  
            
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
                        raise SemanticError(f"13 NameError: Identifier '{var.symbol}' is already declared as {info["type"]}.")  
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
                    raise SemanticError(f"14 NameError: Identifier '{var.symbol}' is already declared as {info["type"]}.")  
                self.declare_id(var.symbol, "a variable")
            return BatchVarDec(declarations=[VarDec(var, values_table[var.symbol]['values'], True, scope) for var in var_names])
        else:
            var = var_names[0]
            if self.lookup_identifier(var.symbol):
                info = self.get_identifier_info(var.symbol)
                raise SemanticError(f"15 NameError: Identifier '{var.symbol}' is already declared as {info["type"]}.")    
            self.declare_id(var.symbol, "a variable")
            return VarDec(var, value, True, scope)

    def parse_immo_arr(self, scope) -> ArrayDec:
        arr_name = Identifier(self.current_token.lexeme)
        name=arr_name.symbol
        if self.lookup_identifier(name):
            info = self.get_identifier_info(name)
            raise SemanticError(f"16 NameError: Identifier '{name}' is already declared as {info["type"]}.")
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
            raise SemanticError(f"17 NameError: Identifier '{inst_name.symbo}' is already declared as {info["type"]}.")
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
            if self.current_token.token == '.':
                join_token = self.find_token_in_line('join')
                if join_token:
                    return self.parse_join(scope, identifier)
                
                join_token = self.find_token_in_line('drop')
                if join_token:
                    return self.parse_drop(scope, identifier)

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
                if not re.match(r'^id\d+$', self.current_token.token):
                    raise SemanticError("Expected 'id' after '.' in accessing a struct instance field.")
                field = Identifier(symbol=self.current_token.lexeme)
                identifier = StructInstField(identifier, field)
                self.current_token = self.get_next_token()
                self.skip_spaces()
            elif self.current_token.token == '[':
                arr_exist = self.is_array(identifier.symbol) or self.is_params(identifier.symbol)
                if arr_exist:
                    join_token = self.find_token_in_line('join')
                    if join_token:
                        return self.parse_join2d(scope, identifier)
                    
                    join_token = self.find_token_in_line('drop')
                    if join_token:
                        return self.parse_drop2d(scope, identifier)
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
            elif self.current_token.token == '(':
                if not self.lookup_id_type(identifier.symbol, "a function"):
                    raise SemanticError(f"NameError: Function '{identifier.symbol}' does not exist.")
                self.current_token = self.get_next_token() # eat ( 
                self.skip_spaces()
                args = []       
                while self.current_token.token != ')':
                    la_token = self.look_ahead()
                    if la_token.token == ',' or la_token.token == ')':
                        arg = self.parse_primary_expr(scope, True)
                    else:
                        arg = self.parse_expr(scope)
                    args.append(arg)
                    self.skip_spaces()
                    if self.current_token.token == ',':
                        self.current_token = self.get_next_token() # eat ,
                        self.skip_spaces()
                self.current_token = self.get_next_token() # eat )
                self.skip_spaces()
                identifier = FuncCallStmt(identifier, args)
            elif self.current_token.token == 'xp_formatting':
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
            print(value)
            open_braces = 0
            placeholders = []
            current_placeholder = ""
            inside_placeholder = False
            final_value = ""
            escaped = False

            for i, char in enumerate(value):
                if escaped:
                    if char in {'{', '}'}:
                        final_value += char  
                    else:
                        final_value += '\\' + char  
                    escaped = False
                    continue

                if char == '\\':
                    escaped = True
                    continue

                if char == '{':
                    if inside_placeholder:
                        raise SemanticError("FormatError: Nested or unexpected '{' found in string literal.")
                    inside_placeholder = True
                    open_braces += 1
                    current_placeholder = ""
                elif char == '}':
                    if not inside_placeholder:
                        raise SemanticError("FormatError: Unexpected '}' found in string literal.")
                    inside_placeholder = False
                    open_braces -= 1
                    if not current_placeholder:
                        raise SemanticError("FormatError: Empty placeholder '{}' found in string literal.")
                    placeholders.append(current_placeholder)
                else:
                    if inside_placeholder:
                        current_placeholder += char
                    else:
                        final_value += char

            if open_braces > 0:
                raise SemanticError("FormatError: Unclosed '{' found in string literal.")

            print(f"Placeholders: {placeholders}")
            print(f"Final string: {final_value}")
            if placeholders:
                results = []
                for i, placeholder in enumerate(placeholders):
                    tokens, error = lexer.run("yo", placeholder)
                    if error:
                        raise SemanticError(f"Lexical error in placeholder {i}: cannot proceed to parsing.\n"+ str(error))
                    print(tokens)
                    tokens.pop()
                    helper = Helper(tokens, self.scope_stack, self.func_flag)
                    result = helper.parse_expr(scope)
                    if isinstance(result, SemanticError):
                        raise SemanticError(f"Error in placeholder {i+1}: {str(result)}")
                    results.append(result)
                literal = FormattedCommsLiteral(value, placeholders, results)
                self.current_token = self.get_next_token()
                self.skip_spaces()
                return literal

            literal = CommsLiteral(final_value)
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
            if self.current_token.token == 'xp_formatting':
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
            prompt_msg = None
            self.current_token = self.get_next_token() # eat load
            if self.current_token.token != '(':
                raise SemanticError("LoadError: Missing parentheses.")
            self.current_token = self.get_next_token() # eat (
            self.skip_spaces()
            if self.current_token.token == 'comms_ltr':
                value = re.sub(r'^"(.*)"$', r'\1', self.current_token.lexeme)
                prompt_msg = CommsLiteral(value)
                self.current_token = self.get_next_token() # eat comms
                self.skip_spaces()
            if self.current_token.token != ')':
                raise SemanticError("LoadError: Missing parentheses.")
            self.current_token = self.get_next_token() # eat )
            self.skip_spaces()
            if tk == 'load':
                return Load(prompt_msg)
            else:
                return LoadNum(prompt_msg)
        else:
            raise SemanticError(f"6 Unexpected token found during parsing: {tk}")
        
    ########### CONDITIONALS #############
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
            if isinstance(stmt, RecallStmt):
                self.recall_stmts.append(stmt)
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
                if isinstance(stmt, RecallStmt):
                    self.recall_stmts.append(stmt)

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
                if isinstance(stmt, RecallStmt):
                    self.recall_stmts.append(stmt)

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
            raise SemanticError("FlankError: There must be at least one choice statement in a flank statement.")
        
        self.flank_flag = True
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
                stmt = self.parse_stmt(scope, True)
                choice_body.append(stmt)
                self.skip_whitespace()
                if isinstance(stmt, RecallStmt):
                    self.recall_stmts.append(stmt)
            self.pop_scope()
            choices.append(ChoiceStmts(values, choice_body))
        
        if not self.current_token or self.current_token.token != 'backup':
            self.flank_flag = False
            raise SemanticError("FlankError: A flank statement must include a backup statement.")

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
            if isinstance(stmt, RecallStmt):
                self.recall_stmts.append(stmt)
        self.pop_scope()

        self.expect("}", "Expected '}' to close a flank statement's body.")
        self.skip_whitespace()
        self.flank_flag = False
        return FlankStmt(expression, choices, backup_body)

    ########## LOOPS #############
    def parse_for(self,scope) -> ForStmt:
        self.current_token = self.get_next_token() # eat for
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("ForError: Expected variable name after for keyword.")
        name = self.current_token.lexeme
        if not self.lookup_id_type(name, "a variable"):
            raise SemanticError(f"NameError: Variable '{name}' is not defined.")
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        self.expect(":", "ForError: Expected ':' after identifier in loop control initialization.")
        self.skip_spaces()
        init_value = self.parse_expr(scope)
        initialization = VarAssignment(name, ":", init_value)
        self.skip_spaces()
        self.expect(",", "ForError: Expected ',' after loop control initialization.")
        self.skip_spaces()
        condition = self.parse_expr(scope)
        self.skip_spaces()
        self.expect(",", "ForError: Expected ',' after loop condition.")
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("ForError: Expected variable name after loop condition.")
        upd_name = Identifier(self.current_token.lexeme)
        if not self.lookup_id_type(upd_name.symbol, "a variable"):
            raise SemanticError(f"NameError: Variable '{upd_name}' is not defined.")
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        operator = self.current_token.token
        self.current_token = self.get_next_token() # eat operator
        self.skip_spaces()
        upd_value = self.parse_expr(scope)
        update = VarAssignment(upd_name, operator, upd_value)
        self.skip_whitespace()
        self.expect("{", "Expected '{' to open a for loop statement's body.")
        self.skip_whitespace()
        body = []
        self.push_scope()
        self.loop_flag = True
        while self.current_token and self.current_token.token != "}":
            stmt = self.parse_stmt(scope)
            body.append(stmt)
            self.skip_whitespace()
            if isinstance(stmt, RecallStmt):
                self.recall_stmts.append(stmt)
        self.expect("}", "Expected '}' to close a for loop statement's body.")
        self.skip_whitespace()
        self.pop_scope()
        self.loop_flag = False
        return ForStmt(initialization, condition, update, body)
    
    def parse_while(self,scope) -> GrindWhileStmt:
        self.current_token = self.get_next_token() # eat while
        self.skip_spaces()
        condition = self.parse_expr(scope)
        self.skip_whitespace()
        self.expect("{", "Expected '{' to open a while loop statement's body.")
        self.skip_whitespace()
        body = []
        self.push_scope()
        self.loop_flag = True
        while self.current_token and self.current_token.token != "}":
            stmt = self.parse_stmt(scope)
            body.append(stmt)
            self.skip_whitespace()
            if isinstance(stmt, RecallStmt):
                self.recall_stmts.append(stmt)
        self.expect("}", "Expected '}' to close a while loop statement's body.")
        self.skip_whitespace()
        self.pop_scope()
        self.loop_flag = False
        return GrindWhileStmt(condition, body)
    
    def parse_grind_while(self,scope) -> GrindWhileStmt:
        self.current_token = self.get_next_token() # eat grind
        self.skip_spaces()
        self.expect("{", "Expected '{' to open a grind while loop statement's body.")
        self.skip_whitespace()
        body = []
        self.push_scope()
        self.loop_flag = True
        while self.current_token and self.current_token.token != "}":
            stmt = self.parse_stmt(scope)
            body.append(stmt)
            self.skip_whitespace()
            if isinstance(stmt, RecallStmt):
                self.recall_stmts.append(stmt)
        self.expect("}", "Expected '}' to close a grind while loop statement's body.")
        self.skip_whitespace()
        self.pop_scope()
        self.loop_flag = False
        self.expect("while", "Missing a while loop condition after a grind-while loop statement's body.")
        self.skip_spaces()
        condition = self.parse_expr(scope)
        self.skip_whitespace()
        return GrindWhileStmt(condition, body, True)

    ########## BUILT-IN FUNCS ###########
    def parse_shoot(self, scope) -> ShootStmt:
        is_Next = False
        if self.current_token.token == 'shootNxt':
            is_Next = True
        self.current_token = self.get_next_token() # eat shoot or shootNxt
        self.expect("(", "Expected opening parentheses after shoot keyword.")
        self.skip_spaces()
        if self.current_token.token == ')':
            self.expect(")", "Expected closing parentheses in function call.")
            self.skip_whitespace()
            return ShootStmt("", is_Next)
        value = self.parse_expr(scope)
        self.skip_spaces()
        self.expect(")", "Expected closing parentheses in function call.")
        self.skip_whitespace()
        return ShootStmt(value, is_Next)

    def parse_join(self, scope, name) -> JoinStmt:
        if self.lookup_identifier(name.symbol):
            info = self.get_identifier_info(name.symbol)
            if info["type"] != "an array" and info["type"] != "a parameter":
                raise SemanticError(f"NameError: Array '{name.symbol}' is not defined.")
        else:
            raise SemanticError(f"NameError: Array '{name.symbol}' is not defined.")
        if info["type"] == "a parameter":
            dimensions = None
        elif info["type"] == "an array":
            dimensions = self.get_dimensions(name.symbol)
        self.expect(".", "Expects '.' in join function call.")
        self.expect("join", "Expects 'join' keyword in join function call.")
        self.expect("(", "Expects '(' after join keyword in join function call.")
        self.skip_spaces()
        if self.current_token.token == '[':
            if dimensions is None or dimensions == 2:
                pass
            else:
                raise SemanticError("DimensionsError: Trying to append a new row to a one dimensional array.")
            self.current_token = self.get_next_token() # eat [
            self.skip_spaces()
            values = [self.parse_inner_arr_values(scope)]
            self.expect("]", "Expects ']' to close array row values.")
            self.skip_spaces()
            self.expect(")", "Expects ')' after to close join arguments.")
            self.skip_whitespace()
            return JoinStmt(name, values, 2)
        else:
            if dimensions is None or dimensions == 1:
                pass
            else:
                raise SemanticError("DimensionsError: Trying to append new elements incorrectly to a two dimensional array, must specify row index first.")
            if self.current_token.token == ')':
                raise SemanticError("JoinError: Elements inside parentheses must not be empty.")
            values = []
            while self.current_token and self.current_token.token != ')':
                value = self.parse_expr(scope)
                values.append(value)
                self.skip_spaces()
                if self.current_token.token == ',':
                    self.current_token = self.get_next_token()  # eat ,
                    self.skip_spaces()
            self.expect(")", "Expects ')' after to close join arguments.")
            self.skip_whitespace()
            return JoinStmt(name, values, 1)

    def parse_join2d(self, scope, arr_name) -> JoinStmt:
        self.expect("[", "Expects '[' to specify row index of two-dimensional array.")
        self.skip_spaces()
        if self.current_token.token == ']':
            raise SemanticError("JoinError: Index must not be blank for join function call.")
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
            raise SemanticError("DimensionsError: Trying to append elements in a specific row to a one dimensional array, must be two-dimensional.")
        self.expect(".", "Expects '.' in join function call.")
        self.expect("join", "Expects 'join' keyword in join function call.")
        self.expect("(", "Expects '(' after join keyword in join function call.")
        self.skip_spaces()
        if self.current_token.token == ')':
            raise SemanticError("JoinError: Elements inside parentheses must not be empty.")
        values = []
        while self.current_token and self.current_token.token != ')':
            value = self.parse_expr(scope)
            values.append(value)
            self.skip_spaces()
            if self.current_token.token == ',':
                self.current_token = self.get_next_token()  # eat ,
                self.skip_spaces()
        self.expect(")", "Expects ')' after to close join arguments.")
        self.skip_whitespace()
        return JoinStmt(arr_name, values, 2, dim)

    def parse_drop(self, scope, name) -> DropStmt:
        if self.lookup_identifier(name.symbol):
            info = self.get_identifier_info(name.symbol)
            if info["type"] != "an array" and info["type"] != "a parameter":
                raise SemanticError(f"NameError: Array '{name.symbol}' is not defined.")
        else:
            raise SemanticError(f"NameError: Array '{name.symbol}' is not defined.")
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
        self.skip_whitespace()
        return DropStmt(name, index, dimensions)
    
    def parse_drop2d(self, scope, arr_name) -> DropStmt:
        self.expect("[", "Expects '[' to specify row index of two-dimensional array.")
        self.skip_spaces()
        if self.current_token.token == ']':
            raise SemanticError("DropError: Index must not be blank for drop function call.")
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
            raise SemanticError("DimensionsError: Trying to drop specific row from a one dimensional array, must be two-dimensional.")
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
        self.skip_whitespace()
        return DropStmt(arr_name, index, dimensions, dim)

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
    #print(result)

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
        

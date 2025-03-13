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

            if la_token.token in {':', 'newline', 'EOF'}:  
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
        pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        func_name = Identifier(self.current_token.lexeme, pos_start, id_pos_end)
        if not self.lookup_id_type(func_name.symbol, "a function"):
            raise SemanticError(f"NameError: Function '{func_name.symbol}' does not exist.")
        self.current_token = self.get_next_token() # eat id
        arg_pos_start = [self.current_token.line, self.current_token.column]
        self.expect("(", "Expects '(' after function name.")
        args = []
        self.skip_spaces()
        arg_pos = [self.current_token.line, self.current_token.column]
        while self.current_token.token != ')':
            la_token = self.look_ahead()
            if la_token.token == ',' or la_token.token == ')':
                arg = self.parse_primary_expr(scope, 'func_call', arg_pos)
            else:
                arg = self.parse_expr(scope)
            args.append(arg)
            self.skip_spaces()
            if self.current_token.token == ',':
                self.current_token = self.get_next_token() # eat ,
                self.skip_spaces()
        pos_end = [self.current_token.line, self.current_token.column]
        self.current_token = self.get_next_token() # eat )
        self.skip_whitespace()
        return FuncCallStmt(func_name, args, pos_start, pos_end, arg_pos_start, pos_end)
    
    ######### ARRAYS AND VARIABLES #########    
    def var_or_arr(self, scope) -> Union[VarDec, ArrayDec]:
        pos_start = [self.current_token.line, self.current_token.column]
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
            return self.parse_empty_array(datatype, scope, pos_start)
        else:
            if self.lookup_identifier(name):
                info = self.get_identifier_info(name)
                raise SemanticError(f"5 NameError: Identifier {name}' was "
                                    f"already declared as {info["type"]}.")
            return self.parse_var_dec(datatype, scope, pos_start)
    
    def parse_var_init(self, scope) -> Union[VarDec, BatchVarDec, VarAssignment]:
        name = self.current_token.lexeme
        pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        var_names = [Identifier(self.current_token.lexeme, pos_start, id_pos_end)]  

        if self.is_array(name): 
            return self.parse_arr_redec(var_names[0], scope)

        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()

        while self.current_token and self.current_token.token == ",":
            self.current_token = self.get_next_token()  # eat ,
            self.skip_spaces()

            if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("Expected variable name after ','.")

            id_pos_start = [self.current_token.line, self.current_token.column]
            var_name_size = len(self.current_token.lexeme)
            id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
            var_names.append(Identifier(self.current_token.lexeme ,id_pos_start, id_pos_end))
            self.current_token = self.get_next_token() # eat id
            self.skip_spaces()
            
            if self.current_token and self.current_token.token == ":":
                is_func = False
                self.current_token = self.get_next_token() # eat :
                self.skip_spaces()
                value = self.parse_expr(scope)
                pos_end = value.pos_end
                declarations = []
                for var in var_names:
                    info = self.lookup_identifier(var.symbol)
                    if info:
                        info = self.get_identifier_info(var.symbol)
                        if info["type"] == 'a parameter':
                            self.declare_id(var.symbol, "a variable")
                            declarations.append(VarAssignment(var, ":", value, pos_start, pos_end))
                        elif info["type"] != "a variable":
                            raise SemanticError(f"6 NameError: Identifier {var.symbol}' was "
                                                f"already declared as {info["type"]}.")
                        else:
                            declarations.append(VarAssignment(var, ":", value, pos_start, pos_end))
                    else:
                        declarations.append(VarDec(var, value, False, scope, pos_start, pos_end))
                        self.declare_id(var.symbol, "a variable")

                self.skip_spaces()
                return BatchVarDec(declarations, True, pos_start, pos_end)

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
                        pos_end = [self.current_token.line, self.current_token.column]
                        self.expect("]", "Expected ']' to close array values.")
                        self.skip_spaces()
                        if self.current_token.token == ',':
                            values.append(inner_values)
                            self.current_token = self.get_next_token()  # eat ,
                            self.skip_spaces()
                        else:
                            values = inner_values
                            break
                    return ArrayRedec(var_names[0], None, values, False, scope, pos_start, pos_end)
                
        value = self.parse_expr(scope)
        values_table = {name: {"values": value}}
        self.skip_spaces()
        
        while self.current_token and self.current_token.token == ",":
            self.current_token = self.get_next_token()  # eat ,
            self.skip_spaces()

            if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("Expected variable name after ','.")
            
            id_pos_start = [self.current_token.line, self.current_token.column]
            var_name_size = len(self.current_token.lexeme)
            id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
            
            var_names.append(Identifier(self.current_token.lexeme, id_pos_start, id_pos_end))
            variable_name = self.current_token.lexeme
            self.current_token = self.get_next_token() # eat id
            self.skip_spaces()

            if not self.current_token or self.current_token.token != ":":
                raise SemanticError("Expected ':' in variable initialization.")
            
            self.current_token = self.get_next_token() # eat :
            self.skip_whitespace()

            value = self.parse_expr(scope)
            values_table[variable_name] = {"values": value}

        pos_end = value.pos_end
        self.skip_spaces()
        if len(var_names) > 1:
            declarations = []
            for var in var_names:
                info = self.lookup_identifier(var.symbol)
                if info:
                    info = self.get_identifier_info(var.symbol)
                    if info["type"] == 'a parameter':
                        self.declare_id(var.symbol, "a variable")
                        declarations.append(VarAssignment(var, ":", values_table[var.symbol]['values'], var.pos_start, values_table[var.symbol]['values'].pos_end))
                    elif info["type"] != "a variable":
                        raise SemanticError(f"7 NameError: Identifier '{var.symbol}' was "
                                            f"already declared as {info["type"]}.")
                    else:
                        declarations.append(VarAssignment(var, ":", values_table[var.symbol]['values'], var.pos_start, values_table[var.symbol]['values'].pos_end))
                else:
                    declarations.append(VarDec(var, values_table[var.symbol]['values'], False, scope, var.pos_start, values_table[var.symbol]['values'].pos_end))
                    self.declare_id(var.symbol, "a variable")
           
            return BatchVarDec(declarations, False, pos_start, pos_end)
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
                            return ArrayRedec(var, None, value, False, scope, pos_start, pos_end)
                        return ArrayOrVar(var.symbol, [VarAssignment(var, ':', value, pos_start, pos_end), ArrayRedec(var, None, value, False, scope, pos_start, pos_end)])
                    return VarAssignment(var, ':', value, pos_start, pos_end)
            else:
                self.declare_id(var.symbol, "a variable")
                return VarDec(var, value, False, scope, pos_start, pos_end) 
        
    def parse_var_dec(self, datatype, scope, pos_start) -> Union[VarDec, BatchVarDec]:
        var_names = []
        while True:
            id_pos_start = [self.current_token.line, self.current_token.column]
            var_name_size = len(self.current_token.lexeme)
            id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
            var_names.append(Identifier(self.current_token.lexeme, id_pos_start, id_pos_end))
            self.current_token = self.get_next_token() # eat id
            self.skip_spaces()

            if self.current_token.token == ",":
                self.current_token = self.get_next_token()
                self.skip_spaces()
            else:
                break
        value = None
        pos_end = [self.current_token.line, self.current_token.column]
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
            pos_end = [self.current_token.line, self.current_token.column + 3]
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
                return BatchVarDec([VarDec(var, value, False, scope) for var in var_names], False, pos_start, pos_end)
            else:
                return BatchVarDec([VarDec(var, DeadLiteral(value, datatype), False, scope) for var in var_names], False, pos_start, pos_end)
        else:
            var = var_names[0]
            if self.lookup_identifier(var.symbol):
                    info = self.get_identifier_info(var.symbol)
                    raise SemanticError(f"10 NameError: Identifier {var.symbol}' was "
                                        f"already declared as {info["type"]}.")    
            self.declare_id(var.symbol, "a variable")
            if value != None:
                return VarDec(var, value, False, scope, pos_start, var.pos_end)
            else:
                return VarDec(var, DeadLiteral(value, datatype), False, scope, pos_start, pos_end)

    def parse_empty_array(self, datatype, scope, pos_start) -> ArrayDec:
        id_pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        arr_name = Identifier(self.current_token.lexeme, id_pos_start, id_pos_end)
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
            pos_end = [self.current_token.line, self.current_token.column - 1]
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
            return ArrayDec(arr_name, dimensions, values, False, scope, datatype, pos_start, pos_end)
        elif self.current_token and self.current_token.token == ':':
            self.current_token = self.get_next_token() #eat :
            self.skip_spaces()
            pos_end = [self.current_token.line, self.current_token.column + 3]
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
            return ArrayDec(arr_name, dimensions, values, False, scope, datatype, pos_start, pos_end)      
    
    def parse_array(self, scope) -> Union[ArrayDec, ArrAssignment]:
        pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        arr_name = Identifier(self.current_token.lexeme, pos_start, id_pos_end)
        name = arr_name.symbol
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        arr_exist = self.is_array(name) or self.is_params(name)
        if arr_exist:
            join_token = self.find_token_in_line('join')
            if join_token:
                return self.parse_join2d(scope, arr_name, pos_start)
            
            join_token = self.find_token_in_line('drop')
            if join_token:
                return self.parse_drop2d(scope, arr_name, pos_start)

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
            pos_end = [self.current_token.line, self.current_token.column - 1]
            self.skip_spaces()
            
        if self.current_token.token == ':':
            self.current_token = self.get_next_token() #eat :
            self.skip_spaces()
            if self.current_token and self.current_token.token == '[':
                if arr_exist:
                    raise SemanticError(f"DeclarationError: Identifier '{name}' was already declared.")
                else:
                    values, pos_end = self.parse_array_values(dimensions, scope)
                    self.declare_id(name, "an array", len(dimensions))
                    return ArrayDec(arr_name, dimensions, values, False, scope, None, pos_start, pos_end)
            else:
                if arr_exist:
                    if all(dim is not None for dim in dimensions):
                        value = self.parse_expr(scope)
                        lhs = ArrElement(arr_name, dimensions, pos_start, pos_end)
                        pos_end = value.pos_end
                        return ArrAssignment(lhs, ':', value, pos_start, pos_end)
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
                    lhs = ArrElement(arr_name, dimensions, pos_start, pos_end)
                    pos_end = value.pos_end
                    return ArrAssignment(lhs, operator, value, pos_start, pos_end)
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
                pos_end = [self.current_token.line, self.current_token.column - 1]
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
            pos_end = [self.current_token.line, self.current_token.column - 1]
            self.skip_spaces()
            if self.current_token.token == ',':
                raise SemanticError(
                    f"ArraySizeError: Redeclaring a one-dimensional array with more than one rows."
                )
            
            if expected_dims[0] is not None and len(values) != expected_dims[0]:
                raise SemanticError(
                    f"ArraySizeError: Expected {expected_dims[0]} elements, but got {len(values)}."
                )
        
        return values, pos_end

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
        pos_start = [self.current_token.line, self.current_token.column]
        dimensions=self.get_dimensions(name.symbol)
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        self.expect(":", "Expected ':' after array name for array re-decleration.")
        self.skip_spaces()
        if dimensions == 1:
            dimensions = [None]
        elif dimensions == 2:
            dimensions = [None, None]
        if self.current_token and self.current_token.token == '[':
            values, pos_end = self.parse_array_values(dimensions, scope)
            return ArrayRedec(name, dimensions, values, False, scope, pos_start, pos_end) 
        elif re.match(r'^id\d+$', self.current_token.token):
            id_pos_start = [self.current_token.line, self.current_token.column]
            rhs_name = self.current_token.lexeme
            rhs_name_size = len(rhs_name)
            id_pos_end = [self.current_token.line, self.current_token.column + rhs_name_size - 1]
            rhs_name_node = Identifier(self.current_token.lexeme, id_pos_start, id_pos_end)
            la_token = self.look_ahead()
            if la_token.token == '(':
                if not self.lookup_id_type(rhs_name, "a function"):
                    raise SemanticError(f"NameError: Function '{rhs_name}' does not exist.")
                values = self.parse_func_call(scope)
                pos_end = values.pos_end
                return ArrayRedec(name, dimensions, values, False, scope, pos_start, pos_end)
            self.current_token = self.get_next_token() # eat id
            self.skip_whitespace()
            info = self.lookup_identifier(rhs_name)
            if info:
                info = self.get_identifier_info(rhs_name)
                if info["type"] == 'a parameter':
                    self.declare_id(name.symbol, "an array")
                    return ArrayRedec(name, dimensions, rhs_name_node, False, scope, pos_start, id_pos_end)
                elif info["type"] != "an array":
                    raise SemanticError(f"RedeclarationError: Array '{name.symbol}' is being redeclared with"
                                        " non-array element.")
                else:
                    return ArrayRedec(name, dimensions, rhs_name_node, False, scope, pos_start, id_pos_end)
            else:
                raise SemanticError(f"NameError: Array '{rhs_name}' does not exist.")
        else:
            raise SemanticError(f"RedeclarationError: Array '{name.symbol}' is being redeclared with"
                                " non-array element.")

    ########## STRUCTS ##########
    def parse_globalstruct(self) -> Union[StructDec, GlobalStructDec]:
        pos_start = [self.current_token.line, self.current_token.column]
        self.current_token = self.get_next_token() # eat build
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("Expected struct name after 'build'.")
        id_pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        struct_name = Identifier(self.current_token.lexeme, id_pos_start, id_pos_end)
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
            return GlobalStructDec(struct_name, pos_start, id_pos_end)

    def parse_struct(self, scope) -> StructDec:
        self.current_token = self.get_next_token() # eat build
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("Expected struct name after 'build'.")
        id_pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1] 
        struct_name = Identifier(self.current_token.lexeme, id_pos_start, id_pos_end)
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
            id_pos_start = [self.current_token.line, self.current_token.column]
            var_name_size = len(self.current_token.lexeme)
            id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
            field_name = Identifier(self.current_token.lexeme, id_pos_start, id_pos_end)  
            self.current_token = self.get_next_token()  # eat id
            self.skip_spaces()
            value = None
            if self.current_token.token == ':':
                self.current_token = self.get_next_token()  # eat :
                self.skip_spaces()
                value = self.parse_expr(scope) 
                fields.append(StructFields(field_name, value, datatype, id_pos_start, value.pos_end))
                if self.lookup_identifier(field_name.symbol):
                    info = self.get_identifier_info(field_name.symbol)
                    raise SemanticError(f"23 NameError: Field name '{field_name.symbol}' cannot be used since it is already declared as {info["type"]}.")
                if field_name.symbol in fields_table:
                    raise SemanticError(f"FieldError: Duplicate field name detected: '{field_name.symbol}'.")
                fields_table.append(field_name.symbol)
                self.skip_whitespace()
            else:
                fields.append(StructFields(field_name, None, datatype, id_pos_start, id_pos_end))
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
        pos_start = [self.current_token.line, self.current_token.column]
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
        id_pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        inst_name = Identifier(self.current_token.lexeme, id_pos_start, id_pos_end)
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
                pos_end = value.pos_end
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
        return StructInst(inst_name, struct_parent, values, False, pos_start, pos_end)

    def parse_inst_ass(self, scope) -> InstAssignment:
        pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        struct_inst_name = Identifier(self.current_token.lexeme, pos_start, id_pos_end)
        self.current_token = self.get_next_token() # eat id
        
        join_token = self.find_token_in_line('join')
        if join_token:
            return self.parse_join(scope, struct_inst_name, pos_start)
        
        join_token = self.find_token_in_line('drop') 
        if join_token:
            return self.parse_drop(scope, struct_inst_name, pos_start)

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
        id_pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        inst_field_name = Identifier(self.current_token.lexeme, id_pos_start, id_pos_end)
        left = StructInstField(struct_inst_name, inst_field_name)
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        operator = self.current_token.token
        self.current_token = self.get_next_token() # eat operator
        self.skip_spaces()
        value = self.parse_expr(scope)
        pos_end = value.pos_end
        return InstAssignment(left, operator, value, pos_start, pos_end)

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
        pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        var_names = [Identifier(self.current_token.lexeme, pos_start, id_pos_end)]  
        name = self.current_token.lexeme
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        while self.current_token and self.current_token.token == ",":
            self.current_token = self.get_next_token()  # eat ,
            self.skip_spaces()

            if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("Expected variable name after ','.")
            
            id_pos_start = [self.current_token.line, self.current_token.column]
            var_name_size = len(self.current_token.lexeme)
            id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
            var_names.append(Identifier(self.current_token.lexeme, id_pos_start, id_pos_end))
            self.current_token = self.get_next_token() # eat id
            self.skip_spaces()

            if self.current_token and self.current_token.token == ":":
                self.current_token = self.get_next_token() # eat :
                self.skip_spaces()
                value = self.parse_expr(scope)
                pos_end = value.pos_end
                if scope not in self.var_list:
                    self.var_list[scope] = []
                for var in var_names:
                    if self.lookup_identifier(var.symbol):
                        info = self.get_identifier_info(var.symbol)
                        raise SemanticError(f"13 NameError: Identifier '{var.symbol}' is already declared as {info["type"]}.")  
                    self.declare_id(var.symbol, "a variable")
                self.skip_spaces()
                return BatchVarDec([VarDec(var, value, True, scope) for var in var_names], False, pos_start, pos_end)
            
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
            
            id_pos_start = [self.current_token.line, self.current_token.column]
            var_name_size = len(self.current_token.lexeme)
            id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
            
            var_names.append(Identifier(self.current_token.lexeme, id_pos_start, id_pos_end))
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
            return BatchVarDec(
                declarations=[
                    VarDec(var, values_table[var.symbol]['values'], True, scope, var.pos_start, values_table[var.symbol]['values'].pos_end)
                    for var in var_names
                ]
            )
        else:
            var = var_names[0]
            if self.lookup_identifier(var.symbol):
                info = self.get_identifier_info(var.symbol)
                raise SemanticError(f"15 NameError: Identifier '{var.symbol}' is already declared as {info["type"]}.")    
            self.declare_id(var.symbol, "a variable")
            return VarDec(var, value, True, scope, pos_start, value.pos_end)

    def parse_immo_arr(self, scope) -> ArrayDec:
        pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        arr_name = Identifier(self.current_token.lexeme, pos_start, id_pos_end)
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
        values, pos_end = self.parse_array_values(dimensions, scope)
        self.declare_id(name, "an array", len(dimensions))
        return ArrayDec(arr_name, dimensions, values, True, scope, None, pos_start, pos_end)
    
    def parse_immo_inst(self, scope) -> ImmoInstDec:
        pos_start = [self.current_token.line, self.current_token.column]
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
        id_pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        inst_name = Identifier(self.current_token.lexeme, id_pos_start, id_pos_end)
        self.current_token = self.get_next_token()  # eat id
        self.skip_spaces()
        values = []
        self.expect(":","Expected ':' after struct instance name.")
        self.skip_spaces()
        while self.current_token.token != ',':
            value = self.parse_expr(scope)
            values.append(value)
            pos_end = value.pos_end
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
        return StructInst(inst_name, struct_parent, values, True, pos_start, pos_end)

    ########## ASS #############
    def parse_var_ass(self, scope) -> VarAssignment:
        pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        var_name = Identifier(self.current_token.lexeme, pos_start, id_pos_end)
        name = self.current_token.lexeme
        if not self.lookup_identifier(name):
            raise SemanticError(f"NameError: Variable '{name}' does not exist.")
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        operator = self.current_token.token
        self.current_token = self.get_next_token() # eat operator
        self.skip_spaces()
        value = self.parse_expr(scope)
        pos_end = value.pos_end
        return VarAssignment(var_name, operator, value, pos_start, pos_end)

    ########## EXPR ############
    def parse_expr(self, scope) -> Expr:
        self.skip_spaces()
        pos_start = [self.current_token.line, self.current_token.column]
        return self.parse_or_expr(scope, pos_start)
    
    def parse_or_expr(self, scope, pos_start=None) -> Expr:
        self.skip_spaces()
        expr_pos_start = [self.current_token.line, self.current_token.column]
        left = self.parse_and_expr(scope, pos_start)
        while self.current_token and self.current_token.token in ['OR', '||']:
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            pos_start = [self.current_token.line, self.current_token.column]
            right = self.parse_and_expr(scope, pos_start)
            expr_pos_end = right.pos_end
            left = BinaryExpr(left, operator, right, expr_pos_start, expr_pos_end)
        return left
    
    def parse_and_expr(self, scope, pos_start=None) -> Expr:
        self.skip_spaces()
        expr_pos_start = [self.current_token.line, self.current_token.column]
        left = self.parse_relat_expr(scope, expr_pos_start)
        while self.current_token and self.current_token.token in ['AND', '&&']:
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            pos_start = [self.current_token.line, self.current_token.column]
            right = self.parse_relat_expr(scope, pos_start)
            expr_pos_end = right.pos_end
            left = BinaryExpr(left, operator, right, expr_pos_start, expr_pos_end)
        return left
    
    def parse_relat_expr(self, scope, pos_start=None) -> Expr:
        self.skip_spaces()
        expr_pos_start = [self.current_token.line, self.current_token.column]
        left = self.parse_additive_expr(scope, expr_pos_start)
        if not self.current_token or self.current_token.token not in ['<', '>', '<=', '>=', '==', '!=']:
            return left

        expr = []
        while self.current_token and self.current_token.token in ['<', '>', '<=', '>=', '==', '!=']:
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            pos_start = [self.current_token.line, self.current_token.column]
            right = self.parse_additive_expr(scope, pos_start)
            expr_pos_end = right.pos_end
            expr.append(BinaryExpr(left, operator, right, expr_pos_start, expr_pos_end))
            left = right

        return ChainRelatExpr(expr, expr_pos_start, expr_pos_end)
    
    def parse_additive_expr(self, scope, pos_start=None) -> Expr:
        self.skip_spaces()
        expr_pos_start = [self.current_token.line, self.current_token.column]
        left = self.parse_multiplicative_expr(scope, expr_pos_start)

        while self.current_token and self.current_token.token in '+-':
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            pos_start = [self.current_token.line, self.current_token.column]
            right = self.parse_multiplicative_expr(scope, pos_start)
            expr_pos_end = right.pos_end
            left = BinaryExpr(left, operator, right, expr_pos_start, expr_pos_end)
        return left

    def parse_multiplicative_expr(self, scope, pos_start=None) -> Expr:
        self.skip_spaces()
        expr_pos_start = [self.current_token.line, self.current_token.column]
        left = self.parse_not_expr(scope, expr_pos_start)

        while self.current_token and self.current_token.token in "/*%":
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            pos_start = [self.current_token.line, self.current_token.column]
            right = self.parse_not_expr(scope, pos_start)
            expr_pos_end = right.pos_end
            left = BinaryExpr(left, operator, right, expr_pos_start, expr_pos_end)

        return left  
    
    def parse_not_expr(self, scope, pos_start=None) -> Expr:
        self.skip_spaces()

        if self.current_token and self.current_token.token == '!':
            expr_pos_start = [self.current_token.line, self.current_token.column]
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            pos_start = [self.current_token.line, self.current_token.column]
            operand = self.parse_exp_expr(scope, pos_start)
            expr_pos_end = operand.pos_end
            return UnaryExpr(operator, operand, expr_pos_start, expr_pos_end)

        return self.parse_exp_expr(scope, pos_start)
    
    def parse_exp_expr(self, scope, pos_start=None) -> Expr:
        self.skip_spaces()
        expr_pos_start = [self.current_token.line, self.current_token.column]
        left = self.parse_primary_expr(scope, None, expr_pos_start)

        while self.current_token and self.current_token.token == '^':
            operator = self.current_token.token
            self.current_token = self.get_next_token()
            self.skip_spaces()
            pos_start = [self.current_token.line, self.current_token.column]
            right = self.parse_exp_expr(scope, pos_start)
            expr_pos_end = right.pos_end
            left = BinaryExpr(left, operator, right, expr_pos_start, expr_pos_end)

        return left 

    def parse_primary_expr(self, scope, is_func_call=None, pos_start=None) -> Expr:
        self.skip_spaces()
        if not self.current_token:
            raise SemanticError("Unexpected end of input during parsing!")
        
        tk = self.current_token.token

        if re.match(r'^id\d+$', tk):
            tk= 'id'

        if tk == 'id':
            id_size = len(self.current_token.lexeme)
            id_pos_end=[self.current_token.line, self.current_token.column + id_size - 1]
            identifier = Identifier(self.current_token.lexeme, pos_start, id_pos_end)
            new_pos_start = [self.current_token.line, self.current_token.column]
            self.current_token = self.get_next_token()
            self.skip_spaces()
            if self.current_token.token == '.':
                
                join_token = self.find_token_in_line('drop')
                if join_token:
                    return self.parse_drop(scope, identifier, new_pos_start)

                join_token = self.find_token_in_line('seek')
                if join_token:
                    return self.parse_seek(scope, identifier, new_pos_start)
                
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
                field_size = len(self.current_token.lexeme)
                pos_end = [self.current_token.line, self.current_token.column + field_size - 1]
                identifier = StructInstField(identifier, field, new_pos_start, pos_end)
                self.current_token = self.get_next_token()
                self.skip_spaces()
            elif self.current_token.token == '[':
                arr_exist = self.is_array(identifier.symbol) or self.is_params(identifier.symbol)
                
                if arr_exist:
                    join_token = self.find_token_in_line('drop')
                    if join_token:
                        return self.parse_drop2d(scope, identifier, new_pos_start)
                    
                    join_token = self.find_token_in_line('seek')
                    if join_token:
                        return self.parse_seek2d(scope, identifier, new_pos_start)
                
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
                        pos_end = [self.current_token.line, self.current_token.column - 1]
                        self.skip_spaces()
                
                identifier = ArrElement(identifier, dimensions, new_pos_start, pos_end)
            elif self.current_token.token == '(':
                if not self.lookup_id_type(identifier.symbol, "a function"):
                    raise SemanticError(f"NameError: Function '{identifier.symbol}' does not exist.")
                arg_pos_start = [self.current_token.line, self.current_token.column]
                self.current_token = self.get_next_token() # eat ( 
                self.skip_spaces()
                arg_pos = [self.current_token.line, self.current_token.column]
                args = []     
                while self.current_token.token != ')':
                    la_token = self.look_ahead()
                    if la_token.token == ',' or la_token.token == ')':
                        arg = self.parse_primary_expr(scope, 'func_call', arg_pos)
                    else:
                        arg = self.parse_expr(scope)
                    args.append(arg)
                    self.skip_spaces()
                    if self.current_token.token == ',':
                        self.current_token = self.get_next_token() # eat ,
                        self.skip_spaces()
                pos_end = [self.current_token.line, self.current_token.column]
                self.current_token = self.get_next_token() # eat )
                self.skip_spaces()
                identifier = FuncCallStmt(identifier, args, pos_start, pos_end, arg_pos_start, pos_end)
            elif self.current_token.token == 'xp_formatting':
                if not self.lookup_id_type(identifier.symbol, "a variable"):
                    raise SemanticError(f"NameError: Variable '{identifier.symbol}' does not exist.")
                value = re.sub(r'^"(.*)"$', r'\1', self.current_token.lexeme)
                if not re.match(r'^\.\d+f$', value):
                    raise SemanticError(f"FormatError: Invalid format specifier '{value}'.")
                digit = int(value[1])
                xp_format_end = [self.current_token.line, self.current_token.column + 2]
                self.current_token = self.get_next_token() # eat format 
                self.skip_spaces()
                return XpFormatting(identifier, digit, new_pos_start, xp_format_end)
            else:
                if not self.lookup_identifier(identifier.symbol):
                    raise SemanticError(f"NameError: Variable '{identifier.symbol}' does not exist.")
                
                info = self.get_identifier_info(identifier.symbol)
                allowed_types = {"a variable"}
                if self.func_flag:
                    allowed_types.add("a parameter")
                    allowed_types.add("an array")
                if is_func_call == 'func_call':
                    allowed_types.add("an array")
                    allowed_types.add("a struct instance")
                elif is_func_call == 'rounds':
                    allowed_types.add("an array")

                if info["type"] not in allowed_types:
                    raise SemanticError(f"20 NameError: Identifier '{identifier.symbol}' is already declared as {info['type']}")

            return identifier
        elif tk == 'hp_ltr':
            ltr_pos_start = [self.current_token.line, self.current_token.column]
            ltr_size = len(self.current_token.lexeme)
            ltr_pos_end = [self.current_token.line, self.current_token.column + ltr_size - 1]
            literal = HpLiteral(self.current_token.lexeme, ltr_pos_start, ltr_pos_end)
            self.current_token = self.get_next_token()
            self.skip_spaces()
            return literal
        elif tk == 'xp_ltr':
            ltr_pos_start = [self.current_token.line, self.current_token.column]
            ltr_size = len(self.current_token.lexeme)
            ltr_pos_end = [self.current_token.line, self.current_token.column + ltr_size - 1]
            literal = XpLiteral(self.current_token.lexeme, ltr_pos_start, ltr_pos_end)
            self.current_token = self.get_next_token()
            self.skip_spaces()
            return literal
        elif re.match(r'^comms_ltr', tk) :
            ltr_pos_start = [self.current_token.line, self.current_token.column]
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
                ltr_size = len(self.current_token.lexeme) - 1
                ltr_pos_end = [self.current_token.line, self.current_token.column + ltr_size]
                literal = FormattedCommsLiteral(value, placeholders, results, ltr_pos_start, ltr_pos_end)
                self.current_token = self.get_next_token()
                self.skip_spaces()
                return literal

            ltr_size = len(self.current_token.lexeme) - 1
            ltr_pos_end = [self.current_token.line, self.current_token.column + ltr_size]
            literal = CommsLiteral(final_value, ltr_pos_start, ltr_pos_end)
            self.current_token = self.get_next_token()
            self.skip_spaces()
            return literal
        elif tk == 'flag_ltr':
            ltr_pos_start = [self.current_token.line, self.current_token.column]
            ltr_size = len(self.current_token.lexeme)
            lexeme = self.current_token.lexeme 
            if lexeme == 'true':
                value = True
            else:
                value = False
            ltr_pos_end = [self.current_token.line, self.current_token.column + ltr_size - 1]
            literal = FlagLiteral(value, ltr_pos_start, ltr_pos_end)
            self.current_token = self.get_next_token()
            self.skip_spaces()
            return literal
        elif tk == '(':
            expr_pos_start = [self.current_token.line, self.current_token.column]
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
                expr_pos_end = [self.current_token.line, self.current_token.column + 2]
                self.current_token = self.get_next_token() # eat format 
                self.skip_spaces()
                return XpFormatting(value, digit, expr_pos_start, expr_pos_end)
            return value
        elif tk == '-':
            ltr_pos_start = [self.current_token.line, self.current_token.column]
            self.current_token = self.get_next_token()
            self.skip_spaces()
            if self.current_token and self.current_token.token == '(':
                self.current_token = self.get_next_token()
                self.skip_spaces()
                expr = self.parse_expr(scope)
                self.expect(')', "Unexpected token found inside parenthesized expression. Expected closing parenthesis.")
                ltr_pos_end = [self.current_token.line, self.current_token.column-1]
                self.skip_spaces()
                return UnaryExpr('-', expr, ltr_pos_start, ltr_pos_end)
            else:
                expr = self.parse_expr(scope)
                if expr.kind not in ['Identifier', 'ArrayElement', 'StructInstField']:
                    raise SemanticError("UnaryError: Invalid expression after unary operator.")
                return UnaryExpr('-', expr, ltr_pos_start, expr.pos_end)
        elif tk == 'dead':
            ltr_pos_start = [self.current_token.line, self.current_token.column]
            ltr_pos_end = [self.current_token.line, self.current_token.column + 3]
            self.current_token = self.get_next_token()
            self.skip_spaces()
            return DeadLiteral(None, None, ltr_pos_start, ltr_pos_end)
        elif tk == 'load' or tk == 'loadNum':
            prompt_msg = None
            func_pos_start = [self.current_token.line, self.current_token.column]
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
            func_pos_end = [self.current_token.line, self.current_token.column]
            self.current_token = self.get_next_token() # eat )
            self.skip_spaces()
            if tk == 'load':
                return Load(prompt_msg, func_pos_start, func_pos_end)
            else:
                return LoadNum(prompt_msg, func_pos_start, func_pos_end)
        elif tk == 'rounds':
            func_pos_start = [self.current_token.line, self.current_token.column]
            self.current_token = self.get_next_token() # eat rounds
            self.expect('(', "Expected '(' after 'rounds'.")
            self.skip_spaces()
            arg_pos = [self.current_token.line, self.current_token.column]
            value = self.parse_primary_expr(scope, 'rounds', arg_pos)
            if value.kind not in ['Identifier', 'ArrayElement', 'StructInstField', 'FuncCallStmt',
                                  'CommsLiteral', 'ToCommsStmt']: 
                raise SemanticError("ArgumentError: Invalid rounds argument.")
            self.skip_spaces()
            self.expect(')', "Expected ')' after rounds arguments.")
            func_pos_end = [self.current_token.line, self.current_token.column-1]
            self.skip_spaces()
            return RoundStmt(value, func_pos_start, func_pos_end)
        elif tk in ('levelUp', 'levelDown'):
            func_pos_start = [self.current_token.line, self.current_token.column]
            self.current_token = self.get_next_token()  # consume levelUp or levelDown
            self.expect('(', f"Expected '(' after '{tk}'.")
            self.skip_spaces()
            arg_pos = [self.current_token.line, self.current_token.column]
            value = self.parse_primary_expr(scope, None, arg_pos)
            valid_kinds = ['Identifier', 'ArrayElement', 'StructInstField', 'FuncCallStmt',
                           'ToCommsStmt']  
            if value.kind not in valid_kinds:
                raise SemanticError(f"ArgumentError: Invalid '{tk}' argument.")
            self.skip_spaces()
            self.expect(')', f"Expected ')' after '{tk}' arguments.")
            func_pos_end = [self.current_token.line, self.current_token.column - 1]
            self.skip_spaces()
            return LevelStmt(value, tk == 'levelUp', func_pos_start, func_pos_end)
        elif tk in ('toHp', 'toXp'):
            func_pos_start = [self.current_token.line, self.current_token.column]
            self.current_token = self.get_next_token()  # consume toHp or toHp
            self.expect('(', f"Expected '(' after '{tk}'.")
            self.skip_spaces()
            arg_pos = [self.current_token.line, self.current_token.column]
            value = self.parse_primary_expr(scope,None,arg_pos)
            valid_kinds = ['Identifier', 'ArrayElement', 'StructInstField'] 
            if value.kind not in valid_kinds:
                raise SemanticError(f"ArgumentError: Invalid '{tk}' argument.")
            self.skip_spaces()
            self.expect(')', f"Expected ')' after '{tk}' arguments.")
            func_pos_end = [self.current_token.line, self.current_token.column - 1]
            self.skip_spaces()
            return ToNumStmt(value, tk == 'toHp', func_pos_start, func_pos_end)
        elif tk == 'toComms':
            func_pos_start = [self.current_token.line, self.current_token.column]
            self.current_token = self.get_next_token()  # consume toComms
            self.expect('(', f"Expected '(' after '{tk}'.")
            self.skip_spaces()
            arg_pos = [self.current_token.line, self.current_token.column]
            value = self.parse_primary_expr(scope, None, arg_pos)
            valid_kinds = ['Identifier', 'ArrayElement', 'StructInstField'] 
            if value.kind not in valid_kinds:
                raise SemanticError(f"ArgumentError: Invalid '{tk}' argument.")
            self.skip_spaces()
            self.expect(')', f"Expected ')' after '{tk}' arguments.")
            func_pos_end = [self.current_token.line, self.current_token.column - 1]
            self.skip_spaces()
            return ToCommsStmt(value, func_pos_start, func_pos_end)
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
                stmt = self.parse_stmt(scope)
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
        pos_start = [self.current_token.line, self.current_token.column]
        self.current_token = self.get_next_token() # eat for
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("ForError: Expected variable name after for keyword.")
        init_pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        name = Identifier(self.current_token.lexeme, init_pos_start, id_pos_end)
        if not self.lookup_id_type(name.symbol, "a variable"):
            raise SemanticError(f"NameError: Variable '{name.symbol}' is not defined.")
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        self.expect(":", "ForError: Expected ':' after identifier in loop control initialization.")
        self.skip_spaces()
        init_value = self.parse_expr(scope)
        pos_end = init_value.pos_end
        initialization = VarAssignment(name, ":", init_value, init_pos_start, pos_end)
        self.skip_spaces()
        self.expect(",", "ForError: Expected ',' after loop control initialization.")
        self.skip_spaces()
        condition = self.parse_expr(scope)
        self.skip_spaces()
        self.expect(",", "ForError: Expected ',' after loop condition.")
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("ForError: Expected variable name after loop condition.")
        id_pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        upd_name = Identifier(self.current_token.lexeme, id_pos_start, id_pos_end)
        if not self.lookup_id_type(upd_name.symbol, "a variable"):
            raise SemanticError(f"NameError: Variable '{upd_name.symbol}' is not defined.")
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        operator = self.current_token.token
        self.current_token = self.get_next_token() # eat operator
        self.skip_spaces()
        upd_value = self.parse_expr(scope)
        update = VarAssignment(upd_name, operator, upd_value, id_pos_start, upd_value.pos_end)
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
        pos_end = [self.current_token.line, self.current_token.column-1]
        self.skip_whitespace()
        self.pop_scope()
        self.loop_flag = False
        return ForStmt(initialization, condition, update, body, pos_start, pos_end)
    
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
        pos_start = [self.current_token.line, self.current_token.column]
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
        pos_end = [self.current_token.line, self.current_token.column-1]
        self.skip_whitespace()
        return ShootStmt(value, is_Next, pos_start, pos_end)

    def parse_join(self, scope, name, pos_start) -> JoinStmt:
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
            pos_end = [self.current_token.line, self.current_token.column-1]
            self.skip_whitespace()
            return JoinStmt(name, values, 2, pos_start, pos_end)
        else:
            if dimensions is None or dimensions == 1:
                pass
            else:
                raise SemanticError("DimensionsError: Trying to append new elements incorrectly to a two dimensional array, must specify row index first.")
            if self.current_token.token == ')':
                raise SemanticError("JoinError: Elements inside parentheses must not be empty.")
            value = self.parse_expr(scope)
            self.skip_spaces()
            self.expect(")", "Expects ')' after to close join arguments.")
            pos_end = [self.current_token.line, self.current_token.column-1]
            self.skip_whitespace()
            return JoinStmt(name, value, 1, pos_start, pos_end)

    def parse_join2d(self, scope, arr_name, pos_start) -> JoinStmt:
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
            raise SemanticError("DimensionsError: Trying to append an element in a specific row to a 1d array, must be a 2d array.")
        self.expect(".", "Expects '.' in join function call.")
        self.expect("join", "Expects 'join' keyword in join function call.")
        self.expect("(", "Expects '(' after join keyword in join function call.")
        self.skip_spaces()
        if self.current_token.token == ')':
            raise SemanticError("JoinError: Elements inside parentheses must not be empty.")
        value = self.parse_expr(scope)
        self.skip_spaces()
        self.expect(")", "Expects ')' after to close join arguments.")
        pos_end = [self.current_token.line, self.current_token.column-1]
        self.skip_whitespace()
        return JoinStmt(arr_name, value, 2, pos_start, pos_end, dim)

    def parse_drop(self, scope, name, pos_start) -> DropStmt:
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
        pos_end = [self.current_token.line, self.current_token.column-1]
        self.skip_whitespace()
        return DropStmt(name, index, dimensions, pos_start, pos_end)
    
    def parse_drop2d(self, scope, arr_name, pos_start) -> DropStmt:
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
        pos_end = [self.current_token.line, self.current_token.column-1]
        self.skip_whitespace()
        return DropStmt(arr_name, index, dimensions, pos_start, pos_end, dim)

    def parse_seek(self, scope, name, pos_start) -> SeekStmt:
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
        self.expect(".", "Expects '.' in seek function call.")
        self.expect("seek", "Expects 'seek' keyword in seek function call.")
        self.expect("(", "Expects '(' after seek keyword in seek function call.")
        self.skip_spaces()
        if self.current_token.token == '[':
            if dimensions is None or dimensions == 2:
                pass
            else:
                raise SemanticError("DimensionsError: Trying to seek a specific row in a 1d array, must be a 2d array.")
            self.current_token = self.get_next_token() # eat [
            self.skip_spaces()
            values = [self.parse_inner_arr_values(scope)]
            self.expect("]", "Expects ']' to close array row values.")
            self.skip_spaces()
            self.expect(")", "Expects ')' after to close seek arguments.")
            pos_end = [self.current_token.line, self.current_token.column-1]
            self.skip_whitespace()
            return SeekStmt(name, values, 2, pos_start, pos_end)
        else:
            if dimensions is None or dimensions == 1:
                pass
            else:
                raise SemanticError("DimensionsError: Trying to seek a specific element in a 2d array, must specify row index first..")
            if self.current_token.token == ')':
                raise SemanticError("SeekError: Elements inside parentheses must not be empty.")
            value = self.parse_expr(scope)
            self.skip_spaces()
            self.expect(")", "Expects ')' after to close seek arguments.")
            pos_end = [self.current_token.line, self.current_token.column-1]
            self.skip_whitespace()
            return SeekStmt(name, value, 1, pos_start, pos_end)
        
    def parse_seek2d(self, scope, arr_name, pos_start) -> SeekStmt:
        self.expect("[", "Expects '[' to specify row index of two-dimensional array.")
        self.skip_spaces()
        if self.current_token.token == ']':
            raise SemanticError("SeekError: Index must not be blank for seek function call.")
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
            raise SemanticError("DimensionsError: Trying to seek a specific row in a 1d array, must be a 2d array.")
        self.expect(".", "Expects '.' in seek function call.")
        self.expect("seek", "Expects 'seek' keyword in seek function call.")
        self.expect("(", "Expects '(' after seek keyword in seek function call.")
        self.skip_spaces()
        if self.current_token.token == ')':
            raise SemanticError("SeekError: Elements inside parentheses must not be empty.")
        value = self.parse_expr(scope)
        self.skip_spaces()
        self.expect(")", "Expects ')' after to close seek arguments.")
        pos_end = [self.current_token.line, self.current_token.column-1]
        self.skip_whitespace()
        return SeekStmt(arr_name, value, 2, pos_start, pos_end, dim)

def check(fn, text):
    lexer = Lexer(fn, text)
    if text == "":
        return "No code in the module.", {}

    tokens, error = lexer.make_tokens()

    if error:
        return 'Lexical errors found, cannot continue with syntax analyzing. Please check lexer tab.\n\nLexical Errors:\n' + "\n\n".join(error), {}

    result = parse(fn, text)

    if result != 'No lexical errors found!\nValid syntax.':
        result = result.split("\n", 1)[-1]
        return f'Syntax errors found, cannot continue with semantic analyzing. Please check syntax tab.\n{result}', {}

    semantic = Semantic(tokens)
    result = semantic.produce_ast()
    #print(result)

    if isinstance(result, SemanticError):
        result.source_code = text.splitlines()
        return str(result), {}
    
    try:
        visitor = ASTVisitor()
        visitor.visit(result)

        analyzer = SemanticAnalyzer(visitor.symbol_table)
        analyzer.visit(result)
        table = analyzer.symbol_table
    except SemanticError as e:
        e.source_code = text.splitlines()
        return str(e), {}

    return result, table

    return result, {}
        

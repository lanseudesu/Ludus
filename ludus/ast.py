from .lexer import Lexer
from .nodes import *
from .parser import parse
import re
from typing import Union
from .runtime.traverser import ASTVisitor, SemanticAnalyzer
from .error import SemanticError
from .helper_parser import Helper

class Semantic:
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        self.current_token = self.get_next_token()
        self.globalstruct = {}
        self.global_func = {}
        self.scope_stack = [{}]
        self.loop_flag_stack = []
        self.flank_flag_stack = []
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
    
    def lookup_id_type(self, name, id_type, node):
        for scope in reversed(self.scope_stack):
            if name  in scope:
                info = self.get_identifier_info(name, node)
                if info["type"] == id_type:
                    return True
                else:
                    raise SemanticError(f"NameError: Identifier '{name}' is already declared as {info["type"]}.", node.pos_start, node.pos_end)
        return False
    
    def get_identifier_info(self, name, node):
        for scope in reversed(self.scope_stack):
            if name in scope:
                return scope[name]  
        raise SemanticError(f"Identifier '{name}' not declared.", node.pos_start, node.pos_end)
    
    def is_array(self, name, node):
        if self.lookup_identifier(name):
            info = self.get_identifier_info(name, node)
            if info["type"] == "an array":
                return True
            else:
                return False
        else:
            return False
        
    def is_params(self, name, node):
        if self.lookup_identifier(name):
            info = self.get_identifier_info(name, node)
            if info["type"] == "a parameter":
                return True
            else:
                return False
        else:
            return False
    
    def get_dimensions(self, name, node):
        info = self.get_identifier_info(name, node)
        if info["type"] != "an array":
            raise SemanticError(f"Identifier '{name}' is not an array", node.pos_start, node.pos_end)
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
        start = [prev_token.line, prev_token.column]
        end = [prev_token.line, prev_token.column]
        self.current_token = self.get_next_token()
        if not prev_token or prev_token.token != token_type:
            raise SemanticError(f"ParserError: {error_message}", start, end)
        
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
                    name_start = [self.current_token.line, self.current_token.column]
                    name_end = [self.current_token.line, self.current_token.column + len(name) - 1]
                    name_node = Identifier(name, name_start, name_end)
                    if la_token is not None and la_token.token in [':',',']: 
                        if self.lookup_identifier(name):
                            info = self.get_identifier_info(name, name_node)
                            raise SemanticError(f"NameError: Identifier {name}' was "
                                                f"already declared as {info["type"]}.", name_start, name_end)
                        program.body.append(self.parse_var_init("global"))
                    elif la_token is not None and la_token.token == '[':  
                        if self.lookup_identifier(name):
                            info = self.get_identifier_info(name, name_node)
                            raise SemanticError(f"NameError: Identifier {name}' was "
                                                f"already declared as {info["type"]}.", name_start, name_end)
                        program.body.append(self.parse_array("global"))
                    else:
                        start = [la_token.line, la_token.column]
                        end = [la_token.line, la_token.column]
                        raise SemanticError(f"ParserError: 1 Unexpected token found during parsing: {la_token.token}", start, end)
                elif self.current_token and self.current_token.token in ['hp','xp','comms','flag']:
                    program.body.append(self.var_or_arr("global"))
                elif self.current_token and self.current_token.token == 'immo':
                    program.body.append(self.parse_immo("global"))
                elif self.current_token and self.current_token.token == 'build':
                    program.body.append(self.parse_globalstruct())
                elif self.current_token and self.current_token.token == 'play':
                    program.body.append(self.parse_play())
                elif self.current_token and self.current_token.token == 'generate':
                    program.body.append(self.parse_func())
                elif self.current_token and self.current_token.token == 'gameOver':
                    break
                else:
                    start = [self.current_toke.line, self.current_toke.column]
                    end = [self.current_toke.line, self.current_toke.column]
                    raise SemanticError(f"ParserError: 2 Unexpected token found during parsing: {self.current_token.token}", self.current_token.line)
            if self.global_func:
                first_func = next(iter(self.global_func))
                start = self.global_func[first_func]["start"]  
                end = self.global_func[first_func]["end"]  
                raise SemanticError(f"FunctionError: Function '{first_func}' was declared but not initialized.", start, end)
            if self.globalstruct:
                first_struct = next(iter(self.globalstruct))
                start = self.globalstruct[first_struct]["start"]  
                end = self.globalstruct[first_struct]["end"]  
                raise SemanticError(f"StructError: Global struct '{first_struct}' was declared but not initialized.", start, end)
        
        except SemanticError as e:
            return e
        return program
                
    def parse_func(self) -> Union[GlobalFuncDec, GlobalFuncBody]: 
        pos_start = [self.current_token.line, self.current_token.column]
        self.current_token = self.get_next_token() # eat generate
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("ParserError: Expected function name after 'generate'.", self.current_token.line)
        name = self.current_token.lexeme
        name_start = [self.current_token.line, self.current_token.column]
        name_end = [self.current_token.line, self.current_token.column + len(name)- 1]
        func_name = Identifier(name, name_start, name_end) 
        
        if self.lookup_identifier(func_name.symbol):
            info = self.get_identifier_info(func_name.symbol, func_name)
            if info["type"] != "a function":
                raise SemanticError(f"NameError: Function name '{func_name.symbol}' was "
                                    f"already declared as {info["type"]}.", name_start, name_end)
        self.declare_id(func_name.symbol, "a function")
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        self.expect("(", "Expected '(' after function name.")
        self.skip_spaces()
        param_names = []
        params = []
        while self.current_token.token != ')':
            if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("ParserError: Expected parameter name after inside parantheses.", self.current_token.line)
            param_name = self.current_token.lexeme
            if param_name in param_names:
                raise SemanticError(f"ParamaterError: Duplicate parameter names: '{param_name}'",
                                    [self.current_token.line, self.current_token.column], 
                                    [self.current_token.line, self.current_token.column + len(param_name) - 1])
            param_names.append(param_name)
            if self.lookup_identifier(param_name):
                raise SemanticError("ParamaneterError: Parameter's name cannot be the same with a global element.",
                                    [self.current_token.line, self.current_token.column], 
                                    [self.current_token.line, self.current_token.column + len(param_name) - 1])
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

        pos_end = [self.current_token.line, self.current_token.column]
        self.current_token = self.get_next_token() # eat )
        self.skip_whitespace()

        node = GlobalFuncDec(func_name, params, pos_start, pos_end)
        if self.current_token.token == '{':
            if func_name.symbol in self.global_func:
                existing_params = self.global_func[func_name.symbol]["params"]

                if str(existing_params) != str(params):
                    raise SemanticError(f"ParameterError: Parameter mismatch for function '{func_name.symbol}'. ", pos_start, pos_end)
                del self.global_func[func_name.symbol]
                return self.create_func(func_name, params)
            raise SemanticError(f"NameError: User-defined function '{func_name.symbol}' was not declared.", name_start, name_end)
        else:
            if func_name.symbol in self.global_func:
                raise SemanticError(f"NameError: User-defined function '{func_name.symbol}' was already declared.", name_start, name_end)
            self.global_func[func_name.symbol] = {
                "params" : params,
                "start" : pos_start,
                "end" : pos_end,
            }
            return node
    
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
            raise SemanticError("ParserError: Expected function declaration keyword 'play'.", self.current_token.line)

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
        line_start = [self.current_token.line, self.current_token.column]

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
                value = self.parse_func_call(scope)
                self.skip_spaces()
                self.expect("newline", "Expected 'newline' after every statements.")
                return value
            else:
                raise SemanticError(f"ParserError: Unexpected token found during parsing: {la_token.token}", self.current_token.line)
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
            line = [self.current_token.line, self.current_token.column]

            in_flank = self.flank_flag_stack and self.flank_flag_stack[-1]
            in_loop = self.loop_flag_stack and self.loop_flag_stack[-1]

            if in_flank or in_loop:
                self.current_token = self.get_next_token()
                self.skip_spaces()
                self.expect("newline", "Expected 'newline' after every statements.")
                return ResumeStmt()
            else:
                raise SemanticError(f"ResumeError: Cannot use resume statement if not within a flank choice body or loop body.",
                                    line, [self.current_token.line, self.current_token.column + 5])
        
        elif self.current_token and self.current_token.token == 'checkpoint':
            line = [self.current_token.line, self.current_token.column]
            in_loop = self.loop_flag_stack and self.loop_flag_stack[-1]
            print(f"loop flag = {in_loop}")

            if in_loop:
                self.current_token = self.get_next_token()
                self.skip_spaces()
                self.expect("newline", "Expected 'newline' after every statements.")
                return CheckpointStmt()
            else:
                raise SemanticError(f"CheckpointError: Cannot use checkpoint statement if not within a loop body.",
                                    line, [self.current_token.line, self.current_token.column + 9])
       
       ###### loops ######
        elif self.current_token and self.current_token.token == 'for':
             return self.parse_for(scope)
        elif self.current_token and self.current_token.token == 'grind':
             return self.parse_grind_while(scope)
        elif self.current_token and self.current_token.token == 'while':
             return self.parse_while(scope)
        
        elif self.current_token and self.current_token.token == 'recall':
             line = [self.current_token.line, self.current_token.column]
             if self.func_flag:
                return self.parse_recall(scope)
             else:
                raise SemanticError(f"RecallError: Cannot use recall if not within a user-defined function body.",
                                    line, [self.current_token.line, self.current_token.column + 5])
        
        ###### built-in funcs ######
        elif self.current_token and self.current_token.token in ['shoot', 'shootNxt']:
            return self.parse_shoot(scope)
        elif self.current_token and self.current_token.token == 'wipe':
            self.current_token = self.get_next_token()
            self.expect("(", "Expects a parentheses after wipe keyword.")
            self.skip_spaces()
            self.expect(")", "Expects a closing parentheses.")
            self.skip_spaces()
            self.expect("newline", "Expected 'newline' after every statements.")
            return WipeStmt()
        else:
            raise SemanticError(f"ParserError: 4 Unexpected token found during parsing: {self.current_token.token}", self.current_token.line)

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

        self.expect("newline", "Expected 'newline' after every statements.")
        return RecallStmt(stmt)

    def parse_func_call(self, scope) -> FuncCallStmt:
        pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        func_name = Identifier(self.current_token.lexeme, pos_start, id_pos_end)
        if not self.lookup_id_type(func_name.symbol, "a function", func_name):
            raise SemanticError(f"NameError: Function '{func_name.symbol}' does not exist.", pos_start, id_pos_end)
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
        return FuncCallStmt(func_name, args, pos_start, pos_end, arg_pos_start, pos_end)
    
    ######### ARRAYS AND VARIABLES #########    
    def var_or_arr(self, scope) -> Union[VarDec, ArrayDec]:
        pos_start = [self.current_token.line, self.current_token.column]
        datatype = self.current_token.token  
        self.current_token = self.get_next_token()
        self.skip_spaces()

        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise SemanticError("ParserError: Expected variable name.", self.current_token.line)
    
        la_token = self.look_ahead()
        name = self.current_token.lexeme
        name_start = [self.current_token.line, self.current_token.column]
        name_end = [self.current_token.line, self.current_token.column + len(name) - 1]
        name_node = Identifier(name, name_start, name_end)
        if la_token is not None and la_token.token == '[':  
            if self.lookup_identifier(name):
                info = self.get_identifier_info(name, name_node)
                raise SemanticError(f"NameError: Identifier {name}' was "
                                    f"already declared as {info["type"]}.", name_start, name_end)
            return self.parse_empty_array(datatype, scope, pos_start)
        else:
            if self.lookup_identifier(name):
                info = self.get_identifier_info(name, name_node)
                raise SemanticError(f"NameError: Identifier {name}' was "
                                    f"already declared as {info["type"]}.", name_start, name_end)
            return self.parse_var_dec(datatype, scope, pos_start)
    
    def parse_var_init(self, scope) -> Union[VarDec, BatchVarDec, VarAssignment]:
        name = self.current_token.lexeme
        pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        var_names = [Identifier(self.current_token.lexeme, pos_start, id_pos_end)]  

        if self.is_array(name, var_names[0]): 
            return self.parse_arr_redec(var_names[0], scope)

        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()

        while self.current_token and self.current_token.token == ",":
            self.current_token = self.get_next_token()  # eat ,
            self.skip_spaces()

            if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("ParserError: Expected variable name after ','.", self.current_token.line)

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
                        info = self.get_identifier_info(var.symbol, var)
                        if info["type"] == 'a parameter':
                            self.declare_id(var.symbol, "a variable")
                            declarations.append(VarAssignment(var, ":", value, pos_start, pos_end))
                        elif info["type"] != "a variable":
                            raise SemanticError(f"NameError: Identifier {var.symbol}' was "
                                                f"already declared as {info["type"]}.", var.pos_start, var.pos_end)
                        else:
                            declarations.append(VarAssignment(var, ":", value, pos_start, pos_end))
                    else:
                        declarations.append(VarDec(var, value, False, scope, pos_start, pos_end))
                        self.declare_id(var.symbol, "a variable")

                self.skip_spaces()
                self.expect("newline", "Expected 'newline' after every statements.")
                return BatchVarDec(declarations, True, pos_start, pos_end)

        self.current_token = self.get_next_token() # eat :
        self.skip_spaces()

        if self.current_token.token == '[' and self.func_flag:
            info = self.lookup_identifier(name)
            if info:
                name_node = var_names[0]
                info = self.get_identifier_info(name, name_node)
                if info["type"] != 'a parameter':
                    raise SemanticError(f"NameError: Identifier {name}' was "
                                        f"already declared as {info["type"]}.", name_node.pos_start, name_node.pos_end)
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
                    self.expect("newline", "Expected 'newline' after every statements.")
                    return ArrayRedec(var_names[0], None, values, False, scope, pos_start, pos_end)
                
        value = self.parse_expr(scope)
        values_table = {name: {"values": value}}
        self.skip_spaces()
        
        while self.current_token and self.current_token.token == ",":
            self.current_token = self.get_next_token()  # eat ,
            self.skip_spaces()

            if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("ParserError: Expected variable name after ','.", self.current_token.line)
            
            id_pos_start = [self.current_token.line, self.current_token.column]
            var_name_size = len(self.current_token.lexeme)
            id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
            
            var_names.append(Identifier(self.current_token.lexeme, id_pos_start, id_pos_end))
            variable_name = self.current_token.lexeme
            self.current_token = self.get_next_token() # eat id
            self.skip_spaces()

            if not self.current_token or self.current_token.token != ":":
                raise SemanticError("ParserError: Expected ':' in variable initialization.", self.current_token.line)
            
            self.current_token = self.get_next_token() # eat :
            self.skip_spaces()

            value = self.parse_expr(scope)
            values_table[variable_name] = {"values": value}

        pos_end = value.pos_end
        self.skip_spaces()
        self.expect("newline", "Expected 'newline' after every statements.")
        if len(var_names) > 1:
            declarations = []
            for var in var_names:
                info = self.lookup_identifier(var.symbol)
                if info:
                    info = self.get_identifier_info(var.symbol, var)
                    if info["type"] == 'a parameter':
                        self.declare_id(var.symbol, "a variable")
                        declarations.append(VarAssignment(var, ":", values_table[var.symbol]['values'], var.pos_start, values_table[var.symbol]['values'].pos_end))
                    elif info["type"] != "a variable":
                        raise SemanticError(f"NameError: Identifier '{var.symbol}' was "
                                            f"already declared as {info["type"]}.", var.pos_start, var.pos_end)
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
                info = self.get_identifier_info(var.symbol, var)
                if info["type"] != "a variable" and info["type"] != "a parameter":
                    raise SemanticError(f"NameError: Identifier '{var.symbol}' was "
                                        f"already declared as {info["type"]}.", var.pos_start, var.pos_end)
                else:
                    if info["type"] == "a parameter" and isinstance(value, Identifier):
                        if self.is_array(value.symbol, value):
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
        
        self.skip_spaces()
        self.expect("newline", "Expected 'newline' after every statements.")

        if len(var_names) > 1:
            for var in var_names:
                if self.lookup_identifier(var.symbol):
                    info = self.get_identifier_info(var.symbol, var)
                    raise SemanticError(f"NameError: Identifier {var.symbol}' was "
                                        f"already declared as {info["type"]}.", var.pos_start, var.pos_end)  
                self.declare_id(var.symbol, "a variable")
            if value != None:
                return BatchVarDec([VarDec(var, value, False, scope) for var in var_names], False, pos_start, pos_end)
            else:
                return BatchVarDec([VarDec(var, DeadLiteral(value, datatype), False, scope) for var in var_names], False, pos_start, pos_end)
        else:
            var = var_names[0]
            if self.lookup_identifier(var.symbol):
                    info = self.get_identifier_info(var.symbol, var)
                    raise SemanticError(f"NameError: Identifier {var.symbol}' was "
                                        f"already declared as {info["type"]}.", var.pos_start, var.pos_end)    
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
                    raise SemanticError("ArraySizeError: Row and column sizes must both be empty or specified.", pos_start, pos_end)
            else:
                if dimensions[0] is None:
                    values = []  # arr[]
                else:
                    values = [default_value] * dimensions[0]

            self.declare_id(name, "an array", len(dimensions))
            self.skip_spaces()
            self.expect("newline", "Expected 'newline' after every statements.")
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
                    raise SemanticError("NullSizeError: Null arrays cannot be initialized with specific size.", pos_start, pos_end)
            else:
                if dimensions[0] is None:
                    values = None  # arr[]
                else:
                    raise SemanticError("NullSizeError: Null arrays cannot be initialized with specific size.", pos_start, pos_end)
                
            self.declare_id(name, "an array", len(dimensions))
            self.skip_spaces()
            self.expect("newline", "Expected 'newline' after every statements.")
            return ArrayDec(arr_name, dimensions, values, False, scope, datatype, pos_start, pos_end)      
    
    def parse_string_arr(self, scope, arr_name, pos_start)  -> StrArrAssignment:
        self.expect("[", "Expects '[' to specify character index of a comms.")
        self.skip_spaces()
        dimensions = []
        if self.current_token.token == ']':
            raise SemanticError("IndexError: Index must not be blank.", self.current_token.line)
        dim = self.parse_expr(scope)
        dimensions.append(dim)
        self.skip_spaces()
        self.expect("]", "Expected ']' to close comms indexing.")
        pos_end = [self.current_token.line, self.current_token.column - 1]
        self.skip_spaces()

        if self.current_token.token not in ['+=', '-=', '*=', '/=', '%=', ':']:
             raise SemanticError("Expected a assignment operator after comms index.", self.current_token.line)
        operator = self.current_token.token
        self.current_token = self.get_next_token() #eat operator
        self.skip_spaces()
        value = self.parse_expr(scope)
        lhs = StringIndexArr(arr_name, dimensions, pos_start, pos_end)
        pos_end = value.pos_end
        self.skip_spaces()
        self.expect("newline", "Expected 'newline' after every statements.")
        return StrArrAssignment(lhs, operator, value, pos_start, pos_end)
    
    def parse_array(self, scope) -> Union[ArrayDec, ArrAssignment]:
        pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        arr_name = Identifier(self.current_token.lexeme, pos_start, id_pos_end)
        name = arr_name.symbol
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()

        if self.lookup_identifier(name):
            info = self.get_identifier_info(name, arr_name)
            if info["type"] == "a variable":
                return self.parse_string_arr(scope, arr_name, pos_start)

        arr_exist = self.is_array(name, arr_name) or self.is_params(name, arr_name)
        if arr_exist:
            join_token = self.find_token_in_line('join')
            if join_token:
                return self.parse_join2d(scope, arr_name, pos_start)
            
            join_token = self.find_token_in_line('drop')
            if join_token:
                node = self.parse_drop2d(scope, arr_name, pos_start)
                self.skip_spaces()
                self.expect("newline", "Expected 'newline' after every statements.") 
                return node

        dimensions = []
        while self.current_token and self.current_token.token == '[':
            self.current_token = self.get_next_token() #eat [
            self.skip_spaces
            if self.current_token and self.current_token.token == ']':
                if arr_exist:
                    raise SemanticError("IndexError: Index must not be blank for array index assignment.", 
                                        pos_start, [self.current_token.line, self.current_token.column])
                dimensions.append(None)
            else:
                dim = self.parse_expr(scope)
                if arr_exist:
                    dimensions.append(dim)
                else:
                    if isinstance(dim, HpLiteral):
                        dimensions.append(dim.value)
                    else:
                        raise SemanticError("ArraySizeError: Array size must be an hp literal only.",
                                            pos_start, [self.current_token.line, self.current_token.column])
                
            self.skip_spaces()
            self.expect("]", "Expected ']' to close array dimension declaration.")
            pos_end = [self.current_token.line, self.current_token.column - 1]
            self.skip_spaces()
            
        if self.current_token.token == ':':
            self.current_token = self.get_next_token() #eat :
            self.skip_spaces()
            if self.current_token and self.current_token.token == '[':
                if arr_exist:
                    raise SemanticError(f"NameError: Array '{name}' was already declared.",
                                        pos_start, id_pos_end)
                else:
                    values, pos_end = self.parse_array_values(dimensions, scope, pos_start)
                    self.declare_id(name, "an array", len(dimensions))
                    self.skip_spaces()
                    self.expect("newline", "Expected 'newline' after every statements.")
                    return ArrayDec(arr_name, dimensions, values, False, scope, None, pos_start, pos_end)
            else:
                if arr_exist:
                    if all(dim is not None for dim in dimensions):
                        value = self.parse_expr(scope)
                        lhs = ArrElement(arr_name, dimensions, pos_start, pos_end)
                        pos_end = value.pos_end
                        self.skip_spaces()
                        self.expect("newline", "Expected 'newline' after every statements.")
                        return ArrAssignment(lhs, ':', value, pos_start, pos_end)
                    else:
                        raise SemanticError(f"IndexError: Index must not be blank for array index assignment for array name '{arr_name.symbol}'.", pos_start, pos_end)
                else:
                    raise SemanticError(f"NameError: Array '{arr_name.symbol}' does not exist.", pos_start, id_pos_end)
        else:
            operator = self.current_token.token
            self.current_token = self.get_next_token() #eat operator
            self.skip_spaces()
            if arr_exist:
                if all(dim is not None for dim in dimensions):
                    value = self.parse_expr(scope)
                    lhs = ArrElement(arr_name, dimensions, pos_start, pos_end)
                    pos_end = value.pos_end
                    self.skip_spaces()
                    self.expect("newline", "Expected 'newline' after every statements.")
                    return ArrAssignment(lhs, operator, value, pos_start, pos_end)
                else:
                    raise SemanticError(f"IndexError: Index must not be blank for array index assignment for array name '{arr_name.symbol}'.", pos_start, pos_end)
            else:
                raise SemanticError(f"NameError: Array '{arr_name.symbol}' does not exist.", pos_start, id_pos_end)

    def parse_array_values(self, expected_dims, scope, pos_start):
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
                raise SemanticError(f"ArraySizeError: Expected {expected_dims[0]} elements, but got {len(values)}.",
                                    pos_start, pos_end)
            for row in values:
                if expected_dims[1] is not None and len(row) != expected_dims[1]:
                    raise SemanticError(f"ArraySizeError: Expected {expected_dims[1]} elements, but got {len(row)}.",
                                        pos_start, pos_end)
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
                    f"ArraySizeError: Redeclaring a one-dimensional array with more than one rows.",
                                    pos_start, pos_end)
            
            if expected_dims[0] is not None and len(values) != expected_dims[0]:
                raise SemanticError(f"ArraySizeError: Expected {expected_dims[0]} elements, but got {len(values)}.",
                                    pos_start, pos_end)
        
        return values, pos_end

    def parse_inner_arr_values(self, scope):
        inner_values = []
        while self.current_token and self.current_token.token != ']':
            value = self.parse_expr(scope)
            if value.kind not in ["HpLiteral", "XpLiteral", "CommsLiteral", "FlagLiteral"]:
                 raise SemanticError("TypeError: Arrays can only be initialied with literal values.", self.current_token.line)
            inner_values.append(value)
            self.skip_spaces()
            if self.current_token.token == ',':
                self.current_token = self.get_next_token()  # eat ,
                self.skip_spaces()
        return inner_values
   
    def parse_arr_redec(self, name, scope):
        pos_start = [self.current_token.line, self.current_token.column]
        dimensions=self.get_dimensions(name.symbol, name)
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        self.expect(":", "Expected ':' after array name for array re-decleration.")
        self.skip_spaces()
        if dimensions == 1:
            dimensions = [None]
        elif dimensions == 2:
            dimensions = [None, None]
        if self.current_token and self.current_token.token == '[':
            values, pos_end = self.parse_array_values(dimensions, scope, pos_start)
            self.skip_spaces()
            self.expect("newline", "Expected 'newline' after every statements.")
            return ArrayRedec(name, dimensions, values, False, scope, pos_start, pos_end) 
        elif re.match(r'^id\d+$', self.current_token.token):
            id_pos_start = [self.current_token.line, self.current_token.column]
            rhs_name = self.current_token.lexeme
            rhs_name_size = len(rhs_name)
            id_pos_end = [self.current_token.line, self.current_token.column + rhs_name_size - 1]
            rhs_name_node = Identifier(self.current_token.lexeme, id_pos_start, id_pos_end)
            la_token = self.look_ahead()
            if la_token.token == '(':
                if not self.lookup_id_type(rhs_name, "a function", rhs_name_node):
                    raise SemanticError(f"NameError: Function '{rhs_name}' does not exist.", id_pos_start, id_pos_end)
                values = self.parse_func_call(scope)
                pos_end = values.pos_end
                self.skip_spaces()
                self.expect("newline", "Expected 'newline' after every statements.") 
                return ArrayRedec(name, dimensions, values, False, scope, pos_start, pos_end)
            self.current_token = self.get_next_token() # eat id
            self.skip_spaces()
            self.expect("newline", "Expected 'newline' after every statements.") 
            info = self.lookup_identifier(rhs_name)
            if info:
                info = self.get_identifier_info(rhs_name, rhs_name_node)
                if info["type"] == 'a parameter':
                    self.declare_id(name.symbol, "an array")
                    return ArrayRedec(name, dimensions, rhs_name_node, False, scope, pos_start, id_pos_end)
                elif info["type"] != "an array":
                    raise SemanticError(f"ValueError: Array '{name.symbol}' is being redeclared with"
                                        " non-array element.", id_pos_start, id_pos_end)
                else:
                    return ArrayRedec(name, dimensions, rhs_name_node, False, scope, pos_start, id_pos_end)
            else:
                raise SemanticError(f"NameError: Array '{rhs_name}' does not exist.",  id_pos_start, id_pos_end)
        else:
            raise SemanticError(f"ValueError: Array '{name.symbol}' is being redeclared with"
                                " non-array element.", self.current_token.line)

    ########## STRUCTS ##########
    def parse_globalstruct(self) -> Union[StructDec, GlobalStructDec]:
        pos_start = [self.current_token.line, self.current_token.column]
        self.current_token = self.get_next_token() # eat build
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("ParserError: Expected struct name after 'build'.", self.current_token.line)
        id_pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        struct_name = Identifier(self.current_token.lexeme, id_pos_start, id_pos_end)
        self.current_token = self.get_next_token() # eat id
        node = GlobalStructDec(struct_name, pos_start, id_pos_end)

        self.skip_whitespace()
        if self.current_token.token == '{':
            if struct_name.symbol in self.globalstruct:
                del self.globalstruct[struct_name.symbol]
                return self.create_struct(struct_name, "global")
                
            raise SemanticError(f"NameError: Global struct '{struct_name.symbol}' was not declared.", id_pos_start, id_pos_end)
        else:
            if struct_name.symbol in self.globalstruct:
                raise SemanticError(f"NameError: Global struct '{struct_name.symbol}' was already declared.", id_pos_start, id_pos_end)
            self.globalstruct[struct_name.symbol] = {
                "start" : pos_start,
                "end" : id_pos_end,
            }
            return node

    def parse_struct(self, scope) -> StructDec:
        self.current_token = self.get_next_token() # eat build
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("ParserError: Expected struct name after 'build'.", self.current_token.line)
        id_pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1] 
        struct_name = Identifier(self.current_token.lexeme, id_pos_start, id_pos_end)
        if self.lookup_identifier(struct_name.symbol):
            info = self.get_identifier_info(struct_name.symbol, struct_name)
            raise SemanticError(f"NameError: Identifier '{struct_name.symbol}' is already declared as {info["type"]}.", id_pos_start, id_pos_end)
        
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
                    info = self.get_identifier_info(field_name.symbol, field_name)
                    raise SemanticError(f"NameError: Field name '{field_name.symbol}' cannot be used since it is already declared as {info["type"]}.", id_pos_start, id_pos_end)
                if field_name.symbol in fields_table:
                    raise SemanticError(f"NameError: Duplicate field name detected: '{field_name.symbol}'.", id_pos_start, id_pos_end)
                fields_table.append(field_name.symbol)
                self.skip_whitespace()
            else:
                fields.append(StructFields(field_name, None, datatype, id_pos_start, id_pos_end))
                if self.lookup_identifier(field_name.symbol):
                    info = self.get_identifier_info(field_name.symbol, field_name)
                    raise SemanticError(f"NameError: Field name '{field_name.symbol}' cannot be used since it is already declared as {info["type"]}.", id_pos_start, id_pos_end)
                if field_name.symbol in fields_table:
                    raise SemanticError(f"NameError: Duplicate field name detected: '{field_name.symbol}'.", id_pos_start, id_pos_end)
                fields_table.append(field_name.symbol)
                self.skip_whitespace()
            if self.current_token and self.current_token.token == ',':
                self.current_token = self.get_next_token()  # eat ,
                self.skip_whitespace()
        self.current_token = self.get_next_token() # eat }
        self.skip_whitespace()
        if name in self.globalstruct:
            raise SemanticError(f"NameError: Global struct '{name}' already exists.", struct_name.pos_start, struct_name.pos_end)
        if self.lookup_identifier(name):
            info = self.get_identifier_info(name, struct_name)
            raise SemanticError(f"NameError: Identifier {name}' was "
                                f"already declared as {info["type"]}.", struct_name.pos_start, struct_name.pos_end) 
        self.declare_id(name, "a struct")
        return StructDec(struct_name, fields, scope)

    def parse_struct_inst(self, scope) -> StructInst:
        pos_start = [self.current_token.line, self.current_token.column]
        self.current_token = self.get_next_token()  # eat 'access'
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise SemanticError("ParserError: Expected struct name after 'access'.", self.current_token.line)
        struct_parent = self.current_token.lexeme
        if not self.lookup_identifier(struct_parent):
            if struct_parent in self.globalstruct:
                pass
            else:
                raise SemanticError(f"NameError: Struct '{struct_parent}' is not defined.",
                                    [self.current_token.line, self.current_token.column],
                                    [self.current_token.line, self.current_token.column + len(struct_parent)-1])
        
        self.current_token = self.get_next_token()  # eat id
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise SemanticError("ParserError: Expected struct instance name after struct name.", self.current_token.line)
        id_pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        inst_name = Identifier(self.current_token.lexeme, id_pos_start, id_pos_end)
        if self.lookup_identifier(inst_name.symbol):
            info = self.get_identifier_info(inst_name.symbol, inst_name)
            raise SemanticError(f"NameError: Identifier '{inst_name.symbol}' is already declared as {info["type"]}.", id_pos_start, id_pos_end)
        self.current_token = self.get_next_token()  # eat id
        self.skip_spaces()
        values = []
        pos_end = id_pos_end
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
                        raise SemanticError("ParserError: Unexpected newline found after struct instance value.", self.current_token.line)
                elif self.current_token.token == 'newline':
                    break
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
            node = self.parse_drop(scope, struct_inst_name, pos_start)
            self.skip_spaces()
            self.expect("newline", "Expected 'newline' after every statements.") 
            return node

        if self.lookup_identifier(struct_inst_name.symbol):
            info = self.get_identifier_info(struct_inst_name.symbol, struct_inst_name)
            if info["type"] != "a struct instance" and info["type"] != "a parameter":
                raise SemanticError(f"NameError: Struct instance '{struct_inst_name.symbol}' is not defined.", pos_start, id_pos_end)
        else:
            raise SemanticError(f"NameError: Struct instance '{struct_inst_name.symbol}' is not defined.", pos_start, id_pos_end)
        
        if self.current_token.token != '.':
            raise SemanticError("ParserError: Expected '.' after struct instance name.", self.current_token.line)
        self.current_token = self.get_next_token() # eat .
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise SemanticError("ParserError: Expected struct instance field name after struct instance name.", self.current_token.line)
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
        self.skip_spaces()
        self.expect("newline", "Expected 'newline' after every statements.") 
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
                raise SemanticError("ParserError: Expected identifier or 'access' after 'immo'.", self.current_token.line)
            la_token = self.look_ahead()
            if la_token is not None and la_token.token in [':',',']:  
                immo_var = self.parse_immo_var(scope)  
                return immo_var
            elif la_token is not None and la_token.token == '[':  
                immo_arr = self.parse_immo_arr(scope)
                return immo_arr
            else:
                raise SemanticError(f"ParserError: 5 Unexpected token found during parsing: {la_token}", self.current_token.line)  
            
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
                raise SemanticError("ParserError: Expected variable name after ','.", self.current_token.line)
            
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
                        info = self.get_identifier_info(var.symbol, var)
                        raise SemanticError(f"NameError: Identifier '{var.symbol}' is already declared as {info["type"]}.", var.pos_start, var.pos_end)  
                    self.declare_id(var.symbol, "a variable")
                self.skip_spaces()
                self.expect("newline", "Expected 'newline' after every statements.") 
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
                raise SemanticError("ParserError: Expected variable name after ','.", self.current_token.line)
            
            id_pos_start = [self.current_token.line, self.current_token.column]
            var_name_size = len(self.current_token.lexeme)
            id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
            
            var_names.append(Identifier(self.current_token.lexeme, id_pos_start, id_pos_end))
            variable_name = self.current_token.lexeme
            self.current_token = self.get_next_token() # eat id
            self.skip_spaces()

            if not self.current_token or self.current_token.token != ":":
                raise SemanticError("ParserError: Expected ':' in variable initialization.", self.current_token.line)
            
            self.current_token = self.get_next_token() # eat :
            self.skip_spaces()

            value = self.parse_expr(scope)
            values_table[variable_name] = {"values": value}
        
        self.skip_spaces()
        self.expect("newline", "Expected 'newline' after every statements.") 
        if len(var_names) > 1:
            for var in var_names:
                if self.lookup_identifier(var.symbol):
                    info = self.get_identifier_info(var.symbol, var)
                    raise SemanticError(f"NameError: Identifier '{var.symbol}' is already declared as {info["type"]}.", var.pos_start, var.pos_end)  
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
                info = self.get_identifier_info(var.symbol, var)
                raise SemanticError(f"NameError: Identifier '{var.symbol}' is already declared as {info["type"]}.", var.pos_start, var.pos_end)    
            self.declare_id(var.symbol, "a variable")
            return VarDec(var, value, True, scope, pos_start, value.pos_end)

    def parse_immo_arr(self, scope) -> ArrayDec:
        pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        arr_name = Identifier(self.current_token.lexeme, pos_start, id_pos_end)
        name=arr_name.symbol
        if self.lookup_identifier(name):
            info = self.get_identifier_info(name, arr_name)
            raise SemanticError(f"NameError: Identifier '{name}' is already declared as {info["type"]}.", pos_start, id_pos_end)
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        dimensions = []
        while self.current_token and self.current_token.token == '[':
            self.current_token = self.get_next_token() #eat [
            self.skip_spaces
            dim = int(self.current_token.lexeme)
            if dim < 2:
                raise SemanticError(f"ArraySizeError: Expected array size to be greater than 1, but got {dim}.", self.current_token.line)
            dimensions.append(dim)
            self.current_token = self.get_next_token() # eat hp_ltr
            self.skip_spaces()
            self.expect("]","Expected ']' to close immutable array declaration.")
            self.skip_spaces()
            
        self.expect(":", "Expected ':' in array initialization or modification.")
        self.skip_spaces()
        values, pos_end = self.parse_array_values(dimensions, scope, pos_start)
        self.declare_id(name, "an array", len(dimensions))
        self.skip_spaces()
        self.expect("newline", "Expected 'newline' after every statements.") 
        return ArrayDec(arr_name, dimensions, values, True, scope, None, pos_start, pos_end)
    
    def parse_immo_inst(self, scope) -> ImmoInstDec:
        pos_start = [self.current_token.line, self.current_token.column]
        self.current_token = self.get_next_token()  # eat 'access'
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise SemanticError("ParserError: Expected struct name after 'access'.", self.current_token.line)
        struct_parent = self.current_token.lexeme
        if not self.lookup_identifier(struct_parent):
            if struct_parent in self.globalstruct:
                pass
            else:
                raise SemanticError(f"NameError: Struct '{struct_parent}' is not defined.", 
                                    [self.current_token.line, self.current_token.column],
                                    [self.current_token.line, self.current_token.column+len(struct_parent)-1])
        self.current_token = self.get_next_token()  # eat id
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
            raise SemanticError("ParserError: Expected struct instance name after struct name.", self.current_token.line)
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
                    raise SemanticError("ParserError: Unexpected newline found after struct instance value.", self.current_token.line)
            elif self.current_token.token == 'newline':
                break
        if self.lookup_identifier(inst_name.symbol):
            info = self.get_identifier_info(inst_name.symbol, inst_name)
            raise SemanticError(f"NameError: Identifier '{inst_name.symbol}' is already declared as {info["type"]}.", id_pos_start, id_pos_end)
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
            raise SemanticError(f"NameError: Variable '{name}' does not exist.", pos_start, id_pos_end)
        self.current_token = self.get_next_token() # eat id
        self.skip_spaces()
        operator = self.current_token.token
        self.current_token = self.get_next_token() # eat operator
        self.skip_spaces()
        value = self.parse_expr(scope)
        pos_end = value.pos_end
        self.skip_spaces()
        self.expect("newline", "Expected 'newline' after every statements.") 
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
            raise SemanticError("ParserError: Unexpected end of input during parsing!")
        
        tk = self.current_token.token

        if re.match(r'^id\d+$', tk):
            tk= 'id'

        if tk == 'id':
            new_pos_start = [self.current_token.line, self.current_token.column]
            id_size = len(self.current_token.lexeme)
            id_pos_end=[self.current_token.line, self.current_token.column + id_size - 1]
            identifier = Identifier(self.current_token.lexeme, new_pos_start, id_pos_end)
            self.current_token = self.get_next_token()
            self.skip_spaces()
            if self.current_token.token == '.':
                
                join_token = self.find_token_in_line('drop')
                if join_token:
                    node = self.parse_drop(scope, identifier, new_pos_start)
                    self.skip_spaces()
                    return node

                join_token = self.find_token_in_line('seek')
                if join_token:
                    return self.parse_seek(scope, identifier, new_pos_start)
                
                if not self.lookup_identifier(identifier.symbol):
                    raise SemanticError(f"NameError: Struct instance '{identifier.symbol}' does not exist.", new_pos_start, id_pos_end)
                
                info = self.get_identifier_info(identifier.symbol, identifier)
                allowed_types = {"a struct instance"}
                if self.func_flag:
                    allowed_types.add("a parameter")
                
                if info["type"] not in allowed_types:
                    raise SemanticError(f"NameError: Identifier '{identifier.symbol}' is already declared as {info['type']}", new_pos_start, id_pos_end)
                
                self.current_token = self.get_next_token()
                self.skip_spaces()
                if not re.match(r'^id\d+$', self.current_token.token):
                    raise SemanticError("ParserError: Expected 'id' after '.' in accessing a struct instance field.", self.current_token.line)
                field_start = [self.current_token.line, self.current_token.column]
                field_size = len(self.current_token.lexeme)
                pos_end = [self.current_token.line, self.current_token.column + field_size - 1]
                field = Identifier(self.current_token.lexeme, field_start, pos_end)  
                identifier = StructInstField(identifier, field, new_pos_start, pos_end)
                self.current_token = self.get_next_token()
                self.skip_spaces()
            elif self.current_token.token == '[':
                arr_exist = self.is_array(identifier.symbol, identifier) or self.is_params(identifier.symbol, identifier)
                
                if arr_exist:
                    join_token = self.find_token_in_line('drop')
                    if join_token:
                        node = self.parse_drop2d(scope, identifier, new_pos_start)
                        self.skip_spaces()
                        return node
                    
                    join_token = self.find_token_in_line('seek')
                    if join_token:
                        return self.parse_seek2d(scope, identifier, new_pos_start)
                
                dimensions = []
                if not self.lookup_identifier(identifier.symbol):
                    raise SemanticError(f"NameError: Variable '{identifier.symbol}' does not exist.", new_pos_start, id_pos_end)

                info = self.get_identifier_info(identifier.symbol, identifier)
                allowed_types = {"an array", "a variable"}
                if self.func_flag:
                    allowed_types.add("a parameter")

                if info["type"] not in allowed_types:
                    raise SemanticError(f"NameError: Identifier '{identifier.symbol}' is already declared as {info['type']}", new_pos_start, id_pos_end)

                error = None
                while self.current_token and self.current_token.token == '[':
                    self.current_token = self.get_next_token()  # eat '['
                    self.skip_spaces()
                    
                    if self.current_token and self.current_token.token == ']':
                        error = SemanticError("IndexError: Index cannot be empty.")
                        self.current_token = self.get_next_token()  # eat ']'
                        self.skip_spaces()
                    else:
                        dim = self.parse_expr(scope)
                        dimensions.append(dim)
                        self.skip_spaces()
                        self.expect("]", "Expected ']' to close array dimension.")

                pos_end = [self.current_token.line, self.current_token.column - 1]
                self.skip_spaces()

                if error:
                    error.pos_start = new_pos_start
                    error.pos_end = pos_end
                    raise error

                if info["type"] == "an array":
                    identifier = ArrElement(identifier, dimensions, new_pos_start, pos_end)
                else:
                    identifier = StringIndexArr(identifier, dimensions, new_pos_start, pos_end)
            elif self.current_token.token == '(':
                if not self.lookup_id_type(identifier.symbol, "a function", identifier):
                    raise SemanticError(f"NameError: Function '{identifier.symbol}' does not exist.", new_pos_start, id_pos_end)
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
                if not self.lookup_id_type(identifier.symbol, "a variable", identifier):
                    raise SemanticError(f"NameError: Variable '{identifier.symbol}' does not exist.", new_pos_start, id_pos_end)
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
                    raise SemanticError(f"NameError: Variable '{identifier.symbol}' does not exist.", new_pos_start, id_pos_end)
                
                info = self.get_identifier_info(identifier.symbol, identifier)
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
                    raise SemanticError(f"NameError: Identifier '{identifier.symbol}' is already declared as {info['type']}", new_pos_start, id_pos_end)

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
            ltr_size = len(self.current_token.lexeme) - 1
            ltr_pos_end = [self.current_token.line, self.current_token.column + ltr_size]
            print(f"value before {self.current_token.lexeme}")
            value = re.sub(r'^"(.*)"$', r'\1', self.current_token.lexeme, flags=re.DOTALL)
            print(value)
            open_braces = 0
            placeholders = []
            current_placeholder = ""
            inside_placeholder = False
            final_value = ""
            escaped = False
            col = self.current_token.column
            ln = self.current_token.line

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
                        raise SemanticError("FormatError: Nested or unexpected '{' found in string literal.", [ln, col+i+1], [ln, col+i+1])
                    inside_placeholder = True
                    open_braces += 1
                    braces_char = col+i+1
                    current_placeholder = ""
                elif char == '}':
                    if not inside_placeholder:
                        raise SemanticError("FormatError: Unexpected '}' found in string literal.", [ln, col+i+1], [ln, col+i+1])
                    inside_placeholder = False
                    open_braces -= 1
                    if not current_placeholder:
                        raise SemanticError("FormatError: Empty placeholder '{}' found in string literal.", [ln, col+i+1], [ln, col+i+1])
                    placeholders.append(current_placeholder)
                else:
                    if inside_placeholder:
                        current_placeholder += char
                    else:
                        final_value += char

            if open_braces > 0:
                raise SemanticError("FormatError: Unclosed '{' found in string literal.", [ln, braces_char], [ln, braces_char])

            print(f"Placeholders: {placeholders}")
            print(f"Final string: {final_value}")
            if placeholders:
                results = []
                for i, placeholder in enumerate(placeholders):
                    lexer = Lexer("yo", placeholder)
                    tokens, error = lexer.make_tokens()
                    if error:
                        raise SemanticError(f"Lexical error in placeholder {i}: cannot proceed to parsing.\n\n" + "\n\n".join(error), ltr_pos_start, ltr_pos_end)
                    print(tokens)
                    tokens.pop()
                    helper = Helper(tokens, self.scope_stack, self.func_flag, ltr_pos_start, ltr_pos_end)
                    result = helper.parse_expr(scope)
                    if isinstance(result, SemanticError):
                        raise SemanticError(f"Error in placeholder {i+1}: {str(result)}", ltr_pos_start, ltr_pos_end)
                    results.append(result)
                ltr_size = len(self.current_token.lexeme) - 1
                ltr_pos_end = [self.current_token.line, self.current_token.column + ltr_size]
                literal = FormattedCommsLiteral(value, placeholders, results, ltr_pos_start, ltr_pos_end)
                self.current_token = self.get_next_token()
                self.skip_spaces()
                return literal

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
                raise SemanticError("FormatError: xp formatting cannot be used as a value within a parentheses.", value.pos_start, value.pos_end)
            self.expect(')', "Unexpected token found inside parenthesised expression. Expected closing parenthesis.")
            self.skip_spaces()
            if self.current_token.token == 'xp_formatting':
                format_str = re.sub(r'^"(.*)"$', r'\1', self.current_token.lexeme)
                if not re.match(r'^\.\d+f$', format_str):
                    raise SemanticError(f"FormatError: Invalid format specifier '{format_str}'.",
                                        [self.current_token.line, self.current_token.column],
                                        [self.current_token.line, self.current_token.column]+2)
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
            #print(self.current_token.token)
            self.current_token = self.get_next_token() # eat load
            #print(self.current_token.token)
            if self.current_token.token != '(':
                #print("here?")
                raise SemanticError("ParserError: Missing parentheses.", self.current_token.line)
            #print(f"3 {self.current_token.token}")
            self.current_token = self.get_next_token() # eat (
            #print(f"4 {self.current_token.token}")
            self.skip_spaces()
            if re.match(r'^comms_ltr', self.current_token.token):
                prompt_msg = self.parse_primary_expr(scope)
                #print(f"5 {self.current_token.token}")
                #print(f"6 {self.current_token.token}")
                self.skip_spaces()
            if self.current_token.token != ')':
                raise SemanticError("ParserError: Missing parentheses.", self.current_token.line)
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
                raise SemanticError("ArgumentError: Invalid rounds argument.", self.current_token.line)
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
                raise SemanticError(f"ArgumentError: Invalid '{tk}' argument.", self.current_token.line)
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
            value = self.parse_expr(scope)
            valid_kinds = ['Identifier', 'ArrayElement', 'StructInstField', 'BinaryExpr'] 
            if value.kind not in valid_kinds:
                raise SemanticError(f"ArgumentError: Invalid '{tk}' argument.", self.current_token.line)
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
            value = self.parse_expr(scope)
            valid_kinds = ['Identifier', 'ArrayElement', 'StructInstField', 'BinaryExpr'] 
            if value.kind not in valid_kinds:
                raise SemanticError(f"ArgumentError: Invalid '{tk}' argument.", self.current_token.line)
            self.skip_spaces()
            self.expect(')', f"Expected ')' after '{tk}' arguments.")
            func_pos_end = [self.current_token.line, self.current_token.column - 1]
            self.skip_spaces()
            return ToCommsStmt(value, func_pos_start, func_pos_end)
        else:
            raise SemanticError(f"ParserError: 6 Unexpected token found during parsing: {tk}", self.current_token.line)
        
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
        
        
        if not hasattr(self, 'flank_flag_stack'):
            self.flank_flag_stack = []

        self.flank_flag_stack.append(True)  
        print(f"flank flag out of flank = {self.flank_flag_stack[-1]}.")

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
            self.flank_flag_stack.pop()
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
        self.flank_flag_stack.pop()
        return FlankStmt(expression, choices, backup_body)

    ########## LOOPS #############
    def parse_for(self,scope) -> ForStmt:
        pos_start = [self.current_token.line, self.current_token.column]
        self.current_token = self.get_next_token() # eat for
        self.skip_spaces()
        if not self.current_token or not re.match(r'^id\d+$', self.current_token.token):
                raise SemanticError("ForError: Expected variable name after for keyword.", self.current_token.line)
        init_pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        name = Identifier(self.current_token.lexeme, init_pos_start, id_pos_end)
        if not self.lookup_id_type(name.symbol, "a variable", name):
            raise SemanticError(f"NameError: Variable '{name.symbol}' is not defined.", init_pos_start, id_pos_end)
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
                raise SemanticError("ForError: Expected variable name after loop condition.", self.current_token.line)
        id_pos_start = [self.current_token.line, self.current_token.column]
        var_name_size = len(self.current_token.lexeme)
        id_pos_end = [self.current_token.line, self.current_token.column + var_name_size - 1]
        upd_name = Identifier(self.current_token.lexeme, id_pos_start, id_pos_end)
        if not self.lookup_id_type(upd_name.symbol, "a variable", upd_name):
            raise SemanticError(f"NameError: Variable '{upd_name.symbol}' is not defined.", id_pos_start, id_pos_end)
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
        
        if not hasattr(self, 'loop_flag_stack'):
            self.loop_flag_stack = []

        self.loop_flag_stack.append(True)  
        print(f"loop flag out of loop = {self.loop_flag_stack[-1]}.")

        while self.current_token and self.current_token.token != "}":
            print(f"loop flag in loop = {self.loop_flag_stack[-1]}.")
            stmt = self.parse_stmt(scope)
            body.append(stmt)
            self.skip_whitespace()
            if isinstance(stmt, RecallStmt):
                self.recall_stmts.append(stmt)


        self.expect("}", "Expected '}' to close a for loop statement's body.")
        pos_end = [self.current_token.line, self.current_token.column-1]
        self.skip_whitespace()
        self.pop_scope()
        self.loop_flag_stack.pop()
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

        if not hasattr(self, 'loop_flag_stack'):
            self.loop_flag_stack = []

        self.loop_flag_stack.append(True)  
        print(f"loop flag out of loop = {self.loop_flag_stack[-1]}.")

        while self.current_token and self.current_token.token != "}":
            print(f"loop flag in loop = {self.loop_flag_stack[-1]}.")
            stmt = self.parse_stmt(scope)
            body.append(stmt)
            self.skip_whitespace()
            if isinstance(stmt, RecallStmt):
                self.recall_stmts.append(stmt)
        self.expect("}", "Expected '}' to close a while loop statement's body.")
        self.skip_whitespace()
        self.pop_scope()

        self.loop_flag_stack.pop()
        return GrindWhileStmt(condition, body)
    
    def parse_grind_while(self,scope) -> GrindWhileStmt:
        self.current_token = self.get_next_token() # eat grind
        self.skip_spaces()
        self.expect("{", "Expected '{' to open a grind while loop statement's body.")
        self.skip_whitespace()
        body = []
        self.push_scope()

        if not hasattr(self, 'loop_flag_stack'):
            self.loop_flag_stack = []

        self.loop_flag_stack.append(True)  
        print(f"loop flag out of loop = {self.loop_flag_stack[-1]}.")

        while self.current_token and self.current_token.token != "}":
            print(f"loop flag in loop = {self.loop_flag_stack[-1]}.")
            stmt = self.parse_stmt(scope)
            body.append(stmt)
            self.skip_whitespace()
            if isinstance(stmt, RecallStmt):
                self.recall_stmts.append(stmt)
        self.expect("}", "Expected '}' to close a grind while loop statement's body.")
        self.skip_whitespace()
        self.pop_scope()

        self.loop_flag_stack.pop()
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
            pos_end = [self.current_token.line, self.current_token.column]
            self.expect(")", "Expected closing parentheses in function call.")
            self.skip_spaces()
            self.expect("newline", "Expected 'newline' after every statements.") 
            return ShootStmt(CommsLiteral("", pos_start, pos_end), is_Next, pos_start, pos_end)
        value = self.parse_expr(scope)
        self.skip_spaces()
        self.expect(")", "Expected closing parentheses in function call.")
        pos_end = [self.current_token.line, self.current_token.column-1]
        self.skip_spaces()
        self.expect("newline", "Expected 'newline' after every statements.") 
        return ShootStmt(value, is_Next, pos_start, pos_end)

    def parse_join(self, scope, name, pos_start) -> JoinStmt:
        if self.lookup_identifier(name.symbol):
            info = self.get_identifier_info(name.symbol, name)
            if info["type"] not in ["an array", "a parameter", "a variable"]: 
                raise SemanticError(f"NameError: Array '{name.symbol}' is not defined.", name.pos_start, name.pos_end)
        else:
            raise SemanticError(f"NameError: Array '{name.symbol}' is not defined.", name.pos_start, name.pos_end)
        if info["type"] == "a parameter" or info["type"] == "a variable":
            dimensions = None
        elif info["type"] == "an array":
            dimensions = self.get_dimensions(name.symbol, name)
        self.expect(".", "Expects '.' in join function call.")
        self.expect("join", "Expects 'join' keyword in join function call.")
        self.expect("(", "Expects '(' after join keyword in join function call.")
        self.skip_spaces()
        if self.current_token.token == '[':
            if info["type"] == "a variable":
                raise SemanticError("DimensionsError: Trying to append a new row to a variable, must be an array.", self.current_token.line)
            if dimensions is None or dimensions == 2:
                pass
            else:
                raise SemanticError("DimensionsError: Trying to append a new row to a one dimensional array.", self.current_token.line)
            self.current_token = self.get_next_token() # eat [
            self.skip_spaces()
            values = [self.parse_inner_arr_values(scope)]
            self.expect("]", "Expects ']' to close array row values.")
            self.skip_spaces()
            self.expect(")", "Expects ')' after to close join arguments.")
            pos_end = [self.current_token.line, self.current_token.column-1]
            self.skip_spaces()
            self.expect("newline", "Expected 'newline' after every statements.") 
            self.skip_whitespace()
            return JoinStmt(name, values, 2, pos_start, pos_end)
        else:
            if dimensions is None or dimensions == 1:
                pass
            else:
                raise SemanticError("DimensionsError: Trying to append new elements incorrectly to a two dimensional array, must specify row index first.", self.current_token.line)
            if self.current_token.token == ')':
                raise SemanticError("ValueError: Elements inside parentheses must not be empty.", self.current_token.line)
            value = self.parse_expr(scope)
            self.skip_spaces()
            self.expect(")", "Expects ')' after to close join arguments.")
            pos_end = [self.current_token.line, self.current_token.column-1]
            self.skip_spaces()
            self.expect("newline", "Expected 'newline' after every statements.") 
            self.skip_whitespace()
            return JoinStmt(name, value, 1, pos_start, pos_end)

    def parse_join2d(self, scope, arr_name, pos_start) -> JoinStmt:
        self.expect("[", "Expects '[' to specify row index of two-dimensional array.")
        self.skip_spaces()
        if self.current_token.token == ']':
            raise SemanticError("IndexError: Index must not be blank for join function call.", self.current_token.line)
        dim = self.parse_expr(scope)
        self.skip_spaces()
        self.expect("]", "Expected ']' to close array dimension declaration.")
        self.skip_spaces()
        info = self.get_identifier_info(arr_name.symbol, arr_name)
        if info["type"] == "an array":
            dimensions = self.get_dimensions(arr_name.symbol, arr_name)
        else:
            dimensions = None
        if dimensions is None or dimensions == 2:
            pass
        else:
            raise SemanticError("DimensionsError: Trying to append an element in a specific row to a 1d array, must be a 2d array.", self.current_token.line)
        self.expect(".", "Expects '.' in join function call.")
        self.expect("join", "Expects 'join' keyword in join function call.")
        self.expect("(", "Expects '(' after join keyword in join function call.")
        self.skip_spaces()
        if self.current_token.token == ')':
            raise SemanticError("ValueError: Elements inside parentheses must not be empty.", self.current_token.line)
        value = self.parse_expr(scope)
        self.skip_spaces()
        self.expect(")", "Expects ')' after to close join arguments.")
        pos_end = [self.current_token.line, self.current_token.column-1]
        self.skip_spaces()
        self.expect("newline", "Expected 'newline' after every statements.") 
        self.skip_whitespace()
        return JoinStmt(arr_name, value, 2, pos_start, pos_end, dim)

    def parse_drop(self, scope, name, pos_start) -> DropStmt:
        if self.lookup_identifier(name.symbol):
            info = self.get_identifier_info(name.symbol, name)
            if info["type"] not in ["an array", "a parameter", "a variable"]: 
                raise SemanticError(f"NameError: Array '{name.symbol}' is not defined.", name.pos_start, name.pos_end)
        else:
            raise SemanticError(f"NameError: Array '{name.symbol}' is not defined.", name.pos_start, name.pos_end)
        if info["type"] == "a parameter" or info["type"] == "a variable":
            dimensions = None
        elif info["type"] == "an array":
            dimensions = self.get_dimensions(name.symbol, name)
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
        self.skip_spaces()
        return DropStmt(name, index, dimensions, pos_start, pos_end)
    
    def parse_drop2d(self, scope, arr_name, pos_start) -> DropStmt:
        self.expect("[", "Expects '[' to specify row index of two-dimensional array.")
        self.skip_spaces()
        if self.current_token.token == ']':
            raise SemanticError("IndexError: Index must not be blank for drop function call.", self.current_token.line)
        dim = self.parse_expr(scope)
        self.skip_spaces()
        self.expect("]", "Expected ']' to close array dimension declaration.")
        self.skip_spaces()
        info = self.get_identifier_info(arr_name.symbol, arr_name)
        if info["type"] == "an array":
            dimensions = self.get_dimensions(arr_name.symbol, arr_name)
        else:
            dimensions = None
        if dimensions is None or dimensions == 2:
            pass
        else:
            raise SemanticError("DimensionsError: Trying to drop specific row from a one dimensional array, must be two-dimensional.", self.current_token.line)
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
        self.skip_spaces()
        return DropStmt(arr_name, index, dimensions, pos_start, pos_end, dim)

    def parse_seek(self, scope, name, pos_start) -> SeekStmt:
        if self.lookup_identifier(name.symbol):
            info = self.get_identifier_info(name.symbol, name)
            if info["type"] not in ["an array", "a parameter", "a variable"]: 
                raise SemanticError(f"NameError: Array '{name.symbol}' is not defined.", name.pos_start, name.pos_end)
        else:
            raise SemanticError(f"NameError: Array '{name.symbol}' is not defined.", name.pos_start, name.pos_end)
        if info["type"] == "a parameter" or info["type"] == "a variable":
            dimensions = None
        elif info["type"] == "an array":
            dimensions = self.get_dimensions(name.symbol, name)
        self.expect(".", "Expects '.' in seek function call.")
        self.expect("seek", "Expects 'seek' keyword in seek function call.")
        self.expect("(", "Expects '(' after seek keyword in seek function call.")
        self.skip_spaces()
        if self.current_token.token == '[':
            if info["type"] == "a variable":
                raise SemanticError("DimensionsError: Trying to seek a specific row  a variable, must be an array.", self.current_token.line)
            if dimensions is None or dimensions == 2:
                pass
            else:
                raise SemanticError("DimensionsError: Trying to seek a specific row in a 1d array, must be a 2d array.", self.current_token.line)
            self.current_token = self.get_next_token() # eat [
            self.skip_spaces()
            values = [self.parse_inner_arr_values(scope)]
            self.expect("]", "Expects ']' to close array row values.")
            self.skip_spaces()
            self.expect(")", "Expects ')' after to close seek arguments.")
            pos_end = [self.current_token.line, self.current_token.column-1]
            self.skip_spaces()
            return SeekStmt(name, values, 2, pos_start, pos_end)
        else:
            if dimensions is None or dimensions == 1:
                pass
            else:
                raise SemanticError("DimensionsError: Trying to seek a specific element in a 2d array, must specify row index first.", self.current_token.line)
            if self.current_token.token == ')':
                raise SemanticError("ValueError: Elements inside parentheses must not be empty.", self.current_token.line)
            value = self.parse_expr(scope)
            self.skip_spaces()
            self.expect(")", "Expects ')' after to close seek arguments.")
            pos_end = [self.current_token.line, self.current_token.column-1]
            self.skip_spaces()
            return SeekStmt(name, value, 1, pos_start, pos_end)
        
    def parse_seek2d(self, scope, arr_name, pos_start) -> SeekStmt:
        self.expect("[", "Expects '[' to specify row index of two-dimensional array.")
        self.skip_spaces()
        if self.current_token.token == ']':
            raise SemanticError("IndexError: Index must not be blank for seek function call.", self.current_token.line)
        dim = self.parse_expr(scope)
        self.skip_spaces()
        self.expect("]", "Expected ']' to close array dimension declaration.")
        self.skip_spaces()
        info = self.get_identifier_info(arr_name.symbol, arr_name)
        if info["type"] == "an array":
            dimensions = self.get_dimensions(arr_name.symbol, arr_name)
        else:
            dimensions = None
        if dimensions is None or dimensions == 2:
            pass
        else:
            raise SemanticError("DimensionsError: Trying to seek a specific row in a 1d array, must be a 2d array.", self.current_token.line)
        self.expect(".", "Expects '.' in seek function call.")
        self.expect("seek", "Expects 'seek' keyword in seek function call.")
        self.expect("(", "Expects '(' after seek keyword in seek function call.")
        self.skip_spaces()
        if self.current_token.token == ')':
            raise SemanticError("ValueError: Elements inside parentheses must not be empty.", self.current_token.line)
        value = self.parse_expr(scope)
        self.skip_spaces()
        self.expect(")", "Expects ')' after to close seek arguments.")
        pos_end = [self.current_token.line, self.current_token.column-1]
        self.skip_spaces()
        return SeekStmt(arr_name, value, 2, pos_start, pos_end, dim)

def check(fn, text, isRuntime=False):
    lexer = Lexer(fn, text)
    if text == "":
        return "No code in the module."  #, {}

    tokens, error = lexer.make_tokens()

    if error:
        return 'Lexical errors found, cannot continue with syntax analyzing. Please check lexer tab.\n\nLexical Errors:\n' + "\n\n".join(error)  #, {}

    result = parse(fn, text)

    if result != 'No lexical errors found!\nValid syntax.':
        result = result.split("\n", 1)[-1]
        return f'Syntax errors found, cannot continue with semantic analyzing. Please check syntax tab.\n\n{result}'  #, {}

    semantic = Semantic(tokens)
    result = semantic.produce_ast()
    #print(result)

    if isinstance(result, SemanticError):
        result.source_code = text.splitlines()
        return str(result) 

    if isRuntime:
        try:
            runtime_visitor = ASTVisitor()
            runtime_visitor.visit(result)

            runtime_analyzer = SemanticAnalyzer(runtime_visitor.symbol_table, isRuntime)
            runtime_analyzer.visit(result)
        except SemanticError as e:
            e.source_code = text.splitlines()
            return str(e)
        
        return "Code Gen successful!"
    else:
        try:
            visitor = ASTVisitor()
            visitor.visit(result)

            analyzer = SemanticAnalyzer(visitor.symbol_table)
            analyzer.visit(result)
            #table = analyzer.symbol_table
        except SemanticError as e:
            e.source_code = text.splitlines()
            return str(e)
        
        return "Semantic analyzing successful, no lexical, syntax, and semantic errors found!"


    # if isinstance(result, SemanticError):
    #     result.source_code = text.splitlines()
    #     return str(result), {}
    
    # try:
    #     visitor = ASTVisitor()
    #     visitor.visit(result)

    #     analyzer = SemanticAnalyzer(visitor.symbol_table)
    #     analyzer.visit(result)
    #     table = analyzer.symbol_table
    # except SemanticError as e:
    #     e.source_code = text.splitlines()
    #     return str(e), {}

    # return result, table

    # return result, {}
        

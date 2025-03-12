from .cfg import parse_table, first_set
from .lexer import Lexer
import re

class Node:
    def __init__(self, tok, value=None):
        self.tok = tok
        self.value = value
        self.children = []

    def add_child(self, child_node):
        self.children.append(child_node)


class Parser:
    def __init__(self, tokens, source_code):
        self.tokens = tokens
        self.source_code = source_code.split("\n")
        self.current_token_index = 0
        self.current_token = self.get_next_token()
        self.save_stack = []

    def get_next_token(self):
        if self.current_token_index < len(self.tokens):
            token = self.tokens[self.current_token_index]
            self.current_token_index += 1
            return token
        return None
    
    def parser(self):
        self.stack = ["<program>"]  
        self.tokens.append("$")  
        null_flag = False

        while self.stack:
            self.top = self.stack.pop()

            while self.current_token.token in {"newline", "space"}:
                self.current_token = self.get_next_token()

            if re.match(r'^id\d+$', self.current_token.token):
                self.current_token.token= 'id'

            if re.match(r'^comms_ltr', self.current_token.token):
                self.current_token.token= 'comms_ltr'

            # print(f"Current Top = {self.top}")
            # print(f"Current Token = {self.current_token.token}")

            if self.top == self.current_token.token:
                # print(f"Matched: {self.current_token.token} and {self.top}")
                self.current_token = self.get_next_token()
                if null_flag:
                    null_flag = False
                    self.save_stack = []
            elif self.top in parse_table:
                # print(f"Parse Table of current top: {parse_table[self.top]}")
                if self.current_token.token in parse_table[self.top]:
                    production = parse_table[self.top][self.current_token.token]
                    # print(f"Expand: {self.top} → {' '.join(production)}")

                    if "λ" not in production:
                        self.stack.extend(reversed(production))
                    else:
                        if self.save_stack != []:
                            pass
                        else:
                            self.save_top = self.top
                            self.save_stack = self.stack.copy()
                        null_flag = True
                    # print(f"stack: {self.stack}")
                    # print(f"save stack: {self.save_stack}")
                else:
                    expected_tokens = list(parse_table[self.top].keys()) 
                    if self.current_token.token not in expected_tokens:
                        if self.top in first_set:  
                            expected_tokens = list(first_set[self.top]) 
                        
                        i = 1
                        while "λ" in expected_tokens:
                            expected_tokens.remove("λ")
                            if self.stack:
                                next_top = self.stack[-i]  
                                if next_top in parse_table:
                                    expected_tokens.extend(list(first_set[next_top]) )  
                                else:
                                    expected_tokens.append(next_top)
                                i += 1


                        expected_tokens = sorted(set(expected_tokens))
                    
                    error_msg = (f"Syntax Error: Unexpected token '{self.current_token.token}' at line {self.current_token.line} and column {self.current_token.column}."
                                f" Expected tokens: {', '.join(expected_tokens)}.\n\n")
                    error_msg += self.generate_error_message()
                    return error_msg
            else:
                if null_flag:
                    # print(f"save stack: {self.save_stack}")
                    # print(f"save top: {self.save_top}")
                    expected_tokens = list(parse_table[self.save_top].keys()) 
                    # print(f"yeppers: {expected_tokens}")
                    if self.save_top in first_set:  
                        expected_tokens = list(first_set[self.save_top]) 
                        # print(f"yeppers2: {expected_tokens}")

                    i = 1
                    while "λ" in expected_tokens:
                        expected_tokens.remove("λ")
                        if self.save_stack:
                            next_top = self.save_stack[-i]  
                            if next_top in parse_table:
                                expected_tokens.extend(list(first_set[next_top]) )  
                            else:
                                expected_tokens.append(next_top)
                            i += 1


                    expected_tokens = sorted(set(expected_tokens))

                    error_msg = (f"Syntax Error: Unexpected token '{self.current_token.token}' at line {self.current_token.line} and column {self.current_token.column}."
                                f" Expected tokens: {', '.join(expected_tokens)}.\n\n")
                    error_msg += self.generate_error_message()
                    return error_msg

                error_msg = (f"Syntax Error: Unexpected token '{self.current_token.token}' at line {self.current_token.line} and column {self.current_token.column}."
                        f" Expected token: {self.top}.\n\n")
                error_msg += self.generate_error_message()
                return error_msg

        while self.current_token.token in {"newline", "space"}:
                self.current_token = self.get_next_token()
        
        if self.current_token.token == 'EOF':
            return 'Valid syntax.'
        else:
            return "Input not fully consumed."

    def generate_error_message(self):
        line_num = self.current_token.line
        col_num = self.current_token.column
        error_line = self.source_code[line_num - 1]  

        underline = " " * (col_num - 1) + "^" * len(self.current_token.lexeme)

        return (f"{error_line}\n{underline}")

def parse(fn, text):
    lexer = Lexer(fn, text)
    if text == "":
        return "No code in the module."
    tokens, error = lexer.make_tokens()

    if error:
         return 'Lexical errors found, cannot continue with syntax analyzing. Please check lexer tab.\n\nLexical Errors:\n' + "\n\n".join(error)
     

    syntax = Parser(tokens, text)
    result = syntax.parser() 

    return f"No lexical errors found!\n{result}"
      





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
    def __init__(self, tokens):
        self.tokens = tokens
        self.current_token_index = 0
        self.current_token = self.get_next_token()

    def get_next_token(self):
        if self.current_token_index < len(self.tokens):
            token = self.tokens[self.current_token_index]
            self.current_token_index += 1
            return token
        return None
    
    def parser(self):
        self.stack = ["<program>"]  
        self.tokens.append("$")  

        while self.stack:
            self.top = self.stack.pop()

            while self.current_token.token in {"newline", "space"}:
                self.current_token = self.get_next_token()

            if re.match(r'^id\d+$', self.current_token.token):
                self.current_token.token= 'id'

            # print(f"Current Top = {self.top}")
            # print(f"Current Token = {self.current_token.token}")

            if self.top == self.current_token.token:
                # print(f"Matched: {self.current_token.token} and {self.top}")
                self.current_token = self.get_next_token()
            elif self.top in parse_table:
                if self.current_token.token in parse_table[self.top]:
                    production = parse_table[self.top][self.current_token.token]
                    # print(f"Expand: {self.top} → {' '.join(production)}")

                    if "λ" not in production:
                        self.stack.extend(reversed(production))
                    # print(self.stack)
                else:
                    expected_tokens = list(parse_table[self.top].keys()) 
                    if self.current_token.token not in expected_tokens:
                        if self.top in first_set:  
                            expected_tokens = list(first_set[self.top]) 
                            
                        if "λ" in expected_tokens:
                            expected_tokens.remove("λ")
                            if self.stack:
                                next_top = self.stack[-1]  
                                if next_top in parse_table:
                                    expected_tokens.extend(parse_table[next_top].keys())  

                        expected_tokens = list(set(expected_tokens))
                    
                    return (f"Syntax Error: Unexpected token '{self.current_token.token}' at line {self.current_token.line} and column {self.current_token.column}."
                            f" Expected tokens: {', '.join(expected_tokens)}.")
            else:
                return (f"Syntax Error: Unexpected token '{self.current_token.token}' at line {self.current_token.line} and column {self.current_token.column}."
                        f" Expected token: {self.top}.")

        while self.current_token.token in {"newline", "space"}:
                self.current_token = self.get_next_token()
        
        if self.current_token.token == 'EOF':
            return 'Valid syntax.'
        else:
            return "Input not fully consumed."

def parse(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()

    if error:
        return 'Lexical errors found, cannot continue with syntax analyzing. Please check lexer tab.' 

    syntax = Parser(tokens)
    result = syntax.parser() 

    return f"No lexical errors found!\n{result}"
      





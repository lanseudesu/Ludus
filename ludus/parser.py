from .cfg import parse_table
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

            #print(self.current_token.token)

            while self.current_token.token in {"newline", "space"}:
                self.current_token = self.get_next_token()

            if re.match(r'^id\d+$', self.current_token.token):
                self.current_token.token= 'id'

            # print(self.top)
            # print(self.current_token.token)

            if self.top == self.current_token.token:
                #print(f"Matched: {self.top}")
                self.current_token = self.get_next_token()
            elif self.top in parse_table:
                if self.current_token.token in parse_table[self.top]:
                    production = parse_table[self.top][self.current_token.token]
                    #print(f"Expand: {self.top} → {' '.join(production)}")

                    if "λ" not in production:
                        self.stack.extend(reversed(production))
                    #print(self.stack)
                else:
                    #print("1") #error append then return false :DDDDD
                    return f"Unexpected token '{self.current_token.token}' at line {self.current_token.line} and column {self.current_token.column}."
            else:
                #print("2")
                return f"Unexpected token '{self.current_token.token}' at line {self.current_token.line} and column {self.current_token.column}."

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

    return result
      





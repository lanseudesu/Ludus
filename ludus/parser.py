from .cfg import parse_table
from .lexer import Lexer
import re

class Node:
    def __init__(self, tok=None):
        self.tok = tok
        self.children = []

    def __str__(self, level=0):
        ret = "\t" * level + repr(self) + "\n"
        for child in self.children:
            ret += child.__str__(level + 1)
        return ret

    def __repr__(self):
        return f"Node({self.tok})"

class programNode(Node):
    pass

class Parser:
    def __init__(self, tokens):
        self.tokens = [token.token for token in tokens]
        self.ln = [token.line for token in tokens]
        self.col = [token.column for token in tokens]
        self.error = []
        self.ast = None

    def parser(self):
        stack = ["<program>"]  
        self.tokens.append("$")  
        pointer = 0  
        root = programNode()  # Create the root of the AST.
        current_node = root

        while stack:
            top = stack.pop()
            current_input = self.tokens[pointer]
            cur_ln = self.ln[pointer]
            cur_col = self.col[pointer]

            while current_input == "newline" or current_input == "space":
                pointer += 1
                current_input = self.tokens[pointer]
                cur_ln = self.ln[pointer]
                cur_col = self.col[pointer]

            if re.match(r'^id\d+$', current_input):
                current_input = 'id'

            print(top)
            print(current_input)

            if top == current_input:
                print(f"Matched: {top}")
                current_node.children.append(Node(current_input))
                pointer += 1
            elif top in parse_table:
                if current_input in parse_table[top]:
                    production = parse_table[top][current_input]
                    new_node = Node(top)
                    current_node.children.append(new_node)
                    current_node = new_node
                    print(f"Expand: {top} → {' '.join(production)}")
                    if "λ" not in production:
                        stack.extend(reversed(production))
                    print(stack)
                else:
                    print("1")
                    self.error.append(f"Unexpected token '{current_input}' at line {cur_ln} and column {cur_col}")
                    return f"Unexpected token '{current_input}' at line {cur_ln} and column {cur_col}."
            else:
                print("2")
                self.error.append(f"Unexpected token '{current_input}' at line {cur_ln} and column {cur_col}")
                return f"Unexpected token '{current_input}' at line {cur_ln} and column {cur_col}."

        if pointer == len(self.tokens) - 1:
            self.ast = root
            return 'Valid syntax.'
        else:
            self.error.append("Input not fully consumed.")
            return "Input not fully consumed."
        
    
def parse(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()

    if error:
        return 'Lexical errors found, cannot continue with syntax analyzing. Please check lexer tab.' 

    syntax = Parser(tokens)
    result = syntax.parser() 

    if result == 'Valid syntax.':
        print(syntax.ast)
        return result
      





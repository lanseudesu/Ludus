from .cfg import parse_table
from .lexer import Lexer

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.error = []

    def parser(self):
        stack = ["<program>"]  
        self.tokens.append("$")  
        pointer = 0  

        while stack:
            top = stack.pop()
            current_input = self.tokens[pointer]

            print(top)
            print(current_input)

            if current_input == "newline" or current_input == "space":
                pointer += 1
            elif top == current_input:
                print(f"Matched: {top}")
                pointer += 1
            elif top in parse_table:
                print(parse_table[top])
                if current_input in parse_table[top]:
                    production = parse_table[top][current_input]
                    print(f"Expand: {top} → {' '.join(production)}")
                    if "λ" not in production:
                        stack.extend(reversed(production))
                    print(stack)
                else:
                    print("1")
                    self.error.append(f"Unexpected token '{current_input}' at position {pointer}")
                    return False
            else:
                self.error.append(f"Unexpected token '{current_input}' at position {pointer}")
                return False

        if pointer == len(self.tokens) - 1:
            print("slmt neso academy!")
            return True
        else:
            self.error.append("Input not fully consumed.")
            return False
        
    
def parse(fn, text):
    lexer = Lexer(fn, text)
    tokens, error = lexer.make_tokens()

    if error:
        pass 

    tokens = [token.token for token in tokens]  

    syntax = Parser(tokens)
    syntax.parser()    





from ..nodes import *

class SymbolTable:
    def __init__(self):
        self.symbols = {}  # Stores variable and function definitions
    
    def define(self, name: str, value):
        self.symbols[name] = value

    def lookup(self, name: str):
        value = self.symbols.get(name, None)
        
        if value is None or isinstance(value, Expr):  # If it's an AST node, it's still unevaluated
            raise Exception(f"Variable '{name}' is not defined before use.")

        return value
    def __repr__(self):
        return f"SymbolTable({self.symbols})"

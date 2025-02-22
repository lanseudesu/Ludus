from ..nodes import *
from ..error import SemanticError

class SymbolTable:
    def __init__(self):
        self.symbols = {}  
    
    def define(self, name: str, value):
        self.symbols[name] = value

    def define_var(self, name: str, value, datatype):
        self.symbols[name] = {
            "type": datatype,
            "value": value,
        }

    def lookup(self, name: str):
        if name in self.symbols:
            value = self.symbols.get(name)
            if value is isinstance(value, Expr): 
                raise SemanticError(f"Variable '{name}' is not defined before use.")
        else:
            raise SemanticError(f"Variable '{name}' is not defined.")

        return value
    def __repr__(self):
        return f"SymbolTable({self.symbols})"

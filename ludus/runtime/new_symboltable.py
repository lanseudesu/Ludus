from ..nodes import *
from ..error import SemanticError

class SymbolTable:
    def __init__(self):
        self.scope_stack = [{}] 
        self.saved_scopes = [{}]
        self.symbols = {}  
    
    def enter_scope(self):
        new_scope = {}
        self.scope_stack.append(new_scope)
    
    def exit_scope(self):
        print("Exit Scope:")
        for scope in reversed(self.scope_stack):
            print(scope)
        if self.scope_stack:
            current_scope = self.scope_stack.pop()
            self.saved_scopes.insert(1, current_scope.copy())
        
    
    def restore_scope(self, scope_index=None):
        if len(self.saved_scopes) > 1:  
            if scope_index is not None:
                restored_scope = self.saved_scopes.pop(scope_index)
            else:
                restored_scope = self.saved_scopes.pop()  
            self.scope_stack.append(restored_scope)
        print("Restore Scope:")
        for scope in reversed(self.scope_stack):
            print(scope)
    
    
    def define(self, name: str, value):
        current_scope = self.scope_stack[-1]
        current_scope[name] = value

    def define_var(self, name: str, value, datatype, immo):
        for scope in reversed(self.scope_stack):
            if name in scope:
                current_scope = scope
                break
        
        current_scope[name] = {
            "type": datatype,
            "value": value,
            "immo": immo
        } 
        
    def define_arr(self, name: str, dimensions, values, immo, datatype):
        current_scope = self.scope_stack[-1]
        for scope in reversed(self.scope_stack):
            if name in scope:
                current_scope = scope
                break
            
        current_scope[name] = {
            "dimensions": dimensions,
            "elements": values,
            "immo": immo,
            "type": datatype
        }

    def define_structinst(self, name: str, parent: str, values, immo):
        current_scope = self.scope_stack[-1]
        current_scope[name] = {
            "parent": parent,
            "fields": values,
            "immo": immo
        }

    def lookup(self, name: str):
        for scope in reversed(self.scope_stack):
            if name in scope:
                value = scope[name]
                if isinstance(value, Expr): 
                    raise SemanticError(f"NameError: Identifier '{name}' is not defined before use.")
                return value  

        raise SemanticError(f"NameError: Identifier '{name}' is not defined.")
    
    def __repr__(self):
        return "SymbolTable:\n" + "\n".join(
            f"{name}: {info}"
            for scope in self.scope_stack
            for name, info in scope.items()
        ) 

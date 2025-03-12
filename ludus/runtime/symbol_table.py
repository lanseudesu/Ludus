from ..nodes import *
from ..error import SemanticError

class SymbolTable:
    def __init__(self):
        self.scope_stack = [{}] 
        self.saved_scopes = [{}]
        self.function_scopes = {}
        self.play_scope = []
        self.func_flag = False
    
    def enter_scope(self):
        new_scope = {}
        self.scope_stack.append(new_scope)
    
    def enter_scope_func(self):
        new_scope = {}
        self.scope_stack.append(new_scope)
        self.saved_scopes_func = [{}]
    
    def exit_scope(self):
        # print("Exit Scope:")
        # for scope in reversed(self.scope_stack):
        #     print(scope)

        if not self.scope_stack:
            return
        
        current_scope = self.scope_stack.pop()

        if self.func_flag:  
            self.saved_scopes_func.insert(1, current_scope.copy())
        else:  
            self.saved_scopes.insert(1, current_scope.copy())
            #print(f"exit scope -> {self.saved_scopes}")
        
    def exit_scope_func(self, func_name):
        self.function_scopes[func_name] = {
            "scope_stack": [scope.copy() for scope in self.scope_stack],
            "saved_scopes": [scope.copy() for scope in self.saved_scopes_func]
        }
        self.scope_stack.pop()

    
    def restore_scope(self, scope_index=None):
        if len(self.saved_scopes) > 1:
            if scope_index is not None and (0 <= scope_index < len(self.saved_scopes)):
                restored_scope = self.saved_scopes[scope_index]
            else:
                restored_scope = self.saved_scopes[1]  
            self.scope_stack.append(restored_scope)
        else:
            raise SemanticError("No saved scope available to restore.")
        # print("Restore Scope:")
        # for scope in reversed(self.scope_stack):
        #     print(scope)

    def restore_scope_func(self, func_name):
        if func_name not in self.function_scopes:
            raise SemanticError(f"Function '{func_name}' has no saved scope.")

        func_data = self.function_scopes[func_name]
        self.scope_stack = [scope.copy() for scope in func_data["scope_stack"]]
        self.saved_scopes = [scope.copy() for scope in func_data["saved_scopes"]]
    
    def define(self, name: str, value):
        current_scope = self.scope_stack[-1]
        current_scope[name] = value

    def define_var(self, name: str, value, datatype, immo):
        current_scope = self.scope_stack[-1]
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

    def define_func(self, name, params, body, recall_stmts):
        current_scope = self.scope_stack[-1]
        current_scope[name] = {
            "params": params,
            "body": body,
            "recall": recall_stmts
        }
    
    def lookup(self, name: str, scope_to_check=None):
        if scope_to_check:
            for scope in reversed(scope_to_check):
                if name in scope:
                    value = scope[name]
                    if isinstance(value, Expr): 
                        raise SemanticError(f"NameError: Identifier '{name}' is not defined before use.")
                    return value  

            raise SemanticError(f"NameError: Identifier '{name}' is not defined.")
        
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
            for scope in self.play_scope
            for name, info in scope.items()
        ) 

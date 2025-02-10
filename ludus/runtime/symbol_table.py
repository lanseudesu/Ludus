from typing import List

class SymbolTableError(Exception):
    def __init__(self, message):
        super().__init__(message)

class SymbolTable:
    def __init__(self):
        self.table = {}
        self.array_table = {}

    TYPE_MAP = {
        int: "hp",
        float: "xp",
        str: "comms",
        bool: "flag"
    }

    def define_variable(self, name: str, value):
        value_type = type(value)
        value_type_str = self.TYPE_MAP.get(value_type, str(value_type))

        if name in self.array_table:  
            raise SymbolTableError(
                f"DeclarationError: '{name}' is already declared as an array."
            )
        
        if name in self.table:
            expected_type = self.table[name]["type"]
            
            if expected_type != value_type_str:
                raise SymbolTableError(
                    f"TypeMismatchError: Type mismatch for variable '{name}'. Expected '{expected_type}', got '{value_type_str}'."
                )

        self.table[name] = {
            "type": value_type_str,
            "value": value
        }

    def define_dead_variable(self, name: str, datatype):
        if name in self.table:
            raise SymbolTableError(
                f"Variable '{name}' was already declared with a value and cannot be re-declared as 'dead'."
            )
        
        if name in self.array_table:  
            raise SymbolTableError(
                f"DeclarationError: '{name}' is already declared as an array."
            )

        self.table[name] = {
            "type": datatype,  
            "value": None
        }

    def define_def_variable(self, name: str, value):
        if name in self.table:
            raise SymbolTableError(
                f"Variable '{name}' was already been declared."
            )
        
        if name in self.array_table:  
            raise SymbolTableError(
                f"DeclarationError: '{name}' is already declared as an array."
            )
        
        value_type = type(value)
        value_type_str = self.TYPE_MAP.get(value_type, str(value_type))

        self.table[name] = {
            "type": value_type_str,
            "value": value
        }

    def define_array(self, name: str, dimensions: list, values: list):
        if name in self.table:
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a variable.")
        elif name in self.array_table:
            raise SymbolTableError(f"DeclarationError: Array '{name}' is already defined.")
        
        if len(dimensions) > 1:
            value_type = type(values[0][0])
        else:
            value_type = type(values[0])

        value_type_str = self.TYPE_MAP.get(value_type, str(value_type))

        self.array_table[name] = {
            "type": value_type_str,
            "dimensions": dimensions,
            "values": values
        }
        
    def define_dead_array(self, name: str, dimensions: list, values: list, datatype):
        if name in self.table:
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a variable.")
        elif name in self.array_table:
            raise SymbolTableError(f"DeclarationError: Array '{name}' is already defined.")
        

        self.array_table[name] = {
            "type": datatype,
            "dimensions": dimensions,
            "values": values
        }

    def get_variable(self, name: str):
        if name not in self.table:
            raise SymbolTableError(f"NameError: Variable '{name}' is not defined.")
        return self.table[name]["value"]

    def get_variable_info(self, name: str):
        if name not in self.table:
            raise SymbolTableError(f"NameError: Variable '{name}' is not defined.")
        return self.table[name]
    
    def __repr__(self):
        if self.table and self.array_table:
            return f"{str(self.table)},{str(self.array_table)}"
        elif self.table and not self.array_table:
            return str(self.table)
        else:
            return str(self.array_table)

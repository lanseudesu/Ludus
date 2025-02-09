class SymbolTableError(Exception):
    def __init__(self, message):
        super().__init__(message)

class SymbolTable:
    def __init__(self):
        self.table = {}  

    TYPE_MAP = {
        int: "hp",
        float: "xp",
        str: "comms",
        bool: "flag"
    }

    def define_variable(self, name: str, value):
        value_type = type(value)
        value_type_str = self.TYPE_MAP.get(value_type, str(value_type))

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

        if datatype not in self.TYPE_MAP.values():
            raise SymbolTableError(
                f"InvalidTypeError: Unknown datatype '{datatype}' for dead variable '{name}'."
            )

        self.table[name] = {
            "type": datatype,  # Store the expected type, even though value is None
            "value": None
        }

    def define_def_variable(self, name: str, value):
        if name in self.table:
            raise SymbolTableError(
                f"Variable '{name}' was already been declared."
            )
        
        value_type = type(value)
        value_type_str = self.TYPE_MAP.get(value_type, str(value_type))

        self.table[name] = {
            "type": value_type_str,
            "value": value
        }

    def get_variable(self, name: str):
        if name not in self.table:
            raise SymbolTableError(f"NameError: Variable '{name}' is not defined.")
        return self.table[name]["value"]

    def get_variable_info(self, name: str):
        """Return both type and value of a variable."""
        if name not in self.table:
            raise SymbolTableError(f"NameError: Variable '{name}' is not defined.")
        return self.table[name]

    def __repr__(self):
        return str(self.table)

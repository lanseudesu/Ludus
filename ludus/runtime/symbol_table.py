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
        if name in self.table:
            expected_type = type(self.table[name])
            received_type = type(value)

            expected_type_str = self.TYPE_MAP.get(expected_type, str(expected_type))
            received_type_str = self.TYPE_MAP.get(received_type, str(received_type))

            if expected_type != received_type:
                raise SymbolTableError(
                    f"TypeMismatchError: Type mismatch for variable '{name}'. Expected '{expected_type_str}', got '{received_type_str}'."
                )

        self.table[name] = value  

    def get_variable(self, name: str):
        if name not in self.table:
            raise SymbolTableError(f"NameError: Variable '{name}' is not defined.")
        return self.table[name]

    def __repr__(self):
        return str(self.table)

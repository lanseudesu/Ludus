from typing import List

class SymbolTableError(Exception):
    def __init__(self, message):
        super().__init__(message)

class SymbolTable:
    def __init__(self):
        self.struct_table = {"global": {}}
        self.table = {"global": {}} 
        self.array_table = {"global": {}}
        self.structinst_table = {}

    TYPE_MAP = {
        int: "hp",
        float: "xp",
        str: "comms",
        bool: "flag"
    }

    ############ VARIABLES ###################

    def define_variable(self, name: str, value, scope):
        value_type = type(value)
        value_type_str = self.TYPE_MAP.get(value_type, str(value_type))

        if name in self.array_table.get(scope, {}):  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as an array.")
        elif name in self.array_table.get("global", {}):
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as an array.")

        
        if name in self.table.get("global", {}):
            scope = "global"
        
        if name in self.table.get(scope, {}):
            if self.table.get(scope, {}).get(name, {}).get("immo", False):
                raise SymbolTableError(f"DeclarationError: '{name}' is declared as an immutable variable.")
            
            expected_type = self.table[scope][name]["type"]
            if expected_type and expected_type != value_type_str:
                raise SymbolTableError(
                    f"TypeMismatchError: Type mismatch for variable '{name}'. Expected '{expected_type}', got '{value_type_str}'."
                )

        if scope not in self.table:
            self.table[scope] = {}

        self.table[scope][name] = {
            "type": value_type_str,
            "value": value,
            "immo": False  
        }

    def define_dead_variable(self, name: str, datatype, scope):
        if name in self.table.get("global", {}) or name in self.table.get(scope, {}):
            raise SymbolTableError(
                f"Variable '{name}' was already declared and cannot be re-declared as 'dead'."
            )
        
        if name in self.array_table.get(scope, {}):  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as an array.")
        elif name in self.array_table.get("global", {}):
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as an array.")

        if scope not in self.table:
            self.table[scope] = {}
        
        self.table[scope][name] = {
            "type": datatype,  
            "value": None,
            "immo" : False
        }

    def define_def_variable(self, name: str, value, scope):
        if name in self.table.get("global", {}):
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a global variable.")
        if name in self.table.get(scope, {}):
            raise SymbolTableError(f"DeclarationError: Variable '{name}' was already been declared.")
        
        if name in self.array_table.get(scope, {}):  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as an array.")
        elif name in self.array_table.get("global", {}):
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a global array.")
        
        value_type = type(value)
        value_type_str = self.TYPE_MAP.get(value_type, str(value_type))

        if scope not in self.table:
            self.table[scope] = {}

        self.table[scope][name] = {
            "type": value_type_str,
            "value": value,
            "immo": False  
        }

    def define_immo_variable(self, name: str, value, scope):
        if name in self.array_table.get(scope, {}) or name in self.array_table.get("global", {}):  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as an array.")
        elif name in self.struct_table.get(scope, {}) or name in self.struct_table.get("global", {}):  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a struct.")
        elif name in self.structinst_table.get(scope, {}):  
            raise SymbolTableError(f"DeclarationError: {name}' is already declared as a struct instance.")
        
        value_type = type(value)
        value_type_str = self.TYPE_MAP.get(value_type, str(value_type))
        
        if scope not in self.table:
            self.table[scope] = {}

        self.table[scope][name] = {
            "type" : value_type_str,
            "value": value,
            "immo" : True
        }
    
    def get_variable(self, name: str, scope: str):
        if scope in self.table and name in self.table[scope]:  
            return self.table[scope][name]["value"]  
        elif "global" in self.table and name in self.table["global"]:
            return self.table["global"][name]["value"]  
        else:
            raise SymbolTableError(f"NameError: Variable '{name}' is not defined in scope '{scope}' or globally.")

    
    def check_var(self, name: str, scope):
        if name in self.table.get("global", {}) or name in self.table.get(scope, {}):
            return True
        else:
            return False

    ############ ARRAYS ###################
    
    def define_array(self, name: str, dimensions: list, values: list, scope, is_Dead=False):
        if name in self.table.get(scope, {}) or name in self.table.get("global", {}):
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a variable.")
        elif name in self.array_table.get(scope, {}):
            if not is_Dead:
                raise SymbolTableError(f"DeclarationError: Array '{name}' is already defined.")
        elif name in self.array_table.get("global", {}):
            if not is_Dead:
                raise SymbolTableError(f"DeclarationError: Array '{name}' is already defined.")
            scope = 'global'

        if len(dimensions) > 1:
            value_type = type(values[0][0])
            for row in values:
                for columns in row:
                    if type(columns) != value_type:
                        raise SymbolTableError(f"TypeMismatchError: Array '{name}' contains mixed data types.")
        else:
            value_type = type(values[0])
            for element in values:
                if type(element) != value_type:
                    raise SymbolTableError(f"TypeMismatchError: Array '{name}' contains mixed data types.")

        if scope not in self.array_table:
            self.array_table[scope] = {}
        
        if is_Dead:
            expected_type = self.array_table[scope][name]["type"]
            if value_type != expected_type:
                raise SymbolTableError(f"TypeMismatchError: Array '{name}' expects '{expected_type}' data type.")

        value_type_str = self.TYPE_MAP.get(value_type, str(value_type))
        
        self.array_table[scope][name] = {
            "type": value_type_str,
            "dimensions": dimensions,
            "values": values,
            "immo" : False
        }
        
    def define_dead_array(self, name: str, dimensions: list, values: list, datatype, scope):
        if name in self.table.get(scope, {}) or name in self.table.get("global", {}):
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a variable.")
        elif name in self.array_table.get(scope, {}) or name in self.array_table.get("global", {}):
            raise SymbolTableError(f"DeclarationError: Array '{name}' is already defined.")

        if scope not in self.array_table:
            self.array_table[scope] = {}
        
        self.array_table[scope][name] = {
            "type": datatype,
            "dimensions": dimensions,
            "values": values,
            "immo" : False
        }

    def check_dead_array(self, name: str, scope):
        if self.array_table[scope][name]["values"] == None:
            return True
        else:
            return False
        
    def check_array(self, name: str, scope):
        if name in self.table.get("global", {}):
            if self.array_table["global"][name]["immo"] == True:
                raise SymbolTableError(f"ImmoArrayError: Array '{name}' is declared as an immutable array.")
            return True, "global"
        elif name in self.array_table.get(scope, {}): 
            if self.array_table[scope][name]["immo"] == True:
                raise SymbolTableError(f"ImmoArrayError: Array '{name}' is declared as an immutable array.")
            return True, scope
        else:
            return False, scope
        
    def get_array_dimensions(self, name: str, scope):
        return self.array_table[scope][name]["dimensions"]
    
    def modify_array(self, name: str, indices: list, value, scope):
        value_type = type(value)
        value_type_str = self.TYPE_MAP.get(value_type, str(value_type))
        
        expected_type = self.array_table[scope][name]["type"]
        
        if value_type_str != expected_type:
            raise SymbolTableError(f"TypeMismatchError: Array {name} expects '{expected_type}' data type, not '{value_type_str}'")
        
        array_data = self.array_table[scope][name]
        dimensions = array_data["dimensions"]
        values = array_data["values"]

        target = values
        for i, index in enumerate(indices):
            if i == len(indices) - 1:
                target[index] = value
            else:
                target = target[index]
    
    def define_immo_array(self, name: str, dimensions: list, values: list, scope):
        if name in self.table.get("global", {}) or name in self.table.get(scope, {}):
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a variable.")
        elif name in self.struct_table.get("global", {}) or name in self.struct_table.get(scope, {}):
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a struct.")
        elif name in self.structinst_table.get(scope, {}):
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a struct instance.")
        
        if len(dimensions) > 1:
            value_type = type(values[0][0])
        else:
            value_type = type(values[0])
        
        datatype = self.TYPE_MAP.get(value_type, str(value_type))
        
        if scope not in self.array_table:
            self.array_table[scope] = {}
        
        self.array_table[scope][name] = {
            "type": datatype,
            "dimensions": dimensions,
            "values": values,
            "immo" : True
        }
   
    ####### STRUCT ################
    
    def define_struct(self, name: str, fields_table, scope):
        if name in self.array_table.get("global", {}) or name in self.array_table.get(scope, {}):  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as an array.")
        elif name in self.table.get("global", {}) or name in self.table.get(scope, {}):  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a variable.")
        elif name in self.struct_table.get("global", {}) or name in self.struct_table.get(scope, {}):  
            raise SymbolTableError(f"DeclarationError: Struct '{name}' already exists.")
        
        for field, details in fields_table.items():
            expected_type = details["datatype"]
            value = details["value"]
            if value is None:
                continue
            actual_type_name = self.TYPE_MAP.get(type(value), None)  
            if actual_type_name != expected_type:
                raise SymbolTableError(f"FieldTypeError: Type mismatch for field '{field}': Expected '{expected_type}', but got '{actual_type_name}'.")
        
        if scope not in self.struct_table:
            self.struct_table[scope] = {}
        
        self.struct_table[scope][name] = {
            "fields": fields_table
        }

    def check_struct(self, name: str, scope):
        if name in self.array_table.get(scope, {}) or name in self.array_table.get("global", {}):  
            raise SymbolTableError(f"DeclarationError: Struct '{name}' does not exist.")
        elif name in self.table.get(scope, {}) or name in self.table.get("global", {}):  
            raise SymbolTableError(f"DeclarationError: Struct '{name}' does not exist.")
        elif name in self.struct_table.get(scope, {}):  
            return True, scope
        elif name in self.struct_table.get("global", {}):
            return True, "global"
        else:
            raise SymbolTableError(f"DeclarationError: Struct '{name}' does not exist.")
    
    def get_fieldtable(self, name: str, scope):
        return self.struct_table[scope][name]["fields"]
    
    def define_structinst(self, name: str, fields_table, scope):
        if name in self.array_table.get(scope, {}) or name in self.array_table.get("global", {}):  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as an array.")
        elif name in self.table.get(scope, {}) or name in self.table.get("global", {}):  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a variable.")
        elif name in self.struct_table.get(scope, {}) or name in self.struct_table.get("global", {}):  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a struct.")
        elif name in self.structinst_table.get(scope, {}):  
            raise SymbolTableError(f"DeclarationError: Struct Instance '{name}' already exists.")
        
        for field, details in fields_table.items():
            expected_type = details["datatype"]
            value = details["value"]
            if value is None:
                continue
            actual_type_name = self.TYPE_MAP.get(type(value), None)  
            if actual_type_name != expected_type:
                raise SymbolTableError(f"FieldTypeError: Type mismatch for field '{field}': Expected '{expected_type}', but got '{actual_type_name}'.")
        
        if scope not in self.structinst_table:
            self.structinst_table[scope] = {}
        
        self.structinst_table[scope][name] = {
            "fields": fields_table,
            "immo" : False
        }

    def check_structinst(self, name: str, scope):
        if name in self.array_table.get("global", {}) or name in self.array_table.get(scope, {}):  
            raise SymbolTableError(f"DeclarationError: Struct Instance '{name}' does not exist.")
        elif name in self.table.get("global", {}) or name in self.table.get(scope, {}):  
            raise SymbolTableError(f"DeclarationError: Struct Instance '{name}' does not exist.")
        elif name in self.struct_table.get("global", {}) or name in self.struct_table.get(scope, {}):  
            raise SymbolTableError(f"DeclarationError: Struct Instance '{name}' does not exist.")
        elif name not in self.structinst_table.get(scope, {}):  
            raise SymbolTableError(f"DeclarationError: Struct Instance '{name}' does not exist.")
        else:
            return
    
    def check_structinst_field(self, name: str, field: str, scope):
        if field not in self.structinst_table[scope][name]["fields"]:
            raise SymbolTableError(f"DeclarationError: Field '{field}' does not exist in Struct Instance '{name}'.")
        
    def modify_structinst_field(self, name: str, field: str, value, scope):
        if self.structinst_table[scope][name]["immo"] == True:
            raise SymbolTableError(f"ImmoStructInstanceError: Struct Instance '{name}' is declared as an immutable struct instance.")
        
        expected_type = self.structinst_table[scope][name]["fields"][field]["datatype"]
        actual_type_name = self.TYPE_MAP.get(type(value), None)  
        if actual_type_name != expected_type:
            raise SymbolTableError(f"FieldTypeError: Type mismatch for field '{field}': Expected '{expected_type}', but got '{actual_type_name}'.")
        
        self.structinst_table[scope][name]["fields"][field]["value"] = value

    def define_immo_structinst(self, name: str, fields_table, scope):
        if name in self.array_table.get(scope, {}) or name in self.array_table.get("global", {}):  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as an array.")
        elif name in self.table.get(scope, {}) or name in self.table.get("global", {}):  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a variable.")
        elif name in self.struct_table.get(scope, {}) or name in self.struct_table.get("global", {}):  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a struct.")
        elif name in self.structinst_table.get(scope, {}):  
            raise SymbolTableError(f"DeclarationError: Struct Instance '{name}' already exists.")
        
        if scope not in self.structinst_table:
            self.structinst_table[scope] = {}

        self.structinst_table[scope][name] = {
            "fields": fields_table,
            "immo" : True
        }
    
    def __repr__(self):
        tables = {
            "Variables": self.table if self.table else None,
            "Arrays": self.array_table if self.array_table else None,
            "Structs": self.struct_table if self.struct_table else None,
            "Struct Instances": self.structinst_table if self.structinst_table else None
        }
        tables = '\n'.join([f"{key}: {value}" for key, value in tables.items() if value is not None])
        return str(tables)

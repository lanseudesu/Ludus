from typing import List

class SymbolTableError(Exception):
    def __init__(self, message):
        super().__init__(message)

class SymbolTable:
    def __init__(self):
        self.struct_table = {}
        self.table = {}
        self.array_table = {}
        self.structinst_table = {}

    TYPE_MAP = {
        int: "hp",
        float: "xp",
        str: "comms",
        bool: "flag"
    }

    ############ VARIABLES ###################

    def define_variable(self, name: str, value):
        value_type = type(value)
        value_type_str = self.TYPE_MAP.get(value_type, str(value_type))

        if name in self.array_table:  
            raise SymbolTableError(
                f"DeclarationError: '{name}' is already declared as an array."
            )
        
        if name in self.table:
            if self.table[name]["immo"] == True:
                raise SymbolTableError(f"DeclarationError: '{name}' is declared as an immutable variable.")
            
            expected_type = self.table[name]["type"]
            
            if expected_type != value_type_str:
                raise SymbolTableError(
                    f"TypeMismatchError: Type mismatch for variable '{name}'. Expected '{expected_type}', got '{value_type_str}'."
                )

        self.table[name] = {
            "type": value_type_str,
            "value": value,
            "immo" : False
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
            "value": None,
            "immo" : False
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
            "type" : value_type_str,
            "value": value,
            "immo" : False
        }

    def define_immo_variable(self, name: str, value):
        if name in self.array_table:  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as an array.")
        elif name in self.struct_table:  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a struct.")
        elif name in self.structinst_table:  
            raise SymbolTableError(f"DeclarationError: {name}' is already declared as a struct instance.")
        
        value_type = type(value)
        value_type_str = self.TYPE_MAP.get(value_type, str(value_type))
        
        self.table[name] = {
            "type" : value_type_str,
            "value": value,
            "immo" : True
        }
    
    def get_variable(self, name: str):
        if name not in self.table:
            raise SymbolTableError(f"NameError: Variable '{name}' is not defined.")
        return self.table[name]["value"]

    def get_variable_info(self, name: str):
        if name not in self.table:
            raise SymbolTableError(f"NameError: Variable '{name}' is not defined.")
        return self.table[name]
    
    def check_var(self, name: str):
        if name in self.table:
            return True
        else:
            return False

    ############ ARRAYS ###################
    
    def define_array(self, name: str, dimensions: list, values: list, is_Dead=False):
        if name in self.table:
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a variable.")
        elif name in self.array_table:
            if not is_Dead:
                raise SymbolTableError(f"DeclarationError: Array '{name}' is already defined.")
        
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

        if is_Dead:
            expected_type = self.array_table[name]["type"]
            if value_type != expected_type:
                raise SymbolTableError(f"TypeMismatchError: Array '{name}' expects '{expected_type}' data type.")

        value_type_str = self.TYPE_MAP.get(value_type, str(value_type))

       
        
        self.array_table[name] = {
            "type": value_type_str,
            "dimensions": dimensions,
            "values": values,
            "immo" : False
        }
        
    def define_dead_array(self, name: str, dimensions: list, values: list, datatype):
        if name in self.table:
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a variable.")
        elif name in self.array_table:
            raise SymbolTableError(f"DeclarationError: Array '{name}' is already defined.")
        

        self.array_table[name] = {
            "type": datatype,
            "dimensions": dimensions,
            "values": values,
            "immo" : False
        }

    def check_dead_array(self, name: str):
        if self.array_table[name]["values"] == None:
            return True
        else:
            return False
        
    def check_array(self, name: str):
        if name in self.array_table:
            if self.array_table[name]["immo"] == True:
                raise SymbolTableError(f"ImmoArrayError: Array '{name}' is declared as an immutable array.")
            return True
        else:
            return False
        
    def get_array_dimensions(self, name: str):
        return self.array_table[name]["dimensions"]
    
    def modify_array(self, name: str, indices: list, value):
        value_type = type(value)
        value_type_str = self.TYPE_MAP.get(value_type, str(value_type))
        
        expected_type = self.array_table[name]["type"]
        
        if value_type_str != expected_type:
            raise SymbolTableError(f"TypeMismatchError: Array {name} expects '{expected_type}' data type, not '{value_type_str}'")
        
        array_data = self.array_table[name]
        dimensions = array_data["dimensions"]
        values = array_data["values"]

        target = values
        for i, index in enumerate(indices):
            if i == len(indices) - 1:
                target[index] = value
            else:
                target = target[index]
    
    def define_immo_array(self, name: str, dimensions: list, values: list):
        if name in self.table:
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a variable.")
        elif name in self.struct_table:
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a struct.")
        elif name in self.structinst_table:
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a struct instance.")
        
        if len(dimensions) > 1:
            value_type = type(values[0][0])
        else:
            value_type = type(values[0])
        
        datatype = self.TYPE_MAP.get(value_type, str(value_type))
        
        self.array_table[name] = {
            "type": datatype,
            "dimensions": dimensions,
            "values": values,
            "immo" : True
        }
   
    ####### STRUCT ################
    
    def define_struct(self, name: str, fields_table):
        if name in self.array_table:  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as an array.")
        elif name in self.table:  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a variable.")
        elif name in self.struct_table:  
            raise SymbolTableError(f"DeclarationError: Struct '{name}' already exists.")
        
        for field, details in fields_table.items():
            expected_type = details["datatype"]
            value = details["value"]
            if value is None:
                continue
            actual_type_name = self.TYPE_MAP.get(type(value), None)  
            if actual_type_name != expected_type:
                raise SymbolTableError(f"FieldTypeError: Type mismatch for field '{field}': Expected '{expected_type}', but got '{actual_type_name}'.")
        
        self.struct_table[name] = {
            "fields": fields_table
        }

    def check_struct(self, name: str):
        if name in self.array_table:  
            raise SymbolTableError(f"DeclarationError: Struct '{name}' does not exist.")
        elif name in self.table:  
            raise SymbolTableError(f"DeclarationError: Struct '{name}' does not exist.")
        elif name not in self.struct_table:  
            raise SymbolTableError(f"DeclarationError: Struct '{name}' does not exist.")
        
        return True
    
    def get_fieldtable(self, name: str):
        return self.struct_table[name]["fields"]
    
    def define_structinst(self, name: str, fields_table):
        if name in self.array_table:  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as an array.")
        elif name in self.table:  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a variable.")
        elif name in self.struct_table:  
            raise SymbolTableError(f"DeclarationError: '{name}' is already declared as a struct.")
        elif name in self.structinst_table:  
            raise SymbolTableError(f"DeclarationError: Struct Instance '{name}' already exists.")
        
        for field, details in fields_table.items():
            expected_type = details["datatype"]
            value = details["value"]
            if value is None:
                continue
            actual_type_name = self.TYPE_MAP.get(type(value), None)  
            if actual_type_name != expected_type:
                raise SymbolTableError(f"FieldTypeError: Type mismatch for field '{field}': Expected '{expected_type}', but got '{actual_type_name}'.")
        
        self.structinst_table[name] = {
            "fields": fields_table
        }

    def check_structinst(self, name: str):
        if name in self.array_table:  
            raise SymbolTableError(f"DeclarationError: Struct Instance '{name}' does not exist.")
        elif name in self.table:  
            raise SymbolTableError(f"DeclarationError: Struct Instance '{name}' does not exist.")
        elif name in self.struct_table:  
            raise SymbolTableError(f"DeclarationError: Struct Instance '{name}' does not exist.")
        elif name not in self.structinst_table:  
            raise SymbolTableError(f"DeclarationError: Struct Instance '{name}' does not exist.")
        
        return True
    
    def check_structinst_field(self, name: str, field: str):
        if field not in self.structinst_table[name]["fields"]:
            raise SymbolTableError(f"DeclarationError: Field '{field}' does not exist in Struct Instance '{name}'.")
        
    def modify_structinst_field(self, name: str, field: str, value):
        expected_type = self.structinst_table[name]["fields"][field]["datatype"]
        actual_type_name = self.TYPE_MAP.get(type(value), None)  
        if actual_type_name != expected_type:
            raise SymbolTableError(f"FieldTypeError: Type mismatch for field '{field}': Expected '{expected_type}', but got '{actual_type_name}'.")
        
        self.structinst_table[name]["fields"][field]["value"] = value
    
    def __repr__(self):
        tables = {
            "Variables": self.table if self.table else None,
            "Arrays": self.array_table if self.array_table else None,
            "Structs": self.struct_table if self.struct_table else None,
            "Struct Instances": self.structinst_table if self.structinst_table else None
        }
        tables = {key: value for key, value in tables.items() if value is not None}
        return str(tables)

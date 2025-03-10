from ludus.nodes import GrindWhileStmt
from ..nodes import *
from .symbol_table import SymbolTable
from .interpreter import evaluate, UnresolvedNumber
from ..error import SemanticError



class ASTVisitor:
    TYPE_MAP = {
        int: "hp",
        float: "xp",
        str: "comms",
        bool: "flag"
    }

    def __init__(self):
        self.symbol_table = SymbolTable()

    def visit(self, node: Stmt):
        method_name = f"visit_{node.kind}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    def generic_visit(self, node: Stmt):
        if hasattr(node, '__dict__'):
            for value in node.__dict__.values():
                if isinstance(value, Stmt):
                    self.visit(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, Stmt):
                            self.visit(item)

    def visit_Program(self, node: Program):
        for stmt in node.body:
            self.visit(stmt)

    def visit_VarDec(self, node: VarDec):
        self.symbol_table.define(node.name.symbol, node.value)

    def visit_ArrayDec(self, node: ArrayDec):
        declared_types = set()
        values = []
        is_empty = False
        
        if node.elements is None:
            self.symbol_table.define_arr(node.name.symbol, node.dimensions, None, node.immo, node.datatype)
        else:
            if len(node.dimensions) == 1:
                is_empty = node.elements == []
                for val in node.elements:
                    value = evaluate(val, self.symbol_table)
                    val_type = self.TYPE_MAP.get(type(value), str(type(value)))
                    declared_types.add(val_type)
                    values.append(value)
            else:
                is_empty = node.elements == [[], []]
                for row in node.elements:
                    inner_values = []
                    for val in row:
                        value = evaluate(val, self.symbol_table)
                        val_type = self.TYPE_MAP.get(type(value), str(type(value)))
                        declared_types.add(val_type)
                        inner_values.append(value)
                    values.append(inner_values)
            
            if len(declared_types) > 1:
                raise SemanticError(f"All elements in an array declaration must have the same type. Found types: {declared_types}")
            if is_empty:
                datatype = node.datatype
            else:
                datatype = declared_types.pop() if declared_types else None
            self.symbol_table.define_arr(node.name.symbol, node.dimensions, values, node.immo, datatype)
    
    def visit_StructDec(self, node: StructDec):
        default_values = {
            'hp': 0,
            'xp': 0.0,
            'comms': '',
            'flag': False
        }
        fields = {}
        for field in node.body:
            value = field.value if field.value is not None else default_values.get(field.datatype)
            if value is None:
                raise SemanticError(f"Unknown data type '{field.datatype}'.")
            if field.value is not None:
                value = evaluate(value, self.symbol_table)
                val_type = self.TYPE_MAP.get(type(value), str(type(value)))
                if field.datatype != val_type:
                    raise SemanticError(f"FieldTypeError: Type mismatch for field '{field.name.symbol}'."
                                        f" Expected '{field.datatype}', but got '{val_type}'.")
            fields[field.name.symbol] = {
                "value": value,
                "datatype": field.datatype
            }
        self.symbol_table.define(node.name.symbol, fields)
    
    def visit_GlobalStructDec(self, node: GlobalStructDec):
        fields = {}
        self.symbol_table.define(node.name.symbol, fields)

    def visit_StructInst(self, node: StructInst):
        fields = []
        for field in node.body:
            value = field.value
            fields.append(value)
            
        self.symbol_table.define_structinst(node.name.symbol, node.parent, fields, node.immo)
    
    def visit_BlockStmt(self, node: BlockStmt):
        self.symbol_table.enter_scope()
        for stmt in node.statements:
            self.visit(stmt)
        self.symbol_table.exit_scope()

    def visit_IfStmt(self, node: IfStmt):
        self.symbol_table.enter_scope()
        for stmt in node.then_branch:
            self.visit(stmt)
        self.symbol_table.exit_scope()
        
        if node.elif_branches:
            for branch in node.elif_branches:
                self.symbol_table.enter_scope()
                for stmt in branch.body:
                    self.visit(stmt)
                self.symbol_table.exit_scope()

        if node.else_branch:
            self.symbol_table.enter_scope()
            for stmt in node.else_branch:
                self.visit(stmt)
            self.symbol_table.exit_scope()

    def visit_FlankStmt(self, node: FlankStmt):
        for choice in node.choices:
            self.symbol_table.enter_scope()
            for stmt in choice.body:
                self.visit(stmt)
            self.symbol_table.exit_scope()

        self.symbol_table.enter_scope()
        for stmt in node.backup_body:
            self.visit(stmt)
        self.symbol_table.exit_scope()

    def visit_ForStmt(self, node: ForStmt):
        self.symbol_table.enter_scope()
        for stmt in node.body:
            self.visit(stmt)
        self.symbol_table.exit_scope()

    def visit_GrindWhileStmt(self, node: GrindWhileStmt):
        self.symbol_table.enter_scope()
        for stmt in node.body:
            self.visit(stmt)
        self.symbol_table.exit_scope()

    def visit_GlobalFuncBody(self, node: GlobalFuncBody):
        body=[]
        self.symbol_table.enter_scope_func()
        self.symbol_table.func_flag = True
        for stmt in node.body:
            self.visit(stmt)
            body.append(stmt)
        self.symbol_table.func_flag = False
        self.symbol_table.define_func(node.name.symbol, node.params, body, node.recall_stmts)
        self.symbol_table.exit_scope_func(node.name.symbol)
        self.symbol_table.define_func(node.name.symbol, node.params, body, node.recall_stmts)

########################################
####### 2ND RUN OF TRAVERSER ###########
########################################

class SemanticAnalyzer(ASTVisitor):
    TYPE_MAP = {
        int: "hp",
        float: "xp",
        str: "comms",
        bool: "flag",
        dict: "array"
    }

    def __init__(self, symbol_table):
        super().__init__()
        self.symbol_table = symbol_table 
        self.i = 1 
        self.checkpoint_flag = False
        self.resume_flag = False
        self.in_func_flag = False
        self.recall_flag = False

    def visit_VarDec(self, node: VarDec):
        if node.value.kind == 'FuncCallStmt':
            rhs_name = node.value.name.symbol
            return_values = evaluate(node.value, self.symbol_table)
            if len(return_values) > 1:
                raise SemanticError(f"RecallError: Function '{rhs_name}' recalls more than one value.")
            value = return_values[0]
            if isinstance(value, list):
                value = value[0]
            if value == []:
                raise SemanticError(f"DeclarationError: Trying to declare an array to a variable: '{node.name.symbol}'.")
        else:    
            value = evaluate(node.value, self.symbol_table)
            
        if isinstance(value, UnresolvedNumber):
            val_type = "hp or xp" 
        elif isinstance(value, dict):
            if "dimensions" in value:
                raise SemanticError(f"DeclarationError: Trying to declare an array to a variable: '{node.name.symbol}'.")
            if "parent" in value:
                raise SemanticError(f"DeclarationError: Trying to declare a struct instance to a variable: '{node.name.symbol}'.")
        elif isinstance(node.value, DeadLiteral):
            val_type = node.value.datatype
        elif isinstance(node.value, Identifier) and value == None:
            id_val = self.symbol_table.lookup(node.value.symbol)
            val_type = id_val["type"]
        else:
            val_type = self.TYPE_MAP.get(type(value), str(type(value)))
        # print(value)
        self.symbol_table.define_var(node.name.symbol, value, val_type, node.immo)

    def visit_VarAssignmentStmt(self, node: VarAssignment):
        if node.right.kind == 'FuncCallStmt':
            rhs_name = node.right.name.symbol
            return_values = evaluate(node.right, self.symbol_table)
            if len(return_values) > 1:
                raise SemanticError(f"RecallError: Function '{rhs_name}' recalls more than one value.")
            new_val = return_values[0]
            if new_val == []:
                raise SemanticError(f"DeclarationError: Trying to assign an array to a variable: '{node.left.symbol}'.")
        elif node.right.kind in {'LoadNum', 'Load'} and node.operator != ':':
            raise SemanticError(f"LoadError: loadNum and load function cannot be used in compound assignment statements.")
        else:
            new_val = evaluate(node.right, self.symbol_table)
 
        if isinstance(new_val, dict):
            if "dimensions" in new_val:
                raise SemanticError(f"DeclarationError: Trying to assign an array to a variable: '{node.left.symbol}'.")
            if "parent" in new_val:
                raise SemanticError(f"DeclarationError: Trying to assign a struct instance to a variable: '{node.left.symbol}'.")

        value = self.symbol_table.lookup(node.left.symbol)
        
        if not isinstance(value, dict):
            datatype = self.TYPE_MAP.get(type(value), str(type(value)))
            self.symbol_table.define_var(node.left.symbol, value, datatype, False)
            value = self.symbol_table.lookup(node.left.symbol)

        if "value" not in value:
            raise SemanticError(f"AssignmentError: Mismatched types — trying to assign a single value to a list object: '{node.left.symbol}'.")
        
        value_type = value["type"]
        if value["immo"]==True:
            raise SemanticError(f"AssignmentError: '{node.left.symbol}' is declared as an immutable variable.")   
        
        if isinstance(new_val, UnresolvedNumber) and not isinstance(value["value"], UnresolvedNumber):
            if value_type == "hp":
                new_val = value["value"]
            elif value_type == "xp":
                new_val = value["value"]
            else:
                raise SemanticError("TypeError: Using loadNum function to assign a non-numeric variable.")
        elif isinstance(new_val, UnresolvedNumber) and isinstance(value["value"], UnresolvedNumber):
            return
        
        if node.operator in ['+=', '-=', '*=', '/=', '%=']:
            if isinstance(value["value"], UnresolvedNumber):
                if isinstance(new_val, int):
                    value["value"] = 0
                    value["type"] = "hp"
                    value_type = value["type"]
                elif isinstance(new_val, float):
                    value["value"] = 0.0
                    value["type"] = "xp"
                    value_type = value["type"]
                elif isinstance(new_val, bool):
                    value["type"] = "hp"
                    value["value"] = 0
                    value_type = value["type"]
                else:
                    raise SemanticError("TypeError: Cannot mix comms and numeric type in an expression.")
            
            if (isinstance(new_val, str) and isinstance(value["value"], bool)) or (isinstance(new_val, bool) and isinstance(value["value"], str)):
                raise SemanticError("TypeError: Cannot mix comms and flags in an expression.")

            if isinstance(new_val, str) != isinstance(value["value"], str):
                raise SemanticError("TypeError: Cannot mix comms and numeric types in an expression.")

            if isinstance(new_val, str) and node.operator != '+=':
                raise SemanticError("TypeError: Only valid assignment operator between comms is '+='.")
            
            operations = {
                '+=': lambda x, y: x + y,
                '-=': lambda x, y: x - y,
                '*=': lambda x, y: x * y,
                '/=': lambda x, y: x / y,
                '%=': lambda x, y: x % y
            }

            if node.operator == '/=': 
                if isinstance(value["value"], int) and isinstance(new_val, int):
                    if new_val == 0:
                        raise SemanticError("ZeroDivisionError: Division by zero is not allowed")
                    new_val = int(operations[node.operator](value["value"], new_val)) 
                else:
                    if new_val == 0 or new_val == 0.0:
                        raise SemanticError("ZeroDivisionError: Division by zero is not allowed")
                    new_val = operations[node.operator](value["value"], new_val)
            elif node.operator == '%=':
                if isinstance(value["value"], int) and isinstance(new_val, int):
                    if new_val == 0:
                        raise SemanticError("ZeroDivisionError: Modulo by zero is not allowed.")
                    new_val = operations[node.operator](value["value"], new_val)
                else:
                    raise SemanticError("ModuloError: Only hp values can be used in modulo operation.")
            else:
                new_val = operations[node.operator](value["value"], new_val)  
        else:
            new_val_type = self.TYPE_MAP.get(type(new_val), str(type(new_val)))
            if value_type == "hp or xp":
                if new_val_type in ["hp", "xp"]:
                    value_type = new_val_type
                else:
                    raise SemanticError(f"TypeError: Invalid type for variable '{node.left.symbol}'. Expected numeric but got '{new_val_type}'.")

        new_val_type = self.TYPE_MAP.get(type(new_val), str(type(new_val)))
        
        if new_val_type != value_type:
            raise SemanticError(f"TypeError: Type mismatch for variable '{node.left.symbol}'. Expected '{value_type}', got '{new_val_type}'.")
        
        self.symbol_table.define_var(node.left.symbol, new_val, new_val_type, value["immo"])

    def visit_BatchVarDec(self, node: BatchVarDec):
        declared_types = set()

        for var_dec in node.declarations:
            kind = var_dec.right.kind if var_dec.kind == 'VarAssignmentStmt' else var_dec.value.kind
            if kind in ['Load', 'LoadNum']:
                raise SemanticError("LoadError: Cannot use loadNum and load function in batch declaration.")

        for var_dec in node.declarations:
            name = var_dec.left.symbol if var_dec.kind == 'VarAssignmentStmt' else var_dec.name.symbol
            kind = var_dec.right if var_dec.kind == 'VarAssignmentStmt' else var_dec.value

            if kind.kind == 'FuncCallStmt':
                return_values = evaluate(kind, self.symbol_table)

                if len(return_values) > 1:
                    if node.batch_ver1:
                        if len(node.declarations) != len(return_values):
                            raise SemanticError(f"Expected {len(node.declarations)} return values, got {len(return_values)}.")

                        for declaration, value in zip(node.declarations, return_values):
                            self.assign_value(declaration, value)
                        return
                    else:
                        raise SemanticError(f"RecallError: Function '{kind.name.symbol}' recalls more than one value.")

            self.visit(var_dec)
            value = self.symbol_table.lookup(name)
            declared_types.add(value["type"])

        if len(declared_types) > 1:
            raise SemanticError(f"All variables in a batch declaration must have the same type. Found types: {declared_types}")

    def assign_value(self, declaration, value):
        if declaration.kind == 'VarDec':
            var_name = declaration.name.symbol
        else:
            var_name = declaration.left.symbol
        
        if isinstance(value, dict):
            if "dimensions" in value:
                raise SemanticError(f"TypeError: Trying to assign an array to variable '{var_name}'.")
            if "parent" in value:
                raise SemanticError(f"TypeError: Trying to assign a struct instance to variable '{var_name}'.")

        val_type = self.TYPE_MAP.get(type(value), str(type(value)))

        if declaration.kind == 'VarDec':
            self.symbol_table.define_var(var_name, value, val_type, declaration.immo)
        else:
            info = self.symbol_table.lookup(var_name)
            if info["immo"]:
                raise SemanticError(f"AssignmentError: '{var_name}' is declared as an immutable variable.")
            if val_type != info["type"]:
                raise SemanticError(f"TypeMismatchError: Type mismatch for variable '{var_name}'. Expected '{info['type']}', got '{val_type}'.")
            self.symbol_table.define_var(var_name, value, val_type, info["immo"])

    def visit_ArrayAssignmentStmt(self, node: ArrAssignment):
        lhs_name = node.left.left.symbol
        lhs_info = self.symbol_table.lookup(lhs_name)
        if not isinstance(lhs_info, dict) or "dimensions" not in lhs_info:
            raise SemanticError(f"TypeError: '{lhs_name}' is not an array.")
        lhs_immo = lhs_info["immo"]
        lhs_type = lhs_info["type"]
        if lhs_immo==True:
            raise SemanticError(f"ArrayAssignmentError: '{lhs_name}' is declared as an immutable array.")
        lhs_data = lhs_info["elements"]
        if lhs_data == None:
            raise SemanticError(f"ArrayAssignmentError: Array '{lhs_name}' is a dead array.")
        lhs_dim = lhs_info["dimensions"]
        if len(lhs_dim) != len(node.left.index):
            raise SemanticError(f"ArrayIndexError: Incorrect number of dimensions for '{lhs_name}'.")
        
        target = lhs_data
        for i, idx in enumerate(node.left.index[:-1]):
            idx = evaluate(idx, self.symbol_table)
            if idx < 0 or idx >= len(target):
                raise SemanticError(f"ArrayIndexError: Index {idx} out of bounds for dimension {i} of array '{lhs_name}'.")
            target = target[idx]

        final_idx = node.left.index[-1]
        final_idx = evaluate(final_idx, self.symbol_table)
        if final_idx < 0 or final_idx >= len(target):
            raise SemanticError(f"ArrayIndexError: Index {final_idx} out of bounds for final dimension of array '{lhs_name}'.")

        if node.right.kind == 'FuncCallStmt':
            rhs_name = node.right.name.symbol
            return_values = evaluate(node.right, self.symbol_table)
            if len(return_values) > 1:
                raise SemanticError(f"RecallError: Function '{rhs_name}' recalls more than one value.")
            value = return_values[0]
            if value == []:
                raise SemanticError(f"AssignmentError: Mismatched types — Trying to assign a list object to an array element.")
        else:
            value = evaluate(node.right, self.symbol_table)
        
        if isinstance(value, dict):
            raise SemanticError(f"AssignmentError: Mismatched types — Trying to assign a list object to an array element.")

        if isinstance (value, UnresolvedNumber):
            if lhs_type == "hp":
                value = 0
            elif lhs_type == "xp":
                value = 0.0    
            else:
                raise SemanticError("TypeError: Using loadNum function to assign a non-numeric array element.")

        if node.operator in ['+=', '-=', '*=', '/=', '%=']:
            if (isinstance(value, str) and isinstance(target[final_idx], bool)) or (isinstance(value, bool) and isinstance(target[final_idx], str)):
                raise SemanticError("TypeError: Cannot mix comms and flags in an expression.")

            if isinstance(value, str) != isinstance(target[final_idx], str):
                raise SemanticError("TypeError: Cannot mix comms and numeric types in an expression.")

            if isinstance(target[final_idx], str) and node.operator != '+=':
                raise SemanticError("TypeError: Only valid assignment operator between comms is '+='.")
            
            operations = {
                '+=': lambda x, y: x + y,
                '-=': lambda x, y: x - y,
                '*=': lambda x, y: x * y,
                '/=': lambda x, y: x / y,
                '%=': lambda x, y: x % y
            }
            
            if node.operator == '/=':
                if isinstance(target[final_idx], int) and isinstance(value, int):
                    if value == 0:
                        raise SemanticError("ZeroDivisionError: Division by zero is not allowed")
                    value = int(operations[node.operator](target[final_idx], value)) 
                else:
                    if value == 0 or value == 0.0:
                        raise SemanticError("ZeroDivisionError: Division by zero is not allowed")
                    value = operations[node.operator](target[final_idx], value)
            elif node.operator == '%=':
                if isinstance(target[final_idx], int) and isinstance(value, int):
                    if value == 0:
                        raise SemanticError("ZeroDivisionError: Modulo by zero is not allowed.")
                    value = operations[node.operator](target[final_idx], value)
                else:
                    raise SemanticError("ModuloError: Only hp values can be used in modulo operation.")
            else:
                value = operations[node.operator](target[final_idx], value)
            target[final_idx] = value
        else:
            target[final_idx] = value
        new_val_type = self.TYPE_MAP.get(type(value), str(type(value)))
        if new_val_type != lhs_type:
            raise SemanticError(f"TypeMismatchError: Array '{lhs_name}' expects '{lhs_type}' data type, not '{new_val_type}'.")
        
        self.symbol_table.define_arr(lhs_name, lhs_dim, lhs_data, lhs_immo, lhs_type)
    
    def visit_ArrayRedec(self, node: ArrayRedec):
        arr_name = node.name
        arr_info = self.symbol_table.lookup(arr_name)
        if not isinstance(arr_info, dict) or "dimensions" not in arr_info:
            raise SemanticError(f"TypeError: '{arr_name}' is not an array.")
        arr_immo = arr_info["immo"]
        arr_type = arr_info["type"]
        arr_dimensions = arr_info["dimensions"]
        if arr_immo==True:
            raise SemanticError(f"RedeclerationError: '{arr_name}' is declared as an immutable array.")

        if isinstance(node.elements, str):
            rhs_arr = self.symbol_table.lookup(node.elements)
            if not isinstance(rhs_arr, dict) or "elements" not in rhs_arr:
                raise SemanticError(f"TypeError: '{node.elements}' is not an array.")
            
            if rhs_arr["elements"] is None:
                raise SemanticError(f"ArrayRedeclarationError: Array {rhs_arr} is a dead array.")
            values = rhs_arr["elements"]
            if len(arr_dimensions) != len(rhs_arr["dimensions"]):
                raise SemanticError(f"RedeclerationError: Incorrect number of dimensions.")
            if rhs_arr["type"] != arr_type:
                raise SemanticError(f"TypeError: Array '{arr_name}' expects '{arr_type}' datatype. Found '{rhs_arr["type"]}'")
            self.symbol_table.define_arr(arr_name, rhs_arr["dimensions"], values, node.immo, arr_type)
        elif isinstance(node.elements, FuncCallStmt):
            return_values = evaluate(node.elements, self.symbol_table)
            print(return_values)
            if len(return_values) > 1:
                raise SemanticError(f"RecallError: Function '{node.elements.name.symbol}' recalls more than one value.")
            rhs_arr = return_values[0]
            if rhs_arr == []:
                if len(arr_dimensions) == 2:
                     self.symbol_table.define_arr(arr_name, arr_dimensions, [[],[]], node.immo, arr_type)
                     return
                else:
                    self.symbol_table.define_arr(arr_name, arr_dimensions, [], node.immo, arr_type)
                    return
            if not isinstance(rhs_arr, dict) or "dimensions" not in rhs_arr:
                raise SemanticError(f"TypeError: Function '{node.elements.name.symbol}' does not recall an array.")
            values = rhs_arr["elements"]
            if len(arr_dimensions) != len(rhs_arr["dimensions"]):
                raise SemanticError(f"RedeclerationError: Incorrect number of dimensions.")
            if rhs_arr["type"] != arr_type:
                raise SemanticError(f"TypeError: Array '{arr_name}' expects '{arr_type}' datatype. Found '{rhs_arr["type"]}'")
            self.symbol_table.define_arr(arr_name, rhs_arr["dimensions"], values, node.immo, arr_type)
        else:
            declared_types = []
            values = []

            if len(node.dimensions) != len(arr_dimensions):
                raise SemanticError(f"RedeclerationError: Incorrect number of dimensions.")
        
            if len(node.dimensions) == 1:
                for val in node.elements:
                    value = evaluate(val, self.symbol_table)
                    val_type = self.TYPE_MAP.get(type(value), str(type(value)))
                    declared_types.append(val_type)
                    values.append(value)
            else:
                for row in node.elements:
                    inner_values = []
                    for val in row:
                        value = evaluate(val, self.symbol_table)
                        val_type = self.TYPE_MAP.get(type(value), str(type(value)))
                        declared_types.append(val_type)
                        inner_values.append(value)
                    values.append(inner_values)

            for elem_type in declared_types:
                if elem_type != arr_type:
                    raise SemanticError(f"TypeError: Array '{arr_name}' expects '{arr_type}' datatype. Found '{elem_type}'")
            self.symbol_table.define_arr(arr_name, node.dimensions, values, node.immo, arr_type)
    
    def visit_StructInst(self, node: StructInst):
        structinst = self.symbol_table.lookup(node.name.symbol)
        structparent = self.symbol_table.lookup(structinst["parent"])
        
        fields = structinst["fields"]
        field_names = list(structparent.keys())
        struct_fields = []

        if len(fields) > len(field_names):
            raise SemanticError(f"Too many values provided for struct '{structinst["parent"]}'." 
                                f" Expected {len(structparent)}, got {len(structinst["fields"])}.")
        
        for i, field in enumerate(field_names):
            default_value = structparent[field]["value"]
            expected_type = structparent[field]["datatype"]

            if i < len(fields):
                value_to_use = fields[i]
                actual_type = self.TYPE_MAP.get(type(value_to_use), None)
                if actual_type != expected_type:
                    raise SemanticError(f"FieldTypeError: Type mismatch for field '{field}'." 
                                      f" Expected '{expected_type}', but got '{actual_type}'.")
                struct_fields.append({
                    "name": field,
                    "value": value_to_use
                })
            else:
                value_to_use = default_value
                struct_fields.append({
                    "name": field,
                    "value": value_to_use
                })
            
        self.symbol_table.define_structinst(node.name.symbol, node.parent, struct_fields, node.immo)

    def visit_GlobalStructDec(self, node: GlobalStructDec):
        pass

    def visit_InstAssignmentStmt(self, node: InstAssignment):
        structinst = self.symbol_table.lookup(node.left.instance.symbol)
        if not isinstance(structinst, dict) or "fields" not in structinst:
            raise SemanticError(f"TypeError: '{node.left.instance.symbol}' is not a struct instance.")
        if structinst["immo"] == True:
            raise SemanticError(f"InstanceAssignmentError: '{node.left.instance.symbol}' is declared as an immutable struct instance.")
        field_names = [field["name"] for field in structinst["fields"]]
        new_field = node.left.field.symbol
        
        if new_field not in field_names:
            raise SemanticError(f"FieldError: Field '{new_field}' does not exist "
                                f"in struct instance '{node.left.instance.symbol}'.")
        
        new_val = evaluate(node.right, self.symbol_table)
        if isinstance(new_val, dict):
            raise SemanticError(f"AssignmentError: Mismatched types — trying to assign a list object from '{node.right.symbol}' to a instance field.")

        for field in structinst["fields"]:
            if new_field == field["name"]:
                old_type = self.TYPE_MAP.get(type(field["value"]), None)
                if isinstance(new_val, UnresolvedNumber):
                    if old_type == "hp":
                        new_val = 0
                    elif old_type == "xp":
                        new_val = 0.0
                    else:
                        raise SemanticError("TypeError: Using loadNum function to assign a non-numeric instance field.")
                if node.operator in ['+=', '-=', '*=', '/=', '%=']:
                    if (isinstance(new_val, str) and isinstance(field["value"], bool)) or (isinstance(new_val, bool) and isinstance(field["value"], str)):
                        raise SemanticError("TypeError: Cannot mix comms and flags in an expression.")

                    if isinstance(new_val, str) != isinstance(field["value"], str):
                        raise SemanticError("TypeError: Cannot mix comms and numeric types in an expression.")

                    if isinstance(new_val, str) and node.operator != '+=':
                        raise SemanticError("TypeError: Only valid assignment operator between comms is '+='.")

                    operations = {
                        '+=': lambda x, y: x + y,
                        '-=': lambda x, y: x - y,
                        '*=': lambda x, y: x * y,
                        '/=': lambda x, y: x / y,
                        '%=': lambda x, y: x % y
                    }

                    if node.operator == '/=': 
                        if isinstance(field["value"], int) and isinstance(new_val, int):
                            if new_val == 0:
                                raise SemanticError("ZeroDivisionError: Division by zero is not allowed")
                            new_val = int(operations[node.operator](field["value"], new_val)) 
                        else:
                            if new_val == 0 or new_val == 0.0:
                                raise SemanticError("ZeroDivisionError: Division by zero is not allowed")
                            new_val = operations[node.operator](field["value"], new_val)
                    elif node.operator == '%=':
                        if isinstance(field["value"], int) and isinstance(new_val, int):
                            if new_val == 0:
                                raise SemanticError("ZeroDivisionError: Modulo by zero is not allowed.")
                            new_val = operations[node.operator](field["value"], new_val)
                        else:
                            raise SemanticError("ModuloError: Only hp values can be used in modulo operation.")
                    else:
                        new_val = operations[node.operator](field["value"], new_val)
                else:
                    new_val = new_val
                
                new_type = self.TYPE_MAP.get(type(new_val), None)
                if old_type != new_type:
                    raise SemanticError(f"FieldTypeError: Type mismatch for field '{field["name"]}'."
                                        f" Expected '{old_type}', but got '{new_type}'.")
                field["value"] = new_val
        
        self.symbol_table.define_structinst(node.left.instance.symbol, structinst["parent"], structinst["fields"], structinst["immo"])

    def visit_IfStmt(self, node: IfStmt):
        conditions = []
        if_condition = evaluate(node.condition, self.symbol_table)
        if not isinstance(if_condition, bool):
            raise SemanticError("TypeError: The condition used does not evaluate to a flag value.")
        conditions.append([if_condition, node.then_branch])
        if node.elif_branches is not None:
            for cond in node.elif_branches:
                elif_condition = evaluate(cond.condition, self.symbol_table)
                if not isinstance(elif_condition, bool):
                    raise SemanticError("TypeError: The condition used does not evaluate to a flag value.")
                conditions.append([elif_condition, cond.body])
        
        for cond in conditions:
            if cond[0] == True:
                self.symbol_table.restore_scope(len(self.symbol_table.scope_stack))
                for stmt in cond[1]:
                    self.visit(stmt)
                    if self.recall_flag and self.in_func_flag:
                        self.symbol_table.exit_scope()
                        return
                    if self.checkpoint_flag:
                        self.symbol_table.exit_scope()
                        return

                    if self.resume_flag:
                        self.symbol_table.exit_scope()
                        return
                self.symbol_table.exit_scope()
                return
            
        
        if node.else_branch is not None:
            self.symbol_table.restore_scope(len(self.symbol_table.scope_stack))
            for stmt in node.else_branch:
                self.visit(stmt)
                if self.recall_flag and self.in_func_flag:
                    self.symbol_table.exit_scope()
                    return
                if self.checkpoint_flag:
                    self.symbol_table.exit_scope()
                    return

                if self.resume_flag:
                    self.symbol_table.exit_scope()
                    return
            self.symbol_table.exit_scope()

    def visit_FlankStmt(self, node: FlankStmt):
        expression = evaluate(node.expression, self.symbol_table)
        for choice in node.choices:
            for choice_value in choice.values:
                value = evaluate(choice_value, self.symbol_table)
                if value == expression:
                    self.symbol_table.restore_scope(len(self.symbol_table.scope_stack))
                    for stmt in choice.body:
                        self.visit(stmt)
                        if self.recall_flag and self.in_func_flag:
                            self.symbol_table.exit_scope()
                            return
                    if self.resume_flag:  
                        self.resume_flag = False
                        self.symbol_table.exit_scope()
                        break
                    self.symbol_table.exit_scope()
                    return

        self.symbol_table.restore_scope(len(self.symbol_table.scope_stack))
        for stmt in node.backup_body:
            self.visit(stmt)
            if self.recall_flag and self.in_func_flag:
                self.symbol_table.exit_scope()
                return
        self.symbol_table.exit_scope()

    def visit_ForStmt(self, node: ForStmt):
        val_name = node.initialization.left
        value = self.symbol_table.lookup(val_name)

        if not isinstance(value, dict):
            datatype = self.TYPE_MAP.get(type(value), str(type(value)))
            self.symbol_table.define_var(val_name, value, datatype, False)
            value = self.symbol_table.lookup(node.left.symbol)

        if "value" not in value:
            raise SemanticError(f"AssignmentError: Mismatched types — trying to assign a single value from '{node.right.symbol}' to a list object.")

        value_type = value["type"]
        if value["immo"]==True:
            raise SemanticError(f"TypeError: '{val_name}' is declared as an immutable variable.")
        new_val = evaluate(node.initialization.right, self.symbol_table)
        if value_type != "hp" or not isinstance(new_val, int):
            raise SemanticError(f"ForError: Only integer variables can be used for loop control.")
        self.symbol_table.define_var(val_name, new_val, value_type, value["immo"])
        
        condition = evaluate(node.condition, self.symbol_table)
        if not isinstance(condition, bool):
            raise SemanticError(f"LoopError: Loop condition does not evaluate to a flag value.")
        
        if condition:
            self.symbol_table.restore_scope(len(self.symbol_table.scope_stack))
            while evaluate(node.condition, self.symbol_table):
                for stmt in node.body:
                    self.visit(stmt)
                    if self.recall_flag and self.in_func_flag:
                        self.symbol_table.exit_scope()
                        return
                    if self.checkpoint_flag:
                        self.checkpoint_flag = False
                        self.symbol_table.exit_scope()
                        self.symbol_table.define_var(val_name, value["value"], value_type, value["immo"])
                        return
                    if self.resume_flag:
                        self.resume_flag = False
                        continue 
                self.visit_VarAssignmentStmt(node.update)
            self.symbol_table.exit_scope()
            
        self.symbol_table.define_var(val_name, value["value"], value_type, value["immo"])
    
    def visit_GrindWhileStmt(self, node: GrindWhileStmt):
        condition = evaluate(node.condition, self.symbol_table)
        if not isinstance(condition, bool):
            raise SemanticError(f"LoopError: Loop condition does not evaluate to a flag value.")
        
        if node.is_grind:
            self.symbol_table.restore_scope(len(self.symbol_table.scope_stack))
            for stmt in node.body:
                self.visit(stmt)
                if self.recall_flag and self.in_func_flag:
                    self.symbol_table.exit_scope()
                    return
                if self.checkpoint_flag:
                    self.checkpoint_flag = False
                    self.symbol_table.exit_scope()
                    return
                if self.resume_flag:
                    self.resume_flag = False
        elif not node.is_grind and condition:
            self.symbol_table.restore_scope(len(self.symbol_table.scope_stack))
            
        while evaluate(node.condition, self.symbol_table):
            for stmt in node.body:
                self.visit(stmt)
                if self.checkpoint_flag:
                    self.checkpoint_flag = False
                    self.symbol_table.exit_scope()
                    return
                if self.resume_flag:
                    self.resume_flag = False
                    continue 
        self.symbol_table.exit_scope()
    
    def visit_BlockStmt(self, node: BlockStmt):
        self.symbol_table.restore_scope(len(self.symbol_table.scope_stack))
        for stmt in node.statements:
            self.visit(stmt)
        self.symbol_table.play_scope = self.symbol_table.scope_stack.copy()
        self.symbol_table.exit_scope()  

    def visit_ResumeStmt(self, node: ResumeStmt):
        self.resume_flag = True 

    def visit_CheckpointStmt(self, node: CheckpointStmt):
        self.checkpoint_flag = True   

    def visit_GlobalFuncBody(self, node: GlobalFuncBody):
        pass

    def visit_FuncCallStmt(self, node: FuncCallStmt, being_assigned = False):
        self.recall_values = []
        prev_stack = [scope.copy() for scope in self.symbol_table.scope_stack]
        prev_saved_stack = [scope.copy() for scope in self.symbol_table.saved_scopes]
        args = []
        if node.args:
            for arg in node.args:
                if arg.kind in ['Load', 'LoadNum']:
                    raise SemanticError("LoadError: Cannot use load and loadNum function as a function argument.")
                args.append(evaluate(arg, self.symbol_table))
        
        self.symbol_table.restore_scope_func(node.name.symbol)
       
        info = self.symbol_table.lookup(node.name.symbol)
        if not info:
            raise SemanticError(f"Function '{node.name.symbol}' is not defined.")

        param_scope = {}
        params = info["params"]

        if node.args and not params:
            raise SemanticError(f"Function '{node.name.symbol}' does not take any arguments, but {len(node.args)} were provided.")
       
        if params:
            if len(args) > len(params):
                raise SemanticError(f"Function '{node.name.symbol}' expects {len(params)} arguments, got {len(args)}.")
            
            for i, param in enumerate(params):
                if i < len(args):  
                    arg_value = args[i]
                    print(f"arg value raw -> {arg_value}") 
                elif param.param_val is not None:
                    arg_value = evaluate(param.param_val, self.symbol_table)
                else:
                    raise SemanticError(f"Missing argument for parameter '{param.param}' and no default value provided.")
            
                param_scope[param.param] = arg_value
            
        if param_scope:
            self.symbol_table.scope_stack.append(param_scope)
            
        global_scope = prev_stack[0]  
        func_global_scope = self.symbol_table.scope_stack[0]  

        for name, value in global_scope.items():
            if name in func_global_scope:
                func_global_scope[name] = value  
        
        self.in_func_flag = True
        
        for stmt in info["body"]:
            self.visit(stmt)
            if self.recall_flag:
                break

        for name, value in func_global_scope.items():
            if name in global_scope:  
                global_scope[name] = value
        
        self.symbol_table.scope_stack = prev_stack.copy()
        self.symbol_table.saved_scopes = prev_saved_stack.copy()

        self.in_func_flag = False
        self.recall_flag = False

        if self.recall_values is None:
            return
        elif self.recall_values and not being_assigned:
            raise SemanticError(f"Function '{node.name.symbol}' has a recall value but is not being assigned anywhere.")
        elif self.recall_values:
            return self.recall_values

    def visit_RecallStmt(self, node: RecallStmt):
        self.recall_values = []
        if len(node.expressions) == 1 and node.expressions[0] == "void":
            self.recall_values = None
        else:
            for expr in node.expressions:
                print(expr)
                if expr == []:
                    self.recall_values.append([])
                    self.recall_flag = True
                    break
                self.recall_values.append(evaluate(expr, self.symbol_table))
        self.recall_flag = True

    def visit_ShootStmt(self, node: ShootStmt):
        if node.element.kind in ['Load', 'LoadNum']:
            raise SemanticError("ArgsError: load and loadNum function are an invalid argument for shoot and shootNxt function.")
        
        element = evaluate(node.element, self.symbol_table)
        print(f"shoot element -> {element}")
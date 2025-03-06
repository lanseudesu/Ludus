from ..nodes import *
from .new_symboltable import SymbolTable
from .new_interpreter import evaluate
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

class SemanticAnalyzer(ASTVisitor):
    i = 1

    TYPE_MAP = {
        int: "hp",
        float: "xp",
        str: "comms",
        bool: "flag"
    }

    def __init__(self, symbol_table):
        super().__init__()
        self.symbol_table = symbol_table  

    def visit_VarDec(self, node: VarDec):
        value = evaluate(node.value, self.symbol_table)
        if isinstance(node.value, DeadLiteral):
            val_type = node.value.datatype
        elif isinstance(node.value, Identifier) and value == None:
            id_val = self.symbol_table.lookup(node.value.symbol)
            val_type = id_val["type"]
        else:
            val_type = self.TYPE_MAP.get(type(value), str(type(value)))
        self.symbol_table.define_var(node.name.symbol, value, val_type, node.immo)

    def visit_VarAssignmentStmt(self, node: VarAssignment):
        value = self.symbol_table.lookup(node.left.symbol)
        value_type = value["type"]
        if value["immo"]==True:
            raise SemanticError(f"AssignmentError: '{node.left.symbol}' is declared as an immutable variable.")
        new_val = evaluate(node.right, self.symbol_table)

        if node.operator in ['+=', '-=', '*=', '/=', '%=']:
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
            new_val = new_val

        new_val_type = self.TYPE_MAP.get(type(new_val), str(type(new_val)))
        
        if new_val_type != value_type:
            raise SemanticError(f"TypeMismatchError: Type mismatch for variable '{node.left.symbol}'. Expected '{value_type}', got '{new_val_type}'.")
        
        self.symbol_table.define_var(node.left.symbol, new_val, new_val_type, value["immo"])

    def visit_BatchVarDec(self, node: BatchVarDec):
        declared_types = set() 
        for var_dec in node.declarations:
            self.visit(var_dec)

            value = self.symbol_table.lookup(var_dec.name.symbol)
            value_type = value["type"]
            declared_types.add(value_type)
        
        if len(declared_types) > 1:
            raise SemanticError(f"All variables in a batch declaration must have the same type. Found types: {declared_types}")

    def visit_ArrayAssignmentStmt(self, node: ArrAssignment):
        lhs_name = node.left.left.symbol
        lhs_info = self.symbol_table.lookup(lhs_name)
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

        value = evaluate(node.right, self.symbol_table)
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
        declared_types = []
        values = []
        arr_name = node.name
        arr_info = self.symbol_table.lookup(arr_name)
        arr_immo = arr_info["immo"]
        arr_type = arr_info["type"]
        arr_dimensions = arr_info["dimensions"]
        if arr_immo==True:
            raise SemanticError(f"RedeclerationError: '{arr_name}' is declared as an immutable array.")
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
        if structinst["immo"] == True:
            raise SemanticError(f"InstanceAssignmentError: '{node.left.instance.symbol}' is declared as an immutable struct instance.")
        field_names = [field["name"] for field in structinst["fields"]]
        new_field = node.left.field.symbol
        
        if new_field not in field_names:
            raise SemanticError(f"FieldError: Field '{new_field}' does not exist "
                                f"in struct instance '{node.left.instance.symbol}'.")
        
        new_val = evaluate(node.right, self.symbol_table)

        for field in structinst["fields"]:
            if new_field == field["name"]:
                old_type = self.TYPE_MAP.get(type(field["value"]), None)
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
                self.symbol_table.restore_scope(self.i)
                for stmt in cond[1]:
                    self.visit(stmt)
                self.symbol_table.exit_scope()
                self.i += 1
                return
            self.i += 1
        
        if node.else_branch is not None:
            self.symbol_table.restore_scope(self.i)
            for stmt in node.else_branch:
                self.visit(stmt)
            self.symbol_table.exit_scope()
            self.i += 1

    def visit_FlankStmt(self, node: FlankStmt):
        expression = evaluate(node.expression, self.symbol_table)
        for choice in node.choices:
            resume = False
            for choice_value in choice.values:
                value = evaluate(choice_value, self.symbol_table)
                if value == expression:
                    self.symbol_table.restore_scope(self.i)
                    for stmt in choice.body:
                        if stmt.kind == "ResumeStmt":
                            resume = True
                        self.visit(stmt)
                    self.symbol_table.exit_scope()
                    self.i += 1
                    if not resume:  
                        return
                    break
            else:
                self.i += 1

        self.symbol_table.restore_scope(self.i)
        for stmt in node.backup_body:
            self.visit(stmt)
        self.symbol_table.exit_scope()
        self.i += 1

    def visit_ForStmt(self, node: ForStmt):
        val_name = node.initialization.left
        value = self.symbol_table.lookup(val_name)
        value_type = value["type"]
        if value["immo"]==True:
            raise SemanticError(f"TypeError: '{val_name}' is declared as an immutable variable.")
        new_val = evaluate(node.initialization.right, self.symbol_table)
        if value_type != "hp" or not isinstance(new_val, int):
            raise SemanticError(f"ForError: Only integer variables can be used for loop control.")
        self.symbol_table.define_var(val_name, new_val, value_type, value["immo"])
        
        condition = evaluate(node.condition, self.symbol_table)
        if not isinstance(condition, bool):
            raise SemanticError(f"ForError: Loop condition does not evaluate to a flag value.")
        
        if evaluate(node.condition, self.symbol_table):
            self.symbol_table.restore_scope(self.i)
            while evaluate(node.condition, self.symbol_table):
                for stmt in node.body:
                    self.visit(stmt)
                self.visit_VarAssignmentStmt(node.update)
            self.symbol_table.exit_scope()
            self.i += 1
        self.symbol_table.define_var(val_name, value["value"], value_type, value["immo"])
    
    
    def visit_BlockStmt(self, node: BlockStmt):
        self.symbol_table.restore_scope(self.i)
        for stmt in node.statements:
            self.visit(stmt)
        
from ..nodes import *
from .new_symboltable import SymbolTable
from .new_interpreter import evaluate
from ..error import SemanticError
import traceback

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

    def visit_VarAssignment(self, node: VarAssignment):
        self.symbol_table.define(node.left.symbol, node.right)

    def visit_ArrayDec(self, node: ArrayDec):
        declared_types = set()
        values = []
        
        if node.elements is None:
            self.symbol_table.define_arr(node.name.symbol, node.dimensions, None, node.immo, node.scope)
        else:
            if len(node.dimensions) == 1:
                for val in node.elements:
                    declared_types.add(val.kind)
                    value = evaluate(val, self.symbol_table)
                    values.append(value)
            else:
                for row in node.elements:
                    inner_values = []
                    for val in row:
                        declared_types.add(val.kind)
                        value = evaluate(val, self.symbol_table)
                        inner_values.append(value)
                    values.append(inner_values)
            
            if len(declared_types) > 1:
                raise SemanticError(f"All variables in a batch declaration must have the same type. Found types: {declared_types}")
            self.symbol_table.define_arr(node.name.symbol, node.dimensions, values, node.immo, node.scope)
    
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
        for stmt in node.statements:
            self.visit(stmt)

class SemanticAnalyzer(ASTVisitor):
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
        else:
            val_type = self.TYPE_MAP.get(type(value), str(type(value)))
        self.symbol_table.define_var(node.name.symbol, value, val_type, node.immo, node.scope)

    def visit_VarAssignmentStmt(self, node: VarAssignment):
        new_val = evaluate(node.right, self.symbol_table)
        new_val_type = self.TYPE_MAP.get(type(new_val), str(type(new_val)))
        value = self.symbol_table.lookup(node.left.symbol)
        value_type = value["type"]

        if value["immo"]==True:
            raise SemanticError(f"AssignmentError: '{node.left.symbol}' is declared as an immutable variable.")

        if new_val_type != value_type:
            raise SemanticError(f"TypeMismatchError: Type mismatch for variable '{node.left.symbol}'. Expected '{value_type}', got '{new_val_type}'.")
        
        self.symbol_table.define_var(node.left.symbol, new_val, new_val_type, value["immo"], value["scope"])

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
        array_info = self.symbol_table.lookup(node.left.symbol)
        array_immo = array_info["immo"]
        array_scope = array_info["scope"]
        if array_immo==True:
            raise SemanticError(f"ArrayAssignmentError: '{node.left.symbol}' is declared as an immutable array.")
        array_data = array_info["elements"]
        array_dim = array_info["dimensions"]
        value = evaluate(node.right, self.symbol_table)
        val_type = self.TYPE_MAP.get(type(value), str(type(value)))

        if len(array_dim) != len(node.index):
            raise SemanticError(f"ArrayIndexError: Incorrect number of dimensions for '{node.left.symbol}'.")
        
        target = array_data
        for i, idx in enumerate(node.index[:-1]):
            if idx < 0 or idx >= len(target):
                raise SemanticError(f"ArrayIndexError: Index {idx} out of bounds for dimension {i} of array '{node.left.symbol}'.")
            target = target[idx]

        final_idx = node.index[-1]
        if final_idx < 0 or final_idx >= len(target):
            raise SemanticError(f"ArrayIndexError: Index {final_idx} out of bounds for final dimension of array '{node.left.symbol}'.")

        expected_type = self.TYPE_MAP.get(type(target[final_idx]), str(type(target[final_idx])))
        if val_type != expected_type:
            raise SemanticError(f"TypeMismatchError: Array '{node.left.symbol}' expects '{expected_type}' data type, not '{val_type}'.")

        target[final_idx] = value
        
        self.symbol_table.define_arr(node.left.symbol, array_dim, array_data, array_immo, array_scope)
    
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
        
        value = evaluate(node.right, self.symbol_table)
        new_type = self.TYPE_MAP.get(type(value), None)

        for field in structinst["fields"]:
            if new_field == field["name"]:
                old_type = self.TYPE_MAP.get(type(field["value"]), None)
                if old_type != new_type:
                    raise SemanticError(f"FieldTypeError: Type mismatch for field '{field["name"]}'."
                                        f" Expected '{old_type}', but got '{new_type}'.")
                field["value"] = value
        
        self.symbol_table.define_structinst(node.left.instance.symbol, structinst["parent"], structinst["fields"], structinst["immo"])

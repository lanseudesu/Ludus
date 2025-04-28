from ludus.nodes import GrindWhileStmt
from ..nodes import *
from .symbol_table import SymbolTable
from .interpreter import evaluate, eval_func, UnresolvedNumber
from ..error import SemanticError
import eel
import math

@eel.expose
def print_shoot(element):
    eel.printShoot(element)

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
        elem_type = None
        values = []
        is_empty = False
        
        if node.elements is None:
            self.symbol_table.define_arr(node.name.symbol, node.dimensions, None, node.immo, node.datatype)
        else:
            if len(node.dimensions) == 1:
                is_empty = node.elements == []
                for val in node.elements:
                    value = evaluate(val, self.symbol_table)
                    if elem_type:
                        new_type = self.TYPE_MAP.get(type(value), str(type(value)))
                        if elem_type != new_type:
                            raise SemanticError(f"TypeError: All elements in an array declaration must have the same type. Found types: '{elem_type}' and '{new_type}'.",
                                                val.pos_start, val.pos_end)
                    else:
                        elem_type = self.TYPE_MAP.get(type(value), str(type(value)))
                    values.append(value)
            else:
                is_empty = node.elements == [[], []]
                for row in node.elements:
                    inner_values = []
                    for val in row:
                        value = evaluate(val, self.symbol_table)
                        if elem_type:
                            new_type = self.TYPE_MAP.get(type(value), str(type(value)))
                            if elem_type != new_type:
                                raise SemanticError(f"TypeError: All elements in an array declaration must have the same type. Found types: '{elem_type}' and '{new_type}'.",
                                                    val.pos_start, val.pos_end)
                        else:
                            elem_type = self.TYPE_MAP.get(type(value), str(type(value)))
                        inner_values.append(value)
                    values.append(inner_values)
            
            if is_empty:
                datatype = node.datatype
            else:
                datatype = elem_type if elem_type else None
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
                eval_value = evaluate(value, self.symbol_table)
                val_type = self.TYPE_MAP.get(type(eval_value), str(type(eval_value)))
                if field.datatype != val_type:
                    if val_type == 'comms':
                        end = value.pos_end[1]+(len(str(eval_value)))+1
                    else:
                        end = value.pos_end[1]+(len(str(eval_value)))-1
                    raise SemanticError(f"TypeError: Type mismatch for field '{field.name.symbol}'."
                                        f" Expected '{field.datatype}', but got '{val_type}'.", 
                                        value.pos_start, value.pos_end)
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
            fields.append(field)
            
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

    def visit_GlobalFuncDec(self, node: GlobalFuncDec):
        self.symbol_table.define(node.name.symbol, node.params)
    
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

    def __init__(self, symbol_table, isRuntime=False):
        super().__init__()
        self.symbol_table = symbol_table 
        self.i = 1 
        self.checkpoint_flag = False
        self.resume_flag = False
        self.in_func_flag = False
        self.recall_flag = False
        self.isRuntime = isRuntime

    def visit(self, node: Stmt, is_runtime=False):
        print(f"runtime is {is_runtime} and self.isruntime is {self.isRuntime}")
        if is_runtime:
            self.isRuntime = True
        print(f"runtime is currently {self.isRuntime}")
        method_name = f"visit_{node.kind}"
        visitor = getattr(self, method_name, self.generic_visit)
        return visitor(node)

    ###### VARIABLES #########
    def visit_VarDec(self, node: VarDec):
        if node.value.kind == 'FuncCallStmt':
            rhs_name = node.value.name.symbol
            return_values = evaluate(node.value, self.symbol_table, self.isRuntime)
            if len(return_values) > 1:
                raise SemanticError(f"ValueError: Function '{rhs_name}' recalls more than one value, but only one was expected.", node.value.pos_start, node.value.pos_end)
            value = return_values[0]
            if value == []:
                raise SemanticError(f"ValueError: Trying to declare an array to a variable: '{node.name.symbol}'.", node.value.pos_start, node.value.pos_end)
            if isinstance(value, list):
                value = value[0]
        else:    
            value = evaluate(node.value, self.symbol_table, self.isRuntime)
            print(f"value is {value}")
            
        if isinstance(value, UnresolvedNumber):
            val_type = "hp or xp" 
        elif isinstance(value, dict):
            if "dimensions" in value:
                raise SemanticError(f"ValueError: Trying to declare an array to a variable: '{node.name.symbol}'.", node.value.pos_start, node.value.pos_end)
            if "parent" in value:
                raise SemanticError(f"ValueError: Trying to declare a struct instance to a variable: '{node.name.symbol}'.", node.value.pos_start, node.value.pos_end)
        elif isinstance(node.value, DeadLiteral):
            val_type = node.value.datatype
        elif isinstance(node.value, Identifier) and value == None:
            id_val = self.symbol_table.lookup(node.value.symbol, node.value.pos_start, node.value.pos_end)
            val_type = id_val["type"]
        else:
            val_type = self.TYPE_MAP.get(type(value), str(type(value)))
        # print(value)
        self.symbol_table.define_var(node.name.symbol, value, val_type, node.immo)

    def visit_VarAssignmentStmt(self, node: VarAssignment):
        if node.right.kind == 'FuncCallStmt':
            rhs_name = node.right.name.symbol
            return_values = evaluate(node.right, self.symbol_table, self.isRuntime)
            if len(return_values) > 1:
                raise SemanticError(f"ValueError: Function '{rhs_name}' recalls more than one value, but only one was expected.", node.right.pos_start, node.right.pos_end)
            new_val = return_values[0]
            if new_val == []:
                raise SemanticError(f"ValueError: Trying to assign an array to a variable: '{node.left.symbol}'.", node.right.pos_start, node.right.pos_end)
        elif node.right.kind in {'LoadNum', 'Load'} and node.operator != ':':
            raise SemanticError(f"ValueError: loadNum and load function cannot be used in compound assignment statements.", node.right.pos_start, node.right.pos_end)
        else:
            new_val = evaluate(node.right, self.symbol_table, self.isRuntime)

        if isinstance(new_val, dict):
            if "dimensions" in new_val:
                raise SemanticError(f"ValueError: Trying to assign an array to a variable: '{node.left.symbol}'.", node.right.pos_start, node.right.pos_end)
            if "parent" in new_val:
                raise SemanticError(f"ValueError: Trying to assign a struct instance to a variable: '{node.left.symbol}'.", node.right.pos_start, node.right.pos_end)

        #print(f"new_val is {new_val}")
        value = self.symbol_table.lookup(node.left.symbol, node.left.pos_start, node.left.pos_end)
        
        if not isinstance(value, dict):
            datatype = self.TYPE_MAP.get(type(value), str(type(value)))
            self.symbol_table.define_var(node.left.symbol, value, datatype, False)
            value = self.symbol_table.lookup(node.left.symbol, node.left.pos_start, node.left.pos_end)

        if "value" not in value:
            raise SemanticError(f"ValueError: Mismatched values — trying to assign a single value to a list object: '{node.left.symbol}'.", node.pos_start, node.pos_end)
        
        value_type = value["type"]
        if value["immo"]==True:
            raise SemanticError(f"ImmoError: '{node.left.symbol}' is declared as an immutable variable.", node.left.pos_start, node.left.pos_end)   
        
        if isinstance(new_val, UnresolvedNumber) and not isinstance(value["value"], UnresolvedNumber):
            if value_type == "hp":
                new_val = value["value"]
            elif value_type == "xp":
                new_val = value["value"]
            else:
                raise SemanticError("TypeError: Using a non-numeric value to assign a non-numeric variable.", node.right.pos_start, node.right.pos_end)
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
                    raise SemanticError("TypeError: Cannot mix comms and numeric type in an expression.", node.pos_start, node.pos_end)
            
            if (isinstance(new_val, str) and isinstance(value["value"], bool)) or (isinstance(new_val, bool) and isinstance(value["value"], str)):
                raise SemanticError("TypeError: Cannot mix comms and flags in an expression.", node.pos_start, node.pos_end)

            if isinstance(new_val, str) != isinstance(value["value"], str):
                raise SemanticError("TypeError: Cannot mix comms and numeric types in an expression.", node.pos_start, node.pos_end)

            if isinstance(new_val, str) and node.operator != '+=':
                raise SemanticError("TypeError: Only valid assignment operator between comms is '+='.", node.pos_start, node.pos_end)
            
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
                        raise SemanticError("ZeroDivisionError: Division by zero is not allowed.", node.pos_start, node.pos_end)
                    new_val = int(operations[node.operator](value["value"], new_val)) 
                else:
                    if new_val == 0 or new_val == 0.0:
                        raise SemanticError("ZeroDivisionError: Division by zero is not allowed.", node.pos_start, node.pos_end)
                    new_val = operations[node.operator](value["value"], new_val)
            elif node.operator == '%=':
                if isinstance(value["value"], int) and isinstance(new_val, int):
                    if new_val == 0:
                        raise SemanticError("ZeroDivisionError: Modulo by zero is not allowed.", node.pos_start, node.pos_end)
                    new_val = operations[node.operator](value["value"], new_val)
                else:
                    raise SemanticError("ModuloError: Only hp values can be used in modulo operation.", node.pos_start, node.pos_end)
            else:
                new_val = operations[node.operator](value["value"], new_val)  
        else:
            new_val_type = self.TYPE_MAP.get(type(new_val), str(type(new_val)))
            if value_type == "hp or xp":
                if new_val_type in ["hp", "xp"]:
                    value_type = new_val_type
                else:
                    raise SemanticError(f"TypeError: Invalid type for variable '{node.left.symbol}'. Expected numeric but got '{new_val_type}'.", node.pos_start, node.pos_end)

        new_val_type = self.TYPE_MAP.get(type(new_val), str(type(new_val)))
        
        if new_val_type != value_type:
            raise SemanticError(f"TypeError: Type mismatch for variable '{node.left.symbol}'. Expected '{value_type}', got '{new_val_type}'.", node.pos_start, node.pos_end)
        
        self.symbol_table.define_var(node.left.symbol, new_val, new_val_type, value["immo"])

    def visit_BatchVarDec(self, node: BatchVarDec):
        variable_type = None
        for var_dec in node.declarations:
            kind = var_dec.right.kind if var_dec.kind == 'VarAssignmentStmt' else var_dec.value.kind
            if kind in ['Load', 'LoadNum']:
                if var_dec.kind == 'VarAssignmentStmt':
                    raise SemanticError("ValueError: Cannot use loadNum and load function in batch declaration.", var_dec.right.pos_start, var_dec.right.pos_end)
                else:
                    raise SemanticError("ValueError: Cannot use loadNum and load function in batch declaration.", var_dec.value.pos_start, var_dec.value.pos_end)

        for var_dec in node.declarations:
            name = var_dec.left.symbol if var_dec.kind == 'VarAssignmentStmt' else var_dec.name.symbol
            name_node = var_dec.left if var_dec.kind == 'VarAssignmentStmt' else var_dec.name
            kind = var_dec.right if var_dec.kind == 'VarAssignmentStmt' else var_dec.value

            if kind.kind == 'FuncCallStmt':
                return_values = evaluate(kind, self.symbol_table, self.isRuntime)

                if len(return_values) > 1:
                    if node.batch_ver1:
                        if len(node.declarations) != len(return_values):
                            if var_dec.kind == 'VarAssignmentStmt':
                                raise SemanticError(f"ValueError: Expected {len(node.declarations)} return values, got {len(return_values)}.", var_dec.right.pos_start, var_dec.right.pos_end)
                            else:
                                raise SemanticError(f"ValueError: Expected {len(node.declarations)} return values, got {len(return_values)}.", var_dec.value.pos_start, var_dec.value.pos_end)

                        for declaration, value in zip(node.declarations, return_values):
                            self.assign_value(declaration, value, node)
                        return
                    else:
                        if var_dec.kind == 'VarAssignmentStmt':
                                raise SemanticError(f"ValueError: Function '{kind.name.symbol}' recalls more than one value.", var_dec.right.pos_start, var_dec.right.pos_end)
                        else:
                            raise SemanticError(f"ValueError: Function '{kind.name.symbol}' recalls more than one value.", var_dec.value.pos_start, var_dec.value.pos_end)

            self.visit(var_dec, is_runtime=self.isRuntime)
            value = self.symbol_table.lookup(name, name_node.pos_start, name_node.pos_end)
            if variable_type and variable_type != value["type"]:
                value_node = var_dec.right if var_dec.kind == 'VarAssignmentStmt' else var_dec.value
                if not node.batch_ver1:
                    raise SemanticError(
                        f"TypeError: Type mismatch in batch declarations. '{first_var}' is declared as {variable_type}, "
                        f"but '{name}' is declared as {value['type']}.",
                        value_node.pos_start, value_node.pos_end
                    )
                else:
                    raise SemanticError(
                        f"TypeError: Type mismatch in batch declarations. '{first_var}' is declared as {variable_type}, "
                        f"but '{name}' is declared as {value['type']}.",
                        node.pos_start, node.pos_end
                    )
            else:
                variable_type = value["type"]
                first_var = name

    def assign_value(self, declaration, value, node):
        if declaration.kind == 'VarDec':
            var_name = declaration.name
            var_right = declaration.value
        else:
            var_name = declaration.left
            var_right = declaration.right
        
        if isinstance(value, dict):
            if "dimensions" in value:
                raise SemanticError(f"ValueError: Trying to assign an array to variable '{var_name.symbol}'.", var_right.pos_start, var_right.pos_end)
            if "parent" in value:
                raise SemanticError(f"ValueError: Trying to assign a struct instance to variable '{var_name.symbol}'.", var_right.pos_start, var_right.pos_end)

        val_type = self.TYPE_MAP.get(type(value), str(type(value)))

        if declaration.kind == 'VarDec':
            self.symbol_table.define_var(var_name.symbol, value, val_type, declaration.immo)
        else:
            info = self.symbol_table.lookup(var_name.symbol, var_name.pos_start, var_name.pos_end)
            if info["immo"]:
                raise SemanticError(f"ImmoError: '{var_name.symbol}' is declared as an immutable variable.", var_name.pos_start, var_name.pos_end)
            if val_type != info["type"]:
                raise SemanticError(f"TypeError: Type mismatch for variable '{var_name.symbol}'. Expected '{info['type']}', got '{val_type}'.", node.pos_start, node.pos_end)
            self.symbol_table.define_var(var_name.symbol, value, val_type, info["immo"])

    def visit_StrArrAssignment(self, node: StrArrAssignment):
        #print(node)
        if node.right.kind in {'LoadNum', 'Load'} and node.operator != ':':
            raise SemanticError(f"ValueError: loadNum and load function cannot be used in compound assignment statements.", node.right.pos_start, node.right.pos_end)
        
        lhs_name = node.left.left.symbol
        lhs_info = self.symbol_table.lookup(lhs_name, node.left.pos_start, node.left.pos_end)
        #print(lhs_info)
        if "type" not in lhs_info or lhs_info["type"] != "comms":
            raise SemanticError(f"TypeError: '{lhs_name}' is not a comms variable.", node.left.pos_start, node.left.pos_end)
        lhs_immo = lhs_info["immo"]
        lhs_type = lhs_info["type"]
        if lhs_immo==True:
            raise SemanticError(f"ImmoError: '{lhs_name}' is declared as an immutable variable.", node.left.left.pos_start, node.left.left.pos_end)
        
        lhs_data = lhs_info["value"]
        str_list = list(lhs_data)

        idx = node.left.index[0]
        if idx.kind in {'LoadNum', 'Load'}:
            raise SemanticError(f"IndexError: loadNum and load function cannot be used as index expression.", idx.pos_start, idx.pos_end)
        
        if idx.kind == 'FuncCallStmt':
                idx_val = eval_func(idx.name.symbol, idx, self.symbol_table) 
        else:    
            idx_val = evaluate(idx, self.symbol_table)

        if isinstance(idx_val, UnresolvedNumber):
            idx_val = 0

        if not isinstance(idx_val, int):
            raise SemanticError(f"IndexError: Comms index must always evaluate to a positive hp value.", idx.pos_start, idx.pos_end)
        if idx_val < 0 or idx_val >= len(lhs_data):
            raise SemanticError(f"IndexError: Index {idx_val} out of bounds for comms '{lhs_name}'.", idx.pos_start, idx.pos_end)
        
    
        if node.right.kind == 'FuncCallStmt':
            rhs_name = node.right.name.symbol
            return_values = evaluate(node.right, self.symbol_table)
            if len(return_values) > 1:
                raise SemanticError(f"ValueError: Function '{rhs_name}' recalls more than one value, but only one was expected.", node.right.pos_start, node.right.pos_end)
            value = return_values[0]
            if value == []:
                raise SemanticError(f"ValueError: Mismatched values — Trying to assign a list object inside a comms variable.", node.right.pos_start, node.right.pos_end)
        else:
            value = evaluate(node.right, self.symbol_table, self.isRuntime)

        if isinstance(value, dict):
            raise SemanticError(f"ValueError: Mismatched values — Trying to assign a list object inside a comms variable.", node.right.pos_start, node.right.pos_end)

        if not isinstance(value, str):
            raise SemanticError(f"TypeError: Comms variable '{lhs_name}' can only be given a string value.", node.right.pos_start, node.right.pos_end)
        
        if len(value) > 1:
            raise SemanticError(f"ValueError: Comms variable '{lhs_name}' can only be given a single character value.", node.right.pos_start, node.right.pos_end)

        if node.operator != ":":
            raise SemanticError(f"TypeError: Invalid operator '{node.operator}' in comms character assignment statement.", node.pos_start, node.pos_end)
        
        str_list[idx_val] = value

        new_string = ''.join(str_list)
        self.symbol_table.define_var(lhs_name, new_string, lhs_type, lhs_immo)    

    ###### ARRAYS #########
    def visit_ArrayAssignmentStmt(self, node: ArrAssignment):
        if node.right.kind in {'LoadNum', 'Load'} and node.operator != ':':
            raise SemanticError(f"ValueError: loadNum and load function cannot be used in compound assignment statements.", node.right.pos_start, node.right.pos_end)
        
        lhs_name = node.left.left.symbol
        lhs_info = self.symbol_table.lookup(lhs_name, node.left.pos_start, node.left.pos_end)
        if not isinstance(lhs_info, dict) or "dimensions" not in lhs_info:
            raise SemanticError(f"TypeError: '{lhs_name}' is not an array.", node.left.pos_start, node.left.pos_end)
        lhs_immo = lhs_info["immo"]
        lhs_type = lhs_info["type"]
        if lhs_immo==True:
            raise SemanticError(f"ImmoError: '{lhs_name}' is declared as an immutable array.", node.left.left.pos_start, node.left.left.pos_end)
        lhs_data = lhs_info["elements"]
        if lhs_data == None:
            raise SemanticError(f"TypeError: Array '{lhs_name}' is a dead array.", node.left.left.pos_start, node.left.left.pos_end )
        lhs_dim = lhs_info["dimensions"]
        if len(lhs_dim) != len(node.left.index):
            raise SemanticError(f"DimensionError: Mismatched dimensions for array '{lhs_name}'. Expected {len(lhs_dim)}, but got {len(node.left.index)}.", node.left.pos_start, node.left.pos_end)
        
        target = lhs_data
        for i, idx in enumerate(node.left.index[:-1]):
            if idx.kind in {'LoadNum', 'Load'}:
                raise SemanticError(f"IndexError: loadNum and load function cannot be used as index expression.", idx.pos_start, idx.pos_end)
            
            if idx.kind == 'FuncCallStmt':
                idx_val = eval_func(idx.name.symbol, idx, self.symbol_table) 
            else:    
                idx_val = evaluate(idx, self.symbol_table)

            if isinstance(idx_val, UnresolvedNumber):
                idx_val = 0

            if not isinstance(idx_val, int):
                raise SemanticError(f"IndexError: Array index must always evaluate to a positive hp value.", idx.pos_start, idx.pos_end)
            if idx_val < 0 or idx_val >= len(target):
                raise SemanticError(f"IndexError: Index {idx_val} out of bounds for dimension {i} of array '{lhs_name}'.", idx.pos_start, idx.pos_end)
            target = target[idx_val]

        final_idx = node.left.index[-1]
        if final_idx.kind in {'LoadNum', 'Load'}:
                raise SemanticError(f"IndexError: loadNum and load function cannot be used as index expression.", final_idx.pos_start, final_idx.pos_end)
        
        if final_idx.kind == 'FuncCallStmt':
                final_idx_val = eval_func(final_idx.name.symbol, final_idx, self.symbol_table) 
        else:    
            final_idx_val = evaluate(final_idx, self.symbol_table)
        
        if isinstance(final_idx_val, UnresolvedNumber):
            final_idx_val = 0

        if not isinstance(final_idx_val, int):
                raise SemanticError(f"IndexError: Array index must always evaluate to a positive hp value.", final_idx.pos_start, final_idx.pos_end)
        if final_idx_val < 0 or final_idx_val >= len(target):
            raise SemanticError(f"IndexError: Index {final_idx_val} out of bounds for final dimension of array '{lhs_name}'.", final_idx.pos_start, final_idx.pos_end)

        if node.right.kind == 'FuncCallStmt':
            rhs_name = node.right.name.symbol
            return_values = evaluate(node.right, self.symbol_table)
            if len(return_values) > 1:
                raise SemanticError(f"ValueError: Function '{rhs_name}' recalls more than one value, but only one was expected.", node.right.pos_start, node.right.pos_end)
            value = return_values[0]
            if value == []:
                raise SemanticError(f"ValueError: Mismatched values — Trying to assign a list object to an array element.", node.right.pos_start, node.right.pos_end)
        else:
            value = evaluate(node.right, self.symbol_table, self.isRuntime)
        
        if isinstance(value, dict):
            raise SemanticError(f"ValueError: Mismatched values — Trying to assign a list object to an array element.", node.right.pos_start, node.right.pos_end)

        if isinstance (value, UnresolvedNumber):
            if lhs_type == "hp":
                value = 0
            elif lhs_type == "xp":
                value = 0.0    
            else:
                raise SemanticError("TypeError: Trying to assign a numeric value into a non-numeric array.", node.right.pos_start, node.right.pos_end)

        if node.operator in ['+=', '-=', '*=', '/=', '%=']:
            if (isinstance(value, str) and isinstance(target[final_idx_val], bool)) or (isinstance(value, bool) and isinstance(target[final_idx_val], str)):
                raise SemanticError("TypeError: Cannot mix comms and flags in an expression.", node.pos_start, node.pos_end)

            if isinstance(value, str) != isinstance(target[final_idx_val], str):
                raise SemanticError("TypeError: Cannot mix comms and numeric types in an expression.", node.pos_start, node.pos_end)

            if isinstance(target[final_idx_val], str) and node.operator != '+=':
                raise SemanticError("TypeError: Only valid assignment operator between comms is '+='.", node.pos_start, node.pos_end)
            
            operations = {
                '+=': lambda x, y: x + y,
                '-=': lambda x, y: x - y,
                '*=': lambda x, y: x * y,
                '/=': lambda x, y: x / y,
                '%=': lambda x, y: x % y
            }
            
            if node.operator == '/=':
                if isinstance(target[final_idx_val], int) and isinstance(value, int):
                    if value == 0:
                        raise SemanticError("ZeroDivisionError: Division by zero is not allowed.", node.pos_start, node.pos_end)
                    value = int(operations[node.operator](target[final_idx_val], value)) 
                else:
                    if value == 0 or value == 0.0:
                        raise SemanticError("ZeroDivisionError: Division by zero is not allowed.", node.pos_start, node.pos_end)
                    value = operations[node.operator](target[final_idx_val], value)
            elif node.operator == '%=':
                if isinstance(target[final_idx_val], int) and isinstance(value, int):
                    if value == 0:
                        raise SemanticError("ZeroDivisionError: Modulo by zero is not allowed.", node.pos_start, node.pos_end)
                    value = operations[node.operator](target[final_idx_val], value)
                else:
                    raise SemanticError("ModuloError: Only hp values can be used in modulo operation.", node.pos_start, node.pos_end)
            else:
                value = operations[node.operator](target[final_idx_val], value)
            target[final_idx_val] = value
        else:
            target[final_idx_val] = value
        new_val_type = self.TYPE_MAP.get(type(value), str(type(value)))
        if new_val_type != lhs_type:
            raise SemanticError(f"TypeError: Array '{lhs_name}' expects '{lhs_type}' data type, not '{new_val_type}'.", node.left.left.pos_start, node.left.left.pos_end)
        
        self.symbol_table.define_arr(lhs_name, lhs_dim, lhs_data, lhs_immo, lhs_type)
    
    def visit_ArrayRedec(self, node: ArrayRedec):
        arr_name = node.name.symbol
        arr_info = self.symbol_table.lookup(arr_name, node.name.pos_start, node.name.pos_end)
        if not isinstance(arr_info, dict) or "dimensions" not in arr_info:
            raise SemanticError(f"TypeError: '{arr_name}' is not an array.", node.name.pos_start, node.name.pos_end)
        arr_immo = arr_info["immo"]
        arr_type = arr_info["type"]
        arr_dimensions = arr_info["dimensions"]
        if arr_immo==True:
            raise SemanticError(f"ImmoError: '{arr_name}' is declared as an immutable array.", node.name.pos_start, node.name.pos_end)

        if isinstance(node.elements, Identifier):
            rhs_arr = self.symbol_table.lookup(node.elements.symbol, node.elements.pos_start, node.elements.pos_end)
            if not isinstance(rhs_arr, dict) or "elements" not in rhs_arr:
                raise SemanticError(f"ValueError: '{node.elements.symbol}' is not an array.", node.elements.pos_start, node.elements.pos_end)
            
            if rhs_arr["elements"] is None:
                raise SemanticError(f"TypeError: Array '{node.elements.symbol}' is a dead array.", node.elements.pos_start, node.elements.pos_end)
            values = rhs_arr["elements"]
            if len(arr_dimensions) != len(rhs_arr["dimensions"]):
                raise SemanticError(f"DimensionsError: Incorrect number of dimensions.", node.pos_start, node.pos_end)
            if rhs_arr["type"] != arr_type:
                raise SemanticError(f"TypeError: Array '{arr_name}' expects '{arr_type}' datatype. Found '{rhs_arr["type"]}'", node.pos_start, node.pos_end)
            self.symbol_table.define_arr(arr_name, rhs_arr["dimensions"], values, node.immo, arr_type)
        elif isinstance(node.elements, FuncCallStmt):
            return_values = evaluate(node.elements, self.symbol_table)
            print(return_values)
            if len(return_values) > 1:
                raise SemanticError(f"ValueError: Function '{node.elements.name.symbol}' recalls more than one value, but only one was expected.", node.elements.pos_start, node.elements.pos_end)
            rhs_arr = return_values[0]
            if rhs_arr == []:
                if len(arr_dimensions) == 2:
                     self.symbol_table.define_arr(arr_name, arr_dimensions, [[],[]], node.immo, arr_type)
                     return
                else:
                    self.symbol_table.define_arr(arr_name, arr_dimensions, [], node.immo, arr_type)
                    return
            if not isinstance(rhs_arr, dict) or "dimensions" not in rhs_arr:
                raise SemanticError(f"ValueError: Function '{node.elements.name.symbol}' does not recall an array.", node.elements.pos_start, node.elements.pos_end)
            values = rhs_arr["elements"]
            if len(arr_dimensions) != len(rhs_arr["dimensions"]):
                raise SemanticError(f"DimensionsError: Incorrect number of dimensions.", node.elements.pos_start, node.elements.pos_end)
            if rhs_arr["type"] != arr_type:
                raise SemanticError(f"TypeError: Array '{arr_name}' expects '{arr_type}' datatype. Found '{rhs_arr["type"]}'", node.pos_start, node.pos_end)
            self.symbol_table.define_arr(arr_name, rhs_arr["dimensions"], values, node.immo, arr_type)
        else:
            values = []

            if len(node.dimensions) != len(arr_dimensions):
                raise SemanticError(f"DimensionsError: Incorrect number of dimensions.", node.pos_start, node.pos_end)
        
            if len(node.dimensions) == 1:
                for val in node.elements:
                    value = evaluate(val, self.symbol_table)
                    val_type = self.TYPE_MAP.get(type(value), str(type(value)))
                    if val_type != arr_type:
                        raise SemanticError(f"TypeError: Array '{arr_name}' expects '{arr_type}' datatype. Found '{val_type}'", val.pos_start, val.pos_end)
                    values.append(value)
            else:
                for row in node.elements:
                    inner_values = []
                    for val in row:
                        value = evaluate(val, self.symbol_table)
                        val_type = self.TYPE_MAP.get(type(value), str(type(value)))
                        if val_type != arr_type:
                            raise SemanticError(f"TypeError: Array '{arr_name}' expects '{arr_type}' datatype. Found '{val_type}'", val.pos_start, val.pos_end)
                        inner_values.append(value)
                    values.append(inner_values)

            self.symbol_table.define_arr(arr_name, node.dimensions, values, node.immo, arr_type)
    
    def visit_JoinStmt(self, node: JoinStmt):
        arr_name = node.arr_name.symbol
        arr_info = self.symbol_table.lookup(arr_name, node.arr_name.pos_start, node.arr_name.pos_end)
        if not isinstance(arr_info, dict) or "dimensions" not in arr_info:
            raise SemanticError(f"TypeError: '{arr_name}' is not an array.", node.arr_name.pos_start, node.arr_name.pos_end)
        arr_immo = arr_info["immo"]
        arr_type = arr_info["type"]
        arr_dimensions = arr_info["dimensions"]
        arr_elements = arr_info["elements"]

        if arr_elements == None:
            raise SemanticError(f"TypeError: Array '{arr_name}' is a dead array and must be defined with a value first.", node.arr_name.pos_start, node.arr_name.pos_end)

        if arr_immo==True:
            raise SemanticError(f"ImmoError: Array '{arr_name}' is declared as an immutable array.", node.arr_name.pos_start, node.arr_name.pos_end)
        
        if node.dimensions and node.dimensions != len(arr_dimensions):
            raise SemanticError(f"DimensionsError: Incorrect number of dimensions.", node.pos_start, node.pos_end)
        
        row_index = None
        if node.row_index:
            if node.row_index.kind in {'LoadNum', 'Load'}:
                raise SemanticError(f"IndexError: loadNum and load function cannot be used as index expression.", node.row_index.pos_start, node.row_index.pos_end)

            if node.row_index.kind == 'FuncCallStmt':
                row_index = eval_func(node.row_index.name.symbol, node.row_index, self.symbol_table) 
            else:    
                row_index = evaluate(node.row_index, self.symbol_table)

            if isinstance(row_index, UnresolvedNumber):
                row_index = 0

            if not isinstance(row_index, int):
                raise SemanticError(f"IndexError: Array index must always evaluate to a positive hp value.", node.row_index.pos_start, node.row_index.pos_end)

        if isinstance(node.value, list):
            evaluated_row = []
            for value in node.value:
                for v in value:
                    elem = self._evaluate_element(v, arr_name, arr_type, node)
                    evaluated_row.append(elem)
            eval = [evaluated_row]
        else:
            elem = self._evaluate_element(node.value, arr_name, arr_type, node)
        
        if len(arr_dimensions) == 1:  
            if isinstance(elem, list):
                raise SemanticError("ValueError: Cannot append nested lists to a 1D array.", node.pos_start, node.pos_end)
            arr_elements.append(elem)

        elif len(arr_dimensions) == 2:  # 2D array
            if row_index is not None: # id[expr].join(expr)
                if row_index >= len(arr_elements) or row_index < 0:
                    raise SemanticError(f"IndexError: Row index {row_index} out of bounds.", node.row_index.pos_start,node.row_index.pos_end)
                if not isinstance(arr_elements[row_index], list):
                    raise SemanticError(f"ValueError: Target row is not a list.", node.pos_start, node.pos_end)
                arr_elements[row_index].append(elem)
            else:
                if not isinstance(eval, list):
                    raise SemanticError("ValueError: Appending non-row values to a 2D array.", node.pos_start, node.pos_end)
                arr_elements.extend(eval)
        
        self.symbol_table.define_arr(arr_name, arr_dimensions, arr_elements, arr_immo, arr_type)
            
    def _evaluate_element(self, value, arr_name, arr_type, node, is_seek=False):
        if value.kind == 'FuncCallStmt':
            return_values = evaluate(value, self.symbol_table)
            if len(return_values) > 1:
                raise SemanticError(f"ValueError: Function '{value.name.symbol}' recalls more than one value.", value.pos_start, value.pos_end) 
            elem = return_values[0]
            if elem == []:
                if is_seek:
                    raise SemanticError(f"ValueError: Trying to seek a whole array, must be an element or a row only.", value.pos_start, value.pos_end)
                raise SemanticError(f"ValueError: Trying to append an array to an array element.", value.pos_start, value.pos_end)
        elif value.kind in {'LoadNum', 'Load'}:
            if is_seek:
                raise SemanticError(f"UnsupportedArgumentError: loadNum and load function cannot be used as an argument to seek function.", value.pos_start, value.pos_end)
            raise SemanticError(f"ValueError: loadNum and load function cannot be used to append an element to an array.", value.pos_start, value.pos_end)
        else:
            elem = evaluate(value, self.symbol_table)

        if isinstance(elem, UnresolvedNumber):
            if arr_type == 'hp':
                elem = 0
            elif arr_type == 'xp':
                elem = 0
            else:
                if is_seek:
                    raise SemanticError(f"TypeError: Seeking a non-numeric element from a numeric array", value.pos_start, value.pos_end)
                raise SemanticError(f"TypeError: Appending a non-numeric element into a numeric array", value.pos_start, value.pos_end)

        if isinstance(elem, dict):
            if is_seek:
                raise SemanticError(f"ValueError: Trying to seek a list object, must be an element or a row only.", value.pos_start, value.pos_end)
            raise SemanticError(f"ValueError: Trying to append a list object to an array.", node.pos_start, node.pos_end)

        elem_type = self.TYPE_MAP.get(type(elem), str(type(elem)))
        if arr_type != elem_type:
            raise SemanticError(f"TypeError: Array '{arr_name}' expects '{arr_type}' but got '{elem_type}'.", value.pos_start, value.pos_end)

        return elem

    def visit_DropStmt(self, node: DropStmt, is_Return=False):
        arr_name = node.arr_name.symbol   
        arr_info = self.symbol_table.lookup(arr_name, node.arr_name.pos_start, node.arr_name.pos_end)
        if not isinstance(arr_info, dict) or "dimensions" not in arr_info:
            raise SemanticError(f"TypeError: '{arr_name}' is not an array.", node.pos_start, node.pos_end)
        arr_immo = arr_info["immo"]
        arr_type = arr_info["type"]
        arr_dimensions = arr_info["dimensions"]
        arr_elements = arr_info["elements"]

        if arr_elements == None:
            raise SemanticError(f"TypeError: Array '{arr_name}' is a dead array and must be defined with a value first.", node.arr_name.pos_start, node.arr_name.pos_end)
        elif arr_elements == []:
            raise SemanticError(f"TypeError: Array '{arr_name}' is an empty array, there is no value to be dropped.", node.arr_name.pos_start, node.arr_name.pos_end)
        
        if arr_immo==True:
            raise SemanticError(f"ImmoError: Array '{arr_name}' is declared as an immutable array.", node.arr_name.pos_start, node.arr_name.pos_end)
        
        if node.dimensions and node.dimensions != len(arr_dimensions):
            raise SemanticError(f"DimensionsError: Incorrect number of dimensions.", node.pos_start, node.pos_end)
        
        row_index = None
        if node.row_index:
            if node.row_index.kind in {'LoadNum', 'Load'}:
                raise SemanticError(f"IndexError: loadNum and load function cannot be used as index expression.", node.row_index.pos_start, node.row_index.pos_end)
            
            if node.row_index.kind == 'FuncCallStmt':
                row_index = eval_func(node.row_index.name.symbol, node.row_index, self.symbol_table) 
            else:    
                row_index = evaluate(node.row_index, self.symbol_table)

            if isinstance(row_index, UnresolvedNumber):
                row_index = 0

            if not isinstance(row_index, int):
                raise SemanticError(f"IndexError: Array index must always evaluate to a positive hp value.", node.row_index.pos_start, node.row_index.pos_end)
        
        elem_index = None
        if node.elem_index:
            if node.elem_index.kind in {'LoadNum', 'Load'}:
                raise SemanticError(f"IndexError: loadNum and load function cannot be used as index expression.", node.elem_index.pos_start, node.elem_index.pos_end)
            
            if node.elem_index.kind == 'FuncCallStmt':
                elem_index = eval_func(node.elem_index.name.symbol, node.elem_index, self.symbol_table) 
            else:    
                elem_index = evaluate(node.elem_index, self.symbol_table)

            if isinstance(row_index, UnresolvedNumber):
                row_index = 0

            if not isinstance(elem_index, int):
                raise SemanticError(f"IndexError: Array index must always evaluate to a positive hp value.", node.elem_index.pos_start, node.elem_index.pos_end)

        if len(arr_dimensions) == 1:  
            if elem_index is not None:
                if elem_index >= len(arr_elements) or elem_index < 0:
                    raise SemanticError(f"IndexError: Index {elem_index} out of bounds for array '{arr_name}'.", node.elem_index.pos_start, node.elem_index.pos_end)
                ret = arr_elements.pop(elem_index)
            else:
                ret = arr_elements.pop()  
            
            if is_Return:
                    self.symbol_table.define_arr(arr_name, arr_dimensions, arr_elements, arr_immo, arr_type)
                    return ret
        
        elif len(arr_dimensions) == 2: 
            if row_index is not None:
                if row_index >= len(arr_elements) or row_index < 0:
                    raise SemanticError(f"IndexError: Row index {row_index} out of bounds for array '{arr_name}'.", 
                                        node.row_index.pos_start, node.row_index.pos_end)
                if not isinstance(arr_elements[row_index], list):
                    raise SemanticError(f"TypeError: Target row '{row_index}' is not a list.")

                if elem_index is not None:
                    if elem_index >= len(arr_elements[row_index]) or elem_index < 0:
                        raise SemanticError(f"IndexError: Index {elem_index} out of bounds for row {row_index} in array '{arr_name}'.", 
                                            node.elem_index.pos_start, node.elem_index.pos_end)
                    ret = arr_elements[row_index].pop(elem_index)
                else:
                    ret = arr_elements[row_index].pop()  
            else:
                if is_Return:
                    raise SemanticError("ReturnError: Cannot remove and return an entire row of a 2D array.", node.pos_start, node.pos_end)
                if elem_index is not None:
                    if elem_index >= len(arr_elements) or elem_index < 0:
                        raise SemanticError(f"IndexError: Row index {elem_index} out of bounds for array '{arr_name}'.", 
                                            node.row_index.pos_start, node.row_index.pos_end)
                    arr_elements.pop(elem_index)
                else:
                    arr_elements.pop()  
            
            if is_Return:
                    self.symbol_table.define_arr(arr_name, arr_dimensions, arr_elements, arr_immo, arr_type)
                    return ret
            
        self.symbol_table.define_arr(arr_name, arr_dimensions, arr_elements, arr_immo, arr_type)

    def visit_SeekStmt(self, node: SeekStmt):
        arr_name = node.arr_name.symbol
        arr_info = self.symbol_table.lookup(arr_name, node.arr_name.pos_start, node.arr_name.pos_end)
        if not isinstance(arr_info, dict) or "dimensions" not in arr_info:
            raise SemanticError(f"TypeError: '{arr_name}' is not an array.", node.pos_start, node.pos_end)
        arr_type = arr_info["type"]
        arr_dimensions = arr_info["dimensions"]
        arr_elements = arr_info["elements"]

        if arr_elements == None:
            raise SemanticError(f"TypeError: Array '{arr_name}' is a dead array and must be defined with a value first.", node.arr_name.pos_start, node.arr_name.pos_end)
        elif arr_elements == []:
            raise SemanticError(f"TypeError: Array '{arr_name}' is an empty array, there is no value to be seeked.", node.arr_name.pos_start, node.arr_name.pos_end)
        
        if node.dimensions and node.dimensions != len(arr_dimensions):
            raise SemanticError(f"DimensionsError: Incorrect number of dimensions.", node.pos_start, node.pos_end)
        
        row_index = None
        if node.row_index:
            if node.row_index.kind in {'LoadNum', 'Load'}:
                raise SemanticError(f"IndexError: loadNum and load function cannot be used as index expression.", node.row_index.pos_start, node.row_index.pos_end)

            if node.row_index.kind == 'FuncCallStmt':
                row_index = eval_func(node.row_index.name.symbol, node.row_index, self.symbol_table) 
            else:    
                row_index = evaluate(node.row_index, self.symbol_table)

            if isinstance(row_index, UnresolvedNumber):
                row_index = 0

            if not isinstance(row_index, int):
                raise SemanticError(f"IndexError: Array index must always evaluate to a positive hp value.", node.row_index.pos_start, node.row_index.pos_end)

        if isinstance(node.value, list):
            evaluated_row = []
            for value in node.value:
                for v in value:
                    elem = self._evaluate_element(v, arr_name, arr_type, node, True)
                    evaluated_row.append(elem)
        else:
            elem = self._evaluate_element(node.value, arr_name, arr_type, node, True)

        if len(arr_dimensions) == 1:  
            if isinstance(elem, list):
                raise SemanticError("ValueError: Cannot seek multiple values in a 1d array.", node.pos_start, node.pos_end)
            try:
                return arr_elements.index(elem)
            except ValueError:
                return -1
        
        elif len(arr_dimensions) == 2:  # 2D array
            if row_index is not None:   # id: id[expr].seek(expr)
                start = [node.row_index.pos_start[0], node.row_index.pos_start[1]-1]
                end = [node.row_index.pos_end[0], node.row_index.pos_end[1]+(len(str(row_index)))]
                if row_index >= len(arr_elements) or row_index < 0:
                    raise SemanticError(f"IndexError: Row index {row_index} out of bounds.", start, end)
                if not isinstance(arr_elements[row_index], list):
                    raise SemanticError(f"ValueError: Target row is not a list.", start, end)
                
                try:
                    return arr_elements[row_index].index(elem)
                except ValueError:
                    return -1
            
            else:   # id: id.seek([elems elems_recur])
                if not isinstance(evaluated_row, list):
                    raise SemanticError("ValueError: Cannot seek a specific element in a 2d array without specifying the index.", node.pos_start, node.pos_end)    
                try:
                    return arr_elements.index(evaluated_row)
                except ValueError:
                    return -1
                
    def visit_RoundStmt(self, node: RoundStmt):
        if node.value.kind == 'FuncCallStmt':
            info = eval_func(node.value.name.symbol, node.value, self.symbol_table) 
        else:    
            info = evaluate(node.value, self.symbol_table)

        if isinstance(info, UnresolvedNumber):
            raise SemanticError(f"TypeError: Can only use rounds function on comms and arrays.", node.pos_start, node.pos_end)

        print(f"rounds info -> {info}")
        if isinstance(info, dict):
            if "dimensions" not in info:
                raise SemanticError(f"TypeError: Can only use rounds function on comms and arrays.", node.pos_start, node.pos_end)
            
            return len(info["elements"])
        
        if not isinstance(info, str):
            raise SemanticError(f"TypeError: Can only use rounds function on comms and arrays.", node.pos_start, node.pos_end)
        
        return len(info)

    ###### STRUCTS #########
    def visit_StructInst(self, node: StructInst):
        structinst = self.symbol_table.lookup(node.name.symbol, node.name.pos_start, node.name.pos_end)
        structparent = self.symbol_table.lookup(structinst["parent"], node.pos_start, node.pos_end)
        
        fields = structinst["fields"]
        field_names = list(structparent.keys())
        struct_fields = []

        if len(fields) > len(field_names):
            first = node.body[0]
            last = node.body[-1]
            raise SemanticError(f"FieldError: Too many values provided for struct '{structinst["parent"]}'." 
                                f" Expected {len(structparent)}, got {len(structinst["fields"])}.", first.pos_start, last.pos_end)
        
        for i, field in enumerate(field_names):
            default_value = structparent[field]["value"]
            expected_type = structparent[field]["datatype"]

            if i < len(fields):
                field_to_eval = fields[i]
                value_to_use = evaluate(field_to_eval, self.symbol_table)
                actual_type = self.TYPE_MAP.get(type(value_to_use), None)
                if actual_type != expected_type:
                    raise SemanticError(f"TypeError: Type mismatch for field '{field}'." 
                                      f" Expected '{expected_type}', but got '{actual_type}'.", 
                                      field_to_eval.pos_start, field_to_eval.pos_end)
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
        if node.right.kind in {'LoadNum', 'Load'} and node.operator != ':':
            raise SemanticError(f"ValueError: loadNum and load function cannot be used in compound assignment statements.", node.right.pos_start, node.right.pos_end)
        
        structinst = self.symbol_table.lookup(node.left.instance.symbol, node.left.instance.pos_start, node.left.instance.pos_end)
        if not isinstance(structinst, dict) or "fields" not in structinst:
            raise SemanticError(f"TypeError: '{node.left.instance.symbol}' is not a struct instance.", node.left.instance.pos_start, node.left.instance.pos_end)
        
        if structinst["immo"] == True:
            raise SemanticError(f"ImmoError: '{node.left.instance.symbol}' is declared as an immutable struct instance.", 
                                node.left.instance.pos_start, node.left.instance.pos_end)
        field_names = [field["name"] for field in structinst["fields"]]
        new_field = node.left.field.symbol
        
        if new_field not in field_names:
            raise SemanticError(f"NameError: Field '{new_field}' does not exist "
                                f"in struct instance '{node.left.instance.symbol}'.", node.left.field.pos_start, node.left.field.pos_end)
        
        if node.right.kind == 'FuncCallStmt':
            rhs_name = node.right.name.symbol
            return_values = evaluate(node.right, self.symbol_table)
            if len(return_values) > 1:
                raise SemanticError(f"ValueError: Function '{rhs_name}' recalls more than one value, but only one was expected.", node.right.pos_start, node.right.pos_end)
            value = return_values[0]
            if value == []:
                raise SemanticError(f"ValueError: Mismatched values — Trying to assign a list object to a struct instance field.", node.right.pos_start, node.right.pos_end)
        else:
            value = evaluate(node.right, self.symbol_table, self.isRuntime)

        if isinstance(value, dict):
            raise SemanticError(f"ValueError: Mismatched values — Trying to assign a list object to a struct instance field.", node.right.pos_start, node.right.pos_end)
        
        for field in structinst["fields"]:
            if new_field == field["name"]:
                old_type = self.TYPE_MAP.get(type(field["value"]), None)
                if isinstance(new_val, UnresolvedNumber):
                    if old_type == "hp":
                        new_val = 0
                    elif old_type == "xp":
                        new_val = 0.0
                    else:
                        raise SemanticError("TypeError: Using loadNum function to assign a non-numeric instance field.", node.right.pos_start, node.right.pos_end)
                if node.operator in ['+=', '-=', '*=', '/=', '%=']:

                    if (isinstance(new_val, str) and isinstance(field["value"], bool)) or (isinstance(new_val, bool) and isinstance(field["value"], str)):
                        raise SemanticError("TypeError: Cannot mix comms and flags in an expression.", node.pos_start, node.pos_end)

                    if isinstance(new_val, str) != isinstance(field["value"], str):
                        raise SemanticError("TypeError: Cannot mix comms and numeric types in an expression.", node.pos_start, node.pos_end)

                    if isinstance(new_val, str) and node.operator != '+=':
                        raise SemanticError("TypeError: Only valid assignment operator between comms is '+='.", node.pos_start, node.pos_end)

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
                                raise SemanticError("ZeroDivisionError: Division by zero is not allowed", node.pos_start, node.pos_end)
                            new_val = int(operations[node.operator](field["value"], new_val)) 
                        else:
                            if new_val == 0 or new_val == 0.0:
                                raise SemanticError("ZeroDivisionError: Division by zero is not allowed", 
                                                    node.pos_start, node.pos_end)
                            new_val = operations[node.operator](field["value"], new_val)
                    elif node.operator == '%=':
                        if isinstance(field["value"], int) and isinstance(new_val, int):
                            if new_val == 0:
                                raise SemanticError("ZeroDivisionError: Modulo by zero is not allowed."
                                                    , node.pos_start, node.pos_end)
                            new_val = operations[node.operator](field["value"], new_val)
                        else:
                            raise SemanticError("ModuloError: Only hp values can be used in modulo operation.", node.pos_start, node.pos_end)
                    else:
                        new_val = operations[node.operator](field["value"], new_val)
                else:
                    new_val = new_val
                
                new_type = self.TYPE_MAP.get(type(new_val), None)
                if old_type != new_type:
                    raise SemanticError(f"TypeError: Type mismatch for field '{field["name"]}'."
                                        f" Expected '{old_type}', but got '{new_type}'.", node.pos_start, node.pos_end)
                field["value"] = new_val
        
        self.symbol_table.define_structinst(node.left.instance.symbol, structinst["parent"], structinst["fields"], structinst["immo"])

    ###### COND #########
    def visit_IfStmt(self, node: IfStmt):
        conditions = []

        if node.condition.kind == 'FuncCallStmt':
            if_condition = eval_func(node.condition.name.symbol, node.condition, self.symbol_table) 
        elif node.condition.kind in {'Load', 'LoadNum'}:
            raise SemanticError(f"TypeError: Cannot use load and loadNum function as condition.", node.condition.pos_start, node.condition.pos_end)
        else:    
            if_condition = evaluate(node.condition, self.symbol_table)

        if not isinstance(if_condition, bool):
            raise SemanticError("TypeError: The condition used does not evaluate to a flag value.", node.condition.pos_start, node.condition.pos_end)
        conditions.append([if_condition, node.then_branch])
        if node.elif_branches is not None:
            for cond in node.elif_branches:

                if cond.condition.kind == 'FuncCallStmt':
                    elif_condition = eval_func(cond.condition.name.symbol, cond.condition, self.symbol_table) 
                elif cond.condition.kind in {'Load', 'LoadNum'}:
                    raise SemanticError(f"TypeError: Cannot use load and loadNum function as condition.", cond.condition.pos_start, cond.condition.pos_end)
                else:    
                    elif_condition = evaluate(cond.condition, self.symbol_table)

                if not isinstance(elif_condition, bool):
                    raise SemanticError("TypeError: The condition used does not evaluate to a flag value.", cond.condition.pos_start, cond.condition.pos_end)
                conditions.append([elif_condition, cond.body])
        
        for cond in conditions:
            if cond[0] == True:
                prev_stack = [scope.copy() for scope in self.symbol_table.scope_stack]
                if self.in_func_flag:
                    self.symbol_table.restore_scope(len(self.symbol_table.saved_scopes) - 1)
                else:
                    self.symbol_table.restore_scope(len(self.symbol_table.scope_stack))
                
                new_scope = self.symbol_table.scope_stack    
                for scope in prev_stack:
                    for name, value in scope.items():
                        if name in new_scope[-1]:
                            new_scope[-1][name] = value  
                
                for stmt in cond[1]:
                    self.visit(stmt, is_runtime=self.isRuntime)
                    if self.recall_flag and self.in_func_flag:
                        self.symbol_table.exit_scope(True)
                        return
                    if self.checkpoint_flag:
                        self.symbol_table.exit_scope(True)
                        return

                    if self.resume_flag:
                        self.symbol_table.exit_scope(True)
                        return
                
                self.symbol_table.exit_scope(True)
                return
        
        if node.else_branch is not None:
            prev_stack = [scope.copy() for scope in self.symbol_table.scope_stack]
            if self.in_func_flag:
                self.symbol_table.restore_scope(len(self.symbol_table.saved_scopes) - 1)
            else:
                self.symbol_table.restore_scope(len(self.symbol_table.scope_stack))
                
            new_scope = self.symbol_table.scope_stack    
            for scope in prev_stack:
                 for name, value in scope.items():
                    if name in new_scope[-1]:
                        new_scope[-1][name] = value  

            for stmt in node.else_branch:
                self.visit(stmt, is_runtime=self.isRuntime)
                if self.recall_flag and self.in_func_flag:
                    self.symbol_table.exit_scope(True)
                    return
                if self.checkpoint_flag:
                    self.symbol_table.exit_scope(True)
                    return

                if self.resume_flag:
                    self.symbol_table.exit_scope(True)
                    return

            self.symbol_table.exit_scope(True)

    def visit_FlankStmt(self, node: FlankStmt):
        if node.expression.kind == 'FuncCallStmt':
            expression = eval_func(node.expression.name.symbol, node.expression, self.symbol_table) 
        elif node.expression.kind in {'Load', 'LoadNum'}:
            raise SemanticError(f"TypeError: Cannot use load and loadNum as flank expression.", node.expression.pos_start, node.expression.pos_end)
        else:    
            expression = evaluate(node.expression, self.symbol_table)

        for choice in node.choices:
            for choice_value in choice.values:
                value = evaluate(choice_value, self.symbol_table)
                if value == expression or ((value == 0 or value == 0.0) and isinstance(expression, UnresolvedNumber)):
                    prev_stack = [scope.copy() for scope in self.symbol_table.scope_stack]
                    if self.in_func_flag:
                        self.symbol_table.restore_scope(len(self.symbol_table.saved_scopes) - 1)
                    else:
                        self.symbol_table.restore_scope(len(self.symbol_table.scope_stack))
                    
                    new_scope = self.symbol_table.scope_stack    
                    for scope in prev_stack:
                        for scope_name, scope_val in scope.items():
                            if scope_name in new_scope[-1]:
                                new_scope[-1][scope_name] = scope_val  

                    for stmt in choice.body:
                        #print(f"runtime before flank: {self.isRuntime}")
                        self.visit(stmt, is_runtime=self.isRuntime)
                        if self.recall_flag and self.in_func_flag:
                            self.symbol_table.exit_scope(True)
                            return
                    if self.resume_flag:  
                        self.resume_flag = False
                        self.symbol_table.exit_scope(True)
                        break
                    self.symbol_table.exit_scope(True)
                    return

        prev_stack = [scope.copy() for scope in self.symbol_table.scope_stack]
        if self.in_func_flag:
            self.symbol_table.restore_scope(len(self.symbol_table.saved_scopes) - 1)
        else:
            self.symbol_table.restore_scope(len(self.symbol_table.scope_stack))
                    
        new_scope = self.symbol_table.scope_stack    
        for scope in prev_stack:
            for scope_name, scope_val in scope.items():
                if scope_name in new_scope[-1]:
                    new_scope[-1][scope_name] = scope_val  

        for stmt in node.backup_body:
            self.visit(stmt, is_runtime=self.isRuntime)
            if self.recall_flag and self.in_func_flag:
                self.symbol_table.exit_scope(True)
                return
        self.symbol_table.exit_scope(True)

    ###### LOOP #########
    def visit_ForStmt(self, node: ForStmt):
        val_name = node.initialization.left.symbol
        value = self.symbol_table.lookup(val_name, node.initialization.left.pos_start, node.initialization.left.pos_end)

        if not isinstance(value, dict):
            datatype = self.TYPE_MAP.get(type(value), str(type(value)))
            self.symbol_table.define_var(val_name, value, datatype, False)
            value = self.symbol_table.lookup(node.left.symbol, node.left.pos_start, node.left.pos_end)

        if "value" not in value:
            raise SemanticError(f"ValueError: Mismatched types — trying to assign a single value from to a list object, '{val_name}'", 
                                node.initialization.pos_start, node.initialization.pos_end)

        value_type = value["type"]
        if value["immo"]==True:
            raise SemanticError(f"TypeError: '{val_name}' is declared as an immutable variable.", node.initialization.pos_start, node.initialization.pos_end) 
        
        if node.initialization.right.kind == 'FuncCallStmt':
            new_val = eval_func(node.initialization.right.name.symbol, node.initialization.right, self.symbol_table) 
        elif node.initialization.right.kind in {'Load', 'LoadNum'}:
            raise SemanticError(f"LoopControlError: Cannot use load and loadNum in loop control initialization.", node.initialization.right.pos_start, node.initialization.right.pos_end)
        else:    
            new_val = evaluate(node.initialization.right, self.symbol_table)
        
        if value_type != "hp" or not isinstance(new_val, int):
            raise SemanticError(f"LoopControlError: Only hp variables can be used for loop control.", node.initialization.pos_start, node.initialization.pos_end)
        self.symbol_table.define_var(val_name, new_val, value_type, value["immo"])
        
        if node.condition.kind == 'FuncCallStmt':
            condition = eval_func(node.condition.name.symbol, node.condition, self.symbol_table) 
        elif node.condition.kind in {'Load', 'LoadNum'}:
            raise SemanticError(f"TypeError: Cannot use load and loadNum function as condition.", node.condition.pos_start, node.condition.pos_end)
        else:    
            condition = evaluate(node.condition, self.symbol_table)

        if not isinstance(condition, bool):
            raise SemanticError(f"LoopConditionError: Loop condition does not evaluate to a flag value.", node.condition.pos_start, node.condition.pos_end)
        
        if condition:
            prev_stack = [scope.copy() for scope in self.symbol_table.scope_stack]
            if self.in_func_flag:
                self.symbol_table.restore_scope(len(self.symbol_table.saved_scopes) - 1)
            else:
                self.symbol_table.restore_scope(len(self.symbol_table.scope_stack))
            
            def eval_cond(cond):
                if cond.kind == 'FuncCallStmt':
                    return eval_func(cond.name.symbol, cond, self.symbol_table) 
                else:    
                    return evaluate(cond, self.symbol_table)
                
            new_scope = self.symbol_table.scope_stack    
            for scope in prev_stack:
                 for scope_name, scope_val in scope.items():
                    if scope_name in new_scope[-1]:
                        new_scope[-1][scope_name] = scope_val
            
            while eval_cond(node.condition):
                for stmt in node.body:
                    self.visit(stmt, is_runtime=self.isRuntime)
                    if self.recall_flag and self.in_func_flag:
                        self.symbol_table.exit_scope(True)
                        return
                    if self.checkpoint_flag:
                        self.checkpoint_flag = False
                        self.symbol_table.exit_scope(True)
                        self.symbol_table.define_var(val_name, value["value"], value_type, value["immo"])
                        return
                    if self.resume_flag:
                        self.resume_flag = False
                        continue 
                self.visit_VarAssignmentStmt(node.update)
            self.symbol_table.exit_scope(True)
            
        self.symbol_table.define_var(val_name, value["value"], value_type, value["immo"])
    
    def visit_GrindWhileStmt(self, node: GrindWhileStmt):
        it_ran = False
        if node.condition.kind == 'FuncCallStmt':
            condition = eval_func(node.condition.name.symbol, node.condition, self.symbol_table) 
        elif node.condition.kind in {'Load', 'LoadNum'}:
            raise SemanticError(f"TypeError: Cannot use load and loadNum function as condition.", node.condition.pos_start, node.condition.pos_end)
        else:    
            condition = evaluate(node.condition, self.symbol_table)

        if not isinstance(condition, bool):
            raise SemanticError(f"LoopConditionError: Loop condition does not evaluate to a flag value.", node.condition.pos_start, node.condition.pos_end)
        
        if node.is_grind:
            it_ran = True
            prev_stack = [scope.copy() for scope in self.symbol_table.scope_stack]
            if self.in_func_flag:
                self.symbol_table.restore_scope(len(self.symbol_table.saved_scopes) - 1)
            else:
                self.symbol_table.restore_scope(len(self.symbol_table.scope_stack))
            
            new_scope = self.symbol_table.scope_stack    
            for scope in prev_stack:
                 for name, value in scope.items():
                    if name in new_scope[-1]:
                        new_scope[-1][name] = value  

            for stmt in node.body:
                self.visit(stmt, is_runtime=self.isRuntime)
                if self.recall_flag and self.in_func_flag:
                    self.symbol_table.exit_scope(True)
                    return
                if self.checkpoint_flag:
                    self.checkpoint_flag = False
                    self.symbol_table.exit_scope(True)
                    return
                if self.resume_flag:
                    self.resume_flag = False
        elif not node.is_grind and condition:
            it_ran = True
            prev_stack = [scope.copy() for scope in self.symbol_table.scope_stack]
            if self.in_func_flag:
                self.symbol_table.restore_scope(len(self.symbol_table.saved_scopes) - 1)
            else:
                self.symbol_table.restore_scope(len(self.symbol_table.scope_stack))
            
            new_scope = self.symbol_table.scope_stack    
            for scope in prev_stack:
                 for name, value in scope.items():
                    if name in new_scope[-1]:
                        new_scope[-1][name] = value  
            
        def eval_cond(cond):
            if cond.kind == 'FuncCallStmt':
                return eval_func(cond.name.symbol, cond, self.symbol_table) 
            else:    
                return evaluate(cond, self.symbol_table)

        while eval_cond(node.condition):
            for stmt in node.body:
                self.visit(stmt, is_runtime=self.isRuntime)
                if self.checkpoint_flag:
                    self.checkpoint_flag = False
                    self.symbol_table.exit_scope(True)
                    return
                if self.resume_flag:
                    self.resume_flag = False
                    continue 
            if node.condition.kind == 'FlagLiteral':
                if not self.isRuntime:
                    if node.condition.value == True:
                        break
        if it_ran:
            self.symbol_table.exit_scope(True)
    
    ###### FUNCS #########
    def visit_BlockStmt(self, node: BlockStmt):
        self.symbol_table.restore_scope(len(self.symbol_table.scope_stack))
        for stmt in node.statements:
            self.visit(stmt, is_runtime=self.isRuntime)
        self.symbol_table.play_scope = self.symbol_table.scope_stack.copy()
        self.symbol_table.exit_scope(True)  

    def visit_ResumeStmt(self, node: ResumeStmt):
        self.resume_flag = True 

    def visit_CheckpointStmt(self, node: CheckpointStmt):
        self.checkpoint_flag = True   

    def visit_GlobalFuncDec(self, node: GlobalFuncDec):
        pass

    def visit_GlobalFuncBody(self, node: GlobalFuncBody):
        pass

    def visit_FuncCallStmt(self, node: FuncCallStmt, being_assigned = False, func_is_runtime=False):
        print(f"in func call and runtime is {self.isRuntime}")
        if func_is_runtime:
            self.isRuntime = func_is_runtime
        print(f"in func call and runtime is now {self.isRuntime}")
        self.recall_values = []
        prev_stack = [scope.copy() for scope in self.symbol_table.scope_stack]
        prev_saved_stack = [scope.copy() for scope in self.symbol_table.saved_scopes]
        args = []
        if node.args:
            for arg in node.args:
                if arg.kind in ['Load', 'LoadNum']:
                    raise SemanticError("UnsupportedArgumentError: Cannot use load and loadNum function as a function argument.", arg.pos_start, arg.pos_end)
                if arg.kind == 'FuncCallStmt':
                    value = eval_func(arg.name.symbol, arg, self.symbol_table) 
                else:    
                    value = evaluate(arg, self.symbol_table)
                
                args.append(value)
        
        self.symbol_table.restore_scope_func(node.name.symbol)
       
        info = self.symbol_table.lookup(node.name.symbol, node.name.pos_start, node.name.pos_end)
        if not info:
            raise SemanticError(f"NameError: Function '{node.name.symbol}' is not defined.", node.name.pos_start, node.name.pos_end)

        param_scope = {}
        params = info["params"]

        if node.args and not params:
            raise SemanticError(f"TypeError: Function '{node.name.symbol}' does not take any arguments, but {len(node.args)} were provided.", node.arg_pos_start, node.arg_pos_end)
       
        if params:
            if len(args) > len(params):
                raise SemanticError(f"TypeError: Function '{node.name.symbol}' expects {len(params)} arguments, got {len(args)}.", node.arg_pos_start, node.arg_pos_end)
            
            for i, param in enumerate(params):
                if i < len(args):  
                    arg_value = args[i]
                    print(f"arg value -> {arg_value}") 
                elif param.param_val is not None:
                    arg_value = evaluate(param.param_val, self.symbol_table)
                else:
                    raise SemanticError(f"TypeError: Missing argument for parameter '{param.param}' and no default value provided.", node.pos_start, node.pos_end)
            
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
            self.visit(stmt, is_runtime=self.isRuntime)
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
            raise SemanticError(f"RecallError: Function '{node.name.symbol}' has a recall value but is not being assigned anywhere.", node.pos_start, node.pos_end)
        elif self.recall_values:
            return self.recall_values

    def visit_RecallStmt(self, node: RecallStmt):
        self.recall_values = []
        if len(node.expressions) == 1 and node.expressions[0] == "void":
            self.recall_values = None
        else:
            for expr in node.expressions:
                #print(expr)
                if expr == []:
                    self.recall_values.append([])
                    self.recall_flag = True
                    break
                if expr.kind in {'Load', 'LoadNum'}:
                    raise SemanticError(f"ValueError: Using load and loadNum in recall is not allowed.", node.pos_start, node.pos_end)
                
                if expr.kind == 'FuncCallStmt':
                    value = eval_func(expr.name.symbol, expr, self.symbol_table) 
                else:    
                    value = evaluate(expr, self.symbol_table)

                self.recall_values.append(value)
        self.recall_flag = True

    ###### BUILT-IN #########
    def visit_ShootStmt(self, node: ShootStmt):
        if node.element.kind in ['Load', 'LoadNum']:
            raise SemanticError("UnsupportedArgumentError: load and loadNum function are an invalid argument for shoot and shootNxt function.", node.element.pos_start, node.element.pos_end)
        
        if node.element.kind == 'FuncCallStmt':
            element = eval_func(node.element.name.symbol, node.element, self.symbol_table) 
        else:    
            element = evaluate(node.element, self.symbol_table)
        
        #print(f"shoot element is {element} before and node element is {node.element}")
        if isinstance(element, UnresolvedNumber):
            element = '0 or 0.0'
        elif not isinstance(element, dict):
            element=element
        elif element is None:
            element = 'dead'
        elif "value" in element:
            element = element["value"]
        elif "elements" in element or "fields" in element:
            raise SemanticError("UnsupportedArgumentError: Cannot use a list object as a shoot argument.", node.pos_start, node.pos_end)
            
        print(f"shoot element -> {element}.")
        if self.isRuntime:
            if isinstance(element, float):
                whole_part = str(int(abs(element)))
                if len(whole_part) > 10:
                    raise SemanticError("TypeError: Whole number part of xp exceeds 10 digits.", node.pos_start, node.pos_end)
                
                element = round(element, 7)
                element = f"{element:.7f}".rstrip('0').rstrip('.') if '.' in f"{element:.7f}" else f"{element:.7f}"

            elif isinstance(element, int):
                if len(str(abs(element))) > 10:
                    raise SemanticError("TypeError: Hp value exceeds 10 digits.", node.pos_start, node.pos_end)

            if node.is_Next:
                print_shoot(str(element) + "\n")
            else:
                print_shoot(str(element))

    def visit_LevelStmt(self, node: LevelStmt):
        if node.value.kind == 'FuncCallStmt':
            info = eval_func(node.value.name.symbol, node.value, self.symbol_table) 
        else:    
            info = evaluate(node.value, self.symbol_table)

        if not isinstance(info, str):
            function_name = "levelUp" if node.up_or_down else "levelDown"
            raise SemanticError(f"TypeError: Can only use {function_name} function on comms.", node.pos_start, node.pos_end)

        return info.upper() if node.up_or_down else info.lower()
    
    def visit_ToNumStmt(self, node: ToNumStmt):
        info = evaluate(node.value, self.symbol_table)

        print(f"info -> {info}")
        
        if isinstance(info, UnresolvedNumber):
            return 0 if node.hp_or_xp else 0.0
        
        if isinstance(info, dict):
            raise SemanticError(f"TypeError: Cannot convert a list object to a number.", node.pos_start, node.pos_end)

        if isinstance(info, str):
            if node.hp_or_xp:  
                if not info.isdigit():
                    raise SemanticError(f"TypeError: Cannot convert '{info}' to an hp — must be a whole number.", node.pos_start, node.pos_end)
                return int(info)
            else: 
                try:
                    return float(info)
                except ValueError:
                    raise SemanticError(f"TypeError: Cannot convert '{info}' to an xp — must be a valid floating-point number.", node.pos_start, node.pos_end)

        if isinstance(info, bool):
            if node.hp_or_xp:
                return 1 if info else 0
            else:
                return 1.0 if info else 0.0
        
        if isinstance(info, int):
            return info if node.hp_or_xp else float(info)

        if isinstance(info, float):
            return int(info) if node.hp_or_xp else info

        raise SemanticError(f"TypeError: Cannot convert '{info}' to a number.", node.pos_start, node.pos_end)

    def visit_ToCommsStmt(self, node: ToCommsStmt):
        info = evaluate(node.value, self.symbol_table)
        
        if isinstance(info, UnresolvedNumber):
            return "0 or 0.0"
        
        if isinstance(info, dict):
            raise SemanticError(f"TypeError: Cannot convert a list object to comms.", node.pos_start, node.pos_end)

        if isinstance(info, bool):
            return "true" if info else "false"
        
        if isinstance(info, str):
            return info

        if isinstance(info, int) or isinstance(info, float):
            return str(info)
        raise SemanticError(f"TypeError: Cannot convert '{info}' to comms.", node.pos_start, node.pos_end)

########################################
####### RUNTIME OF TRAVERSER ###########
########################################


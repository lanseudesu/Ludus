from .symbol_table import SymbolTable
from ..error import SemanticError
import eel
import time

symbol_table = SymbolTable()
input_value = None
stopper = False
current_run_id = 0
test_flag = False

class UnresolvedNumber:
    def __init__(self, possible_types=("int", "float")):
        self.possible_types = possible_types
    
    def __repr__(self):
        return "0 or 0.0"

@eel.expose
def pass_input(value): # receives input from js
    global input_value
    print(f"Received input from frontend: {value}")
    input_value = value  

@eel.expose
def get_input_from_frontend(prompt="Enter value"): # pass input to js
    print(f"Prompting user: {prompt}")
    eel.requestInput(prompt)  

@eel.expose
def reset_interpreter():
    global input_value, stopper, current_run_id
    input_value = None
    stopper = False
    current_run_id += 1

def eval_func(name, node, symbol_table):
    return_values = evaluate(node, symbol_table)
    if len(return_values) > 1:
        raise SemanticError(f"ValueError: Function '{name}' recalls more than one value, but only one was expected.", node.pos_start, node.pos_end)
    value = return_values[0]
    if value == []:
        raise SemanticError(f"ValueError: Function '{name}' is recalling an array.", node.pos_start, node.pos_end)
    if isinstance(value, list):
        value = value[0]

    return value

def evaluate(ast_node, symbol_table, isRuntime=False):
    from .traverser import SemanticAnalyzer 
    traverser = SemanticAnalyzer(symbol_table, isRuntime)
    global input_value
    global stopper
    global test_flag
    
    TYPE_MAP = {
        int: "hp",
        float: "xp",
        str: "comms",
        bool: "flag",
        dict: "array",
        type(None): "dead"
    }

    if ast_node.kind == "HpLiteral":
        return ast_node.value
    elif ast_node.kind == "XpLiteral":
        return ast_node.value
    elif ast_node.kind == "CommsLiteral":
        return ast_node.value
    elif ast_node.kind == "FlagLiteral":
        return ast_node.value
    elif ast_node.kind == "BinaryExpr":
        return eval_binary_expr(ast_node, symbol_table)
    elif ast_node.kind == "ChainRelatExpr":
        return eval_chain_relat_expr(ast_node, symbol_table)
    elif ast_node.kind == "Identifier":
        value = symbol_table.lookup(ast_node.symbol, ast_node.pos_start, ast_node.pos_end)
        # print(value)
        if value is None:
            return value
        if not isinstance(value, dict):
            return value
        if "value" in value:
            return value["value"]
        elif "elements" in value or "fields" in value:
            return value
    
    elif ast_node.kind == 'StructInstField':
        
        structinst = symbol_table.lookup(ast_node.instance.symbol, ast_node.instance.pos_start, ast_node.instance.pos_end)
        if not isinstance(structinst, dict) or "fields" not in structinst:
            raise SemanticError(f"TypeError: '{ast_node.instance.symbol}' is not a struct instance.", 
                                ast_node.instance.pos_start, ast_node.instance.pos_end)
        for fld in structinst["fields"]:
            if fld["name"] == ast_node.field.symbol:
                return fld["value"]
        raise SemanticError(f"NameError: Field '{ast_node.field.symbol}' is not defined in struct instance '{ast_node.instance.symbol}'.", 
                            ast_node.field.pos_start, ast_node.field.pos_end)
    
    elif ast_node.kind == 'ArrayElement':
        arr_name = ast_node.left.symbol
        arr = symbol_table.lookup(arr_name, ast_node.left.pos_start, ast_node.left.pos_end)

        if not isinstance(arr, dict) or "dimensions" not in arr:
            raise SemanticError(f"TypeError: '{arr_name}' is not an array.", 
                                ast_node.left.pos_start, ast_node.left.pos_end)
        if len(ast_node.index) != len(arr["dimensions"]):
            raise SemanticError(f"ArrayIndexError: Incorrect number of dimensions for {arr_name}.", 
                                ast_node.index.pos_start, ast_node.index.pos_end)
        
        target = arr["elements"]
        for i, idx in enumerate(ast_node.index[:-1]):
            if idx.kind in {'LoadNum', 'Load'}:
                raise SemanticError(f"IndexError: loadNum and load function cannot be used as index expression.", idx.pos_start, idx.pos_end)
            
            if idx.kind == 'FuncCallStmt':
                idx_val = eval_func(idx.name.symbol, idx, symbol_table) 
            else:    
                idx_val = evaluate(idx, symbol_table)
                        
            if isinstance(idx_val, UnresolvedNumber):
                idx_val = 0
            
            if not isinstance(idx_val, int):
                raise SemanticError(f"IndexError: Array index must always evaluate to a positive hp value.", idx.pos_start, idx.pos_end)
            
            if idx_val < 0 or idx_val >= len(target):
                raise SemanticError(f"ArrayIndexError: Index {idx_val} out of bounds for dimension {i} of array '{arr_name}'.", idx.pos_start, idx.pos_end)
            target = target[idx_val]
        
        final_idx = ast_node.index[-1]
        
        if final_idx.kind in {'LoadNum', 'Load'}:
            raise SemanticError(f"IndexError: loadNum and load function cannot be used as index expression.", final_idx.pos_start, final_idx.pos_end)
        
        if final_idx.kind == 'FuncCallStmt':
            final_idx_val = eval_func(final_idx.name.symbol, final_idx, symbol_table) 
        else:    
            final_idx_val = evaluate(final_idx, symbol_table)
        
        if isinstance(final_idx_val, UnresolvedNumber):
                final_idx_val = 0
        
        if not isinstance(final_idx_val, int):
            raise SemanticError(f"IndexError: Array index must always evaluate to a positive hp value.", final_idx.pos_start, final_idx.pos_end)
        if final_idx_val < 0 or final_idx_val >= len(target):
            raise SemanticError(f"ArrayIndexError: Index {final_idx_val} out of bounds for final dimension of array '{arr_name}'.", final_idx.pos_start, final_idx.pos_end)
        
        return target[final_idx_val]
    
    elif ast_node.kind == "DeadLiteral":
        return None
    
    elif ast_node.kind == "UnaryExpr":
        if ast_node.operand.kind in {'LoadNum', 'Load'}:
            raise SemanticError(f"InvalidOperand: loadNum and load function cannot be used as unary operand.", ast_node.operand.pos_start, ast_node.operand.pos_end)
        
        if ast_node.operand.kind == 'FuncCallStmt':
            value = eval_func(ast_node.operand.name.symbol, ast_node.operand, symbol_table) 
        else:    
            value = evaluate(ast_node.operand, symbol_table)
        
        operand = value
        op_type = TYPE_MAP.get(type(operand), str(type(operand)))
        if ast_node.operator == '-':
            if isinstance(operand, UnresolvedNumber):
                return 0
            if not isinstance(operand, (int, float, bool)):
                raise SemanticError(f"TypeError: Cannot apply '-' to non-numeric type: {op_type}", ast_node.operand.pos_start, ast_node.operand.pos_end) 
            return -operand
        elif ast_node.operator == '!':
            if not isinstance(operand, bool):
                raise SemanticError(f"TypeError: Cannot apply '!' to non-flag type: {op_type}", ast_node.operand.pos_start, ast_node.operand.pos_end)
            return not operand
        else:
            raise SemanticError(f"Unknown unary operator: {ast_node.operator}")
    
    elif ast_node.kind == "FuncCallStmt":
        print(f"funccallstmt in interpreter runtime is {isRuntime}")
        value = symbol_table.lookup(ast_node.name.symbol, ast_node.name.pos_start, ast_node.name.pos_end)
        recall = value["recall"]
        if recall == []:
            raise SemanticError(f"RecallError: Function '{ast_node.name.symbol}' does not return a value.", ast_node.pos_start, ast_node.pos_end)
        if all(rec.expressions == ["void"] for rec in recall):
            raise SemanticError(f"RecallError: Function '{ast_node.name.symbol}' does not return a value.", ast_node.pos_start, ast_node.pos_end)
        
        result = traverser.visit_FuncCallStmt(ast_node, True, isRuntime)
        #print(f"yoyo {result}")
        return result
    
    elif ast_node.kind == "Load":
        print(f"loadnode = {ast_node} in loadNUm")
        if isRuntime:
            if ast_node.prompt_msg is not None:
                prompt = evaluate(ast_node.prompt_msg, symbol_table)
            else:
                prompt = ""
            
            run_id_snapshot = current_run_id  # snapshot of the current run ID before waiting for input
            get_input_from_frontend(prompt)

            print(f"before sleep {input_value} and {stopper}")

            while input_value is None and stopper is False:
                if current_run_id != run_id_snapshot:  # this checks if runtime was clicked
                    print("Cancelled waiting for input due to new run.")
                    raise SemanticError("test")
                eel.sleep(0)

            print(f"Received input: {input_value}")

            val = input_value
            input_value = None  
            
            return val
        else:
            return ""
    
    elif ast_node.kind == "LoadNum":
        
        print(f"loadnode = {ast_node} in loadNUm")
        if isRuntime:
            if ast_node.prompt_msg is not None:
                prompt = evaluate(ast_node.prompt_msg, symbol_table)
            else:
                prompt = ""
            
            run_id_snapshot = current_run_id  
            get_input_from_frontend(prompt)

            print(f"before sleep {input_value} and {stopper}")

            while input_value is None and stopper is False:
                if current_run_id != run_id_snapshot:  # this checks if runtime was clicked
                    print("Cancelled waiting for input due to new run.")
                    raise SemanticError("test")
                eel.sleep(0)
            
            print(f"Received input: {input_value}")
            
            val = input_value
            input_value = None
            

            try:
                if '.' in val:
                    return float(val)
                else:
                    return int(val)
            except:
                raise SemanticError(f"TypeError: Invalid numeric input: '{val}'", ast_node.pos_start, ast_node.pos_end)
        else:
            return UnresolvedNumber()
    
    elif ast_node.kind == "XpFormatting":
        if ast_node.lhs.kind in {'Load', 'LoadNum'}:
            raise SemanticError(f"FormatError: 'load' and 'loadNum' function are not allowed in xp formatting.", ast_node.pos_start, ast_node.pos_end)
        
        if ast_node.lhs.kind == 'FuncCallStmt':
            value = eval_func(ast_node.lhs.name.symbol, ast_node.lhs, symbol_table) 
        else:    
            value = evaluate(ast_node.lhs, symbol_table)
        
        if isinstance(value, UnresolvedNumber):
            value = 0.0

        print (f"xp format val = {value}")
        
        if not isinstance(value, dict):
            if value is None:
                raise SemanticError("FormatError: Cannot use xp formatting on a dead value.", ast_node.pos_start, ast_node.pos_end)
            elif not isinstance(value, float):
                raise SemanticError("FormatError: Using xp formatting on a non-xp value.", ast_node.pos_start, ast_node.pos_end)
            
            formatted_digits = f".{ast_node.digits}f"
            formatted = f"{value:{formatted_digits}}"  
            print(f"formatted {formatted}")
            
            return formatted
        
        else:
            if "elements" in value or "fields" in value:
                raise SemanticError("FormatError: Using xp formatting on a non-xp value.", ast_node.pos_start, ast_node.pos_end)
            elif value["type"] != "xp":
                raise SemanticError("FormatError: Using xp formatting on a non-xp value.", ast_node.pos_start, ast_node.pos_end)
            elif value["value"] is None:
                raise SemanticError("FormatError: Cannot use xp formatting on a dead value.", ast_node.pos_start, ast_node.pos_end)
            
            formatted_digits = f".{ast_node.digits}f"
            formatted = f"{value:{formatted_digits}}"  
            print(f"formatted {formatted}")
            
            return formatted
    
    elif ast_node.kind == "FormCommsLiteral":
        evaluated_values = []

        for expr in ast_node.expressions:
            if expr.kind in {'Load', 'LoadNum'}:
                raise SemanticError(f"FormatError: 'load' and 'loadNum' function are not allowed as placeholders.", expr.pos_start, expr.pos_end)
            
            if expr.kind == 'FuncCallStmt':
                result = eval_func(expr.name.symbol, expr, symbol_table) 
            else:    
                result = evaluate(expr, symbol_table)
            print(f"res {result}")
            
            if not isinstance(result, dict):
                if result is None:
                    result = 'dead'
                elif isinstance(result, UnresolvedNumber):
                    result = '0 or 0.0'
                elif isinstance(result, int) or isinstance(result, float) or isinstance(result, str):
                    result=result
                elif result == False:
                    result = 'false'
                elif result == True:
                    result='true'  
                else:
                    raise SemanticError("Cannot unpack placeholder.", expr.pos_start, expr.pos_end)
            elif "value" in result:
                if result is None:
                    result = 'dead'
                elif isinstance(result, UnresolvedNumber):
                    result = '0 or 0.0'
                elif isinstance(result, int) or isinstance(result, float) or isinstance(result, str):
                    result=result
                elif result == False:
                    result = 'false'
                elif result == True:
                    result='true'  
                else:
                    raise SemanticError("Cannot unpack placeholder.", expr.pos_start, expr.pos_end)
            elif "elements" in result or "fields" in result:
                raise SemanticError("TypeError: Cannot format a list object within a comms literal.", expr.pos_start, expr.pos_end)
            
            evaluated_values.append(str(result))  

        formatted = ast_node.value
        for placeholder, result in zip(ast_node.placeholders, evaluated_values):
            formatted = formatted.replace(f"{{{placeholder}}}", result, 1)
        return formatted
    elif ast_node.kind == 'DropStmt':
        result = traverser.visit_DropStmt(ast_node, True)
        return result
    elif ast_node.kind == 'SeekStmt':
        result = traverser.visit_SeekStmt(ast_node)
        return result
    elif ast_node.kind == 'RoundStmt':
        result = traverser.visit_RoundStmt(ast_node)
        return result
    elif ast_node.kind == 'LevelStmt':
        result = traverser.visit_LevelStmt(ast_node)
        return result
    elif ast_node.kind == 'ToNumStmt':
        result = traverser.visit_ToNumStmt(ast_node)
        return result
    elif ast_node.kind == 'ToCommsStmt':
        result = traverser.visit_ToCommsStmt(ast_node)
        return result
    else:
        raise SemanticError(f"Unknown node kind: {ast_node.kind}")

def eval_binary_expr(binop, symbol_table):
    if binop.left.kind in {'Load', 'LoadNum'} or binop.right.kind in {'Load', 'LoadNum'}:
        raise SemanticError("OperandError: Cannot use load or loadNum function in a binary expression.", binop.pos_start, binop.pos_end)
    
    lhs = evaluate(binop.left, symbol_table)
    rhs = evaluate(binop.right, symbol_table)
    
    if isinstance(lhs, UnresolvedNumber) and not isinstance(rhs, UnresolvedNumber):
        if isinstance(rhs, int) or isinstance(rhs, bool):
            lhs = 0
        elif isinstance(rhs, float):
            lhs = 0.0
        else:
            raise SemanticError("TypeError: Cannot mix comms and numeric types in an expression.", binop.pos_start, binop.pos_end)
    elif not isinstance(lhs, UnresolvedNumber) and isinstance(rhs, UnresolvedNumber):
        if isinstance(lhs, int) or isinstance(lhs, bool):
            rhs = 0
        elif isinstance(lhs, float):
            rhs = 0.0
        else:
            raise SemanticError("TypeError: Cannot mix comms and numeric types in an expression.", binop.pos_start, binop.pos_end)
    elif isinstance(lhs, UnresolvedNumber) and isinstance(rhs, UnresolvedNumber):
        if binop.operator in ['+', '-', '*', '/']:
            return UnresolvedNumber()
        elif binop.operator in ['<', '>', '<=', '>=', '==', '!=']:
            return eval_relational_expr(0, 0, binop.operator)  
        else:
            raise SemanticError(f"TypeError: Operation '{binop.operator}' not supported for numerical numbers.", binop.pos_start, binop.pos_end)

    if isinstance(rhs, list):
        if len(rhs) > 1:
            raise SemanticError("TypeError: Cannot use list in an expression.", binop.pos_start, binop.pos_end)
        rhs = rhs[0]
    if isinstance(lhs, list):
        if len(lhs) > 1:
            raise SemanticError("TypeError: Cannot use list in an expression.", binop.pos_start, binop.pos_end)
        lhs = lhs[0]
    
    if isinstance(rhs, dict) or isinstance(lhs, dict):
        raise SemanticError("TypeError: Trying to use a list object in an expression.", binop.pos_start, binop.pos_end)

    if binop.operator in ['AND', 'OR', '&&', '||']:
        if isinstance(lhs, bool) and isinstance(rhs, bool):
            return eval_logic_expr(lhs, rhs, binop.operator)
        else:
            raise SemanticError("TypeError: Only flag values can be used as operands on logical expressions.", binop.pos_start, binop.pos_end)

    if (isinstance(lhs, str) and isinstance(rhs, bool)) or (isinstance(lhs, bool) and isinstance(rhs, str)):
        raise SemanticError("TypeError: Cannot mix comms and flags in an expression.")

    if isinstance(lhs, str) != isinstance(rhs, str):
        raise SemanticError("TypeError: Cannot mix comms and numeric types in an expression.", binop.pos_start, binop.pos_end)

    if binop.operator in ['<', '>', '<=', '>=', '==', '!=']:
        if isinstance(lhs, str) and isinstance(rhs, str):
            return eval_relat_str(lhs, rhs, binop.operator, binop)
        return eval_relational_expr(lhs, rhs, binop.operator, binop)

    if lhs is None or rhs is None:
        raise SemanticError("TypeError: 'dead' types cannot be used as an operand.", binop.pos_start, binop.pos_end)
    
    if isinstance(lhs, str) and isinstance(rhs, str):
        if binop.operator != '+':
            raise SemanticError("TypeError: Only valid operator between comms is '+'.", binop.pos_start, binop.pos_end)
        print(f"lhs -> {lhs}, rhs -> {rhs}")
        return lhs + rhs

    return eval_numeric_binary_expr(lhs, rhs, binop.operator, binop)

def eval_numeric_binary_expr(lhs, rhs, operator, binop):
    # print(f"lhs -> {lhs}")
    # print(f"rhs -> {rhs}")
    
    try:
        if operator == "^":
            result = lhs ** rhs
        elif operator == "+":
            result = lhs + rhs
        elif operator == "-":
            result = lhs - rhs
        elif operator == "*":
            result = lhs * rhs
        elif operator == "/":
            if isinstance(lhs, int) and isinstance(rhs, int):
                if rhs == 0:
                    raise SemanticError("ZeroDivisionError: Division by zero is not allowed", binop.pos_start, binop.pos_end)
                result = lhs / rhs
            else:
                if rhs == 0 or rhs == 0.0:
                    raise SemanticError("ZeroDivisionError: Division by zero is not allowed", binop.pos_start, binop.pos_end)
                result = lhs / rhs
        else:
            if isinstance(lhs, int) and isinstance(rhs, int):
                if rhs == 0:
                    raise SemanticError("ZeroDivisionError: Modulo by zero is not allowed.", binop.pos_start, binop.pos_end)
                result = lhs % rhs
            else:
                raise SemanticError("ModuloError: Only hp values can be used in modulo operation.", binop.pos_start, binop.pos_end)
        return result
    except TypeError as e:
        error_message = str(e)
        if "unsupported operand type(s)" in error_message and "'NoneType'" in error_message:
            raise SemanticError("TypeError: 'dead' types cannot be used as an operand.", binop.pos_start, binop.pos_end)
        else:
            raise SemanticError(error_message)
    
def eval_relational_expr(lhs, rhs, operator, binop):
    if operator == '<':
        if lhs is None or rhs is None:
            raise SemanticError("TypeError: 'dead' types cannot be used as an operand in '<' operation.", binop.pos_start, binop.pos_end)
        return lhs < rhs
    elif operator == '>':
        if lhs is None or rhs is None:
            raise SemanticError("TypeError: 'dead' types cannot be used as an operand in '>' operation.", binop.pos_start, binop.pos_end)
        return lhs > rhs
    elif operator == '<=':
        if lhs is None or rhs is None:
            raise SemanticError("TypeError: 'dead' types cannot be used as an operand in '<=' operation.", binop.pos_start, binop.pos_end)
        return lhs <= rhs
    elif operator == '>=':
        if lhs is None or rhs is None:
            raise SemanticError("TypeError: 'dead' types cannot be used as an operand in '>=' operation.", binop.pos_start, binop.pos_end)
        return lhs >= rhs
    elif operator == '==':
        return lhs == rhs
    elif operator == '!=':
        return lhs != rhs
    else:
        raise SemanticError(f"Unknown relational operator: {operator}.", binop.pos_start, binop.pos_end)
    
def eval_relat_str(lhs, rhs, operator, binop):
    if operator == '==':
        return lhs == rhs
    elif operator == '!=':
        return lhs != rhs
    else:
        raise SemanticError("TypeError: Only valid relational operator between comms is '==' and '!='.", binop.pos_start, binop.pos_end)
    
def eval_chain_relat_expr(chain_expr, symbol_table):
    result = True
    for expr in chain_expr.expressions:
        if not eval_binary_expr(expr, symbol_table):
            result = False
            break
    return result

def eval_logic_expr(lhs, rhs, operator):
    if operator == '&&' or operator == 'AND':
        return lhs and rhs
    elif operator == '||' or operator == 'OR':
        return lhs or rhs
    else:
        raise SemanticError(f"Unknown logical operator: {operator}.")


from .symbol_table import SymbolTable
from ..error import SemanticError

symbol_table = SymbolTable()

class UnresolvedNumber:
    def __init__(self, possible_types=("int", "float")):
        self.possible_types = possible_types
    
    def __repr__(self):
        return "0 or 0.0"

def evaluate(ast_node, symbol_table):
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
        value = symbol_table.lookup(ast_node.symbol)
        print(value)
        if value is None:
            return value
        if not isinstance(value, dict):
            return value
        if "value" in value:
            return value["value"]
        elif "elements" in value or "fields" in value:
            return value
    elif ast_node.kind == 'StructInstField':
        structinst = symbol_table.lookup(ast_node.instance.symbol)
        if not isinstance(structinst, dict) or "fields" not in structinst:
            raise SemanticError(f"TypeError: '{ast_node.instance.symbol}' is not a struct instance.")
        for fld in structinst["fields"]:
            if fld["name"] == ast_node.field.symbol:
                return fld["value"]
            else:
                raise SemanticError(f"FieldError: Field '{ast_node.field.symbol}' does not exist "
                                f"in struct instance '{ast_node.instance.symbol}'.")
    elif ast_node.kind == 'ArrayElement':
        arr_name = ast_node.left.symbol
        arr = symbol_table.lookup(arr_name)
        if not isinstance(arr, dict) or "dimensions" not in arr:
            raise SemanticError(f"TypeError: '{arr_name}' is not an array.")
        if len(ast_node.index) != len(arr["dimensions"]):
            raise SemanticError(f"ArrayIndexError: Incorrect number of dimensions for {arr_name}.")
        target = arr["elements"]
        for i, idx in enumerate(ast_node.index[:-1]):
            idx = evaluate(idx, symbol_table)
            if idx < 0 or idx >= len(target):
                raise SemanticError(f"ArrayIndexError: Index {idx} out of bounds for dimension {i} of array '{arr_name}'.")
            target = target[idx]
        final_idx = ast_node.index[-1]
        final_idx = evaluate(final_idx, symbol_table)
        if final_idx < 0 or final_idx >= len(target):
            raise SemanticError(f"ArrayIndexError: Index {final_idx} out of bounds for final dimension of array '{arr_name}'.")
        
        return target[final_idx]
    elif ast_node.kind == "DeadLiteral":
        return None
    elif ast_node.kind == "UnaryExpr":
        operand = evaluate(ast_node.operand, symbol_table)
        if ast_node.operator == '-':
            if not isinstance(operand, (int, float, bool)):
                raise SemanticError(f"TypeError: Cannot apply '-' to non-numeric type: {type(operand).__name__}") # gawing hp xp and stuff
            return -operand
        elif ast_node.operator == '!':
            if not isinstance(operand, bool):
                raise SemanticError(f"TypeError: Cannot apply '!' to non-flag type: {type(operand).__name__}")
            return not operand
        else:
            raise SemanticError(f"Unknown unary operator: {ast_node.operator}")
    elif ast_node.kind == "FuncCallStmt":
        value = symbol_table.lookup(ast_node.name.symbol)
        recall = value["recall"]
        if recall == []:
            raise SemanticError(f"Function '{ast_node.name.symbol}' does not return a value.")
        if all(rec.expressions == ["void"] for rec in recall):
            raise SemanticError(f"Function '{ast_node.name.symbol}' does not return a value.")
        from .traverser import SemanticAnalyzer  # if needed
        traverser = SemanticAnalyzer(symbol_table)
        result = traverser.visit_FuncCallStmt(ast_node, True)
        # print(f"yoyo {result}")
        return result
    elif ast_node.kind == "Load":
        return ""
    elif ast_node.kind == "LoadNum":
        return UnresolvedNumber()

def eval_binary_expr(binop, symbol_table):
    if binop.left.kind in {'Load', 'LoadNum'} or binop.right.kind in {'Load', 'LoadNum'}:
        raise SemanticError("LoadError: Cannot use load or loadNum function in a binary expression.")
    lhs = evaluate(binop.left, symbol_table)
    rhs = evaluate(binop.right, symbol_table)
    
    if isinstance(lhs, UnresolvedNumber) and not isinstance(rhs, UnresolvedNumber):
        if isinstance(rhs, int) or isinstance(rhs, bool):
            lhs = 0
        elif isinstance(rhs, float):
            lhs = 0.0
        else:
            raise SemanticError("TypeError: Cannot mix comms and numeric types in an expression.")
    elif not isinstance(lhs, UnresolvedNumber) and isinstance(rhs, UnresolvedNumber):
        if isinstance(lhs, int) or isinstance(lhs, bool):
            rhs = 0
        elif isinstance(lhs, float):
            rhs = 0.0
        else:
            raise SemanticError("TypeError: Cannot mix comms and numeric types in an expression.")
    elif isinstance(lhs, UnresolvedNumber) and isinstance(rhs, UnresolvedNumber):
        if binop.operator in ['+', '-', '*', '/']:
            return UnresolvedNumber()
        elif binop.operator in ['<', '>', '<=', '>=', '==', '!=']:
            return eval_relational_expr(0, 0, binop.operator)  
        else:
            raise SemanticError(f"TypeError: Operation '{binop.operator}' not supported for unresolved numbers.")

    if isinstance(rhs, list):
        if len(rhs) > 1:
            raise SemanticError("TypeError: Cannot use list in an expression.")
        rhs = rhs[0]
    if isinstance(lhs, list):
        if len(lhs) > 1:
            raise SemanticError("TypeError: Cannot use list in an expression.")
        lhs = lhs[0]
    
    if isinstance(rhs, dict) or isinstance(lhs, dict):
        raise SemanticError("TypeError: Trying to use a list object in an expression.")

    if binop.operator in ['AND', 'OR', '&&', '||']:
        if isinstance(lhs, bool) and isinstance(rhs, bool):
            return eval_logic_expr(lhs, rhs, binop.operator)
        else:
            raise SemanticError("TypeError: Only flag values can be used as operands on logical expressions.")

    if (isinstance(lhs, str) and isinstance(rhs, bool)) or (isinstance(lhs, bool) and isinstance(rhs, str)):
        raise SemanticError("TypeError: Cannot mix comms and flags in an expression.")

    if isinstance(lhs, str) != isinstance(rhs, str):
        raise SemanticError("TypeError: Cannot mix comms and numeric types in an expression.")

    if binop.operator in ['<', '>', '<=', '>=', '==', '!=']:
        if isinstance(lhs, str) and isinstance(rhs, str):
            return eval_relat_str(lhs, rhs, binop.operator)
        return eval_relational_expr(lhs, rhs, binop.operator)

    if isinstance(lhs, str) and isinstance(rhs, str):
        return eval_concat(lhs, rhs, binop.operator)

    return eval_numeric_binary_expr(lhs, rhs, binop.operator)

def eval_concat(lhs, rhs, operator):
    if operator != '+':
        raise SemanticError("TypeError: Only valid operator between comms is '+'.")
    return lhs + rhs

def eval_numeric_binary_expr(lhs, rhs, operator):
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
                    raise SemanticError("ZeroDivisionError: Division by zero is not allowed")
                result = int(lhs / rhs)
            else:
                if rhs == 0 or rhs == 0.0:
                    raise SemanticError("ZeroDivisionError: Division by zero is not allowed")
                result = lhs / rhs
        else:
            if isinstance(lhs, int) and isinstance(rhs, int):
                if rhs == 0:
                    raise SemanticError("ZeroDivisionError: Modulo by zero is not allowed.")
                result = lhs % rhs
            else:
                raise SemanticError("ModuloError: Only hp values can be used in modulo operation.")
        return result
    except TypeError as e:
        error_message = str(e)
        if "unsupported operand type(s)" in error_message and "'NoneType'" in error_message:
            raise SemanticError("TypeError: 'dead' types cannot be used as an operand.")
        else:
            raise SemanticError(error_message)
    
def eval_relational_expr(lhs, rhs, operator):
    if operator == '<':
        if lhs is None or rhs is None:
            raise SemanticError("TypeError: 'dead' types cannot be used as an operand in '<' operation.")
        return lhs < rhs
    elif operator == '>':
        if lhs is None or rhs is None:
            raise SemanticError("TypeError: 'dead' types cannot be used as an operand in '>' operation.")
        return lhs > rhs
    elif operator == '<=':
        if lhs is None or rhs is None:
            raise SemanticError("TypeError: 'dead' types cannot be used as an operand in '<=' operation.")
        return lhs <= rhs
    elif operator == '>=':
        if lhs is None or rhs is None:
            raise SemanticError("TypeError: 'dead' types cannot be used as an operand in '>=' operation.")
        return lhs >= rhs
    elif operator == '==':
        return lhs == rhs
    elif operator == '!=':
        return lhs != rhs
    else:
        raise SemanticError(f"Unknown relational operator: {operator}.")
    
def eval_relat_str(lhs, rhs, operator):
    if operator == '==':
        return lhs == rhs
    elif operator == '!=':
        return lhs != rhs
    else:
        raise SemanticError("TypeError: Only valid relational operator between comms is '==' and '!='.")
    
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


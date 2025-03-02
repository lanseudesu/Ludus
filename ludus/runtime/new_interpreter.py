from .new_symboltable import SymbolTable
from ..error import SemanticError

symbol_table = SymbolTable()

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
        if value is None:
            raise SemanticError(f"Variable '{ast_node.symbol}' is not defined.")
        return value["value"]
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
    
def eval_binary_expr(binop, symbol_table):
    lhs = evaluate(binop.left, symbol_table)
    rhs = evaluate(binop.right, symbol_table)

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
            if rhs == 0:
                raise SemanticError("ZeroDivisionError: Division by zero is not allowed")
            result = lhs / rhs
        else:
            if rhs == 0:
                raise SemanticError("ZeroDivisionError: Modulo by zero is not allowed.")
            result = lhs % rhs
        return result
    except TypeError:
        raise SemanticError("TypeError: 'dead' types cannot be used as an operand.")
    
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


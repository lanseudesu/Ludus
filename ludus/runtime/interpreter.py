from .symbol_table import SymbolTable

class SemanticError(Exception):
    def __init__(self, message):
        super().__init__(message)

symbol_table = SymbolTable()

def eval_numeric_binary_expr(lhs, rhs, operator):
    if operator == "+":
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
        result = lhs / rhs
    return result

def eval_binary_expr(binop, symbol_table):
    lhs = evaluate(binop.left, symbol_table)  
    rhs = evaluate(binop.right, symbol_table)  

    if isinstance(lhs, str) and isinstance(rhs, str):
        return eval_concat(lhs, rhs, binop.operator)

    if (isinstance(lhs, str) and isinstance(rhs, bool)) or (isinstance(lhs, bool) and isinstance(rhs, str)):
        raise SemanticError("TypeError: Cannot mix comms and flags in an expression.")

    if isinstance(lhs, str) != isinstance(rhs, str):
        raise SemanticError("TypeError: Cannot mix comms and numeric types in an expression.")

    return eval_numeric_binary_expr(lhs, rhs, binop.operator)
def eval_concat(lhs, rhs, operator):
    if operator != '+':
        raise SemanticError(f"TypeError: Only valid operator between comms is '+'.")

    result = lhs + rhs
    return result
    
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
    elif ast_node.kind == "Identifier":
        return symbol_table.get_variable(ast_node.symbol)
    else:
        raise SemanticError("This AST Node has not yet been setup for interpretation.")
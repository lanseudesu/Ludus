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
    lhs = evaluate(binop.left, symbol_table)  # Pass symbol_table
    rhs = evaluate(binop.right, symbol_table)  # Pass symbol_table

    return eval_numeric_binary_expr(lhs, rhs, binop.operator)

def evaluate(ast_node, symbol_table):
    if ast_node.kind == "HpLiteral":
        return ast_node.value
    elif ast_node.kind == "XpLiteral":
        return ast_node.value
    elif ast_node.kind == "BinaryExpr":
        return eval_binary_expr(ast_node, symbol_table)
    elif ast_node.kind == "Identifier":
        return symbol_table.get_variable(ast_node.symbol)
    else:
        raise SemanticError("This AST Node has not yet been setup for interpretation.")
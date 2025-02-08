from typing import List
import json

class NodeType:
    PROGRAM         = "Program"
    NUMERIC_LITERAL = "NumericLiteral"
    IDENTIFIER      = "Identifier"
    BINARY_EXPR     = "BinaryExpr"

class Stmt:
    def __init__(self, kind: str):
        self.kind = kind

    def __repr__(self, indent=0):
        return self.custom_repr(self, indent)

    def custom_repr(self, obj, indent):
        ind = ' ' * (indent * 2)
        items = []
        for key, value in obj.__dict__.items():
            if isinstance(value, Stmt):
                items.append(f'{ind}  {key}: {value.__repr__(indent + 1)}')
            elif isinstance(value, list):
                items.append(f'{ind}  {key}: [\n' + ',\n'.join(item.__repr__(indent + 2) if isinstance(item, Stmt) else f'{ind}  {json.dumps(item)}' for item in value) + f'\n{ind}  ]')
            else:
                items.append(f'{ind}  {key}: {json.dumps(value)}')
        return f'{ind}{{\n{",\n".join(items)}\n{ind}}}'

class Program(Stmt):
    def __init__(self, body: List[Stmt]):
        super().__init__(NodeType.PROGRAM)
        self.body = body

class Expr(Stmt):
    def __init__(self, kind: str):
        super().__init__(kind)

class BinaryExpr(Expr):
    def __init__(self, left: Expr, right: Expr, operator: str):
        super().__init__(NodeType.BINARY_EXPR)
        self.left = left
        self.right = right
        self.operator = operator

class Identifier(Expr):
    def __init__(self, symbol: str):
        super().__init__(NodeType.IDENTIFIER)
        self.symbol = symbol

class NumericLiteral(Expr):
    def __init__(self, value: float):
        super().__init__(NodeType.NUMERIC_LITERAL)
        self.value = value
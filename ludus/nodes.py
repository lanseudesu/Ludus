from typing import List
import json

class NodeType:
    PROGRAM         = "Program"
    HP_LITERAL      = "HpLiteral"
    XP_LITERAL      = "XpLiteral"
    COMMS_LITERAL   = "CommsLiteral"
    FLAG_LITERAL    = "FlagLiteral"
    IDENTIFIER      = "Identifier"
    BINARY_EXPR     = "BinaryExpr"
    FUNCTION_DEC    = "FunctionDec"
    BLOCK_STMT      = "BlockStmt"
    PLAY_FUNC       = "PlayFunc"
    VAR_DEC         = "VarDec"
    BATCH_VAR_DEC   = "BatchVarDec"

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
    def __init__(self, left: Expr, operator: str, right: Expr, ):
        super().__init__(NodeType.BINARY_EXPR)
        self.left = left
        self.operator = operator
        self.right = right
        
class Identifier(Expr):
    def __init__(self, symbol: str):
        super().__init__(NodeType.IDENTIFIER)
        self.symbol = symbol

class HpLiteral(Expr):
    def __init__(self, value):
        super().__init__(NodeType.HP_LITERAL)
        self.value = int(value)

class XpLiteral(Expr):
    def __init__(self, value):
        super().__init__(NodeType.XP_LITERAL)
        self.value = float(value)

class CommsLiteral(Expr):
    def __init__(self, value):
        super().__init__(NodeType.COMMS_LITERAL)
        self.value = str(value)

class FlagLiteral(Expr):
    def __init__(self, value: bool):
        super().__init__(NodeType.FLAG_LITERAL)
        self.value = value

class PlayFunc(Stmt):
    def __init__(self, body: 'BlockStmt'):
        super().__init__(NodeType.PLAY_FUNC)
        self.name = 'play'
        self.body = body

class FunctionDec(Stmt):
    def __init__(self, name: Identifier, parameters: List[Identifier], body: 'BlockStmt'):
        super().__init__(NodeType.FUNCTION_DEC)
        self.name = name
        self.parameters = parameters
        self.body = body

class BlockStmt(Stmt):
    def __init__(self, statements: List[Stmt]):
        super().__init__(NodeType.BLOCK_STMT)
        self.statements = statements

class VarDec(Stmt):
    def __init__(self, name: Identifier, value: Expr):
        super().__init__(NodeType.VAR_DEC)
        self.name = name
        self.value = value

class BatchVarDec(Stmt):
    def __init__(self, declarations: list[VarDec]):
        super().__init__(NodeType.BATCH_VAR_DEC)
        self.declarations = declarations
from typing import List, Optional

class NodeType:
    PROGRAM             = "Program"
    HP_LITERAL          = "HpLiteral"
    XP_LITERAL          = "XpLiteral"
    COMMS_LITERAL       = "CommsLiteral"
    FLAG_LITERAL        = "FlagLiteral"
    DEAD_LITERAL        = "DeadLiteral"
    IDENTIFIER          = "Identifier"
    BINARY_EXPR         = "BinaryExpr"
    FUNCTION_DEC        = "FunctionDec"
    BLOCK_STMT          = "BlockStmt"
    PLAY_FUNC           = "PlayFunc"
    VAR_DEC             = "VarDec"
    BATCH_VAR_DEC       = "BatchVarDec"
    ARRAY_DEC           = "ArrayDec"
    ASS_STMT            = "AssignmentStmt"
    ARR_ASS_STMT        = "ArrayAssignmentStmt"
    VAR_ASS_STMT        = "VarAssignmentStmt"
    STRUCT_FIELD        = "StructField"
    STRUCT_DEC          = "StructDec"
    STRUCT_INST         = "StructInst"
    INST_ASS_STMT       = "InstAssignmentStmt"
    STRUCT_INST_FIELD   = "StructInstField"
    IMMO_VAR_DEC        = "ImmoVarDec"
    BATCH_IMMO_VAR_DEC  = "BatchImmoVarDec"
    IMMO_ARRAY_DEC      = "ImmoArrayDec"
    IMMO_INST           = "ImmoStructInst"
    GLOBAL_STRUCT_DEC   = "GlobalStructDec"

class Stmt:
    def __init__(self, kind: str):
        self.kind = kind

    def __repr__(self, indent=0):
        return self.custom_repr(self, indent)

    def custom_repr(self, obj, indent=0):
        ind = ' ' * (indent * 2)
        items = []

        for key, value in obj.__dict__.items():
            if isinstance(value, Stmt):  
                items.append(f'{ind}  {key}: {value.custom_repr(value, indent + 1)}')
            elif isinstance(value, list):
                if all(isinstance(item, (int, float, str, bool, type(None))) for item in value):
                    formatted_list = ', '.join(self.format_value(item) for item in value)
                    items.append(f'{ind}  {key}: [ {formatted_list} ]')
                else:
                    formatted_list = []
                    for item in value:
                        if isinstance(item, list):  
                            nested_formatted = '[\n' + ',\n'.join(f'{ind}    {self.format_value(it)}' if not isinstance(it, Stmt) 
                                                                else f'{ind}    {it.custom_repr(it, indent + 2)}' 
                                                                for it in item) + f'\n{ind}  ]'
                            formatted_list.append(nested_formatted)
                        elif isinstance(item, Stmt):
                            formatted_list.append(f'{ind}  {item.custom_repr(item, indent + 1)}')
                        else:
                            formatted_list.append(f'{ind}  {self.format_value(item)}')
                    
                    items.append(f'{ind}  {key}: [\n' + ',\n'.join(formatted_list) + f'\n{ind}  ]')
            else:
                items.append(f'{ind}  {key}: {self.format_value(value)}')

        return f'{ind}{{\n' + ",\n".join(items) + f'\n{ind}}}'

    def format_value(self, value):
        if value is None:
            return "None"
        elif isinstance(value, str):
            return f'"{value}"'
        else:
            return str(value)

class Program(Stmt):
    def __init__(self, body: List[Stmt]):
        super().__init__(NodeType.PROGRAM)
        self.body = body

class Expr(Stmt):
    def __init__(self, kind: str):
        super().__init__(kind)

class BinaryExpr(Expr):
    def __init__(self, left: Expr, operator: str, right: Expr):
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

class DeadLiteral(Expr):
    def __init__(self, value: None, datatype: str):
        super().__init__(NodeType.DEAD_LITERAL)
        self.value = value
        self.datatype = datatype

    def get_expected_type(self):
        type_map = {
            "hp": int,
            "xp": float,
            "comms": str,
            "flag": bool
        }
        return type_map.get(self.datatype, None)

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

class ArrayDec(Stmt):
    def __init__(self, name: Identifier, dimensions: List[Optional[int]], elements: List[Expr]):
        super().__init__(NodeType.ARRAY_DEC)
        self.name = name
        self.dimensions = dimensions
        self.elements = elements

class AssignmentStmt(Stmt):
    def __init__(self, kind: str):
        super().__init__(NodeType.ASS_STMT)
        self.kind = kind

class ArrAssignment(AssignmentStmt):
    def __init__(self, left: Identifier, operator: str, right: Expr):
        super().__init__(NodeType.ARR_ASS_STMT)
        self.left = left
        self.operator = operator
        self.right = right

class VarAssignment(AssignmentStmt):
    def __init__(self, left: Identifier, operator: str, right: Expr):
        super().__init__(NodeType.VAR_ASS_STMT)
        self.left = left
        self.operator = operator
        self.right = right

class StructFields(Stmt):
    def __init__(self, name: Identifier, value: Expr):
        super().__init__(NodeType.STRUCT_FIELD)
        self.name = name
        self.value = value

class StructDec(Stmt):
    def __init__(self, name: Identifier, body: List[StructFields]):
        super().__init__(NodeType.STRUCT_DEC)
        self.name = name
        self.body = body

class StructInst(Stmt):
    def __init__(self, name: Identifier, parent: str, body: List[StructFields]):
        super().__init__(NodeType.STRUCT_INST)
        self.name = name
        self.parent = parent
        self.body = body

class StructInstField(Stmt):
    def __init__(self, instance: Identifier, field: Identifier):
        super().__init__(NodeType.STRUCT_INST_FIELD)
        self.instance = instance
        self.field = field

class InstAssignment(AssignmentStmt):
    def __init__(self, left: StructInstField, operator: str, right: Expr):
        super().__init__(NodeType.INST_ASS_STMT)
        self.left = left
        self.operator = operator
        self.right = right

class ImmoVarDec(Stmt):
    def __init__(self, name: Identifier, value: Expr):
        super().__init__(NodeType.IMMO_VAR_DEC)
        self.name = name
        self.value = value

class BatchImmoVarDec(Stmt):
    def __init__(self, declarations: list[ImmoVarDec]):
        super().__init__(NodeType.BATCH_IMMO_VAR_DEC)
        self.declarations = declarations

class ImmoArrayDec(Stmt):
    def __init__(self, name: Identifier, dimensions: List[Optional[int]], elements: List[Expr]):
        super().__init__(NodeType.IMMO_ARRAY_DEC)
        self.name = name
        self.dimensions = dimensions
        self.elements = elements

class ImmoInstDec(Stmt):
    def __init__(self, name: Identifier, parent: str, body: List[StructFields]):
        super().__init__(NodeType.IMMO_INST)
        self.name = name
        self.parent = parent
        self.body = body

class GlobalStructDec(Stmt):
    def __init__(self, name: Identifier):
        super().__init__(NodeType.GLOBAL_STRUCT_DEC)
        self.name = name
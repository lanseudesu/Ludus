from typing import List, Optional

class NodeType:
    PROGRAM             = "Program"
    HP_LITERAL          = "HpLiteral"
    XP_LITERAL          = "XpLiteral"
    COMMS_LITERAL       = "CommsLiteral"
    FLAG_LITERAL        = "FlagLiteral"
    DEAD_LITERAL        = "DeadLiteral"
    IDENTIFIER          = "Identifier"
    UNARY_EXPR          = "UnaryExpr"
    BINARY_EXPR         = "BinaryExpr"
    CHAIN_RELAT_EXPR    = "ChainRelatExpr"
    FUNCTION_DEC        = "FunctionDec"
    BLOCK_STMT          = "BlockStmt"
    PLAY_FUNC           = "PlayFunc"
    VAR_DEC             = "VarDec"
    BATCH_VAR_DEC       = "BatchVarDec"
    ARRAY_DEC           = "ArrayDec"
    ARRAY_REDEC         = "ArrayRedec"
    ARR_ELEMENT         = "ArrayElement"
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
    IF_STMT             = "IfStmt"
    ELIF_STMT           = "ElifStmt"
    FLANK_STMT          = "FlankStmt"
    CHOICE_STMT         = "ChoiceStmt"
    RESUME_STMT         = "ResumeStmt"
    CHECKPOINT_STMT     = "CheckpointStmt"
    FOR_STMT            = "ForStmt"
    GRINDWHILE_STMT     = "GrindWhileStmt"
    PARAMS              = "Params"
    RECALL_STMT         = "RecallStmt"
    GLOBAL_FUNC_NAME    = "GlobalFuncDec"
    GLOBAL_FUNC_BODY    = "GlobalFuncBody"
    FUNC_CALL           = "FuncCallStmt"
    ARR_VAR             = "ArrVar"
    LOAD_STR            = "Load"
    LOAD_NUM            = "LoadNum"
    SHOOT               = "ShootStmt"
    XP_FORMAT           = "XpFormatting"
    FORM_COMMS_LITERAL  = "FormCommsLiteral"
    WIPE                = "WipeStmt"
    JOIN_STMT           = "JoinStmt"
    DROP_STMT           = "DropStmt"

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

class BlockStmt(Stmt):
    def __init__(self, statements: List[Stmt]):
        super().__init__(NodeType.BLOCK_STMT)
        self.statements = statements

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

class FormattedCommsLiteral(Expr):
    def __init__(self, value, placeholders, expressions):
        super().__init__(NodeType.FORM_COMMS_LITERAL)
        self.value = str(value)              
        self.placeholders = placeholders     
        self.expressions = expressions 

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

class UnaryExpr(Expr):
    def __init__(self, operator: str, operand: Expr):
        super().__init__(NodeType.UNARY_EXPR)
        self.operator = operator
        self.operand = operand

class ChainRelatExpr(Expr):
    def __init__(self, expressions: List[Expr]):
        super().__init__(NodeType.CHAIN_RELAT_EXPR)
        self.expressions = expressions

class PlayFunc(Stmt):
    def __init__(self, body: BlockStmt):
        super().__init__(NodeType.PLAY_FUNC)
        self.name = 'play'
        self.body = body

class FunctionDec(Stmt):
    def __init__(self, name: Identifier, parameters: List[Identifier], body: 'BlockStmt'):
        super().__init__(NodeType.FUNCTION_DEC)
        self.name = name
        self.parameters = parameters
        self.body = body

class VarDec(Stmt):
    def __init__(self, name: Identifier, value: Expr, immo: bool, scope: str):
        super().__init__(NodeType.VAR_DEC)
        self.name = name
        self.value = value
        self.immo = immo
        self.scope = scope

class BatchVarDec(Stmt):
    def __init__(self, declarations: list[Stmt], batch_ver1=False):
        super().__init__(NodeType.BATCH_VAR_DEC)
        self.declarations = declarations
        self.batch_ver1 = batch_ver1

class ArrayDec(Stmt):
    def __init__(self, name: Identifier, dimensions: List[Optional[int]], 
                 elements: List[Expr], immo: bool, scope: str, datatype=None):
        super().__init__(NodeType.ARRAY_DEC)
        self.name = name
        self.dimensions = dimensions
        self.elements = elements
        self.immo = immo
        self.scope = scope
        self.datatype = datatype

class ArrayRedec(Stmt):
    def __init__(self, name: Identifier, dimensions: List[Optional[int]], 
                 elements: List[Expr], immo: bool, scope: str):
        super().__init__(NodeType.ARRAY_REDEC)
        self.name = name
        self.dimensions = dimensions
        self.elements = elements
        self.immo = immo
        self.scope = scope

class AssignmentStmt(Stmt):
    def __init__(self, kind: str):
        super().__init__(NodeType.ASS_STMT)
        self.kind = kind

class ArrElement(Expr):
    def __init__(self, left: Identifier, index: Expr):
        super().__init__(NodeType.ARR_ELEMENT)
        self.left = left
        self.index = index

class ArrAssignment(AssignmentStmt):
    def __init__(self, left: ArrElement, operator: str, right: Expr):
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
    def __init__(self, name: Identifier, value: Expr, datatype: str):
        super().__init__(NodeType.STRUCT_FIELD)
        self.name = name
        self.value = value
        self.datatype = datatype

class StructDec(Stmt):
    def __init__(self, name: Identifier, body: List[StructFields], scope: str):
        super().__init__(NodeType.STRUCT_DEC)
        self.name = name
        self.body = body
        self.scope = scope

class StructInst(Stmt):
    def __init__(self, name: Identifier, parent: str, body: List[Expr], immo: bool):
        super().__init__(NodeType.STRUCT_INST)
        self.name = name
        self.parent = parent
        self.body = body
        self.immo = immo

class StructInstField(Expr):
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

class IfStmt(Stmt):
    def __init__(self, condition, then_branch, elif_branches=None, else_branch=None):
        super().__init__(NodeType.IF_STMT)
        self.condition = condition         
        self.then_branch = then_branch     
        self.elif_branches = elif_branches  
        self.else_branch = else_branch

class ElifStmt(Stmt):
    def __init__(self, condition, body):
        super().__init__(NodeType.ELIF_STMT)
        self.condition = condition         
        self.body = body     

class ChoiceStmts(Stmt):
    def __init__(self, values: List[Expr], body):
        super().__init__(NodeType.CHOICE_STMT)
        self.values = values
        self.body = body

class FlankStmt(Stmt):
    def __init__(self, expression, choices: List[ChoiceStmts], backup_body):
        super().__init__(NodeType.FLANK_STMT)
        self.expression = expression
        self.choices = choices
        self.backup_body = backup_body

class ResumeStmt(Stmt):
    def __init__(self):
        super().__init__(NodeType.RESUME_STMT)

class CheckpointStmt(Stmt):
    def __init__(self):
        super().__init__(NodeType.CHECKPOINT_STMT)

class ForStmt(Stmt):
    def __init__(self, initialization: VarAssignment, condition: Expr, 
                 update: VarAssignment, body: List[Stmt]):
        super().__init__(NodeType.FOR_STMT)
        self.initialization = initialization
        self.condition = condition
        self.update = update
        self.body = body

class GrindWhileStmt(Stmt):
    def __init__(self, condition: Expr, body: List[Stmt], is_grind=False):
        super().__init__(NodeType.GRINDWHILE_STMT)
        self.condition = condition
        self.body = body
        self.is_grind = is_grind

class Params(Stmt):
    def __init__(self, param: str, param_val=None):
        super().__init__(NodeType.PARAMS)
        self.param = param
        self.param_val = param_val

class RecallStmt(Stmt):
    def __init__(self, expressions: List[Expr]):
        super().__init__(NodeType.RECALL_STMT)
        self.expressions = expressions

class GlobalFuncDec(Stmt):
    def __init__(self, name: Identifier, params: List[Stmt]):
        super().__init__(NodeType.GLOBAL_FUNC_NAME)
        self.name = name
        self.params = params

class GlobalFuncBody(Stmt):
    def __init__(self, name: Identifier, params: List[Stmt], body: BlockStmt, recall_stmts: List[RecallStmt]):
        super().__init__(NodeType.GLOBAL_FUNC_BODY)
        self.name = name
        self.params = params
        self.body = body
        self.recall_stmts = recall_stmts
    
class FuncCallStmt(Stmt):
    def __init__(self, name: Identifier, args: List[Expr]):
        super().__init__(NodeType.FUNC_CALL)
        self.name = name
        self.args = args

class ArrayOrVar(Stmt):
    def __init__(self, lhs_name: str, statements: List[Stmt]):
        super().__init__(NodeType.ARR_VAR)
        self.lhs_name = lhs_name
        self.statements = statements

class Load(Expr):
    def __init__(self, prompt_msg: str):
        super().__init__(NodeType.LOAD_STR)
        self.prompt_msg = prompt_msg

class LoadNum(Expr):
    def __init__(self, prompt_msg: str):
        super().__init__(NodeType.LOAD_NUM)
        self.prompt_msg = prompt_msg

class ShootStmt(Stmt):
    def __init__(self, element, is_Next=False):
        super().__init__(NodeType.SHOOT)
        self.element = element
        self.is_Next = is_Next

class XpFormatting(Expr):
    def __init__(self, lhs, digits):
        super().__init__(NodeType.XP_FORMAT)
        self.lhs = lhs
        self.digits = digits

class WipeStmt(Stmt):
    def __init__(self):
        super().__init__(NodeType.WIPE)

class JoinStmt(Stmt):
    def __init__(self, arr_name, value, dimensions, row_index=None):
        super().__init__(NodeType.JOIN_STMT)
        self.arr_name = arr_name
        self.value = value
        self.dimensions = dimensions
        self.row_index = row_index

class DropStmt(Stmt):
    def __init__(self, arr_name, elem_index, dimensions, row_index=None):
        super().__init__(NodeType.DROP_STMT)
        self.arr_name = arr_name
        self.elem_index = elem_index
        self.dimensions = dimensions
        self.row_index = row_index
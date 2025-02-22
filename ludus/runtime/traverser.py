from ..nodes import *
from .new_symboltable import SymbolTable
from .new_interpreter import evaluate
from ..error import SemanticError

class ASTVisitor:
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

    def visit_VarAssignment(self, node: VarAssignment):
        self.symbol_table.define(node.left.symbol, node.right)

    def visit_FunctionDec(self, node: FunctionDec):
        self.symbol_table.define(node.name.symbol, {
            "params": [param.symbol for param in node.parameters],
            "body": node.body
        })

    def visit_BlockStmt(self, node: BlockStmt):
        for stmt in node.statements:
            self.visit(stmt)

class SemanticAnalyzer(ASTVisitor):
    TYPE_MAP = {
        int: "hp",
        float: "xp",
        str: "comms",
        bool: "flag"
    }

    def __init__(self, symbol_table):
        super().__init__()
        self.symbol_table = symbol_table  

    def visit_VarDec(self, node: VarDec):
        value = evaluate(node.value, self.symbol_table)
        if isinstance(node.value, DeadLiteral):
            val_type = node.value.datatype
        else:
            val_type = self.TYPE_MAP.get(type(value), str(type(value)))
        self.symbol_table.define_var(node.name.symbol, value, val_type)

    def visit_VarAssignmentStmt(self, node: VarAssignment):
        new_val = evaluate(node.right, self.symbol_table)
        new_val_type = self.TYPE_MAP.get(type(new_val), str(type(new_val)))
        value = self.symbol_table.lookup(node.left.symbol)
        value_type = value["type"]

        if new_val_type != value_type:
            raise SemanticError(f"TypeMismatchError: Type mismatch for variable '{node.left.symbol}'. Expected '{value_type}', got '{new_val_type}'.")
        self.symbol_table.define_var(node.left.symbol, new_val, new_val_type)

    def visit_BatchVarDec(self, node: BatchVarDec):
        declared_types = set() 
        for var_dec in node.declarations:
            self.visit(var_dec)

            value = self.symbol_table.lookup(var_dec.name.symbol)
            value_type = value["type"]
            declared_types.add(value_type)
        
        if len(declared_types) > 1:
            raise SemanticError(f"All variables in a batch declaration must have the same type. Found types: {declared_types}")


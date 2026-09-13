# P8.T5 — compute: AST-based sandboxed evaluator
from __future__ import annotations

import ast
import operator
import re
from typing import Any, ClassVar

from harness.registry.tool import Tool, ToolResult

_ALLOWED_NAMES = {
    "pi": 3.141592653589793,
    "e": 2.718281828459045,
    "abs": abs,
    "min": min,
    "max": max,
    "round": round,
    "sum": sum,
    "len": len,
    "float": float,
    "int": int,
    "str": str,
}

_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


class ComputeTool(Tool):
    name = "compute"
    description = "Evaluate a safe arithmetic expression"
    parameters: ClassVar[dict] = {"expression": {"type": "string", "description": "Arithmetic expression to evaluate", "required": True}}

    def run(self, **params) -> ToolResult:
        expr = params.get("expression", "")
        try:
            result = _safe_eval(expr)
            return ToolResult(ok=True, data={"expression": expr, "result": result})
        except (ComputeError, SyntaxError, TypeError, ValueError, ZeroDivisionError) as exc:
            return ToolResult(ok=False, error=f"Compute error: {exc}")


class ComputeError(Exception):
    pass


def _safe_eval(expr: str) -> Any:
    expr = expr.replace("^", "**")
    if re.search(r'(?i)import\s+\w+|__\w+__|exec\s*\(|eval\s*\(|open\s*\(', expr):
        raise ComputeError("Disallowed operation in expression")
    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError as exc:
        raise ComputeError(f"Syntax error: {exc}") from exc
    return _eval_node(tree.body)


def _eval_node(node: ast.AST) -> Any:
    if isinstance(node, ast.Expression):
        return _eval_node(node.body)
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ComputeError(f"Unsupported constant: {type(node.value).__name__}")
    if isinstance(node, ast.Num):  # Python 3.7 compat
        return node.n
    if isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_BINOPS:
            raise ComputeError(f"Unsupported operator: {op_type.__name__}")
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        return _ALLOWED_BINOPS[op_type](left, right)
    if isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in _ALLOWED_BINOPS:
            raise ComputeError(f"Unsupported unary operator: {op_type.__name__}")
        operand = _eval_node(node.operand)
        return _ALLOWED_BINOPS[op_type](operand)
    if isinstance(node, ast.Call):
        raise ComputeError("Function calls not allowed")
    if isinstance(node, ast.Name):
        if node.id in _ALLOWED_NAMES:
            return _ALLOWED_NAMES[node.id]
        raise ComputeError(f"Unknown name: {node.id}")
    raise ComputeError(f"Unsupported expression type: {type(node).__name__}")

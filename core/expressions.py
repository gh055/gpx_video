"""
===============================================================================
GPX Video Generator & DaVinci Resolve Integration
===============================================================================

- Allow safe expressions for unit conversions in custom widgets

Author: ghoss
License: MIT
===============================================================================
"""

import ast
import operator


class SafeExpression:

    # Allowed binary operators
    _operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }


    """
    Safely evaluates a basic math string against a context dict (e.g., {'val': 3100.0}).
    """
    @classmethod
    def evaluate(cls, expression_str: str, context: dict):

        try:
            tree = ast.parse(expression_str, mode='eval')
            return cls._eval_node(tree.body, context)

        except Exception as e:
            raise ValueError(f"Invalid math formula '{expression_str}': {e}")


    @classmethod
    def _eval_node(cls, node, context):

        if isinstance(node, ast.Constant):  # Numbers (e.g., 1000.0)
            return node.value

        elif isinstance(node, ast.Name):  # Variables (e.g., val)
            if node.id in context:
                return context[node.id]
            raise NameError(f"Undefined variable in expression: '{node.id}'")

        elif isinstance(node, ast.BinOp):  # Binary operations (val / 1000.0)
            left = cls._eval_node(node.left, context)
            right = cls._eval_node(node.right, context)
            op_type = type(node.op)
            if op_type in cls._operators:
                return cls._operators[op_type](left, right)
            raise TypeError(f"Unsupported operator: {op_type.__name__}")

        elif isinstance(node, ast.UnaryOp):  # Unary operations (-val)
            operand = cls._eval_node(node.operand, context)
            op_type = type(node.op)
            if op_type in cls._operators:
                return cls._operators[op_type](operand)
            raise TypeError(f"Unsupported unary operator: {op_type.__name__}")

        else:
            raise TypeError(f"Unsupported expression construct: {type(node).__name__}")
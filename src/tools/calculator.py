# ============================================================================
# FILE: src/tools/calculator.py
# ============================================================================
"""Calculator tool for safe arithmetic evaluation."""
import re
import ast
import operator
from typing import Any, Dict
from src.tools.base import Tool
from src.models import ToolResult


class Calculator(Tool):
    """Tool for safely evaluating arithmetic expressions."""
    
    # Allowed operators for safe evaluation
    ALLOWED_OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }
    
    @property
    def name(self) -> str:
        return "Calculator"
    
    @property
    def description(self) -> str:
        return "Safely evaluates arithmetic expressions like '(41*7)+13'. Supports +, -, *, /, ** (power), and parentheses."
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Arithmetic expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    
    def execute(self, input_data: Dict[str, Any]) -> ToolResult:
        """
        Execute the calculator with the given expression.
        
        Args:
            input_data: Must contain "expression" key with arithmetic string
            
        Returns:
            ToolResult with calculation result or error
        """
        # Validate input
        if not self.validate_input(input_data):
            return ToolResult(
                success=False,
                error="Invalid input: 'expression' field is required and must be a string"
            )
        
        expression = input_data["expression"].strip()
        
        # Basic safety checks
        if not expression:
            return ToolResult(
                success=False,
                error="Expression cannot be empty"
            )
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r'__',  # Dunder methods
            r'import',  # Import statements
            r'exec',  # Code execution
            r'eval',  # Eval calls
            r'open',  # File operations
            r'lambda',  # Lambda functions
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, expression, re.IGNORECASE):
                return ToolResult(
                    success=False,
                    error=f"Unsafe expression: contains forbidden pattern '{pattern}'"
                )
        
        # Only allow numbers, operators, parentheses, and whitespace
        if not re.match(r'^[\d\s\+\-\*\/\(\)\.\*\*]+$', expression):
            return ToolResult(
                success=False,
                error="Expression contains invalid characters. Only numbers, +, -, *, /, **, (, ) are allowed"
            )
        
        try:
            result = self._safe_eval(expression)
            return ToolResult(
                success=True,
                output=result
            )
        except ZeroDivisionError:
            return ToolResult(
                success=False,
                error="Division by zero"
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=f"Evaluation error: {str(e)}"
            )
    
    def _safe_eval(self, expression: str) -> float:
        """
        Safely evaluate an arithmetic expression using AST parsing.
        
        Args:
            expression: Arithmetic expression string
            
        Returns:
            Numerical result
            
        Raises:
            ValueError: If expression contains unsupported operations
            SyntaxError: If expression is malformed
        """
        try:
            node = ast.parse(expression, mode='eval')
        except SyntaxError as e:
            raise ValueError(f"Invalid expression syntax: {e}")
        
        return self._eval_node(node.body)
    
    def _eval_node(self, node):
        """
        Recursively evaluate an AST node.
        
        Args:
            node: AST node to evaluate
            
        Returns:
            Evaluated value
        """
        if isinstance(node, ast.Num):  # Python < 3.8
            return node.n
        elif isinstance(node, ast.Constant):  # Python >= 3.8
            return node.value
        elif isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)
            
            if op_type not in self.ALLOWED_OPERATORS:
                raise ValueError(f"Operator {op_type.__name__} not allowed")
            
            return self.ALLOWED_OPERATORS[op_type](left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_type = type(node.op)
            
            if op_type not in self.ALLOWED_OPERATORS:
                raise ValueError(f"Operator {op_type.__name__} not allowed")
            
            return self.ALLOWED_OPERATORS[op_type](operand)
        else:
            raise ValueError(f"Unsupported node type: {type(node).__name__}")


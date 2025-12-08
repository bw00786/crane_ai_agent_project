# ============================================================================
# FILE: tests/test_calculator.py
# ============================================================================
"""Unit tests for Calculator tool."""
import pytest
from src.tools.calculator import Calculator


@pytest.fixture
def calculator():
    """Create a Calculator instance for testing."""
    return Calculator()


class TestCalculatorBasics:
    """Test basic calculator functionality."""
    
    def test_simple_addition(self, calculator):
        """Test basic addition."""
        result = calculator.execute({"expression": "5 + 3"})
        assert result.success is True
        assert result.output == 8
        assert result.error is None
    
    def test_simple_subtraction(self, calculator):
        """Test basic subtraction."""
        result = calculator.execute({"expression": "10 - 4"})
        assert result.success is True
        assert result.output == 6
    
    def test_multiplication(self, calculator):
        """Test multiplication."""
        result = calculator.execute({"expression": "6 * 7"})
        assert result.success is True
        assert result.output == 42
    
    def test_division(self, calculator):
        """Test division."""
        result = calculator.execute({"expression": "20 / 4"})
        assert result.success is True
        assert result.output == 5.0
    
    def test_negative_numbers(self, calculator):
        """Test with negative numbers."""
        result = calculator.execute({"expression": "-5 + 3"})
        assert result.success is True
        assert result.output == -2
    
    def test_decimal_numbers(self, calculator):
        """Test with decimal numbers."""
        result = calculator.execute({"expression": "2.5 * 4"})
        assert result.success is True
        assert result.output == 10.0


class TestCalculatorComplex:
    """Test complex expressions."""
    
    def test_expression_with_parentheses(self, calculator):
        """Test expression with parentheses."""
        result = calculator.execute({"expression": "(41 * 7) + 13"})
        assert result.success is True
        assert result.output == 300
    
    def test_nested_parentheses(self, calculator):
        """Test nested parentheses."""
        result = calculator.execute({"expression": "((10 + 5) * 2) - 3"})
        assert result.success is True
        assert result.output == 27
    
    def test_power_operation(self, calculator):
        """Test power operation."""
        result = calculator.execute({"expression": "2 ** 3"})
        assert result.success is True
        assert result.output == 8
    
    def test_floating_point(self, calculator):
        """Test floating point numbers."""
        result = calculator.execute({"expression": "3.5 + 2.5"})
        assert result.success is True
        assert result.output == 6.0
    
    def test_complex_expression(self, calculator):
        """Test complex multi-operation expression."""
        result = calculator.execute({"expression": "((2 + 3) * 4) / 2"})
        assert result.success is True
        assert result.output == 10.0
    
    def test_order_of_operations(self, calculator):
        """Test that order of operations is correct."""
        result = calculator.execute({"expression": "2 + 3 * 4"})
        assert result.success is True
        assert result.output == 14  # Not 20


class TestCalculatorErrors:
    """Test error handling."""
    
    def test_division_by_zero(self, calculator):
        """Test division by zero error."""
        result = calculator.execute({"expression": "10 / 0"})
        assert result.success is False
        assert "zero" in result.error.lower()
    
    def test_invalid_expression(self, calculator):
        """Test invalid mathematical expression."""
        result = calculator.execute({"expression": "10 +"})
        assert result.success is False
        assert result.error is not None
    
    def test_empty_expression(self, calculator):
        """Test empty expression."""
        result = calculator.execute({"expression": ""})
        assert result.success is False
        assert "empty" in result.error.lower()
    
    def test_missing_expression_field(self, calculator):
        """Test missing expression field."""
        result = calculator.execute({})
        assert result.success is False
        assert "expression" in result.error.lower()
    
    def test_whitespace_only_expression(self, calculator):
        """Test expression with only whitespace."""
        result = calculator.execute({"expression": "   "})
        assert result.success is False
        assert "empty" in result.error.lower()
    
    def test_invalid_operator(self, calculator):
        """Test invalid operator."""
        result = calculator.execute({"expression": "5 % 3"})
        assert result.success is False
        assert "invalid" in result.error.lower() or "unsafe" in result.error.lower() or "forbidden" in result.error.lower()
    
    def test_mismatched_parentheses(self, calculator):
        """Test mismatched parentheses."""
        result = calculator.execute({"expression": "((5 + 3)"})
        assert result.success is False


class TestCalculatorSecurity:
    """Test security features."""
    
    def test_reject_import_statement(self, calculator):
        """Test that import statements are rejected."""
        result = calculator.execute({"expression": "import os"})
        assert result.success is False
        assert "forbidden" in result.error.lower() or "invalid" in result.error.lower()
    
    def test_reject_eval(self, calculator):
        """Test that eval is rejected."""
        result = calculator.execute({"expression": "eval('5+5')"})
        assert result.success is False
    
    def test_reject_exec(self, calculator):
        """Test that exec is rejected."""
        result = calculator.execute({"expression": "exec('x=1')"})
        assert result.success is False
    
    def test_reject_dunder_methods(self, calculator):
        """Test that dunder methods are rejected."""
        result = calculator.execute({"expression": "__import__('os')"})
        assert result.success is False
    
    def test_reject_invalid_characters(self, calculator):
        """Test that invalid characters are rejected."""
        result = calculator.execute({"expression": "5 + 3; import os"})
        assert result.success is False
        assert "invalid" in result.error.lower() or "unsafe" in result.error.lower() or "forbidden" in result.error.lower()
    
    def test_reject_lambda(self, calculator):
        """Test that lambda is rejected."""
        result = calculator.execute({"expression": "lambda x: x+1"})
        assert result.success is False
    
    def test_reject_open(self, calculator):
        """Test that open() is rejected."""
        result = calculator.execute({"expression": "open('file.txt')"})
        assert result.success is False


class TestCalculatorProperties:
    """Test calculator properties and metadata."""
    
    def test_name_property(self, calculator):
        """Test that calculator has correct name."""
        assert calculator.name == "Calculator"
    
    def test_description_property(self, calculator):
        """Test that calculator has description."""
        assert len(calculator.description) > 0
        assert "arithmetic" in calculator.description.lower()
    
    def test_input_schema_property(self, calculator):
        """Test that calculator has valid input schema."""
        schema = calculator.input_schema
        assert "properties" in schema
        assert "expression" in schema["properties"]
        assert "required" in schema
        assert "expression" in schema["required"]
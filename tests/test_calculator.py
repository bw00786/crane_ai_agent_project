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
    
    def test_reject_dunder_methods(self, calculator):
        """Test that dunder methods are rejected."""
        result = calculator.execute({"expression": "__import__('os')"})
        assert result.success is False
    
    def test_reject_invalid_characters(self, calculator):
        """Test that invalid characters are rejected."""
        result = calculator.execute({"expression": "5 + 3; import os"})
        assert result.success is False
        assert "invalid" in result.error.lower()
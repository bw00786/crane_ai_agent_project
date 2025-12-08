 ============================================================================
# FILE: tests/test_planner.py
# ============================================================================
"""Unit tests for LLM Planner."""
import pytest
from src.planner.llm_planner import LLMPlanner
from src.tools.base import ToolRegistry
from src.tools.calculator import Calculator
from src.tools.todo_store import TodoStore


@pytest.fixture
def tool_registry():
    """Create a tool registry with standard tools."""
    registry = ToolRegistry()
    registry.register(Calculator())
    registry.register(TodoStore())
    return registry


@pytest.fixture
def planner(tool_registry):
    """Create a planner instance."""
    return LLMPlanner(tool_registry, model="llama3.2")


class TestPlannerValidation:
    """Test planner validation logic."""
    
    def test_empty_prompt_raises_error(self, planner):
        """Test that empty prompt raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            planner.create_plan("")
    
    def test_whitespace_only_prompt_raises_error(self, planner):
        """Test that whitespace-only prompt raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            planner.create_plan("   \n\t  ")
    
    def test_none_prompt_raises_error(self, planner):
        """Test that None prompt raises error."""
        with pytest.raises((ValueError, AttributeError)):
            planner.create_plan(None)


class TestPlannerJsonExtraction:
    """Test JSON extraction from LLM responses."""
    
    def test_extract_json_from_markdown(self, planner):
        """Test extracting JSON from markdown code blocks."""
        text = """Here is the plan:
```json
{"steps": [{"step_number": 1, "tool": "Calculator", "input": {}, "reasoning": "test"}]}
```
"""
        json_str = planner._extract_json(text)
        assert "steps" in json_str
        assert json_str.strip().startswith("{")
    
    def test_extract_plain_json(self, planner):
        """Test extracting plain JSON without markdown."""
        text = '{"steps": [{"step_number": 1, "tool": "Calculator", "input": {}, "reasoning": "test"}]}'
        json_str = planner._extract_json(text)
        assert json_str == text.strip()
    
    def test_extract_json_without_language_tag(self, planner):
        """Test extracting JSON from code block without json tag."""
        text = """```
{"steps": [{"step_number": 1, "tool": "Calculator", "input": {}, "reasoning": "test"}]}
```"""
        json_str = planner._extract_json(text)
        assert "steps" in json_str
    
    def test_extract_json_with_surrounding_text(self, planner):
        """Test extracting JSON when surrounded by other text."""
        text = """Some explanation here
{"steps": [{"step_number": 1, "tool": "Calculator", "input": {}, "reasoning": "test"}]}
More text here"""
        json_str = planner._extract_json(text)
        assert "steps" in json_str


class TestPlannerStepValidation:
    """Test individual step validation."""
    
    def test_validate_step_with_nonexistent_tool(self, planner):
        """Test that nonexistent tool causes validation error."""
        step_data = {
            "step_number": 1,
            "tool": "NonexistentTool",
            "input": {},
            "reasoning": "test"
        }
        
        with pytest.raises(ValueError, match="not found"):
            planner._validate_step(step_data, 1)
    
    def test_validate_step_missing_required_field(self, planner):
        """Test that missing required field causes validation error."""
        step_data = {
            "step_number": 1,
            "tool": "Calculator",
            # Missing 'input' and 'reasoning'
        }
        
        with pytest.raises(ValueError, match="required"):
            planner._validate_step(step_data, 1)
    
    def test_validate_step_invalid_input_type(self, planner):
        """Test that invalid input type causes validation error."""
        step_data = {
            "step_number": 1,
            "tool": "Calculator",
            "input": "not a dict",  # Should be a dict
            "reasoning": "test"
        }
        
        with pytest.raises(ValueError, match="dictionary"):
            planner._validate_step(step_data, 1)
    
    def test_validate_valid_calculator_step(self, planner):
        """Test that valid calculator step passes validation."""
        step_data = {
            "step_number": 1,
            "tool": "Calculator",
            "input": {"expression": "5 + 3"},
            "reasoning": "Calculate the sum"
        }
        
        step = planner._validate_step(step_data, 1)
        assert step.tool == "Calculator"
        assert step.input["expression"] == "5 + 3"
    
    def test_validate_valid_todo_step(self, planner):
        """Test that valid TodoStore step passes validation."""
        step_data = {
            "step_number": 1,
            "tool": "TodoStore",
            "input": {"operation": "add", "title": "Test todo"},
            "reasoning": "Add a test todo"
        }
        
        step = planner._validate_step(step_data, 1)
        assert step.tool == "TodoStore"
        assert step.input["operation"] == "add"
    
    def test_validate_step_invalid_tool_input(self, planner):
        """Test that invalid input for tool fails validation."""
        step_data = {
            "step_number": 1,
            "tool": "Calculator",
            "input": {"wrong_field": "value"},  # Missing 'expression'
            "reasoning": "test"
        }
        
        with pytest.raises(ValueError, match="validation failed"):
            planner._validate_step(step_data, 1)


class TestPlannerToolRegistry:
    """Test planner interaction with tool registry."""
    
    def test_planner_uses_registry_tools(self, planner):
        """Test that planner has access to registry tools."""
        tools = planner.tool_registry.list_tools()
        assert "Calculator" in tools
        assert "TodoStore" in tools
    
    def test_format_tools_for_prompt(self, planner):
        """Test that tools are formatted correctly for prompt."""
        tools_str = planner._format_tools_for_prompt()
        assert "Calculator" in tools_str
        assert "TodoStore" in tools_str
        assert "Input Schema" in tools_str


class TestPlannerIntegration:
    """Integration tests with real LLM (requires Ollama running)."""
    
    @pytest.mark.skip(reason="Requires Ollama running - run manually")
    def test_create_plan_simple_calculator(self, planner):
        """Test creating a plan for simple calculation."""
        plan = planner.create_plan("Calculate 15 times 8")
        
        assert len(plan.steps) >= 1
        assert plan.steps[0].tool == "Calculator"
        assert "15" in str(plan.steps[0].input.get("expression", ""))
        assert "8" in str(plan.steps[0].input.get("expression", ""))
    
    @pytest.mark.skip(reason="Requires Ollama running - run manually")
    def test_create_plan_simple_todo(self, planner):
        """Test creating a plan for adding a todo."""
        plan = planner.create_plan("Add a todo to buy groceries")
        
        assert len(plan.steps) >= 1
        assert plan.steps[0].tool == "TodoStore"
        assert plan.steps[0].input.get("operation") == "add"
        assert "title" in plan.steps[0].input
    
    @pytest.mark.skip(reason="Requires Ollama running - run manually")
    def test_create_plan_multi_step(self, planner):
        """Test creating a multi-step plan."""
        plan = planner.create_plan(
            "Add a todo to buy milk, then show me all my tasks"
        )
        
        assert len(plan.steps) >= 2
        # First step should add a todo
        assert plan.steps[0].tool == "TodoStore"
        assert plan.steps[0].input.get("operation") == "add"
        # Second step should list todos
        assert plan.steps[1].tool == "TodoStore"
        assert plan.steps[1].input.get("operation") == "list"
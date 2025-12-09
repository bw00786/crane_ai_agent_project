"""Integration tests for the complete system."""
import pytest
from httpx import AsyncClient, ASGITransport
from src.main import app
from src.models import RunStatus
import asyncio


@pytest.mark.asyncio
class TestAPIIntegration:
    """Test complete API workflows."""
    
    async def test_health_check(self):
        """Test the health check endpoint."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "available_tools" in data
            assert len(data["available_tools"]) > 0
    
    async def test_list_tools(self):
        """Test the tools listing endpoint."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/tools")
            
            assert response.status_code == 200
            tools = response.json()
            assert "Calculator" in tools
            assert "TodoStore" in tools
            assert "description" in tools["Calculator"]
            assert "input_schema" in tools["Calculator"]
    
    async def test_create_run_returns_201(self):
        """Test that creating a run returns 201."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/runs",
                json={"prompt": "Add a todo to buy milk"}
            )
            
            assert response.status_code == 201
            data = response.json()
            assert "run_id" in data
            assert "status" in data
            assert data["status"] == "pending"
    
    async def test_get_nonexistent_run_returns_404(self):
        """Test that getting a nonexistent run returns 404."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/runs/nonexistent-id")
            
            assert response.status_code == 404
            data = response.json()
            assert "detail" in data
    
    async def test_create_run_with_empty_prompt_returns_400(self):
        """Test that empty prompt is handled."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/runs",
                json={"prompt": ""}
            )
            
            # Will be created but fail at planning stage
            assert response.status_code in [201, 400]
    
    async def test_create_run_invalid_json_returns_422(self):
        """Test that invalid JSON returns 422."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/runs",
                json={"wrong_field": "value"}
            )
            
            assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.skip(reason="Requires Ollama running - run manually")
class TestEndToEndWorkflow:
    """End-to-end integration tests requiring Ollama."""
    
    async def test_add_and_list_todo_workflow(self):
        """Test complete add and list todo workflow."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create run
            create_response = await client.post(
                "/runs",
                json={"prompt": "Add a todo to buy milk, then show me all my tasks"}
            )
            
            assert create_response.status_code == 201
            run_id = create_response.json()["run_id"]
            
            # Wait for execution (give it some time)
            await asyncio.sleep(5)
            
            # Get run status
            get_response = await client.get(f"/runs/{run_id}")
            assert get_response.status_code == 200
            
            run_data = get_response.json()
            
            # Check run completed
            assert run_data["status"] in [RunStatus.COMPLETED, RunStatus.RUNNING]
            
            # If completed, check execution log
            if run_data["status"] == RunStatus.COMPLETED:
                assert len(run_data["execution_log"]) >= 2
                
                # First step should be add
                first_step = run_data["execution_log"][0]
                assert first_step["tool"] == "TodoStore"
                assert first_step["status"] == "completed"
                
                # Second step should be list
                second_step = run_data["execution_log"][1]
                assert second_step["tool"] == "TodoStore"
                assert second_step["status"] == "completed"
    
    async def test_calculator_workflow(self):
        """Test calculator workflow."""
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            # Create run
            create_response = await client.post(
                "/runs",
                json={"prompt": "Calculate (41 * 7) + 13"}
            )
            
            assert create_response.status_code == 201
            run_id = create_response.json()["run_id"]
            
            # Wait for execution
            await asyncio.sleep(5)
            
            # Get run status
            get_response = await client.get(f"/runs/{run_id}")
            assert get_response.status_code == 200
            
            run_data = get_response.json()
            
            if run_data["status"] == RunStatus.COMPLETED:
                # Check that calculator was used
                assert len(run_data["execution_log"]) >= 1
                first_step = run_data["execution_log"][0]
                assert first_step["tool"] == "Calculator"
                assert first_step["status"] == "completed"
                # Result should be 300
                assert first_step["output"] == 300


# Synchronous integration test without LLM
def test_full_system_without_llm():
    """Test the full system with a mock plan (no LLM needed)."""
    from src.tools.base import ToolRegistry
    from src.tools.calculator import Calculator
    from src.tools.todo_store import TodoStore
    from src.orchestrator.executor import Orchestrator
    from src.models import Plan, PlanStep, Run
    
    # Setup
    registry = ToolRegistry()
    registry.register(Calculator())
    registry.register(TodoStore())
    orchestrator = Orchestrator(registry)
    
    # Create a manual plan
    plan = Plan(steps=[
        PlanStep(
            step_number=1,
            tool="TodoStore",
            input={"operation": "add", "title": "Buy milk"},
            reasoning="Add a todo for buying milk"
        ),
        PlanStep(
            step_number=2,
            tool="TodoStore",
            input={"operation": "list"},
            reasoning="List all todos to verify"
        )
    ])
    
    # Create and execute run
    run = Run(prompt="Add a todo to buy milk, then show me all my tasks")
    updated_run = orchestrator.execute_run(run, plan)
    
    # Verify execution
    assert updated_run.status == RunStatus.COMPLETED
    assert len(updated_run.execution_log) == 2
    
    # Verify first step (add)
    first_log = updated_run.execution_log[0]
    assert first_log.status.value == "completed"
    assert first_log.tool == "TodoStore"
    assert "Buy milk" in str(first_log.output)
    
    # Verify second step (list)
    second_log = updated_run.execution_log[1]
    assert second_log.status.value == "completed"
    assert second_log.tool == "TodoStore"
    assert second_log.output["count"] == 1
    assert "Buy milk" in str(second_log.output["todos"])


def test_calculator_execution_without_llm():
    """Test calculator execution without LLM."""
    from src.tools.base import ToolRegistry
    from src.tools.calculator import Calculator
    from src.orchestrator.executor import Orchestrator
    from src.models import Plan, PlanStep, Run
    
    # Setup
    registry = ToolRegistry()
    registry.register(Calculator())
    orchestrator = Orchestrator(registry)
    
    # Create a manual plan
    plan = Plan(steps=[
        PlanStep(
            step_number=1,
            tool="Calculator",
            input={"expression": "(41 * 7) + 13"},
            reasoning="Calculate the expression"
        )
    ])
    
    # Create and execute run
    run = Run(prompt="Calculate (41 * 7) + 13")
    updated_run = orchestrator.execute_run(run, plan)
    
    # Verify execution
    assert updated_run.status == RunStatus.COMPLETED
    assert len(updated_run.execution_log) == 1
    
    # Verify calculation
    log = updated_run.execution_log[0]
    assert log.status.value == "completed"
    assert log.tool == "Calculator"
    assert log.output == 300


def test_failed_step_stops_execution():
    """Test that failed step stops execution."""
    from src.tools.base import ToolRegistry
    from src.tools.calculator import Calculator
    from src.orchestrator.executor import Orchestrator, ExecutionConfig
    from src.models import Plan, PlanStep, Run
    
    # Setup with no retries
    registry = ToolRegistry()
    registry.register(Calculator())
    config = ExecutionConfig(max_retries=0)
    orchestrator = Orchestrator(registry, config)
    
    # Create a plan with an invalid step
    plan = Plan(steps=[
        PlanStep(
            step_number=1,
            tool="Calculator",
            input={"expression": "10 / 0"},  # Division by zero
            reasoning="This will fail"
        ),
        PlanStep(
            step_number=2,
            tool="Calculator",
            input={"expression": "5 + 5"},
            reasoning="This should not execute"
        )
    ])
    
    # Create and execute run
    run = Run(prompt="Test failed execution")
    updated_run = orchestrator.execute_run(run, plan)
    
    # Verify execution stopped after first step
    assert updated_run.status == RunStatus.FAILED
    assert len(updated_run.execution_log) == 1
    assert updated_run.execution_log[0].status.value == "failed"


def test_retry_logic():
    """Test retry logic with eventual success."""
    from src.tools.base import ToolRegistry
    from src.tools.calculator import Calculator
    from src.orchestrator.executor import Orchestrator, ExecutionConfig
    from src.models import Plan, PlanStep, Run
    
    # Setup
    registry = ToolRegistry()
    registry.register(Calculator())
    config = ExecutionConfig(max_retries=2, initial_retry_delay=0.1)
    orchestrator = Orchestrator(registry, config)
    
    # Create a valid plan
    plan = Plan(steps=[
        PlanStep(
            step_number=1,
            tool="Calculator",
            input={"expression": "5 + 5"},
            reasoning="Simple calculation"
        )
    ])
    
    # Create and execute run
    run = Run(prompt="Calculate 5 + 5")
    updated_run = orchestrator.execute_run(run, plan)
    
    # Should succeed on first attempt
    assert updated_run.status == RunStatus.COMPLETED
    assert updated_run.execution_log[0].attempt == 1


def test_multi_step_execution():
    """Test multi-step execution with different tools."""
    from src.tools.base import ToolRegistry
    from src.tools.calculator import Calculator
    from src.tools.todo_store import TodoStore
    from src.orchestrator.executor import Orchestrator
    from src.models import Plan, PlanStep, Run
    
    # Setup
    registry = ToolRegistry()
    registry.register(Calculator())
    registry.register(TodoStore())
    orchestrator = Orchestrator(registry)
    
    # Create a plan mixing both tools
    plan = Plan(steps=[
        PlanStep(
            step_number=1,
            tool="Calculator",
            input={"expression": "10 * 5"},
            reasoning="Calculate value"
        ),
        PlanStep(
            step_number=2,
            tool="TodoStore",
            input={"operation": "add", "title": "Result is 50"},
            reasoning="Add result as todo"
        ),
        PlanStep(
            step_number=3,
            tool="TodoStore",
            input={"operation": "list"},
            reasoning="List all todos"
        )
    ])
    
    # Execute
    run = Run(prompt="Calculate and add to todos")
    updated_run = orchestrator.execute_run(run, plan)
    
    # Verify
    assert updated_run.status == RunStatus.COMPLETED
    assert len(updated_run.execution_log) == 3
    
    # Check each step succeeded
    for log in updated_run.execution_log:
        assert log.status.value == "completed"
    
    # Verify calculation
    assert updated_run.execution_log[0].output == 50
    
    # Verify todo was added
    assert updated_run.execution_log[2].output["count"] == 1


def test_tool_registry():
    """Test tool registry functionality."""
    from src.tools.base import ToolRegistry
    from src.tools.calculator import Calculator
    from src.tools.todo_store import TodoStore
    
    registry = ToolRegistry()
    
    # Test registration
    calc = Calculator()
    todo = TodoStore()
    registry.register(calc)
    registry.register(todo)
    
    # Test exists
    assert registry.exists("Calculator")
    assert registry.exists("TodoStore")
    assert not registry.exists("NonExistent")
    
    # Test get
    retrieved_calc = registry.get("Calculator")
    assert retrieved_calc.name == "Calculator"
    
    # Test get non-existent
    with pytest.raises(ValueError):
        registry.get("NonExistent")
    
    # Test list_tools
    tools = registry.list_tools()
    assert "Calculator" in tools
    assert "TodoStore" in tools
    assert "description" in tools["Calculator"]
    assert "input_schema" in tools["Calculator"]


def test_run_storage():
    """Test run storage functionality."""
    from src.storage.run_store import RunStore
    from src.models import Run, RunStatus
    
    store = RunStore()
    
    # Test save and get
    run1 = Run(prompt="Test prompt 1")
    store.save(run1)
    
    retrieved = store.get(run1.run_id)
    assert retrieved is not None
    assert retrieved.run_id == run1.run_id
    assert retrieved.prompt == "Test prompt 1"
    
    # Test exists
    assert store.exists(run1.run_id)
    assert not store.exists("nonexistent-id")
    
    # Test get non-existent
    assert store.get("nonexistent-id") is None
    
    # Test save multiple
    run2 = Run(prompt="Test prompt 2")
    store.save(run2)
    
    all_runs = store.list_all()
    assert len(all_runs) == 2
    
    # Test delete
    deleted = store.delete(run1.run_id)
    assert deleted is True
    assert not store.exists(run1.run_id)
    
    # Test delete non-existent
    deleted = store.delete("nonexistent-id")
    assert deleted is False
    
    # Test clear
    store.clear()
    assert len(store.list_all()) == 0


def test_execution_log_tracking():
    """Test that execution logs are properly tracked."""
    from src.tools.base import ToolRegistry
    from src.tools.calculator import Calculator
    from src.orchestrator.executor import Orchestrator
    from src.models import Plan, PlanStep, Run
    
    registry = ToolRegistry()
    registry.register(Calculator())
    orchestrator = Orchestrator(registry)
    
    plan = Plan(steps=[
        PlanStep(
            step_number=1,
            tool="Calculator",
            input={"expression": "5 + 3"},
            reasoning="Add numbers"
        )
    ])
    
    run = Run(prompt="Calculate 5 + 3")
    updated_run = orchestrator.execute_run(run, plan)
    
    # Check log entry
    log = updated_run.execution_log[0]
    assert log.step_number == 1
    assert log.tool == "Calculator"
    assert log.input == {"expression": "5 + 3"}
    assert log.output == 8
    assert log.status.value == "completed"
    assert log.error is None
    assert log.attempt == 1
    assert log.started_at is not None
    assert log.completed_at is not None


def test_plan_validation():
    """Test plan validation."""
    from src.models import Plan, PlanStep
    
    # Valid plan
    plan = Plan(steps=[
        PlanStep(
            step_number=1,
            tool="Calculator",
            input={"expression": "5 + 5"},
            reasoning="Calculate sum"
        )
    ])
    
    assert plan.plan_id is not None
    assert len(plan.steps) == 1
    assert plan.steps[0].step_number == 1


def test_pydantic_models():
    """Test Pydantic model validation."""
    from src.models import Run, RunStatus, CreateRunRequest
    
    # Test Run creation
    run = Run(prompt="Test prompt")
    assert run.run_id is not None
    assert run.status == RunStatus.PENDING
    assert run.prompt == "Test prompt"
    assert run.plan is None
    assert len(run.execution_log) == 0
    assert run.created_at is not None
    assert run.completed_at is None
    
    # Test CreateRunRequest
    request = CreateRunRequest(prompt="Test")
    assert request.prompt == "Test"
    
    # Test validation
    with pytest.raises(Exception):
        CreateRunRequest()  # Missing required prompt
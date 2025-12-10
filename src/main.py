"""FastAPI application entry point for the ToDoList Microservice ."""
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from typing import Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

from src.models import (
    CreateRunRequest, CreateRunResponse, Run, RunStatus
)
from src.tools.base import ToolRegistry
from src.tools.calculator import Calculator
from src.tools.todo_store import TodoStore
from src.planner.llm_planner import LLMPlanner
from src.orchestrator.executor import Orchestrator, ExecutionConfig
from src.storage.run_store import RunStore


# Initialize components
tool_registry = ToolRegistry()
run_store = RunStore()
executor_pool = ThreadPoolExecutor(max_workers=4)

# Register tools
calculator = Calculator()
todo_store = TodoStore()
tool_registry.register(calculator)
tool_registry.register(todo_store)

# Initialize planner and orchestrator
planner = LLMPlanner(tool_registry, model="gpt-oss")
orchestrator = Orchestrator(
    tool_registry,
    config=ExecutionConfig(
        max_retries=2,
        initial_retry_delay=1.0,
        backoff_multiplier=2.0
    )
)

# Create FastAPI app
app = FastAPI(
    title="AI Agent Runtime",
    description="Minimal agent runtime with planning and execution capabilities",
    version="1.0.0"
)


@app.get("/health")
async def health_check() -> Dict[str, Any]:  # <-- Use Any
    """
    Health check endpoint.
    
    Returns:
        Status information
    """
    return {
        "status": "healthy",
        "service": "agent-runtime",
        "available_tools": ", ".join(tool_registry.list_tools().keys())
    }


@app.post("/runs", response_model=CreateRunResponse, status_code=201)
async def create_run(request: CreateRunRequest) -> CreateRunResponse:
    """
    Create and execute a new run from a natural language prompt.
    
    Args:
        request: Contains the user prompt
        
    Returns:
        Run ID and initial status
        
    Raises:
        HTTPException: If run creation or planning fails
    """
    try:
        # Create new run
        run = Run(prompt=request.prompt)
        run_store.save(run)
        
        # Execute asynchronously (non-blocking)
        asyncio.create_task(execute_run_async(run.run_id))
        
        return CreateRunResponse(
            run_id=run.run_id,
            status=run.status
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to create run: {str(e)}"
        )


async def execute_run_async(run_id: str) -> None:
    """
    Execute a run asynchronously in the background.
    
    Args:
        run_id: ID of the run to execute
    """
    run = run_store.get(run_id)
    if not run:
        return
    
    try:
        # Generate plan
        plan = await asyncio.get_event_loop().run_in_executor(
            executor_pool,
            planner.create_plan,
            run.prompt
        )
        
        # Execute plan
        updated_run = await asyncio.get_event_loop().run_in_executor(
            executor_pool,
            orchestrator.execute_run,
            run,
            plan
        )
        
        # Save updated run
        run_store.save(updated_run)
        
    except Exception as e:
        # Mark run as failed
        run.status = RunStatus.FAILED
        run.error = f"Execution failed: {str(e)}"
        run_store.save(run)


@app.get("/runs/{run_id}")
async def get_run(run_id: str) -> Run:
    """
    Get the complete state of a run.
    
    Args:
        run_id: ID of the run to retrieve
        
    Returns:
        Complete run object with execution log
        
    Raises:
        HTTPException: If run not found
    """
    print(f"Getting run ID {run_id}")
    run = run_store.get(run_id)
    print(f"run value is {run}")
    
    if not run:
        raise HTTPException(
            status_code=404,
            detail=f"Run '{run_id}' not found"
        )
    
    return run


@app.get("/tools")
async def list_tools() -> Dict[str, Any]:
    """
    List all available tools and their schemas.
    
    Returns:
        Dictionary of available tools
    """
    return tool_registry.list_tools()


@app.exception_handler(Exception)
async def global_exception_handler(request, exc: Exception):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "type": type(exc).__name__
        }
    )


def main():
    """Run the FastAPI application."""
    print("Starting AI Agent Runtime...")
    print(f"Available tools: {list(tool_registry.list_tools().keys())}")
    print("Make sure Ollama is running: ollama serve")
    print("Make sure gpt-oss is pulled: ollama pull gpt-oss")
    print("\nStarting server on http://localhost:8000")
    print("API docs available at http://localhost:8000/docs")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


if __name__ == "__main__":
    main()
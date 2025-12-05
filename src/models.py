# ============================================================================
# FILE: src/models.py
# ============================================================================
"""Data models for the agent runtime system."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
import uuid


class RunStatus(str, Enum):
    """Possible run execution states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class StepStatus(str, Enum):
    """Possible step execution states."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class PlanStep(BaseModel):
    """A single step in an execution plan."""
    step_number: int
    tool: str
    input: Dict[str, Any]
    reasoning: str


class Plan(BaseModel):
    """Structured execution plan."""
    plan_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    steps: List[PlanStep]


class ExecutionLogEntry(BaseModel):
    """Record of a single step execution."""
    step_number: int
    tool: str
    input: Dict[str, Any]
    output: Optional[Any] = None
    status: StepStatus
    error: Optional[str] = None
    attempt: int = 1
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class Run(BaseModel):
    """Complete run state."""
    run_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    prompt: str
    status: RunStatus = RunStatus.PENDING
    plan: Optional[Plan] = None
    execution_log: List[ExecutionLogEntry] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None


class CreateRunRequest(BaseModel):
    """Request to create a new run."""
    prompt: str


class CreateRunResponse(BaseModel):
    """Response after creating a run."""
    run_id: str
    status: RunStatus


class ToolResult(BaseModel):
    """Result from tool execution."""
    success: bool
    output: Any = None
    error: Optional[str] = None


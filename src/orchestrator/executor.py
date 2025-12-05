# ============================================================================
# FILE: src/orchestrator/executor.py
# ============================================================================
"""Execution orchestrator for running plans."""
import time
from datetime import datetime
from typing import Optional
from src.models import (
    Run, RunStatus, ExecutionLogEntry, StepStatus, Plan
)
from src.tools.base import ToolRegistry


class ExecutionConfig:
    """Configuration for execution behavior."""
    
    def __init__(
        self,
        max_retries: int = 2,
        initial_retry_delay: float = 1.0,
        backoff_multiplier: float = 2.0,
        step_timeout: float = 30.0
    ):
        self.max_retries = max_retries
        self.initial_retry_delay = initial_retry_delay
        self.backoff_multiplier = backoff_multiplier
        self.step_timeout = step_timeout


class Orchestrator:
    """Orchestrates plan execution with retry logic and state tracking."""
    
    def __init__(
        self,
        tool_registry: ToolRegistry,
        config: Optional[ExecutionConfig] = None
    ):
        """
        Initialize the orchestrator.
        
        Args:
            tool_registry: Registry of available tools
            config: Execution configuration (uses defaults if not provided)
        """
        self.tool_registry = tool_registry
        self.config = config or ExecutionConfig()
    
    def execute_run(self, run: Run, plan: Plan) -> Run:
        """
        Execute a complete run with the given plan.
        
        Args:
            run: Run object to execute
            plan: Plan to execute
            
        Returns:
            Updated Run object with execution results
        """
        # Update run with plan
        run.plan = plan
        run.status = RunStatus.RUNNING
        
        try:
            # Execute each step sequentially
            for step in plan.steps:
                log_entry = self._execute_step_with_retry(step)
                run.execution_log.append(log_entry)
                
                # If step failed after all retries, mark run as failed
                if log_entry.status == StepStatus.FAILED:
                    run.status = RunStatus.FAILED
                    run.error = f"Step {step.step_number} failed: {log_entry.error}"
                    run.completed_at = datetime.utcnow()
                    return run
            
            # All steps completed successfully
            run.status = RunStatus.COMPLETED
            run.completed_at = datetime.utcnow()
            
        except Exception as e:
            # Unexpected error during execution
            run.status = RunStatus.FAILED
            run.error = f"Execution error: {str(e)}"
            run.completed_at = datetime.utcnow()
        
        return run
    
    def _execute_step_with_retry(self, step) -> ExecutionLogEntry:
        """
        Execute a single step with retry logic.
        
        Args:
            step: PlanStep to execute
            
        Returns:
            ExecutionLogEntry with results
        """
        attempt = 0
        last_error = None
        retry_delay = self.config.initial_retry_delay
        
        while attempt <= self.config.max_retries:
            attempt += 1
            
            # Create log entry for this attempt
            log_entry = ExecutionLogEntry(
                step_number=step.step_number,
                tool=step.tool,
                input=step.input,
                status=StepStatus.RUNNING,
                attempt=attempt
            )
            
            try:
                # Execute the step
                result = self._execute_step(step)
                
                # Update log entry with results
                log_entry.status = StepStatus.COMPLETED if result.success else StepStatus.FAILED
                log_entry.output = result.output
                log_entry.error = result.error
                log_entry.completed_at = datetime.utcnow()
                
                # If successful, return immediately
                if result.success:
                    return log_entry
                
                # If failed, store error for potential retry
                last_error = result.error
                
            except Exception as e:
                # Unexpected error during execution
                log_entry.status = StepStatus.FAILED
                log_entry.error = f"Execution exception: {str(e)}"
                log_entry.completed_at = datetime.utcnow()
                last_error = str(e)
            
            # If this was the last attempt, return the failed entry
            if attempt > self.config.max_retries:
                return log_entry
            
            # Wait before retrying (exponential backoff)
            print(f"Step {step.step_number} failed (attempt {attempt}), retrying in {retry_delay}s...")
            time.sleep(retry_delay)
            retry_delay *= self.config.backoff_multiplier
        
        # This should never be reached, but just in case
        log_entry.status = StepStatus.FAILED
        log_entry.error = last_error or "Unknown error"
        log_entry.completed_at = datetime.utcnow()
        return log_entry
    
    def _execute_step(self, step):
        """
        Execute a single step without retry logic.
        
        Args:
            step: PlanStep to execute
            
        Returns:
            ToolResult from execution
            
        Raises:
            ValueError: If tool not found
        """
        # Get the tool
        tool = self.tool_registry.get(step.tool)
        
        # Execute the tool with the provided input
        result = tool.execute(step.input)
        
        return result
    
    def can_retry_run(self, run: Run) -> bool:
        """
        Check if a run can be safely retried (idempotency check).
        
        Args:
            run: Run to check
            
        Returns:
            True if run can be retried
        """
        # Can retry if:
        # 1. Run has failed
        # 2. Run has not completed any non-idempotent operations
        #    (For this simple implementation, we allow retry of failed runs)
        
        if run.status != RunStatus.FAILED:
            return False
        
        # Check if any steps were completed
        # For safety, we could add more sophisticated checks here
        completed_steps = [
            log for log in run.execution_log 
            if log.status == StepStatus.COMPLETED
        ]
        
        # For TodoStore operations, 'add' creates new items each time
        # so we should be cautious about retrying
        for log in completed_steps:
            if log.tool == "TodoStore" and log.input.get("operation") == "add":
                # This could create duplicates
                return False
        
        return True
    
    def resume_run(self, run: Run) -> Run:
        """
        Resume a failed run from where it left off.
        
        Args:
            run: Failed run to resume
            
        Returns:
            Updated run with new execution results
        """
        if not self.can_retry_run(run):
            raise ValueError("Run cannot be resumed")
        
        if not run.plan:
            raise ValueError("Run has no plan to resume")
        
        # Find the last completed step
        last_completed_step = 0
        for log in run.execution_log:
            if log.status == StepStatus.COMPLETED:
                last_completed_step = max(last_completed_step, log.step_number)
        
        # Resume from the next step
        run.status = RunStatus.RUNNING
        
        try:
            for step in run.plan.steps:
                # Skip already completed steps
                if step.step_number <= last_completed_step:
                    continue
                
                log_entry = self._execute_step_with_retry(step)
                run.execution_log.append(log_entry)
                
                if log_entry.status == StepStatus.FAILED:
                    run.status = RunStatus.FAILED
                    run.error = f"Step {step.step_number} failed on resume: {log_entry.error}"
                    run.completed_at = datetime.utcnow()
                    return run
            
            run.status = RunStatus.COMPLETED
            run.completed_at = datetime.utcnow()
            run.error = None
            
        except Exception as e:
            run.status = RunStatus.FAILED
            run.error = f"Resume execution error: {str(e)}"
            run.completed_at = datetime.utcnow()
        
        return run



# ============================================================================
# FILE: src/storage/run_store.py
# ============================================================================
"""In-memory storage for run state."""
from typing import Dict, Optional
from src.models import Run


class RunStore:
    """Thread-safe in-memory storage for runs."""
    
    def __init__(self):
        self._runs: Dict[str, Run] = {}
    
    def save(self, run: Run) -> None:
        """
        Save or update a run.
        
        Args:
            run: Run object to save
        """
        self._runs[run.run_id] = run
    
    def get(self, run_id: str) -> Optional[Run]:
        """
        Retrieve a run by ID.
        
        Args:
            run_id: ID of the run to retrieve
            
        Returns:
            Run object if found, None otherwise
        """
        return self._runs.get(run_id)
    
    def exists(self, run_id: str) -> bool:
        """
        Check if a run exists.
        
        Args:
            run_id: ID of the run to check
            
        Returns:
            True if run exists, False otherwise
        """
        return run_id in self._runs
    
    def delete(self, run_id: str) -> bool:
        """
        Delete a run.
        
        Args:
            run_id: ID of the run to delete
            
        Returns:
            True if run was deleted, False if it didn't exist
        """
        if run_id in self._runs:
            del self._runs[run_id]
            return True
        return False
    
    def list_all(self) -> Dict[str, Run]:
        """
        List all runs.
        
        Returns:
            Dictionary of all runs keyed by run_id
        """
        return self._runs.copy()
    
    def clear(self) -> None:
        """Clear all runs (useful for testing)."""
        self._runs.clear()
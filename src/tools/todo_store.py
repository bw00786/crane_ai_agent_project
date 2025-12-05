# ============================================================================
# FILE: src/tools/todo_store.py
# ============================================================================
"""TodoStore tool for in-memory task management."""
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid
from src.tools.base import Tool
from src.models import ToolResult


class Todo:
    """Represents a single todo item."""
    
    def __init__(self, title: str, description: str = ""):
        self.id = str(uuid.uuid4())
        self.title = title
        self.description = description
        self.completed = False
        self.created_at = datetime.utcnow().isoformat()
        self.completed_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert todo to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "created_at": self.created_at,
            "completed_at": self.completed_at
        }


class TodoStore(Tool):
    """Tool for managing todos with CRUD operations."""
    
    def __init__(self):
        self._todos: Dict[str, Todo] = {}
    
    @property
    def name(self) -> str:
        return "TodoStore"
    
    @property
    def description(self) -> str:
        return "Manages todo items. Supports operations: add, list, complete, delete. State persists within the session."
    
    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "list", "complete", "delete"],
                    "description": "Operation to perform"
                },
                "title": {
                    "type": "string",
                    "description": "Todo title (required for 'add')"
                },
                "description": {
                    "type": "string",
                    "description": "Todo description (optional for 'add')"
                },
                "todo_id": {
                    "type": "string",
                    "description": "Todo ID (required for 'complete' and 'delete')"
                }
            },
            "required": ["operation"]
        }
    
    def execute(self, input_data: Dict[str, Any]) -> ToolResult:
        """
        Execute a todo operation.
        
        Args:
            input_data: Must contain "operation" and operation-specific parameters
            
        Returns:
            ToolResult with operation result or error
        """
        operation = input_data.get("operation")
        
        if not operation:
            return ToolResult(
                success=False,
                error="Missing required field: 'operation'"
            )
        
        if operation not in ["add", "list", "complete", "delete"]:
            return ToolResult(
                success=False,
                error=f"Invalid operation: '{operation}'. Must be one of: add, list, complete, delete"
            )
        
        # Route to appropriate handler
        if operation == "add":
            return self._add_todo(input_data)
        elif operation == "list":
            return self._list_todos(input_data)
        elif operation == "complete":
            return self._complete_todo(input_data)
        elif operation == "delete":
            return self._delete_todo(input_data)
    
    def _add_todo(self, input_data: Dict[str, Any]) -> ToolResult:
        """Add a new todo item."""
        title = input_data.get("title", "").strip()
        
        if not title:
            return ToolResult(
                success=False,
                error="'title' is required for add operation"
            )
        
        description = input_data.get("description", "")
        todo = Todo(title=title, description=description)
        self._todos[todo.id] = todo
        
        return ToolResult(
            success=True,
            output={
                "message": f"Todo added successfully",
                "todo": todo.to_dict()
            }
        )
    
    def _list_todos(self, input_data: Dict[str, Any]) -> ToolResult:
        """List all todos."""
        todos_list = [todo.to_dict() for todo in self._todos.values()]
        
        return ToolResult(
            success=True,
            output={
                "count": len(todos_list),
                "todos": todos_list
            }
        )
    
    def _complete_todo(self, input_data: Dict[str, Any]) -> ToolResult:
        """Mark a todo as completed."""
        todo_id = input_data.get("todo_id", "").strip()
        
        if not todo_id:
            return ToolResult(
                success=False,
                error="'todo_id' is required for complete operation"
            )
        
        if todo_id not in self._todos:
            return ToolResult(
                success=False,
                error=f"Todo with id '{todo_id}' not found"
            )
        
        todo = self._todos[todo_id]
        if todo.completed:
            return ToolResult(
                success=True,
                output={
                    "message": "Todo was already completed",
                    "todo": todo.to_dict()
                }
            )
        
        todo.completed = True
        todo.completed_at = datetime.utcnow().isoformat()
        
        return ToolResult(
            success=True,
            output={
                "message": "Todo marked as completed",
                "todo": todo.to_dict()
            }
        )
    
    def _delete_todo(self, input_data: Dict[str, Any]) -> ToolResult:
        """Delete a todo item."""
        todo_id = input_data.get("todo_id", "").strip()
        
        if not todo_id:
            return ToolResult(
                success=False,
                error="'todo_id' is required for delete operation"
            )
        
        if todo_id not in self._todos:
            return ToolResult(
                success=False,
                error=f"Todo with id '{todo_id}' not found"
            )
        
        todo = self._todos.pop(todo_id)
        
        return ToolResult(
            success=True,
            output={
                "message": "Todo deleted successfully",
                "deleted_todo": todo.to_dict()
            }
        )

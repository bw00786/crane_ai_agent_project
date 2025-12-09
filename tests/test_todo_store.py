# ============================================================================
# FILE: tests/test_todo_store.py
# ============================================================================
"""Unit tests for TodoStore tool."""
import pytest
from src.tools.todo_store import TodoStore


@pytest.fixture
def todo_store():
    """Create a fresh TodoStore instance for each test."""
    return TodoStore()


class TestTodoStoreAdd:
    """Test todo addition functionality."""
    
    def test_add_simple_todo(self, todo_store):
        """Test adding a simple todo."""
        result = todo_store.execute({
            "operation": "add",
            "title": "Buy milk"
        })
        assert "todo" in result.output
        assert result.output["todo"]["title"] == "Buy milk"
        assert result.output["todo"]["completed"] is False
        assert "id" in result.output["todo"]
    
    def test_add_todo_with_description(self, todo_store):
        """Test adding a todo with description."""
        result = todo_store.execute({
            "operation": "add",
            "title": "Finish project",
            "description": "Complete the AI agent assignment"
        })
        assert result.output["todo"]["description"] == "Complete the AI agent assignment"
    
    def test_add_todo_missing_title(self, todo_store):
        """Test that adding without title fails."""
        result = todo_store.execute({
            "operation": "add"
        })
        
        assert result.success is False
        assert "title" in result.error.lower()
    
    def test_add_todo_empty_title(self, todo_store):
        """Test that empty title fails."""
        result = todo_store.execute({
            "operation": "add",
            "title": "   "
        })
        
        assert result.success is False
    
    def test_add_multiple_todos(self, todo_store):
        """Test adding multiple todos."""
        result1 = todo_store.execute({
            "operation": "add",
            "title": "Task 1"
        })
        result2 = todo_store.execute({
            "operation": "add",
            "title": "Task 2"
        })
        
        assert result1.success is True
        assert result2.success is True
        assert result1.output["todo"]["id"] != result2.output["todo"]["id"]
    
    def test_add_todo_has_timestamps(self, todo_store):
        """Test that added todo has creation timestamp."""
        result = todo_store.execute({
            "operation": "add",
            "title": "Test todo"
        })
        assert "created_at" in result.output["todo"]
        assert result.output["todo"]["created_at"] is not None


class TestTodoStoreList:
    """Test todo listing functionality."""
    
    def test_list_empty(self, todo_store):
        """Test listing with no todos."""
        result = todo_store.execute({"operation": "list"})
        assert result.output["count"] == 0
        assert result.output["todos"] == []
    
    def test_list_after_adding(self, todo_store):
        """Test listing after adding todos."""
        # Add two todos
        todo_store.execute({
            "operation": "add",
            "title": "Task 1"
        })
        todo_store.execute({
            "operation": "add",
            "title": "Task 2"
        })
        
        # List todos
        result = todo_store.execute({"operation": "list"})
        assert result.output["count"] == 2
        assert len(result.output["todos"]) == 2
    
    def test_list_returns_all_fields(self, todo_store):
        """Test that list returns all todo fields."""
        todo_store.execute({
            "operation": "add",
            "title": "Test todo",
            "description": "Test description"
        })
        
        result = todo_store.execute({"operation": "list"})
        todo = result.output["todos"][0]
        assert "id" in todo
        assert "title" in todo
        assert "description" in todo
        assert "completed" in todo
        assert "created_at" in todo


class TestTodoStoreComplete:
    """Test todo completion functionality."""
    
    def test_complete_todo(self, todo_store):
        """Test completing a todo."""
        # Add a todo
        add_result = todo_store.execute({
            "operation": "add",
            "title": "Task to complete"
        })
        todo_id = add_result.output["todo"]["id"]
        
        # Complete the todo
        complete_result = todo_store.execute({
            "operation": "complete",
            "todo_id": todo_id
        })
        
        assert complete_result.success is True
        assert complete_result.output["todo"]["completed"] is True
        assert complete_result.output["todo"]["completed_at"] is not None
    
    def test_complete_nonexistent_todo(self, todo_store):
        """Test completing a todo that doesn't exist."""
        result = todo_store.execute({
            "operation": "complete",
            "todo_id": "nonexistent-id"
        })
        
        assert result.success is False
        assert "not found" in result.error.lower()
    
    def test_complete_already_completed(self, todo_store):
        """Test completing an already completed todo."""
        # Add and complete a todo
        add_result = todo_store.execute({
            "operation": "add",
            "title": "Task"
        })
        todo_id = add_result.output["todo"]["id"]
        todo_store.execute({
            "operation": "complete",
            "todo_id": todo_id
        })
        
        # Try to complete again
        result = todo_store.execute({
            "operation": "complete",
            "todo_id": todo_id
        })
        assert "already completed" in result.output["message"].lower()
    
    def test_complete_missing_todo_id(self, todo_store):
        """Test completing without providing todo_id."""
        result = todo_store.execute({
            "operation": "complete"
        })
        
        assert result.success is False
        assert "todo_id" in result.error.lower()
    
    def test_complete_empty_todo_id(self, todo_store):
        """Test completing with empty todo_id."""
        result = todo_store.execute({
            "operation": "complete",
            "todo_id": "   "
        })
        
        assert result.success is False


class TestTodoStoreDelete:
    """Test todo deletion functionality."""
    
    def test_delete_todo(self, todo_store):
        """Test deleting a todo."""
        # Add a todo
        add_result = todo_store.execute({
            "operation": "add",
            "title": "Task to delete"
        })
        todo_id = add_result.output["todo"]["id"]
        
        # Delete the todo
        delete_result = todo_store.execute({
            "operation": "delete",
            "todo_id": todo_id
        })
        assert "deleted" in delete_result.output["message"].lower()
        
        # Verify it's gone
        list_result = todo_store.execute({"operation": "list"})
        assert list_result.output["count"] == 0
    
    def test_delete_nonexistent_todo(self, todo_store):
        """Test deleting a todo that doesn't exist."""
        result = todo_store.execute({
            "operation": "delete",
            "todo_id": "nonexistent-id"
        })
        
        assert result.success is False
        assert "not found" in result.error.lower()
    
    def test_delete_missing_todo_id(self, todo_store):
        """Test deleting without providing todo_id."""
        result = todo_store.execute({
            "operation": "delete"
        })
        
        assert result.success is False
        assert "todo_id" in result.error.lower()
    
    def test_delete_returns_deleted_todo(self, todo_store):
        """Test that delete returns the deleted todo."""
        add_result = todo_store.execute({
            "operation": "add",
            "title": "Task to delete"
        })
        todo_id = add_result.output["todo"]["id"]
        
        delete_result = todo_store.execute({
            "operation": "delete",
            "todo_id": todo_id
        })
        assert "deleted_todo" in delete_result.output
        assert delete_result.output["deleted_todo"]["title"] == "Task to delete"


class TestTodoStoreInvalidOperations:
    """Test invalid operations and error handling."""
    
    def test_missing_operation(self, todo_store):
        """Test request without operation field."""
        result = todo_store.execute({})
        
        assert result.success is False
        assert "operation" in result.error.lower()
    
    def test_invalid_operation(self, todo_store):
        """Test invalid operation name."""
        result = todo_store.execute({
            "operation": "invalid_op"
        })
        
        assert result.success is False
        assert "invalid operation" in result.error.lower()
    
    def test_empty_operation(self, todo_store):
        """Test empty operation string."""
        result = todo_store.execute({
            "operation": ""
        })
        
        assert result.success is False


class TestTodoStoreFlow:
    """Test complete add and list flow."""
    
    def test_add_and_list_flow(self, todo_store):
        """Test the complete add and list workflow."""
        # Add first todo
        result1 = todo_store.execute({
            "operation": "add",
            "title": "Buy milk"
        })
        assert result1.success is True
        
        # Add second todo
        result2 = todo_store.execute({
            "operation": "add",
            "title": "Buy eggs"
        })
        assert result2.success is True
        
        # List all todos
        list_result = todo_store.execute({
            "operation": "list"
        })
        
        assert list_result.success is True
        assert list_result.output["count"] == 2
        
        titles = [todo["title"] for todo in list_result.output["todos"]]
        assert "Buy milk" in titles
        assert "Buy eggs" in titles
    
    def test_full_crud_flow(self, todo_store):
        """Test complete CRUD workflow."""
        # Create
        add_result = todo_store.execute({
            "operation": "add",
            "title": "Test task"
        })
        assert add_result.success is True
        todo_id = add_result.output["todo"]["id"]
        
        # Read (list)
        list_result = todo_store.execute({"operation": "list"})
        assert list_result.output["count"] == 1
        
        # Update (complete)
        complete_result = todo_store.execute({
            "operation": "complete",
            "todo_id": todo_id
        })
        assert complete_result.success is True
        
        # Verify completed
        list_result2 = todo_store.execute({"operation": "list"})
        assert list_result2.output["todos"][0]["completed"] is True
        
        # Delete
        delete_result = todo_store.execute({
            "operation": "delete",
            "todo_id": todo_id
        })
        
        # Verify deleted
        list_result3 = todo_store.execute({"operation": "list"})
        assert list_result3.output["count"] == 0


class TestTodoStoreProperties:
    """Test TodoStore properties and metadata."""
    
    def test_name_property(self, todo_store):
        """Test that TodoStore has correct name."""
        assert todo_store.name == "TodoStore"
    
    def test_description_property(self, todo_store):
        """Test that TodoStore has description."""
        assert len(todo_store.description) > 0
        assert "todo" in todo_store.description.lower()
    
    def test_input_schema_property(self, todo_store):
        """Test that TodoStore has valid input schema."""
        schema = todo_store.input_schema
        assert "properties" in schema
        assert "operation" in schema["properties"]
        assert "required" in schema
        assert "operation" in schema["required"]


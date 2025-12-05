# ============================================================================
# FILE: src/tools/base.py
# ============================================================================
"""Base tool interface and registry."""
from abc import ABC, abstractmethod
from typing import Any, Dict
from src.models import ToolResult


class Tool(ABC):
    """Abstract base class for all tools."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique tool identifier."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what the tool does."""
        pass
    
    @property
    @abstractmethod
    def input_schema(self) -> Dict[str, Any]:
        """JSON schema defining the expected input parameters."""
        pass
    
    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool with given input.
        
        Args:
            input_data: Parameters for tool execution
            
        Returns:
            ToolResult with success status, output, and optional error
        """
        pass
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input against the tool's schema.
        Basic validation - can be overridden for complex schemas.
        
        Args:
            input_data: Parameters to validate
            
        Returns:
            True if valid, False otherwise
        """
        schema = self.input_schema
        required = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # Check required fields
        for field in required:
            if field not in input_data:
                return False
        
        # Check field types (basic type checking)
        for field, value in input_data.items():
            if field in properties:
                expected_type = properties[field].get("type")
                if expected_type == "string" and not isinstance(value, str):
                    return False
                elif expected_type == "number" and not isinstance(value, (int, float)):
                    return False
                elif expected_type == "integer" and not isinstance(value, int):
                    return False
                elif expected_type == "boolean" and not isinstance(value, bool):
                    return False
        
        return True


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self):
        self._tools: Dict[str, Tool] = {}
    
    def register(self, tool: Tool) -> None:
        """Register a tool in the registry."""
        self._tools[tool.name] = tool
    
    def get(self, name: str) -> Tool:
        """Get a tool by name."""
        if name not in self._tools:
            raise ValueError(f"Tool '{name}' not found in registry")
        return self._tools[name]
    
    def exists(self, name: str) -> bool:
        """Check if a tool exists."""
        return name in self._tools
    
    def list_tools(self) -> Dict[str, Dict[str, Any]]:
        """List all available tools with their descriptions and schemas."""
        return {
            name: {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            }
            for name, tool in self._tools.items()
        }

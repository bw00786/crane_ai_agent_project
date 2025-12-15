# ============================================================================
# FILE: src/planner/llm_planner.py
# ============================================================================
"""LLM-based planner using Ollama."""
import json
import re
from typing import Dict, Any, Optional
import ollama
from src.models import Plan, PlanStep
from src.tools.base import ToolRegistry


class LLMPlanner:
    """Planner that uses Ollama to generate structured plans from prompts."""
    
    def __init__(self, tool_registry: ToolRegistry, model: str = "gpt-oss"):
        """
        Initialize the LLM planner.
        
        Args:
            tool_registry: Registry of available tools
            model: Ollama model name to use (default: llama3.2)
        """
        self.tool_registry = tool_registry
        self.model = model
        self._verify_ollama_connection()
    
    def _verify_ollama_connection(self) -> None:
        """Verify Ollama is running and model is available."""
        try:
            # Try to list models to verify connection
            ollama.list()
        except Exception as e:
            print(f"Warning: Could not connect to Ollama: {e}")
            print("Make sure Ollama is running: 'ollama serve'")
    
    def create_plan(self, prompt: str) -> Plan:
        """
        Generate a structured plan from a natural language prompt.
        
        Args:
            prompt: User's natural language task description
            
        Returns:
            Plan object with validated steps
            
        Raises:
            ValueError: If plan generation or validation fails
        """
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        # Get available tools for context
        tools_info = self._format_tools_for_prompt()
        
        # Create system prompt
        system_prompt = self._build_system_prompt(tools_info)
        
        # Generate plan using LLM
        try:
            raw_plan = self._generate_plan_with_llm(system_prompt, prompt)
            plan = self._parse_and_validate_plan(raw_plan)
            return plan
        except Exception as e:
            # Fallback: try one more time with simplified prompt
            try:
                print(f"First attempt failed: {e}. Trying simplified prompt...")
                raw_plan = self._generate_plan_with_fallback(tools_info, prompt)
                plan = self._parse_and_validate_plan(raw_plan)
                return plan
            except Exception as fallback_error:
                raise ValueError(f"Failed to generate valid plan: {fallback_error}")
    
    def _format_tools_for_prompt(self) -> str:
        """Format available tools for inclusion in the prompt."""
        tools = self.tool_registry.list_tools()
        tools_str = ""
        
        for name, info in tools.items():
            tools_str += f"\nTool: {name}\n"
            tools_str += f"Description: {info['description']}\n"
            tools_str += f"Input Schema: {json.dumps(info['input_schema'], indent=2)}\n"
        
        return tools_str
    
    def _build_system_prompt(self, tools_info: str) -> str:
        """Build the system prompt for plan generation."""
        return f"""You are a task planning assistant. Your job is to convert user requests into structured execution plans.

Available Tools:
{tools_info}

You must respond with ONLY a valid JSON object (no other text) with this exact structure:
{{
  "steps": [
    {{
      "step_number": 1,
      "tool": "ToolName",
      "input": {{"param": "value"}},
      "reasoning": "why this step is needed"
    }}
  ]
}}

Rules:
1. Use only the tools listed above
2. Tool names must match exactly (e.g., "Calculator", "TodoStore")
3. Input must match the tool's schema
4. Steps should be sequential and logical
5. Respond ONLY with the JSON object, no markdown, no explanation

Examples:

User: "Add a todo to buy milk"
{{
  "steps": [
    {{
      "step_number": 1,
      "tool": "TodoStore",
      "input": {{"operation": "add", "title": "Buy milk"}},
      "reasoning": "Create a new todo item with the title 'Buy milk'"
    }}
  ]
}}

User: "Calculate 15 * 8 and add the result as a todo"
{{
  "steps": [
    {{
      "step_number": 1,
      "tool": "Calculator",
      "input": {{"expression": "15 * 8"}},
      "reasoning": "Calculate the multiplication result"
    }},how does the 
    {{
      "step_number": 2,
      "tool": "TodoStore",
      "input": {{"operation": "add", "title": "Result: 120"}},
      "reasoning": "Add the calculation result as a todo"
    }}
  ]
}}"""
    
    def _generate_plan_with_llm(self, system_prompt: str, user_prompt: str) -> str:
        """
        Generate plan using Ollama LLM.
        
        Args:
            system_prompt: System context and instructions
            user_prompt: User's task description
            
        Returns:
            Raw LLM response
        """
        try:
            response = ollama.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                options={
                    "temperature": 0.1,  # Low temperature for more consistent output
                    "num_predict": 1000,
                }
            )
            return response['message']['content']
        except Exception as e:
            raise ValueError(f"LLM generation failed: {e}")
    
    def _generate_plan_with_fallback(self, tools_info: str, user_prompt: str) -> str:
        """Simplified fallback plan generation."""
        simple_prompt = f"""Create a JSON plan with steps to accomplish: {user_prompt}

Available tools and their formats:
{tools_info}

Respond with ONLY this JSON format:
{{"steps": [{{"step_number": 1, "tool": "ToolName", "input": {{}}, "reasoning": "explanation"}}]}}"""
        
        response = ollama.chat(
            model=self.model,
            messages=[{"role": "user", "content": simple_prompt}],
            options={"temperature": 0.1}
        )
        return response['message']['content']
    
    def _parse_and_validate_plan(self, raw_response: str) -> Plan:
        """
        Parse LLM response and validate the plan.
        
        Args:
            raw_response: Raw text from LLM
            
        Returns:
            Validated Plan object
            
        Raises:
            ValueError: If parsing or validation fails
        """
        # Extract JSON from response (handle markdown code blocks)
        json_str = self._extract_json(raw_response)
        
        # Parse JSON
        try:
            plan_data = json.loads(json_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in response: {e}")
        
        # Validate structure
        if "steps" not in plan_data:
            raise ValueError("Plan missing 'steps' field")
        
        if not isinstance(plan_data["steps"], list):
            raise ValueError("'steps' must be a list")
        
        if len(plan_data["steps"]) == 0:
            raise ValueError("Plan must have at least one step")
        
        # Convert to Plan object and validate each step
        steps = []
        for i, step_data in enumerate(plan_data["steps"], 1):
            try:
                step = self._validate_step(step_data, i)
                steps.append(step)
            except Exception as e:
                raise ValueError(f"Invalid step {i}: {e}")
        
        return Plan(steps=steps)
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from text, handling markdown code blocks."""
        # Try to find JSON in markdown code block
        json_block = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', text, re.DOTALL)
        if json_block:
            return json_block.group(1)
        
        # Try to find raw JSON object
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json_match.group(0)
        
        # Return as-is and let JSON parser fail with clear error
        return text.strip()
    
    def _validate_step(self, step_data: Dict[str, Any], expected_number: int) -> PlanStep:
        """
        Validate a single plan step.
        
        Args:
            step_data: Raw step data from plan
            expected_number: Expected step number
            
        Returns:
            Validated PlanStep object
            
        Raises:
            ValueError: If validation fails
        """
        # Check required fields
        required_fields = ["step_number", "tool", "input", "reasoning"]
        for field in required_fields:
            if field not in step_data:
                raise ValueError(f"Missing required field: '{field}'")
        
        # Validate step number
        step_number = step_data["step_number"]
        if not isinstance(step_number, int):
            raise ValueError(f"step_number must be an integer, got {type(step_number)}")
        
        # Validate tool exists
        tool_name = step_data["tool"]
        if not self.tool_registry.exists(tool_name):
            raise ValueError(f"Tool '{tool_name}' not found. Available tools: {list(self.tool_registry.list_tools().keys())}")
        
        # Validate input against tool schema
        tool = self.tool_registry.get(tool_name)
        input_data = step_data["input"]
        
        if not isinstance(input_data, dict):
            raise ValueError(f"input must be a dictionary, got {type(input_data)}")
        
        if not tool.validate_input(input_data):
            raise ValueError(f"Input validation failed for tool '{tool_name}'. Expected schema: {tool.input_schema}")
        
        # Create PlanStep
        return PlanStep(
            step_number=step_number,
            tool=tool_name,
            input=input_data,
            reasoning=step_data["reasoning"]
        )

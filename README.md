# crane_ai_agent_project# AI Agent Runtime

A minimal AI agent runtime system that converts natural language prompts into structured execution plans and executes them with robust error handling and state management.

## System Architecture

### Overview

The system follows a clean, modular architecture with clear separation of concerns:

```
┌─────────────┐
│   REST API  │  FastAPI endpoints for user interaction
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Run Store  │  In-memory state management
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Planner   │  Ollama/gpt-oss for natural language → structured plans
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Orchestrator │  Sequential execution with retry logic
└──────┬──────┘
       │
       ▼
┌─────────────┐
│Tool Registry│  Calculator, TodoStore
└─────────────┘
```

### Core Components

1. **Tool System** (`src/tools/`)
   - `base.py`: Abstract Tool interface and ToolRegistry
   - `calculator.py`: Safe arithmetic evaluation using AST parsing
   - `todo_store.py`: In-memory CRUD operations for tasks

2. **Planning Component** (`src/planner/`)
   - `llm_planner.py`: Uses Ollama with gpt-oss to generate structured JSON plans
   - Validates plans against available tools and schemas
   - Includes fallback logic for model failures

3. **Execution Orchestrator** (`src/orchestrator/`)
   - `executor.py`: Sequential step execution
   - Configurable retry logic with exponential backoff
   - Complete execution history tracking
   - Idempotency checks for safe re-execution

4. **Storage Layer** (`src/storage/`)
   - `run_store.py`: Thread-safe in-memory run persistence

5. **REST API** (`src/main.py`)
   - FastAPI application with three endpoints
   - Asynchronous execution for non-blocking operations
   - Comprehensive error handling

### Data Flow

1. User submits prompt via `POST /runs`
2. System creates a Run object and saves it (status: PENDING)
3. Planner generates structured plan using Ollama
4. Orchestrator executes plan steps sequentially
5. Each step logs results to execution_log
6. Run status updates to COMPLETED or FAILED
7. User retrieves state via `GET /runs/{run_id}`

## Setup and Installation

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed and running
- gpt-oss model downloaded

### Installation Steps

1. **Clone or extract the repository**

```bash
cd agent-runtime
```

2. **Install Ollama** (if not already installed)

```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Or download from https://ollama.ai/download
```

3. **Pull the gpt-oss model**

```bash
ollama pull gpt-oss
```

4. **Start Ollama server** (in a separate terminal)

```bash
ollama serve
```

5. **Install Python dependencies**

```bash
pip install -r requirements.txt
```

## Running the Application

### Start the Server

```bash
python -m src.main
```

Or:

```bash
cd src
python main.py
```

The server will start on `http://localhost:8000`

You can access the auto-generated API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Verify Installation

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "service": "agent-runtime",
  "available_tools": ["Calculator", "TodoStore"]
}
```

## API Usage Examples

### 1. Health Check

```bash
curl http://localhost:8000/health
```

### 2. List Available Tools

```bash
curl http://localhost:8000/tools
```

### 3. Create a Run - Simple Todo

```bash
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Add a todo to buy milk"}'
```

Response:
```json
{
  "run_id": "abc-123-def",
  "status": "pending"
}
```

### 4. Create a Run - Multi-step

```bash
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Add a todo to buy milk, then show me all my tasks"}'
```

### 5. Create a Run - Calculator

```bash
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Calculate (41 * 7) + 13"}'
```

### 6. Get Run Status

```bash
curl http://localhost:8000/runs/abc-123-def
```

Response (completed):
```json
{
  "run_id": "abc-123-def",
  "prompt": "Add a todo to buy milk, then show me all my tasks",
  "status": "completed",
  "plan": {
    "plan_id": "plan-456",
    "steps": [
      {
        "step_number": 1,
        "tool": "TodoStore",
        "input": {"operation": "add", "title": "Buy milk"},
        "reasoning": "Create a new todo item"
      },
      {
        "step_number": 2,
        "tool": "TodoStore",
        "input": {"operation": "list"},
        "reasoning": "Retrieve all tasks to show the user"
      }
    ]
  },
  "execution_log": [
    {
      "step_number": 1,
      "tool": "TodoStore",
      "input": {"operation": "add", "title": "Buy milk"},
      "output": {
        "message": "Todo added successfully",
        "todo": {
          "id": "todo-789",
          "title": "Buy milk",
          "completed": false
        }
      },
      "status": "completed",
      "error": null,
      "attempt": 1
    },
    {
      "step_number": 2,
      "tool": "TodoStore",
      "input": {"operation": "list"},
      "output": {
        "count": 1,
        "todos": [
          {
            "id": "todo-789",
            "title": "Buy milk",
            "completed": false
          }
        ]
      },
      "status": "completed",
      "error": null,
      "attempt": 1
    }
  ],
  "created_at": "2024-01-15T10:00:00",
  "completed_at": "2024-01-15T10:00:05"
}
```

## Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_calculator.py
pytest tests/test_todo_store.py
pytest tests/test_planner.py
pytest tests/test_integration.py
```

### Run Tests with Coverage

```bash
pytest --cov=src tests/
```

### Run Tests Verbosely

```bash
pytest -v
```

### Test Organization

- `test_calculator.py`: Unit tests for Calculator tool (valid/invalid inputs, security)
- `test_todo_store.py`: Unit tests for TodoStore (CRUD operations, add/list flow)
- `test_planner.py`: Unit tests for planner validation (invalid tool, prompt handling)
- `test_integration.py`: Integration test for full system without requiring LLM

**Note**: Some tests are marked with `@pytest.mark.skip` because they require Ollama to be running. Remove the skip decorator to run them manually:

```bash
pytest -v tests/test_planner.py -k "not skip"
```

## Design Decisions and Trade-offs

### 1. LLM Choice: gpt-oss via Ollama

**Decision**: Use gpt-oss (13 gb) through Ollama

**Rationale**:
- Runs locally without API costs
- Fast inference for the task at hand
- Easy to set up and manage
- Good balance of capability and speed

**Trade-offs**:
- Slower than cloud APIs (Claude, GPT-4)
- May require multiple attempts for consistent JSON output
- Limited by local hardware

**Alternatives Considered**:
- GPT-4/Claude API: More reliable but requires API keys and costs
- Rule-based planner: More reliable but less flexible

### 2. Async Execution

**Decision**: Execute runs asynchronously in background

**Rationale**:
- Non-blocking API responses
- Better user experience (immediate run_id)
- LLM calls can take 2-10 seconds

**Trade-offs**:
- More complex state management
- Need polling to check status
- Could add WebSocket for real-time updates (not implemented)

### 3. In-Memory Storage

**Decision**: Use simple in-memory dictionaries for state

**Rationale**:
- Simplicity for POC
- No external dependencies
- Fast read/write operations
- Sufficient for demo purposes

**Trade-offs**:
- Data lost on restart
- Not suitable for production
- No persistence across sessions

**Production Alternative**: Would use PostgreSQL or Redis for persistence

### 4. Retry Logic with Exponential Backoff

**Decision**: 2 retries with 1s initial delay, 2x backoff

**Rationale**:
- Handles transient failures gracefully
- Prevents immediate re-execution hammering
- Configurable through ExecutionConfig

**Trade-offs**:
- Adds latency to failed operations
- May retry non-retriable errors
- Could be smarter about which errors to retry

### 5. Sequential Execution Only

**Decision**: Steps execute one at a time in order

**Rationale**:
- Simpler implementation
- Easier debugging and logging
- Many steps depend on previous results
- POC scope doesn't require parallelization

**Trade-offs**:
- Slower for independent steps
- No parallel execution optimization

**Future Enhancement**: Could add dependency graph and parallel execution

### 6. AST-Based Calculator

**Decision**: Use Python's AST parser instead of `eval()`

**Rationale**:
- Security: No code injection possible
- Safe: Only allow arithmetic operators
- Explicit: Clear what operations are permitted

**Trade-offs**:
- More complex implementation
- Limited to basic arithmetic
- No variables or functions

### 7. Prompt Engineering for JSON Output

**Decision**: Use structured prompts with examples

**Rationale**:
- Improves consistency of LLM output
- Reduces parsing errors
- Clear expectations set upfront

**Trade-offs**:
- Still not 100% reliable
- Requires fallback extraction logic
- May need prompt tuning for different models

## Known Limitations

### 1. LLM Reliability
- Llama 3.2 may occasionally generate invalid JSON
- Plan quality depends on model's understanding
- Fallback logic catches most issues but not all

### 2. No Persistence
- All state lost on server restart
- TodoStore doesn't persist between sessions
- No database integration

### 3. No Authentication
- Public API with no auth
- All users share the same TodoStore instance
- Not suitable for multi-user scenarios

### 4. Limited Error Recovery
- Some errors are not retriable (e.g., invalid tool)
- No circuit breaker for failing tools
- No partial plan re-execution

### 5. No Streaming
- Run status must be polled
- No real-time updates
- No progress indicators during execution

### 6. Tool Limitations
- Calculator: Only basic arithmetic (no variables, functions)
- TodoStore: No search, filtering, or sorting
- No tool for external API calls

### 7. Testing Gaps
- Integration tests require manual LLM setup
- No performance testing
- No load testing
- Limited edge case coverage

## Potential Improvements

### If I Had More Time

#### 1. Enhanced Observability (4-8 hours)
- **Structured logging**: Add proper logging throughout
- **Metrics**: Prometheus metrics for success rates, latency
- **Tracing**: OpenTelemetry for distributed tracing
- **Dashboards**: Grafana dashboards for monitoring

#### 2. Better LLM Integration (4-6 hours)
- **Function calling**: Use native function calling if available
- **Streaming**: Stream plan generation for progress updates
- **Caching**: Cache plans for similar prompts
- **Multiple models**: Support switching between models

#### 3. Persistence Layer (6-8 hours)
- **PostgreSQL**: Store runs, plans, and execution logs
- **SQLAlchemy**: ORM for database operations
- **Migrations**: Alembic for schema management
- **Redis**: Cache frequently accessed runs

#### 4. Advanced Execution (8-12 hours)
- **Parallel execution**: DAG-based execution for independent steps
- **Conditional logic**: Support if/else in plans
- **Loop support**: Iterate over collections
- **Human-in-the-loop**: Approval steps for sensitive operations

#### 5. Enhanced Error Handling (4-6 hours)
- **Circuit breakers**: Prevent cascade failures
- **Retry policies**: Per-tool retry configuration
- **Error classification**: Distinguish retriable vs permanent errors
- **Compensation**: Rollback mechanisms for failed transactions

#### 6. More Tools (2-4 hours each)
- **WebSearch**: Search the internet
- **Database**: Query databases
- **HTTP**: Make API calls
- **FileSystem**: Read/write files
- **Email**: Send emails

#### 7. Security Enhancements (6-8 hours)
- **Authentication**: JWT-based auth
- **Authorization**: Role-based access control
- **Rate limiting**: Prevent abuse
- **Input validation**: Enhanced security checks
- **Sandboxing**: Isolated tool execution

#### 8. Testing Improvements (4-6 hours)
- **Property-based testing**: Use Hypothesis
- **Load testing**: Locust or k6 tests
- **Integration tests**: Full end-to-end scenarios
- **Mock LLM**: Deterministic test fixtures

#### 9. Developer Experience (4-6 hours)
- **CLI tool**: Command-line interface for interactions
- **Docker**: Containerized deployment
- **Docker Compose**: One-command setup
- **Documentation**: API documentation, architecture diagrams

#### 10. UI/Frontend (12-16 hours)
- **Web UI**: React-based interface
- **Real-time updates**: WebSocket integration
- **Plan visualization**: Show execution progress
- **History view**: Browse past runs

## Project Structure

```
agent-runtime/
├── src/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application
│   ├── models.py               # Pydantic data models
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── base.py            # Tool interface & registry
│   │   ├── calculator.py      # Calculator tool
│   │   └── todo_store.py      # TodoStore tool
│   ├── planner/
│   │   ├── __init__.py
│   │   └── llm_planner.py     # Ollama-based planner
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   └── executor.py        # Execution orchestrator
│   └── storage/
│       ├── __init__.py
│       └── run_store.py       # In-memory storage
├── tests/
│   ├── __init__.py
│   ├── test_calculator.py     # Calculator tests
│   ├── test_todo_store.py     # TodoStore tests
│   ├── test_planner.py        # Planner tests
│   └── test_integration.py    # Integration tests
├── requirements.txt
├── README.md
└── .gitignore
```

## Troubleshooting

### Ollama Connection Issues

**Problem**: `Could not connect to Ollama`

**Solution**:
```bash
# Start Ollama server
ollama serve

# Verify it's running
ollama list
```

### Model Not Found

**Problem**: `model 'gpt-oss' not found`

**Solution**:
```bash
# Pull the model
ollama pull gpt-oss

# Verify it's available
ollama list
```

### JSON Parsing Errors

**Problem**: LLM returns invalid JSON

**Solution**:
- The system has fallback logic built-in
- Try the request again (LLM output varies)
- Consider using a different model (gpt-oss is more reliable than 1b)

### Port Already in Use

**Problem**: `Address already in use`

**Solution**:
```bash
# Find and kill the process using port 8000
lsof -ti:8000 | xargs kill -9

# Or change the port in main.py
uvicorn.run(app, host="0.0.0.0", port=8001)
```

## Technical Interview Discussion Points

### Architecture Questions
- Why did you choose this component structure?
- How would you scale this to handle 1000 concurrent users?
- What would be your first three priorities for production-readiness?

### Implementation Questions
- Walk me through how a request flows through the system
- How does the retry logic work and why did you choose exponential backoff?
- What security considerations did you implement in the Calculator?

### Testing Questions
- What's your testing strategy and why?
- What would you add to the test suite if you had more time?
- How would you test the LLM integration reliably?

### Trade-off Questions
- Why Ollama instead of cloud APIs?
- Why in-memory storage instead of a database?
- Why sequential execution instead of parallel?

## License

This is a technical assessment project for educational purposes.

---

**Author**: Bruce Wilkins  
**Date**: December 2025  
**Assignment**: AI Engineer Position - Crane  
**Time Spent**: ~4 hours
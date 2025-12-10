# Quick Start Guide

Get up and running in 5 minutes!

## Prerequisites Check

```bash
# Check Python version (needs 3.8+)
python --version

# Check if Ollama is installed
ollama --version
```

## Setup Steps

### 1. Install Ollama (if needed)

**macOS/Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download from https://ollama.ai/download

### 2. Start Ollama & Pull Model

```bash
# Terminal 1: Start Ollama server
ollama serve

# Terminal 2: Pull gpt-oss
ollama pull gpt-oss
```

### 3. Install Python Dependencies

```bash
cd agent-runtime
## Start the virtual environment
# on MacOS: 
  python -m venv venv 
  source venv/bin/activate

 # on Windows
  python -m venv venv
  .\venv\scripts\activate 


pip install -r requirements.txt
```

### 4. Run the Application

```bash
python -m src.main
```

You should see:
```
Starting AI Agent Runtime...
Available tools: ['Calculator', 'TodoStore']
...
Starting server on http://localhost:8000
```

### 5. Test It!

**Terminal 3:**

```bash
# Health check
curl http://localhost:8000/health

# Create a run
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Add a todo to buy milk, then show me all my tasks"}'

# Get the run_id from the response, then check status
curl http://localhost:8000/runs/YOUR_RUN_ID_HERE
```

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_calculator.py -v
```

## API Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Example Prompts to Try

```bash
# Simple calculation
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Calculate (41 * 7) + 13"}'

# Add a todo
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Add a todo to buy groceries"}'

# Multi-step: calculate and add as todo
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Calculate 15 times 8, then add the result as a todo"}'

# Add and list
curl -X POST http://localhost:8000/runs \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Add todos for buying milk and eggs, then show me all tasks"}'
```

## Troubleshooting

### "Could not connect to Ollama"
→ Make sure `ollama serve` is running in another terminal

### "model 'gpt-oss' not found"
→ Run `ollama pull gpt-oss`

### Port 8000 already in use
→ Change port in `src/main.py` or kill the process: `lsof -ti:8000 | xargs kill -9`

### Tests failing
→ Some integration tests require Ollama running. Skip them with: `pytest -v -k "not skip"`

## What's Next?

1. Read the full [README.md](README.md) for detailed architecture
2. Explore the code structure
3. Try modifying prompts and see how plans change
4. Run the test suite to understand the components
5. Check out the API docs at `/docs`

## Quick Architecture Overview

```
User Prompt → Planner (gpt-oss) → Structured Plan → Orchestrator → Tools → Results
                                                           ↓
                                                       Run Store
```

That's it! You're ready to explore the AI Agent Runtime. 🚀
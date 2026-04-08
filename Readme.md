# Pharmesol Inbound Sales Agent

AI-powered inbound sales agent that handles phone calls from pharmacies interested in Pharmesol's automation platform. Built with a FastAPI backend, React frontend, and OpenAI function calling.

## What It Does

- Identifies callers by phone number and personalizes the conversation with their pharmacy data
- Conducts natural, human-sounding sales conversations (not robotic chatbot talk)
- Sends follow-up emails and schedules demos/callbacks via tool calls
- Checks real-time availability for demo slots
- Streams responses in real-time via SSE

## Production Features

- **Tool registry** with Pydantic input validation and auto-generated OpenAI schemas
- **Code-enforced guardrails** — email verification, per-session rate limiting, pre-execution checks
- **Prompt injection protection** — external API data is sanitized before entering the system prompt
- **Retry/resilience** — exponential backoff on OpenAI API errors (429s, 500s, timeouts)
- **Bounded tool loops** — max iteration limit prevents runaway API spend
- **Context summarization** — older messages are summarized (not dropped) to manage token limits while preserving critical details
- **Output guardrails** — regex-based checks block dosage info, medical advice, unauthorized guarantees
- **Structured logging** — JSON logs with session tracking via structlog

## Setup

### Prerequisites

- Docker and Docker Compose
- An OpenAI API key

### 1. Configure environment

Create `backend/.env`:

```
OPEN_API_KEY=sk-your-openai-api-key
```

### 2. Run with Docker Compose

```bash
docker compose up --build
```

This starts:
- **Backend** at `http://localhost:8000`
- **Frontend** at `http://localhost:3000`

### 3. Run locally (without Docker)

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.server:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm start
```

### CLI mode

```bash
cd backend
python -m backend.main
```

## Project Structure

```
backend/
  config.py              # Centralized settings (pydantic-settings)
  agent.py               # SalesAgent — orchestration, streaming, retry
  context.py             # Summarization-based context management
  prompts.py             # Dynamic system prompt builder
  server.py              # FastAPI endpoints (SSE streaming)
  pharmacy_lookup.py     # Caller identification via phone lookup
  output_guardrails.py   # Response safety checks
  logging_config.py      # structlog configuration
  tools/
    registry.py          # ToolRegistry with Pydantic validation
    definitions.py       # Tool implementations
    guardrails.py        # Pre-execution safety checks
  availability.json      # Demo/callback slot data

frontend/
  src/
    api.js               # SSE streaming client
    App.js               # Root component
    components/
      PhoneEntry.js      # Phone input screen
      ChatWindow.jsx     # Chat interface
      MessageBubble.js   # Message display
      ActionBanner.js    # Tool action notifications
```

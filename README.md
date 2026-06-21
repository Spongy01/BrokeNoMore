# BrokeNoMore

**An AI agent that answers questions about your finances through natural conversation.**

![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)
![LangGraph](https://img.shields.io/badge/LangGraph-agent-orange)
![Langfuse](https://img.shields.io/badge/Langfuse-observability-purple)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Overview

BrokeNoMore lets you ask plain-English questions about your bank transactions and get precise, data-backed answers — no spreadsheets, no dashboards. You upload a CSV from Chase or Discover and the agent routes your question to the right SQL-backed tool, returning only what you asked for. The core design principle: the LLM never sees raw transaction data; it only sees structured tool results.

---

## Key Features

- **Conversational finance agent** — ask "How much did I spend on food in March?" and get a direct answer, not a table dump
- **Gemini function-calling loop** via LangGraph — structured tool selection with multi-turn memory and SQLite checkpointing
- **7 specialised tools** including a read-only SQL sandbox for arbitrary queries the other tools can't handle
- **CSV ingestion** for Chase Checking and Discover Credit with automatic keyword-based categorisation
- **JWT auth** with bcrypt password hashing and per-user data isolation
- **Langfuse observability** — every agent run is traced with span-level latency breakdowns and dataset-linked eval scores
- **Eval harness** — 30 golden Q&A pairs across 6 query categories, scored on both tool routing and answer accuracy

---

## Architecture

```
Client (Next.js)
       │
       ▼
  FastAPI  ──── JWT auth ────► User DB
       │
       ▼
  Agent Service (LangGraph)
       │
    ┌──┴──────────────────────────────┐
    │  call_model  ←──── call_tools   │
    │       │                 ▲       │
    │       └── tool_calls? ──┘       │
    └──────────────────────────────── ┘
               │
    ┌──────────┴────────────────────────────────────────────────┐
    │  get_spending_by_category   get_monthly_summary           │
    │  get_top_merchants          get_recent_transactions       │
    │  get_category_trend         get_spending_by_source        │
    │  execute_custom_sql  (read-only sandbox, LIMIT 500)       │
    └───────────────────────┬───────────────────────────────────┘
                            │
                     SQLAlchemy (async)
                            │
                        SQLite DB
```

The agent is a LangGraph `StateGraph` with two nodes — `call_model` and `call_tools` — connected by a conditional edge. The model runs until it stops emitting tool calls, at which point the graph exits. LangGraph's `AsyncSqliteSaver` checkpointer persists conversation state per thread, enabling multi-turn memory without re-sending history on every request.

The choice of direct Gemini function-calling over a higher-level framework (like LangChain agents or LangGraph's prebuilt ReAct) keeps the control flow explicit and easy to trace: each iteration is a single model call followed by synchronous tool dispatch, with no hidden retry logic or prompt manipulation.

---

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI, Uvicorn, Pydantic v2 |
| Agent orchestration | LangGraph (`StateGraph`), `AsyncSqliteSaver` |
| LLM | Google Gemini (`google-genai` SDK) |
| Database | SQLite via SQLAlchemy async (`aiosqlite`) |
| Auth | JWT (`python-jose`), bcrypt |
| Observability | Langfuse (traces, dataset evals, latency spans) |
| Frontend | Next.js 14, Tailwind CSS, shadcn/ui, TanStack Query |
| CSV ingestion | Chase Checking, Discover Credit (keyword categorisation) |

---

## Evaluation Results

The eval harness runs 30 golden questions against a seeded fixture database and scores each trace on two dimensions: **tool routing** (did the agent call the right tool?) and **answer accuracy** (did the response contain the expected values?).

**Best run results (across 5 eval runs):**

| Metric | Score |
|---|---|
| Tool routing accuracy | 90.0% (27/30) |
| Answer accuracy | 90.0% (27/30) |
| Overall (both correct) | 86.7% (26/30) |

Each question is scored independently on two dimensions — the agent must call the right tool *and* include the expected values in its response. The Langfuse metrics script (`eval/metrics.py`) also reports p50/p80/p95 latency and per-span breakdowns (`call_model`, `call_tools`, overhead) for any named run.

---

## Getting Started

### Prerequisites

- Python 3.12+
- A Google Gemini API key
- (Optional) Langfuse account for observability

### Installation

```bash
git clone https://github.com/yourusername/BrokeNoMore.git
cd BrokeNoMore

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### Environment setup

Create `backend/.env`:

```env
GEMINI_API_KEY=your_gemini_key_here
JWT_SECRET=your_secret_here
JWT_LIFETIME_SECONDS=3600

# Optional — for Langfuse tracing
LANGFUSE_PUBLIC_KEY=pk-...
LANGFUSE_SECRET_KEY=sk-...
LANGFUSE_HOST=https://cloud.langfuse.com
```

### Run the backend

```bash
cd backend
uvicorn main:app --reload
```

API available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

### Run the frontend

```bash
cd frontend
npm install
npm run dev
```

UI available at `http://localhost:3000`.

---

## Usage

### Example conversation

```
User:  How much did I spend on food last month?
Agent: You spent $153 on Food & Dining.

User:  Break that down by month for me.
Agent: Here's your Food & Dining trend:
       - February 2026: $49.50
       - March 2026: $60.00
       - April 2026: $43.50

User:  And which card did most of that go on?
Agent: Most of your food spending went on your Chase Checking account.
       You spent $669.48 total on Chase vs $243.49 on Discover.
```

### Upload transactions via CSV

```bash
curl -X POST http://localhost:8000/transactions/upload-csv \
  -H "Authorization: Bearer <your_token>" \
  -F "file=@chase_statement.csv" \
  -F "source=Chase Checking" \
  -F "user_id=<your_user_id>"
```

Supported sources: `Chase Checking`, `Discover Credit`.

### Query the agent directly

```bash
curl -X POST http://localhost:8000/query \
  -H "Authorization: Bearer <your_token>" \
  -H "Content-Type: application/json" \
  -d '{"message": "What are my top merchants?", "thread_id": "abc123"}'
```

### Run the eval harness

```bash
cd backend
python -m eval.runner --run-name my_eval_run

# View metrics for a completed run (requires Langfuse)
python -m eval.metrics --run-name my_eval_run
```

---

## Project Structure

```
BrokeNoMore/
├── backend/
│   ├── main.py                    # App factory, CORS, lifespan
│   ├── auth.py                    # JWT encode/decode, bcrypt, get_current_user
│   ├── database.py                # Async engine, session factory, init_db
│   ├── models.py                  # ORM models (Transaction, User, UserThread)
│   ├── schemas.py                 # Pydantic request/response schemas
│   ├── tools.py                   # 7 tool functions + TOOL_DEFINITIONS
│   ├── llm/
│   │   ├── base.py                # BaseLLMProvider ABC
│   │   └── gemini.py              # GeminiProvider + GeminiChatModel
│   ├── routers/
│   │   ├── auth.py                # Register, login, password reset
│   │   ├── transactions.py        # Upload CSV, add/list transactions
│   │   └── query.py               # POST /query → run_agent
│   ├── services/
│   │   ├── agent_service.py       # LangGraph graph, run_agent, Langfuse tracing
│   │   ├── transaction_service.py # Business logic
│   │   ├── csv_service.py         # Chase + Discover CSV parsers
│   │   └── user_service.py        # Auth business logic
│   ├── repositories/
│   │   └── transaction_repo.py    # All SQL — CRUD, aggregations
│   └── eval/
│       ├── questions.py           # 30 golden Q&A pairs
│       ├── fixtures.py            # In-memory test DB seeding
│       ├── runner.py              # Eval loop, Langfuse scoring
│       └── metrics.py             # Latency + accuracy reporting
├── frontend/
│   ├── app/
│   │   ├── (auth)/                # Login, register, password reset pages
│   │   └── (protected)/           # Dashboard, chat interface
│   ├── components/
│   │   ├── nav.tsx
│   │   └── upload-csv-dialog.tsx
│   └── lib/
│       ├── api.ts                 # Typed API client
│       ├── auth-context.tsx       # JWT storage + auth state
│       └── types.ts
└── requirements.txt
```

---

## Roadmap

- **Streaming responses** — token-by-token SSE via `POST /query/stream`
- **Clarification requests** — return `needs_clarification` flag when the agent lacks enough context (e.g. ambiguous date range) instead of guessing
- **Multi-bank support** — extend CSV parser to handle more institutions (Amex, Capital One, etc.)
- **Budgeting alerts** — notify when a category exceeds a user-defined monthly limit
- **Scheduled summaries** — weekly email digest of spending highlights

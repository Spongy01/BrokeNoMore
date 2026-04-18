# BrokeNoMore Backend — Architecture Review

Generated: 2026-04-18  
Reviewer: Claude Code (architectural review — no fixes applied)

---

## 1. File Responsibility Map

| File | Responsibility |
|---|---|
| `main.py` | App factory, CORS middleware, router registration, DB init on startup via lifespan |
| `database.py` | Async SQLAlchemy engine + session factory, `Base`, `init_db()`, `get_db()` dependency |
| `models.py` | `Transaction` ORM model (maps to `transactions` table) |
| `schemas.py` | Pydantic v2 request/response schemas: `TransactionCreate`, `TransactionResponse`, `QueryRequest`, `QueryResponse` |
| `repositories/transaction_repo.py` | All DB queries — CRUD + aggregations. No business logic. |
| `services/transaction_service.py` | Business logic wrapping the repo; converts ORM rows to `TransactionResponse` objects |
| `services/csv_service.py` | CSV parsing for Chase and Discover formats; produces `list[TransactionCreate]` |
| `services/agent_service.py` | Gemini function-calling loop; dispatches tool calls, manages conversation history |
| `tools.py` | Tool functions callable by the agent + `TOOL_DEFINITIONS` for Gemini |
| `llm/base.py` | `BaseLLMProvider` ABC, `LLMResponse`, `ToolCall` dataclasses |
| `llm/gemini.py` | `GeminiProvider` — normalises history/tools for the Gemini API, calls `generate_content` |
| `routers/transactions.py` | HTTP routes: `POST /transactions`, `GET /transactions`, `POST /transactions/upload-csv` |
| `routers/query.py` | HTTP route: `POST /query` |

---

## 2. Knowledge Graph — File-to-File Dependencies

```
main.py
  → database.py          (init_db)
  → models.py            (Transaction — ensures table is in metadata)
  → routers/transactions.py
  → routers/query.py

routers/transactions.py
  → database.py          (get_db dependency)
  → schemas.py           (TransactionCreate, TransactionResponse)
  → services/transaction_service.py
  → services/csv_service.py

routers/query.py
  → schemas.py           (QueryRequest, QueryResponse)
  → services/agent_service.py

services/transaction_service.py
  → repositories/transaction_repo.py
  → schemas.py           (TransactionCreate, TransactionResponse)

services/csv_service.py
  → schemas.py           (TransactionCreate)

services/agent_service.py
  → llm/base.py          (BaseLLMProvider)
  → llm/gemini.py        (GeminiProvider)
  → tools.py             (TOOL_DEFINITIONS, all 5 tool functions)

tools.py
  → database.py          (async_session_maker — opens its own sessions)
  → services/transaction_service.py

repositories/transaction_repo.py
  → models.py            (Transaction)
  → schemas.py           (TransactionCreate)
  → database.py          (AsyncSession type — indirectly via SQLAlchemy)

llm/gemini.py
  → llm/base.py          (BaseLLMProvider, LLMResponse, ToolCall)

llm/base.py
  (no project imports — pure dataclasses/ABC)

database.py
  (no project imports — entry point of the dependency graph)

models.py
  → database.py          (Base)

schemas.py
  (no project imports — pure Pydantic)
```

---

## 3. Request Flow Traces

### 3a. POST /transactions — Adding a single transaction

```
Client
  → POST /transactions  (JSON body: TransactionCreate)

routers/transactions.py :: create_transaction()
  1. FastAPI deserialises body into TransactionCreate (Pydantic validates amount, type, etc.)
  2. Injects AsyncSession via Depends(get_db)
  3. Calls _service.add_transaction(session, data)

services/transaction_service.py :: add_transaction()
  4. Calls _repo.create(session, data)

repositories/transaction_repo.py :: create()
  5. Constructs Transaction ORM row from data.model_dump()
  6. session.add(row)
  7. await session.commit()
  8. await session.refresh(row)
  9. Returns Transaction ORM object

services/transaction_service.py :: add_transaction()  (continued)
  10. TransactionResponse.model_validate(row)  [from_attributes=True converts ORM → Pydantic]
  11. Returns TransactionResponse

routers/transactions.py :: create_transaction()  (continued)
  12. FastAPI serialises TransactionResponse → JSON
  13. Returns HTTP 201

Client  ←  { id, user_id, amount, ..., created_at }
```

**No issues in this flow.**

---

### 3b. POST /query — Agent answering a question with tool calling

```
Client
  → POST /query  (JSON body: { user_id, message, history })

routers/query.py :: query()
  1. FastAPI deserialises body into QueryRequest
  2. Calls run_agent(user_id, message, history)

services/agent_service.py :: run_agent()
  3. Appends user message to history: [*history, {"role":"user","content":message}]
  4. Enters loop (max 5 iterations):

  --- Iteration 1 ---
  5. Calls provider.chat(history, TOOL_DEFINITIONS, SYSTEM_PROMPT)

  llm/gemini.py :: chat()
    6. normalize_history(history) → list[t.Content]
       - "user" roles → Content(role="user", parts=[Part(text=...)])
       - "assistant" roles → Content(role="model", parts=[Part(text=...)])
       - "tool" roles → Content(role="user", parts=[Part(function_response=...)])
    7. normalize_tools(TOOL_DEFINITIONS) → list[t.Tool]
    8. GenerateContentConfig with system_instruction + tools
    9. self._client.models.generate_content(...)   ← SYNCHRONOUS CALL (see issue #1)
    10. If response.function_calls → returns LLMResponse(text=None, tool_call=ToolCall(...))
        If response.text → returns LLMResponse(text=..., tool_call=None)

  services/agent_service.py  (continued)
  11. response.tool_call is not None  → enters tool dispatch branch
  12. Strips "user_id" from Gemini's args (security guard — uses server-side user_id)
  13. Calls the matching tool function, e.g. get_spending_by_category(user_id)

  tools.py :: get_spending_by_category()
    14. Opens its own session via async_session_maker
    15. Calls _service.get_spending_by_category(session, user_id)
    16. Returns { "spending": [{"category":..., "total":...}, ...] }

  services/agent_service.py  (continued)
  17. Appends tool result to history:
      [*history, {"role":"tool","content":json.dumps(result),"name":tc.name}]
      *** MODEL'S FUNCTION CALL TURN IS NOT STORED — see issue #2 ***
  18. Loops back to step 5

  --- Iteration 2 (if model calls another tool or returns text) ---
  19. history now contains [user_msg, tool_result] with NO model function_call between them
      Gemini receives two consecutive "user" role messages — malformed conversation

  --- When model returns text ---
  20. Appends assistant message to history
  21. Returns (response.text, history)

routers/query.py :: query()  (continued)
  22. Filters tool messages from returned history (clean_history)
  23. Returns QueryResponse(response=text, history=clean_history)

Client  ←  { response: "...", history: [...] }
```

---

## 4. Issues Found

### CRITICAL

---

**[CRITICAL-1] `llm/gemini.py:67` — Synchronous API call blocks the event loop**

```python
response = self._client.models.generate_content(...)   # line 67
```

`self._client.models.generate_content()` is a **synchronous** method from `google-genai`. The enclosing `chat()` is declared `async def`, but calling a sync network I/O function inside it blocks the entire uvicorn event loop for the duration of the Gemini API round-trip. Under concurrent load, this will stall all other requests.

Fix: use the async client:
```python
response = await self._client.aio.models.generate_content(...)
```

---

**[CRITICAL-2] `services/agent_service.py:56-63` — Model's function-call turn is never stored in history**

After Gemini returns a function call, only the tool *result* is appended to history:

```python
history = [
    *history,
    {"role": "tool", "content": json.dumps(result), "name": tc.name},
]
```

The model's own function-call turn is **never recorded**. On the very next loop iteration, `normalize_history` sends Gemini a conversation that looks like:

```
user: "what did I spend on food?"
user: FunctionResponse(name="get_spending_by_category", ...)   ← no model turn before this
```

Gemini's API requires a `model` turn containing the `FunctionCall` before the `FunctionResponse` (user role). Sending a `FunctionResponse` without a preceding `FunctionCall` from the model is a malformed request and will either raise an API error or produce garbage output on any multi-tool-call interaction.

The model's function call must be stored between the user message and the tool result:
```python
history = [
    *history,
    {"role": "assistant", "tool_call": {"name": tc.name, "args": tc.args}},   # add this
    {"role": "tool", "content": json.dumps(result), "name": tc.name},
]
```
And `normalize_history` must emit a `Content(role="model", parts=[Part(function_call=...)])` for that turn.

---

### WARNING

---

**[WARNING-1] `routers/transactions.py:29-43` — `POST /transactions/upload-csv` has no Pydantic response model**

The endpoint returns a raw `dict`:
```python
return {"imported": imported, "skipped": len(skipped), "skipped_transactions": skipped}
```
This violates the CLAUDE.md rule "Every route must have a Pydantic request AND response schema". If the shape ever changes, there is no compile-time or Swagger-visible contract.

---

**[WARNING-2] `services/transaction_service.py:61-72` — `get_category_trend` aggregates in Python, not SQL**

`get_by_category` fetches all matching ORM rows and the Python code does monthly bucketing with `defaultdict`. For users with many transactions in one category, this is an unbounded memory load. The aggregation should be a `GROUP BY strftime('%Y-%m', date)` query in the repository.

---

**[WARNING-3] `database.py:24-29` — Redundant `session.close()` in `get_db`**

```python
async with async_session_maker() as session:
    try:
        yield session
    finally:
        await session.close()    # redundant — async with already calls __aexit__
```

The `async with` context manager on `async_session_maker()` already calls `close()` on exit. The explicit `finally` block calls it a second time, which is harmless but misleading.

---

**[WARNING-4] `llm/gemini.py:68` — Model name hardcoded**

```python
model="gemini-2.5-flash",
```

Not configurable via env var or constructor argument. Any model change requires editing source code.

---

**[WARNING-5] `MIGRATION.md` references `compare_months()` tool which was never implemented**

MIGRATION.md's Phase 4 checklist mentions `compare_months()` among the tool functions. This function does not exist in `tools.py` and is not in `TOOL_DEFINITIONS`. The checklist is therefore misleading (it's marked `[X]`). Not a runtime error, but a documentation inconsistency.

---

### INFO

---

**[INFO-1] `tools.py:6` — Module-level `TransactionService` singleton**

```python
_service = TransactionService()
```

`TransactionService` (and the `TransactionRepository` inside it) are stateless, so sharing the singleton is safe. But `tools.py` opens its own DB sessions independently of the FastAPI `get_db` dependency, meaning tool calls run in separate transactions from the request session. Currently fine but worth knowing if transaction isolation ever matters.

---

**[INFO-2] `schemas.py:33` — `QueryRequest.history` is `list[dict]` with no structural validation**

Any dict can be in the history list. Malformed history (missing `role` or `content` keys) will cause a `KeyError` inside `normalize_history`. A typed `HistoryMessage` schema with a literal `role` field would catch this at the boundary.

---

**[INFO-3] `database.py:4` — DB path is relative to CWD**

```python
DATABASE_URL = "sqlite+aiosqlite:///./brokenomore.db"
```

The database is created relative to wherever uvicorn is launched. CLAUDE.md's command (`cd backend && uvicorn main:app`) is correct, but launching from a different directory silently creates a second DB file elsewhere.

---

**[INFO-4] `models.py` — `source` field absent from MIGRATION.md model spec**

MIGRATION.md lists model fields as `(id, user_id, amount, transaction_type, category, description, date, created_at)`. The `source` column was added in a later commit but MIGRATION.md was not updated. The code is correct; the documentation is stale.

---

## 5. TOOL_DEFINITIONS vs Function Signature Audit

| Tool name | Function signature | TOOL_DEFINITIONS params | Match? |
|---|---|---|---|
| `get_spending_by_category` | `(user_id: str)` | `user_id` required | ✓ |
| `get_monthly_summary` | `(user_id: str, year: int, month: int)` | `user_id`, `year`, `month` required | ✓ |
| `get_top_merchants` | `(user_id: str, limit: int = 5)` | `user_id` required, `limit` optional | ✓ |
| `get_recent_transactions` | `(user_id: str, limit: int = 10)` | `user_id` required, `limit` optional | ✓ |
| `get_category_trend` | `(user_id: str, category: str)` | `user_id`, `category` required | ✓ |

All five tool definitions exactly match their function signatures. The `user_id` stripping in `agent_service.py:53` is correctly applied for all tools.

---

## 6. Schema ↔ Service Return Type Audit

| Route | Request Schema | Service Return | Response Schema | Match? |
|---|---|---|---|---|
| `POST /transactions` | `TransactionCreate` | `TransactionResponse` | `TransactionResponse` | ✓ |
| `GET /transactions` | query param `user_id: str` | `list[TransactionResponse]` | `list[TransactionResponse]` | ✓ |
| `POST /transactions/upload-csv` | `UploadFile + Form` | `int` (count) | none (raw dict) | ⚠ WARNING-1 |
| `POST /query` | `QueryRequest` | `tuple[str, list[dict]]` | `QueryResponse` | ✓ |

---

## 7. Issue Summary

| ID | Severity | Location | Description |
|---|---|---|---|
| CRITICAL-1 | CRITICAL | `llm/gemini.py:67` | Sync `generate_content` blocks event loop |
| CRITICAL-2 | CRITICAL | `services/agent_service.py:56-63` | Model function-call turn not stored in history; malformed Gemini conversation on multi-step tool calls |
| WARNING-1 | WARNING | `routers/transactions.py:29-43` | `upload-csv` endpoint missing Pydantic response model |
| WARNING-2 | WARNING | `services/transaction_service.py:61-72` | Category trend aggregated in Python instead of SQL |
| WARNING-3 | WARNING | `database.py:26-28` | Redundant `session.close()` inside `async with` |
| WARNING-4 | WARNING | `llm/gemini.py:68` | Gemini model name hardcoded |
| WARNING-5 | WARNING | `MIGRATION.md` | `compare_months()` listed but never implemented |
| INFO-1 | INFO | `tools.py:6` | Tools use independent DB sessions outside request context |
| INFO-2 | INFO | `schemas.py:33` | `history: list[dict]` unvalidated — KeyError risk in normalize_history |
| INFO-3 | INFO | `database.py:4` | SQLite path relative to CWD |
| INFO-4 | INFO | `MIGRATION.md` | `source` field missing from documented model spec |

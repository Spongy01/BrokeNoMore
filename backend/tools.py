import re
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from database import async_session_maker
from services.transaction_service import TransactionService

_service = TransactionService()


def _to_float(value) -> float:
    return float(value) if isinstance(value, Decimal) else value


# --- SQL guard helpers ---

_BLACKLISTED_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE",
    "REPLACE", "PRAGMA", "ATTACH", "DETACH", "VACUUM", "REINDEX", "ANALYZE",
]
_BLACKLIST_RE = re.compile(
    r"\b(" + "|".join(_BLACKLISTED_KEYWORDS) + r")\b",
    re.IGNORECASE,
)


def _strip_sql_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", "", sql)
    return sql


def _validate_sql_guard(sql: str) -> str:
    cleaned = _strip_sql_comments(sql)
    statements = [s.strip() for s in cleaned.split(";") if s.strip()]
    if len(statements) > 1:
        raise ValueError("Multi-statement queries are not allowed.")
    normalized = cleaned.strip().upper()
    if not (normalized.startswith("SELECT") or normalized.startswith("WITH")):
        raise ValueError("Only SELECT or WITH queries are allowed.")
    match = _BLACKLIST_RE.search(cleaned)
    if match:
        raise ValueError(f"Forbidden keyword detected: {match.group().upper()}")
    if ":user_id" not in cleaned:
        raise ValueError(
            "Query must filter to your account. "
            "Add WHERE user_id = :user_id (or AND user_id = :user_id) to your query."
        )
    return cleaned


def _serialize_row(row_mapping) -> dict:
    result = {}
    for k, v in row_mapping.items():
        if isinstance(v, Decimal):
            result[k] = float(v)
        elif isinstance(v, (datetime, date)):  # datetime before date (subclass order matters)
            result[k] = v.isoformat()
        else:
            result[k] = v
    return result


# --- Tool functions ---

async def get_spending_by_category(user_id: str) -> dict:
    async with async_session_maker() as session:
        rows = await _service.get_spending_by_category(session, user_id)
    return {
        "spending": [
            {"category": r["category"], "total": _to_float(r["total"])}
            for r in rows
        ]
    }


async def get_monthly_summary(user_id: str, year: int, month: int) -> dict:
    async with async_session_maker() as session:
        result = await _service.get_monthly_summary(session, user_id, year, month)
    return {
        "credits": _to_float(result["credits"]),
        "debits": _to_float(result["debits"]),
        "net": _to_float(result["net"]),
    }


async def get_top_merchants(user_id: str, limit: int = 5) -> dict:
    async with async_session_maker() as session:
        rows = await _service.get_top_merchants(session, user_id, limit)
    return {
        "merchants": [
            {"merchant": r["merchant"], "total": _to_float(r["total"])}
            for r in rows
        ]
    }


async def get_recent_transactions(user_id: str, limit: int = 10) -> dict:
    async with async_session_maker() as session:
        rows = await _service.get_recent(session, user_id, limit)
    return {
        "transactions": [r.model_dump(mode="json") for r in rows]
    }


async def get_spending_by_source(user_id: str) -> dict:
    async with async_session_maker() as session:
        rows = await _service.get_spending_by_source(session, user_id)
    return {
        "by_source": [
            {"source": r["source"], "total": _to_float(r["total"])}
            for r in rows
        ]
    }


async def get_category_trend(user_id: str, category: str) -> dict:
    async with async_session_maker() as session:
        monthly = await _service.get_category_trend(session, user_id, category)
    return {
        "category": category,
        "monthly": [
            {"month": entry["month"], "total": _to_float(entry["total"])}
            for entry in monthly
        ],
    }


async def execute_custom_sql(user_id: str, sql_query: str) -> dict:
    try:
        cleaned_sql = _validate_sql_guard(sql_query)
    except ValueError as e:
        return {"error": str(e)}

    if not re.search(r"\bLIMIT\b", cleaned_sql, re.IGNORECASE):
        cleaned_sql = cleaned_sql.rstrip().rstrip(";") + " LIMIT 500"

    async with async_session_maker() as session:
        try:
            await session.execute(text("PRAGMA query_only = ON"))
            stmt = text(cleaned_sql).bindparams(user_id=user_id)
            result = await session.execute(stmt)
            rows = [_serialize_row(row._mapping) for row in result.fetchmany(500)]
            return {"rows": rows, "count": len(rows)}
        except SQLAlchemyError as e:
            orig = e.orig
            safe_msg = str(orig) if orig else type(e).__name__
            return {"error": f"Query execution failed: {safe_msg}"}


# --- Gemini function-calling definitions ---

TOOL_DEFINITIONS = [
    {
        "name": "get_spending_by_category",
        "description": "Returns total spending grouped by category for a user.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_monthly_summary",
        "description": "Returns total credits, debits, and net balance for a specific month.",
        "parameters": {
            "type": "object",
            "properties": {
                "year": {
                    "type": "integer",
                    "description": "The calendar year (e.g. 2026).",
                },
                "month": {
                    "type": "integer",
                    "description": "The calendar month as a number 1–12.",
                },
            },
            "required": ["year", "month"],
        },
    },
    {
        "name": "get_top_merchants",
        "description": "Returns the top merchants by total spend for a user.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of merchants to return (default 5).",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_recent_transactions",
        "description": "Returns the most recent transactions for a user.",
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of transactions to return (default 10).",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_spending_by_source",
        "description": "Returns total spending grouped by bank account or card source (e.g. Chase Checking, Discover Credit)",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "get_category_trend",
        "description": (
            "Returns monthly spend totals for a specific category to show spending trends over time. "
            "The category must be one of the following exact values: "
            "Food & Dining, Transportation, Shopping, Entertainment, "
            "Bills & Utilities, Health & Medical, Travel, Education, Other."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "description": (
                        "The spending category to analyse. Must be one of: "
                        "Food & Dining, Transportation, Shopping, Entertainment, "
                        "Bills & Utilities, Health & Medical, Travel, Education, Other."
                    ),
                },
            },
            "required": ["category"],
        },
    },
    {
        "name": "execute_custom_sql",
        "description": (
            "Executes a custom read-only SQL SELECT query against the transactions table. "
            "Use this for any question the other tools cannot answer — e.g. arbitrary date ranges, "
            "multi-column grouping, conditional aggregations, or uncommon filters.\n\n"
            "Schema: transactions(id INTEGER, user_id TEXT, amount REAL, "
            "transaction_type TEXT ('credit'|'debit'), category TEXT, description TEXT, "
            "date TEXT (YYYY-MM-DD), created_at TEXT, source TEXT)\n\n"
            "RULES:\n"
            "1. Always include WHERE user_id = :user_id — mandatory, bound server-side.\n"
            "2. :user_id is the only named parameter. All other values must be SQL literals.\n"
            "3. Only SELECT or WITH (CTE) queries. No INSERT/UPDATE/DELETE/DROP/etc.\n"
            "4. Single statement only — no semicolons.\n"
            "5. Always include a LIMIT clause (max 500)."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "sql_query": {
                    "type": "string",
                    "description": (
                        "A SQLite SELECT or WITH query. Must contain WHERE user_id = :user_id. "
                        "Example: SELECT category, SUM(amount) AS total FROM transactions "
                        "WHERE user_id = :user_id AND transaction_type = 'debit' "
                        "AND date >= '2026-01-01' GROUP BY category ORDER BY total DESC LIMIT 10"
                    ),
                },
            },
            "required": ["sql_query"],
        },
    },
]

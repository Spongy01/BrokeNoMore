from decimal import Decimal

from database import async_session_maker
from services.transaction_service import TransactionService

_service = TransactionService()


def _to_float(value) -> float:
    return float(value) if isinstance(value, Decimal) else value


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


# --- Gemini function-calling definitions ---

TOOL_DEFINITIONS = [
    {
        "name": "get_spending_by_category",
        "description": "Returns total spending grouped by category for a user.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user's unique identifier.",
                },
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "get_monthly_summary",
        "description": "Returns total credits, debits, and net balance for a specific month.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user's unique identifier.",
                },
                "year": {
                    "type": "integer",
                    "description": "The calendar year (e.g. 2024).",
                },
                "month": {
                    "type": "integer",
                    "description": "The calendar month as a number 1–12.",
                },
            },
            "required": ["user_id", "year", "month"],
        },
    },
    {
        "name": "get_top_merchants",
        "description": "Returns the top merchants by total spend for a user.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user's unique identifier.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of merchants to return (default 5).",
                },
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "get_recent_transactions",
        "description": "Returns the most recent transactions for a user.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user's unique identifier.",
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of transactions to return (default 10).",
                },
            },
            "required": ["user_id"],
        },
    },
    {
        "name": "get_category_trend",
        "description": "Returns monthly spend totals for a specific category to show spending trends over time.",
        "parameters": {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "The user's unique identifier.",
                },
                "category": {
                    "type": "string",
                    "description": "The spending category to analyse (e.g. 'food', 'transport').",
                },
            },
            "required": ["user_id", "category"],
        },
    },
]

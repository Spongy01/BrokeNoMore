import os
from datetime import date
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

TEST_DATABASE_URL = "sqlite+aiosqlite:///./eval_test.db"

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)

test_session_maker = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

SYNTHETIC_TRANSACTIONS = [
    # February 2026 — Chase Checking
    {"user_id": "eval_user", "amount": 12.50, "transaction_type": "debit", "category": "Food & Dining", "description": "Aldi", "date": "2026-02-01", "source": "Chase Checking"},
    {"user_id": "eval_user", "amount": 45.00, "transaction_type": "debit", "category": "Shopping", "description": "Amazon", "date": "2026-02-03", "source": "Chase Checking"},
    {"user_id": "eval_user", "amount": 9.99, "transaction_type": "debit", "category": "Entertainment", "description": "Spotify", "date": "2026-02-05", "source": "Chase Checking"},
    {"user_id": "eval_user", "amount": 35.00, "transaction_type": "debit", "category": "Transportation", "description": "Uber", "date": "2026-02-10", "source": "Chase Checking"},
    {"user_id": "eval_user", "amount": 22.00, "transaction_type": "debit", "category": "Food & Dining", "description": "Chipotle", "date": "2026-02-14", "source": "Chase Checking"},
    {"user_id": "eval_user", "amount": 60.00, "transaction_type": "debit", "category": "Bills & Utilities", "description": "Verizon", "date": "2026-02-18", "source": "Chase Checking"},
    {"user_id": "eval_user", "amount": 15.00, "transaction_type": "debit", "category": "Food & Dining", "description": "Dunkin", "date": "2026-02-20", "source": "Chase Checking"},
    {"user_id": "eval_user", "amount": 80.00, "transaction_type": "debit", "category": "Shopping", "description": "Amazon", "date": "2026-02-22", "source": "Chase Checking"},
    {"user_id": "eval_user", "amount": 25.00, "transaction_type": "debit", "category": "Transportation", "description": "Uber", "date": "2026-02-25", "source": "Chase Checking"},
    {"user_id": "eval_user", "amount": 2000.00, "transaction_type": "credit", "category": "Other", "description": "Payroll", "date": "2026-02-28", "source": "Chase Checking"},
    # March 2026 — Chase Checking
    {"user_id": "eval_user", "amount": 18.00, "transaction_type": "debit", "category": "Food & Dining", "description": "Aldi", "date": "2026-03-01", "source": "Chase Checking"},
    {"user_id": "eval_user", "amount": 55.00, "transaction_type": "debit", "category": "Shopping", "description": "Amazon", "date": "2026-03-03", "source": "Chase Checking"},
    {"user_id": "eval_user", "amount": 9.99, "transaction_type": "debit", "category": "Entertainment", "description": "Spotify", "date": "2026-03-05", "source": "Chase Checking"},
    {"user_id": "eval_user", "amount": 40.00, "transaction_type": "debit", "category": "Transportation", "description": "Uber", "date": "2026-03-08", "source": "Chase Checking"},
    {"user_id": "eval_user", "amount": 30.00, "transaction_type": "debit", "category": "Food & Dining", "description": "Chipotle", "date": "2026-03-12", "source": "Chase Checking"},
    {"user_id": "eval_user", "amount": 60.00, "transaction_type": "debit", "category": "Bills & Utilities", "description": "Verizon", "date": "2026-03-15", "source": "Chase Checking"},
    {"user_id": "eval_user", "amount": 12.00, "transaction_type": "debit", "category": "Food & Dining", "description": "Dunkin", "date": "2026-03-18", "source": "Chase Checking"},
    {"user_id": "eval_user", "amount": 120.00, "transaction_type": "debit", "category": "Shopping", "description": "Amazon", "date": "2026-03-20", "source": "Chase Checking"},
    {"user_id": "eval_user", "amount": 20.00, "transaction_type": "debit", "category": "Entertainment", "description": "Netflix", "date": "2026-03-25", "source": "Chase Checking"},
    {"user_id": "eval_user", "amount": 2000.00, "transaction_type": "credit", "category": "Other", "description": "Payroll", "date": "2026-03-28", "source": "Chase Checking"},
    # April 2026 — Discover Credit
    {"user_id": "eval_user", "amount": 8.50, "transaction_type": "debit", "category": "Food & Dining", "description": "Aldi", "date": "2026-04-01", "source": "Discover Credit"},
    {"user_id": "eval_user", "amount": 35.00, "transaction_type": "debit", "category": "Shopping", "description": "Walmart", "date": "2026-04-03", "source": "Discover Credit"},
    {"user_id": "eval_user", "amount": 14.99, "transaction_type": "debit", "category": "Entertainment", "description": "Netflix", "date": "2026-04-05", "source": "Discover Credit"},
    {"user_id": "eval_user", "amount": 25.00, "transaction_type": "debit", "category": "Transportation", "description": "Uber", "date": "2026-04-08", "source": "Discover Credit"},
    {"user_id": "eval_user", "amount": 20.00, "transaction_type": "debit", "category": "Food & Dining", "description": "Chipotle", "date": "2026-04-10", "source": "Discover Credit"},
    {"user_id": "eval_user", "amount": 50.00, "transaction_type": "debit", "category": "Health & Medical", "description": "CVS", "date": "2026-04-12", "source": "Discover Credit"},
    {"user_id": "eval_user", "amount": 15.00, "transaction_type": "debit", "category": "Food & Dining", "description": "Dunkin", "date": "2026-04-15", "source": "Discover Credit"},
    {"user_id": "eval_user", "amount": 45.00, "transaction_type": "debit", "category": "Shopping", "description": "Walmart", "date": "2026-04-18", "source": "Discover Credit"},
    {"user_id": "eval_user", "amount": 30.00, "transaction_type": "debit", "category": "Entertainment", "description": "Steam", "date": "2026-04-20", "source": "Discover Credit"},
    {"user_id": "eval_user", "amount": 500.00, "transaction_type": "credit", "category": "Other", "description": "Transfer", "date": "2026-04-25", "source": "Discover Credit"},
]


async def setup_eval_db() -> None:
    from models import Base, Transaction

    db_path = Path("eval_test.db")
    if db_path.exists():
        db_path.unlink()

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with test_session_maker() as session:
        rows = [
            Transaction(
                user_id=t["user_id"],
                amount=t["amount"],
                transaction_type=t["transaction_type"],
                category=t["category"],
                description=t["description"],
                date=date.fromisoformat(t["date"]),
                source=t["source"],
            )
            for t in SYNTHETIC_TRANSACTIONS
        ]
        session.add_all(rows)
        await session.commit()


async def teardown_eval_db() -> None:
    await test_engine.dispose()
    db_path = Path("eval_test.db")
    if db_path.exists():
        db_path.unlink()

from decimal import Decimal
from typing import Any

from sqlalchemy import select, func, extract
from sqlalchemy.ext.asyncio import AsyncSession

from models import Transaction
from schemas import TransactionCreate


class TransactionRepository:

    async def create(self, session: AsyncSession, data: TransactionCreate) -> Transaction:
        row = Transaction(**data.model_dump())
        session.add(row)
        await session.commit()
        await session.refresh(row)
        return row

    async def get_all(self, session: AsyncSession, user_id: str) -> list[Transaction]:
        result = await session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.date.desc())
        )
        return list(result.scalars().all())

    async def get_by_category(
        self, session: AsyncSession, user_id: str, category: str
    ) -> list[Transaction]:
        result = await session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id, Transaction.category == category)
            .order_by(Transaction.date.desc())
        )
        return list(result.scalars().all())

    async def get_spending_by_category(
        self, session: AsyncSession, user_id: str
    ) -> list[dict[str, Any]]:
        result = await session.execute(
            select(Transaction.category, func.sum(Transaction.amount).label("total"))
            .where(Transaction.user_id == user_id)
            .group_by(Transaction.category)
            .order_by(func.sum(Transaction.amount).desc())
        )
        return [{"category": row.category, "total": Decimal(str(row.total))} for row in result]

    async def get_monthly_summary(
        self, session: AsyncSession, user_id: str, year: int, month: int
    ) -> dict[str, Decimal]:
        result = await session.execute(
            select(
                Transaction.transaction_type,
                func.sum(Transaction.amount).label("total"),
            )
            .where(
                Transaction.user_id == user_id,
                extract("year", Transaction.date) == year,
                extract("month", Transaction.date) == month,
            )
            .group_by(Transaction.transaction_type)
        )
        rows = {row.transaction_type: Decimal(str(row.total)) for row in result}
        credits = rows.get("credit", Decimal("0"))
        debits = rows.get("debit", Decimal("0"))
        return {"credits": credits, "debits": debits, "net": credits - debits}

    async def get_top_merchants(
        self, session: AsyncSession, user_id: str, limit: int = 5
    ) -> list[dict[str, Any]]:
        result = await session.execute(
            select(Transaction.description, func.sum(Transaction.amount).label("total"))
            .where(Transaction.user_id == user_id)
            .group_by(Transaction.description)
            .order_by(func.sum(Transaction.amount).desc())
            .limit(limit)
        )
        return [{"merchant": row.description, "total": Decimal(str(row.total))} for row in result]

    async def get_recent(
        self, session: AsyncSession, user_id: str, limit: int = 10
    ) -> list[Transaction]:
        result = await session.execute(
            select(Transaction)
            .where(Transaction.user_id == user_id)
            .order_by(Transaction.date.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def bulk_create(
        self, session: AsyncSession, transactions: list[TransactionCreate]
    ) -> int:
        rows = [Transaction(**t.model_dump()) for t in transactions]
        session.add_all(rows)
        await session.commit()
        return len(rows)

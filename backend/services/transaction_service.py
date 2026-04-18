from collections import defaultdict

from sqlalchemy.ext.asyncio import AsyncSession

from repositories.transaction_repo import TransactionRepository
from schemas import TransactionCreate, TransactionResponse

_repo = TransactionRepository()


class TransactionService:

    async def add_transaction(
        self, session: AsyncSession, data: TransactionCreate
    ) -> TransactionResponse:
        row = await _repo.create(session, data)
        return TransactionResponse.model_validate(row)

    async def get_transactions(
        self, session: AsyncSession, user_id: str
    ) -> list[TransactionResponse]:
        rows = await _repo.get_all(session, user_id)
        return [TransactionResponse.model_validate(r) for r in rows]

    async def get_summary(self, session: AsyncSession, user_id: str) -> dict:
        spending = await _repo.get_spending_by_category(session, user_id)
        recent = await _repo.get_recent(session, user_id)
        return {
            "spending_by_category": spending,
            "recent_transactions": [
                TransactionResponse.model_validate(r).model_dump() for r in recent
            ],
        }

    async def get_spending_by_category(
        self, session: AsyncSession, user_id: str
    ) -> list[dict]:
        return await _repo.get_spending_by_category(session, user_id)

    async def get_monthly_summary(
        self, session: AsyncSession, user_id: str, year: int, month: int
    ) -> dict:
        return await _repo.get_monthly_summary(session, user_id, year, month)

    async def get_top_merchants(
        self, session: AsyncSession, user_id: str, limit: int = 5
    ) -> list[dict]:
        return await _repo.get_top_merchants(session, user_id, limit)

    async def get_recent(
        self, session: AsyncSession, user_id: str, limit: int = 10
    ) -> list[TransactionResponse]:
        rows = await _repo.get_recent(session, user_id, limit)
        return [TransactionResponse.model_validate(r) for r in rows]

    async def bulk_create(
        self, session: AsyncSession, transactions: list[TransactionCreate]
    ) -> int:
        return await _repo.bulk_create(session, transactions)

    async def get_category_trend(
        self, session: AsyncSession, user_id: str, category: str
    ) -> list[dict]:
        rows = await _repo.get_by_category(session, user_id, category)
        monthly: dict[str, float] = defaultdict(float)
        for row in rows:
            key = row.date.strftime("%Y-%m")
            monthly[key] += float(row.amount)
        return [
            {"month": month, "total": total}
            for month, total in sorted(monthly.items())
        ]

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

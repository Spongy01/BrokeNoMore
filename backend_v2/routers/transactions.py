from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import TransactionCreate, TransactionResponse
from services.transaction_service import TransactionService

router = APIRouter(prefix="/transactions", tags=["transactions"])
_service = TransactionService()


@router.post("", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    data: TransactionCreate,
    session: AsyncSession = Depends(get_db),
):
    return await _service.add_transaction(session, data)


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    user_id: str,
    session: AsyncSession = Depends(get_db),
):
    return await _service.get_transactions(session, user_id)


@router.post("/upload-csv")
async def upload_csv():
    # TODO: Phase 6 — implement CSV parsing and bulk insert
    return {"message": "CSV upload coming in Phase 6"}

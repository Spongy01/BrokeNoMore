from fastapi import APIRouter, Depends, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from schemas import TransactionCreate, TransactionResponse
from services.transaction_service import TransactionService
from services.csv_service import parse_csv

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
async def upload_csv(
    file: UploadFile,
    user_id: str = Form(...),
    source: str = Form(...),
    session: AsyncSession = Depends(get_db),
):
    content = await file.read()
    transactions, skipped = await parse_csv(content, user_id, source)
    imported = await _service.bulk_create(session, transactions)
    return {
        "imported": imported,
        "skipped": len(skipped),
        "skipped_transactions": skipped,
    }

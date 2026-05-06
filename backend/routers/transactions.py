from fastapi import APIRouter, Depends, Form, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from auth import get_current_user
from database import get_db
from models import User
from schemas import CsvUploadResponse, TransactionCreate, TransactionInput, TransactionResponse
from services.transaction_service import TransactionService
from services.csv_service import parse_csv

router = APIRouter(prefix="/transactions", tags=["transactions"])
_service = TransactionService()


@router.post("", response_model=TransactionResponse, status_code=201)
async def create_transaction(
    data: TransactionInput,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    full_data = TransactionCreate(**data.model_dump(), user_id=current_user.id)
    return await _service.add_transaction(session, full_data)


@router.get("", response_model=list[TransactionResponse])
async def list_transactions(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    return await _service.get_transactions(session, current_user.id)


@router.post("/upload-csv", response_model=CsvUploadResponse, status_code=200)
async def upload_csv(
    file: UploadFile,
    source: str = Form(...),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
):
    content = await file.read()
    transactions, skipped = await parse_csv(content, current_user.id, source)
    imported = await _service.bulk_create(session, transactions)
    return {
        "imported": imported,
        "skipped": len(skipped),
        "skipped_transactions": skipped,
    }

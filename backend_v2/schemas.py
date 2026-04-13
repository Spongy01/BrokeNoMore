from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class TransactionCreate(BaseModel):
    user_id: str
    amount: Decimal
    transaction_type: str
    category: str
    description: str
    date: date

    @field_validator("transaction_type")
    @classmethod
    def validate_transaction_type(cls, v: str) -> str:
        if v not in ("credit", "debit"):
            raise ValueError("transaction_type must be 'credit' or 'debit'")
        return v


class TransactionResponse(TransactionCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class QueryRequest(BaseModel):
    user_id: str
    message: str
    history: list[dict] = []


class QueryResponse(BaseModel):
    response: str
    history: list[dict]

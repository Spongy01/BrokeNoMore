from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


# ---------------------------------------------------------------------------
# Auth schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    created_at: datetime


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ---------------------------------------------------------------------------
# Transaction schemas
# ---------------------------------------------------------------------------

class TransactionInput(BaseModel):
    """Router-layer input — no user_id (injected from JWT)."""
    amount: Decimal
    transaction_type: str
    category: str
    description: str
    date: date
    source: str | None = None

    @field_validator("transaction_type")
    @classmethod
    def validate_transaction_type(cls, v: str) -> str:
        if v not in ("credit", "debit"):
            raise ValueError("transaction_type must be 'credit' or 'debit'")
        return v


class TransactionCreate(BaseModel):
    """Internal schema used by service → repo layers (includes user_id)."""
    user_id: str
    amount: Decimal
    transaction_type: str
    category: str
    description: str
    date: date
    source: str | None = None

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


class CsvUploadResponse(BaseModel):
    imported: int
    skipped: int
    skipped_transactions: list[str]


# ---------------------------------------------------------------------------
# Query schemas
# ---------------------------------------------------------------------------

class QueryRequest(BaseModel):
    message: str
    thread_id: str | None = None  # None starts a new conversation


class QueryResponse(BaseModel):
    response: str
    thread_id: str

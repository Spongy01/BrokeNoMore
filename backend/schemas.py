from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TransactionCreate(BaseModel):
    user_id: str
    amount: Decimal
    transaction_type: str
    category: str
    description: str
    date: date
    source: str | None = None  # "Chase Checking", "Discover Credit", or None

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


class UserMessage(BaseModel):
    role: Literal["user"]
    content: str


class ToolCallDetail(BaseModel):
    name: str
    args: dict


class AssistantMessage(BaseModel):
    role: Literal["assistant"]
    content: str | None = None
    tool_call: ToolCallDetail | None = None


class ToolResultMessage(BaseModel):
    role: Literal["tool"]
    content: str
    name: str


HistoryMessage = Annotated[
    Union[UserMessage, AssistantMessage, ToolResultMessage],
    Field(discriminator="role"),
]


class CsvUploadResponse(BaseModel):
    imported: int
    skipped: int
    skipped_transactions: list[str]


class QueryRequest(BaseModel):
    user_id: str
    message: str
    history: list[HistoryMessage] = []


class QueryResponse(BaseModel):
    response: str
    history: list[HistoryMessage]

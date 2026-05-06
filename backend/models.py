import uuid as uuid_lib

from sqlalchemy import Boolean, Column, Date, DateTime, Index, Integer, Numeric, String, Text
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid_lib.uuid4()))
    email = Column(String(255), nullable=False, unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    token = Column(String(86), primary_key=True)  # urlsafe_b64(32 bytes) → 43 chars; doubled for safety
    user_id = Column(String(36), nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)


class UserThread(Base):
    __tablename__ = "user_threads"

    thread_id = Column(String(64), primary_key=True)
    user_id = Column(String(36), nullable=False, index=True)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    transaction_type = Column(String(8), nullable=False)  # "credit" or "debit"
    category = Column(String(64), nullable=False)
    description = Column(Text, nullable=False)
    date = Column(Date, nullable=False)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    source = Column(String(64), nullable=True)  # "Chase Checking", "Discover Credit", or None

    __table_args__ = (
        Index("ix_transactions_user_id", "user_id"),
    )

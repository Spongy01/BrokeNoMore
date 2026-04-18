from sqlalchemy import Column, Integer, String, Numeric, Text, Date, DateTime, Index
from sqlalchemy.sql import func

from database import Base


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

from datetime import date
from decimal import Decimal
from typing import Literal
from datetime import datetime
from pydantic import ConfigDict
from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    description: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(gt=0)
    transaction_type: Literal["RECEITA", "DESPESA"]
    occurred_on: date
    category: str = Field(min_length=1, max_length=100)

class TransactionResponse(BaseModel):
    id: int
    description: str
    amount: Decimal
    transaction_type: Literal["RECEITA", "DESPESA"]
    occurred_on: date
    category: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TransactionReceipt(BaseModel):
    status: Literal["received"]
    transaction: TransactionResponse

class TransactionSummary(BaseModel):
    start_date: date
    end_date: date
    total_income: Decimal
    total_expenses: Decimal
    balance: Decimal


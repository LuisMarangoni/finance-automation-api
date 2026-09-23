from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    description: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(gt=0)
    transaction_type: Literal["RECEITA", "DESPESA"]
    occurred_on: date
    category: str = Field(min_length=1, max_length=100)
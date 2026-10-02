from decimal import Decimal
from enum import StrEnum
from pydantic import BaseModel, Field
from datetime import datetime
from pydantic import ConfigDict
from typing import Literal
from pydantic import BaseModel, Field, model_validator


class PayrollPeriodStatus(StrEnum):
    OPEN = "OPEN"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    CLOSED = "CLOSED"

class PayrollItemType(StrEnum):
    EARNING = "EARNING"
    DEDUCTION = "DEDUCTION"

class PayrollItemReviewStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"

class PayrollPeriodCreate(BaseModel):
    year: int = Field(ge=2020, le=2100)
    month: int = Field(ge=1, le=12)


class PayrollItemCreate(BaseModel):
    employee_id: int = Field(gt=0)
    code: str = Field(min_length=1, max_length=30)
    description: str = Field(min_length=1, max_length=200)
    amount: Decimal = Field(gt=0, decimal_places=2)
    item_type: PayrollItemType
    source: str = Field(default="MANUAL", min_length=1, max_length=30)

class PayrollPeriodResponse(BaseModel):
    id: int
    year: int
    month: int
    status: PayrollPeriodStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class PayrollItemResponse(BaseModel):
    id: int
    period_id: int
    employee_id: int
    code: str
    description: str
    amount: Decimal
    item_type: PayrollItemType
    source: str
    review_status: PayrollItemReviewStatus
    review_note: str | None
    reviewed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

class PayrollItemReviewRequest(BaseModel):
    status: Literal["APPROVED", "REJECTED"]
    note: str | None = Field(default=None, max_length=500)
    @model_validator(mode="after")
    def exigir_motivo_quando_rejeitado(self):
        if self.status == "REJECTED" and (
                self.note is None or not self.note.strip()
        ):
            raise ValueError("A note is required when rejecting a payroll item")

        return self

class PayrollPeriodSummaryResponse(BaseModel):
    period_id: int
    year: int
    month: int
    total_approved_earnings: Decimal
    total_approved_deductions: Decimal
    approved_balance: Decimal
    approved_items_count: int
    pending_items_count: int
    rejected_items_count: int
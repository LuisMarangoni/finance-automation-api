from decimal import Decimal
from enum import StrEnum
from pydantic import BaseModel, Field
from datetime import datetime
from pydantic import ConfigDict


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
    review_status: PayrollItemReviewStatus = PayrollItemReviewStatus.PENDING

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
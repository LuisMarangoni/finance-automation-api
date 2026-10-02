from fastapi import Depends, FastAPI, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.database import Base, engine, get_db
from typing import Literal
from fastapi import Query
from fastapi import Depends, FastAPI, Query, status
from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy import case, func, select
from datetime import date
from decimal import Decimal
from fastapi import Body
from pydantic import ValidationError
from app.csv_import import parse_transactions_csv
from app.models import PayrollPeriodModel, TransactionModel

from app.payroll_schemas import (
    PayrollItemCreate,
    PayrollItemResponse,
    PayrollPeriodCreate,
    PayrollPeriodResponse,
)

from app.models import (
    PayrollItemModel,
    PayrollPeriodModel,
    TransactionModel,
)

from app.schemas import (
    TransactionCreate,
    TransactionReceipt,
    TransactionResponse,
    TransactionSummary,
)


Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Finance Automation API",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "finance-automation-api",
    }


@app.post(
    "/transactions",
    status_code=status.HTTP_201_CREATED,
    response_model=TransactionReceipt,
)

def registrar_transacao(
        transacao: TransactionCreate,
        db: Session = Depends(get_db),
):
    registro = TransactionModel(**transacao.model_dump())

    db.add(registro)
    db.commit()
    db.refresh(registro)

    return TransactionReceipt(
        status="received",
        transaction=TransactionResponse.model_validate(registro),
    )

@app.post(
    "/transactions/import",
    status_code=status.HTTP_201_CREATED,
)
def importar_transacoes_csv(
        content: str = Body(..., media_type="text/csv"),
        db: Session = Depends(get_db),
):
    try:
        transacoes = parse_transactions_csv(content)
    except (ValueError, ValidationError) as erro:
        raise HTTPException(
            status_code=422,
            detail=str(erro),
        ) from erro

    registros = [
        TransactionModel(**transacao.model_dump())
        for transacao in transacoes
    ]

    try:
        db.add_all(registros)
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "status": "imported",
        "imported_count": len(registros),
    }

@app.get(
    "/transactions",
    response_model=list[TransactionResponse],
)

def listar_transacoes(
        transaction_type: Literal["RECEITA", "DESPESA"] | None = None,
        category: str | None = Query(default=None, min_length=1, max_length=100),
        limit: int = Query(default=50, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        db: Session = Depends(get_db),
):
    consulta = select(TransactionModel)

    if transaction_type is not None:
        consulta = consulta.where(
            TransactionModel.transaction_type == transaction_type
        )

    if category is not None:
        consulta = consulta.where(
            TransactionModel.category == category
        )

    consulta = (
        consulta
        .order_by(
            TransactionModel.occurred_on.desc(),
            TransactionModel.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    registros = db.scalars(consulta).all()

    return [
        TransactionResponse.model_validate(registro)
        for registro in registros
    ]

@app.get(
    "/transactions/summary",
    response_model=TransactionSummary,
)

def resumir_transacoes(
        start_date: date,
        end_date: date,
        db: Session = Depends(get_db),
):
    if start_date > end_date:
        raise HTTPException(
            status_code=422,
            detail="start_date must be on or before end_date",
        )

    receita = func.coalesce(
        func.sum(
            case(
                (
                    TransactionModel.transaction_type == "RECEITA",
                    TransactionModel.amount,
                ),
                else_=0,
            )
        ),
        0,
    ).label("total_income")

    despesa = func.coalesce(
        func.sum(
            case(
                (
                    TransactionModel.transaction_type == "DESPESA",
                    TransactionModel.amount,
                ),
                else_=0,
            )
        ),
        0,
    ).label("total_expenses")

    consulta = (
        select(receita, despesa)
        .where(TransactionModel.occurred_on >= start_date)
        .where(TransactionModel.occurred_on <= end_date)
    )

    resultado = db.execute(consulta).one()
    total_receitas = Decimal(str(resultado.total_income)).quantize(
        Decimal("0.01")
    )
    total_despesas = Decimal(str(resultado.total_expenses)).quantize(
        Decimal("0.01")
    )

    return TransactionSummary(
        start_date=start_date,
        end_date=end_date,
        total_income=total_receitas,
        total_expenses=total_despesas,
        balance=total_receitas - total_despesas,
    )

@app.post(
    "/payroll/periods",
    status_code=status.HTTP_201_CREATED,
    response_model=PayrollPeriodResponse,
)
def criar_competencia_folha(
        competencia: PayrollPeriodCreate,
        db: Session = Depends(get_db),
):
    existente = db.scalar(
        select(PayrollPeriodModel).where(
            PayrollPeriodModel.year == competencia.year,
            PayrollPeriodModel.month == competencia.month,
            )
    )

    if existente is not None:
        raise HTTPException(
            status_code=409,
            detail="Payroll period already exists",
        )

    periodo = PayrollPeriodModel(
        year=competencia.year,
        month=competencia.month,
        status="OPEN",
    )

    db.add(periodo)
    db.commit()
    db.refresh(periodo)

    return PayrollPeriodResponse.model_validate(periodo)

@app.post(
    "/payroll/periods/{period_id}/items",
    status_code=status.HTTP_201_CREATED,
    response_model=PayrollItemResponse,
)
def criar_item_folha(
        period_id: int,
        item: PayrollItemCreate,
        db: Session = Depends(get_db),
):
    periodo = db.get(PayrollPeriodModel, period_id)

    if periodo is None:
        raise HTTPException(
            status_code=404,
            detail="Payroll period not found",
        )

    registro = PayrollItemModel(
        period_id=period_id,
        employee_id=item.employee_id,
        code=item.code,
        description=item.description,
        amount=item.amount,
        item_type=item.item_type.value,
        source=item.source,
        review_status=item.review_status.value,
    )

    db.add(registro)
    db.commit()
    db.refresh(registro)

    return PayrollItemResponse.model_validate(registro)
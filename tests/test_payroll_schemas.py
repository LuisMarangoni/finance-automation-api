from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.payroll_schemas import (
    PayrollItemCreate,
    PayrollItemType,
    PayrollPeriodCreate,
)


def test_deve_validar_competencia_de_folha():
    competencia = PayrollPeriodCreate(
        year=2026,
        month=9,
    )

    assert competencia.year == 2026
    assert competencia.month == 9


def test_deve_validar_item_de_folha():
    item = PayrollItemCreate(
        employee_id=1,
        code="ATRASO",
        description="Desconto de atraso aprovado",
        amount=Decimal("45.50"),
        item_type=PayrollItemType.DEDUCTION,
        source="JOURNEY",
    )

    assert item.employee_id == 1
    assert item.amount == Decimal("45.50")
    assert item.item_type == PayrollItemType.DEDUCTION


def test_nao_deve_aceitar_mes_invalido():
    with pytest.raises(ValidationError):
        PayrollPeriodCreate(
            year=2026,
            month=13,
        )


def test_nao_deve_aceitar_valor_negativo_na_folha():
    with pytest.raises(ValidationError):
        PayrollItemCreate(
            employee_id=1,
            code="ATRASO",
            description="Desconto inválido",
            amount=Decimal("-10.00"),
            item_type=PayrollItemType.DEDUCTION,
        )
from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.schemas import TransactionCreate


def test_deve_validar_lancamento_financeiro():
    lancamento = TransactionCreate(
        description="Pagamento de energia",
        amount=Decimal("180.50"),
        transaction_type="DESPESA",
        occurred_on=date(2026, 9, 23),
        category="Moradia",
    )

    assert lancamento.description == "Pagamento de energia"
    assert lancamento.amount == Decimal("180.50")
    assert lancamento.transaction_type == "DESPESA"


def test_nao_deve_aceitar_valor_zero_ou_negativo():
    with pytest.raises(ValidationError):
        TransactionCreate(
            description="Lançamento inválido",
            amount=Decimal("0"),
            transaction_type="DESPESA",
            occurred_on=date(2026, 9, 23),
            category="Moradia",
        )
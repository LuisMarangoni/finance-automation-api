from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_deve_criar_competencia_de_folha():
    resposta = client.post(
        "/payroll/periods",
        json={
            "year": 2051,
            "month": 1,
        },
    )

    assert resposta.status_code == 201
    assert resposta.json()["year"] == 2051
    assert resposta.json()["month"] == 1
    assert resposta.json()["status"] == "OPEN"

def test_deve_criar_item_de_folha_pendente():
    periodo = client.post(
        "/payroll/periods",
        json={
            "year": 2051,
            "month": 2,
        },
    )

    assert periodo.status_code == 201
    period_id = periodo.json()["id"]

    resposta = client.post(
        f"/payroll/periods/{period_id}/items",
        json={
            "employee_id": 1,
            "code": "ATRASO",
            "description": "Desconto de atraso pendente de aprovação",
            "amount": "45.50",
            "item_type": "DEDUCTION",
            "source": "JOURNEY",
        },
    )

    assert resposta.status_code == 201
    assert resposta.json()["period_id"] == period_id
    assert resposta.json()["employee_id"] == 1
    assert resposta.json()["review_status"] == "PENDING"
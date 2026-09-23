from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    resposta = client.get("/health")

    assert resposta.status_code == 200
    assert resposta.json() == {
        "status": "ok",
        "service": "finance-automation-api",
    }

def test_criar_transacao_valida():
    resposta = client.post(
        "/transactions",
        json={
            "description": "Conta de energia",
            "amount": 189.90,
            "transaction_type": "DESPESA",
            "occurred_on": "2026-09-23",
            "category": "Moradia",
        },
    )

    assert resposta.status_code == 201
    assert resposta.json()["status"] == "received"
    assert resposta.json()["transaction"]["description"] == "Conta de energia"
    assert resposta.json()["transaction"]["transaction_type"] == "DESPESA"


def test_rejeitar_transacao_com_valor_invalido():
    resposta = client.post(
        "/transactions",
        json={
            "description": "Transação inválida",
            "amount": 0,
            "transaction_type": "DESPESA",
            "occurred_on": "2026-09-23",
            "category": "Outros",
        },
    )

    assert resposta.status_code == 422
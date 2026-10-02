from fastapi.testclient import TestClient
from decimal import Decimal
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

def test_item_criado_nao_pode_ser_aprovado_pela_requisicao():
    periodo = client.post(
        "/payroll/periods",
        json={
            "year": 2051,
            "month": 3,
        },
    )
    assert periodo.status_code == 201

    period_id = periodo.json()["id"]

    resposta = client.post(
        f"/payroll/periods/{period_id}/items",
        json={
            "employee_id": 1,
            "code": "BONUS",
            "description": "Bônus pendente de revisão",
            "amount": "100.00",
            "item_type": "EARNING",
            "source": "MANUAL",
            "review_status": "APPROVED",
        },
    )

    assert resposta.status_code == 201
    assert resposta.json()["review_status"] == "PENDING"

def test_deve_aprovar_item_pendente_e_registrar_revisao():
    periodo = client.post(
        "/payroll/periods",
        json={"year": 2051, "month": 4},
    )
    assert periodo.status_code == 201

    item = client.post(
        f"/payroll/periods/{periodo.json()['id']}/items",
        json={
            "employee_id": 1,
            "code": "BONUS",
            "description": "Bônus para revisão",
            "amount": "100.00",
            "item_type": "EARNING",
            "source": "MANUAL",
        },
    )
    assert item.status_code == 201

    resposta = client.patch(
        f"/payroll/items/{item.json()['id']}/review",
        json={
            "status": "APPROVED",
            "note": "Conferido pelo RH",
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()["review_status"] == "APPROVED"
    assert resposta.json()["review_note"] == "Conferido pelo RH"
    assert resposta.json()["reviewed_at"] is not None

def test_deve_rejeitar_item_com_motivo_e_impedir_nova_revisao():
    periodo = client.post(
        "/payroll/periods",
        json={"year": 2051, "month": 5},
    )
    assert periodo.status_code == 201

    item = client.post(
        f"/payroll/periods/{periodo.json()['id']}/items",
        json={
            "employee_id": 1,
            "code": "ATRASO",
            "description": "Desconto para revisão",
            "amount": "45.50",
            "item_type": "DEDUCTION",
            "source": "JOURNEY",
        },
    )
    assert item.status_code == 201

    item_id = item.json()["id"]

    rejeicao = client.patch(
        f"/payroll/items/{item_id}/review",
        json={
            "status": "REJECTED",
            "note": "Valor divergente; revisar o registro de jornada.",
        },
    )

    assert rejeicao.status_code == 200
    assert rejeicao.json()["review_status"] == "REJECTED"
    assert rejeicao.json()["review_note"] == (
        "Valor divergente; revisar o registro de jornada."
    )
    assert rejeicao.json()["reviewed_at"] is not None

    segunda_revisao = client.patch(
        f"/payroll/items/{item_id}/review",
        json={
            "status": "APPROVED",
            "note": "Tentativa de alterar a decisão.",
        },
    )

    assert segunda_revisao.status_code == 409

def test_deve_listar_itens_da_competencia_filtrando_por_status():
    periodo = client.post(
        "/payroll/periods",
        json={"year": 2051, "month": 6},
    )
    assert periodo.status_code == 201

    period_id = periodo.json()["id"]

    item_pendente = client.post(
        f"/payroll/periods/{period_id}/items",
        json={
            "employee_id": 1,
            "code": "ATRASO",
            "description": "Desconto aguardando revisao",
            "amount": "45.50",
            "item_type": "DEDUCTION",
            "source": "JOURNEY",
        },
    )
    assert item_pendente.status_code == 201

    item_aprovado = client.post(
        f"/payroll/periods/{period_id}/items",
        json={
            "employee_id": 2,
            "code": "BONUS",
            "description": "Bonus aprovado",
            "amount": "100.00",
            "item_type": "EARNING",
            "source": "MANUAL",
        },
    )
    assert item_aprovado.status_code == 201

    revisao = client.patch(
        f"/payroll/items/{item_aprovado.json()['id']}/review",
        json={
            "status": "APPROVED",
            "note": "Conferido pelo RH",
        },
    )
    assert revisao.status_code == 200

    todos = client.get(
        f"/payroll/periods/{period_id}/items",
    )
    assert todos.status_code == 200
    assert len(todos.json()) == 2

    pendentes = client.get(
        f"/payroll/periods/{period_id}/items",
        params={"review_status": "PENDING"},
    )
    assert pendentes.status_code == 200
    assert len(pendentes.json()) == 1
    assert pendentes.json()[0]["id"] == item_pendente.json()["id"]
    assert pendentes.json()[0]["review_status"] == "PENDING"

def test_resumo_soma_apenas_itens_aprovados():
    periodo = client.post(
        "/payroll/periods",
        json={"year": 2051, "month": 7},
    )
    assert periodo.status_code == 201

    period_id = periodo.json()["id"]

    def criar_item(code, amount, item_type):
        resposta = client.post(
            f"/payroll/periods/{period_id}/items",
            json={
                "employee_id": 1,
                "code": code,
                "description": f"Item {code}",
                "amount": amount,
                "item_type": item_type,
                "source": "MANUAL",
            },
        )
        assert resposta.status_code == 201
        return resposta.json()

    ganho = criar_item("BONUS", "100.00", "EARNING")
    desconto = criar_item("ATRASO", "30.00", "DEDUCTION")
    pendente = criar_item("FALTA", "20.00", "DEDUCTION")

    for item in (ganho, desconto):
        revisao = client.patch(
            f"/payroll/items/{item['id']}/review",
            json={
                "status": "APPROVED",
                "note": "Conferido pelo RH",
            },
        )
        assert revisao.status_code == 200

    resposta = client.get(
        f"/payroll/periods/{period_id}/summary",
    )

    assert resposta.status_code == 200
    resumo = resposta.json()
    assert Decimal(resumo["total_approved_earnings"]) == Decimal("100.00")
    assert Decimal(resumo["total_approved_deductions"]) == Decimal("30.00")
    assert Decimal(resumo["approved_balance"]) == Decimal("70.00")
    assert resumo["approved_items_count"] == 2
    assert resumo["pending_items_count"] == 1
    assert resumo["rejected_items_count"] == 0

def test_nao_envia_competencia_com_itens_pendentes_para_aprovacao():
    periodo = client.post(
        "/payroll/periods",
        json={"year": 2051, "month": 8},
    )
    assert periodo.status_code == 201

    period_id = periodo.json()["id"]

    item = client.post(
        f"/payroll/periods/{period_id}/items",
        json={
            "employee_id": 1,
            "code": "ATRASO",
            "description": "Desconto aguardando revisao",
            "amount": "45.50",
            "item_type": "DEDUCTION",
            "source": "JOURNEY",
        },
    )
    assert item.status_code == 201

    envio_pendente = client.post(
        f"/payroll/periods/{period_id}/submit",
    )
    assert envio_pendente.status_code == 409

    revisao = client.patch(
        f"/payroll/items/{item.json()['id']}/review",
        json={
            "status": "APPROVED",
            "note": "Conferido pelo RH",
        },
    )
    assert revisao.status_code == 200

    envio = client.post(
        f"/payroll/periods/{period_id}/submit",
    )
    assert envio.status_code == 200
    assert envio.json()["status"] == "PENDING_APPROVAL"

    segundo_envio = client.post(
        f"/payroll/periods/{period_id}/submit",
    )
    assert segundo_envio.status_code == 409

def test_deve_aprovar_e_encerrar_competencia():
    periodo = client.post(
        "/payroll/periods",
        json={"year": 2051, "month": 9},
    )
    assert periodo.status_code == 201

    period_id = periodo.json()["id"]

    item = client.post(
        f"/payroll/periods/{period_id}/items",
        json={
            "employee_id": 1,
            "code": "BONUS",
            "description": "Bonus para revisao",
            "amount": "100.00",
            "item_type": "EARNING",
            "source": "MANUAL",
        },
    )
    assert item.status_code == 201

    revisao_item = client.patch(
        f"/payroll/items/{item.json()['id']}/review",
        json={
            "status": "APPROVED",
            "note": "Conferido pelo RH",
        },
    )
    assert revisao_item.status_code == 200

    envio = client.post(
        f"/payroll/periods/{period_id}/submit",
    )
    assert envio.status_code == 200
    assert envio.json()["status"] == "PENDING_APPROVAL"

    aprovacao = client.post(
        f"/payroll/periods/{period_id}/approve",
    )
    assert aprovacao.status_code == 200
    assert aprovacao.json()["status"] == "APPROVED"

    encerramento = client.post(
        f"/payroll/periods/{period_id}/close",
    )
    assert encerramento.status_code == 200
    assert encerramento.json()["status"] == "CLOSED"

    novo_item = client.post(
        f"/payroll/periods/{period_id}/items",
        json={
            "employee_id": 1,
            "code": "EXTRA",
            "description": "Tentativa de alteracao apos encerramento",
            "amount": "10.00",
            "item_type": "EARNING",
            "source": "MANUAL",
        },
    )
    assert novo_item.status_code == 409
from fastapi.testclient import TestClient
from app.main import app
from uuid import uuid4
from decimal import Decimal


client = TestClient(app)


def test_deve_receber_lancamento_financeiro():
    resposta = client.post(
        "/transactions",
        json={
            "description": "Pagamento de energia",
            "amount": 180.50,
            "transaction_type": "DESPESA",
            "occurred_on": "2026-09-23",
            "category": "Moradia",
        },
    )

    assert resposta.status_code == 201
    assert resposta.json()["status"] == "received"
    assert resposta.json()["transaction"]["description"] == "Pagamento de energia"
    assert resposta.json()["transaction"]["transaction_type"] == "DESPESA"
    assert resposta.json()["transaction"]["category"] == "Moradia"

def test_deve_rejeitar_lancamento_com_valor_negativo():
    resposta = client.post(
        "/transactions",
        json={
            "description": "Pagamento inválido",
            "amount": -50.00,
            "transaction_type": "DESPESA",
            "occurred_on": "2026-09-23",
            "category": "Moradia",
        },
    )

    assert resposta.status_code == 422

def test_deve_listar_transacoes_persistidas():
    criacao = client.post(
        "/transactions",
        json={
            "description": "Conta de internet para listagem",
            "amount": 99.90,
            "transaction_type": "DESPESA",
            "occurred_on": "2026-09-24",
            "category": "Moradia",
        },
    )

    assert criacao.status_code == 201

    resposta = client.get("/transactions")

    assert resposta.status_code == 200
    assert any(
        transacao["description"] == "Conta de internet para listagem"
        for transacao in resposta.json()
    )

def test_deve_filtrar_transacoes_por_tipo_e_categoria():
    categoria = "Categoria para teste de filtro"

    transacoes = [
        {
            "description": "Despesa usada no filtro",
            "amount": 75.00,
            "transaction_type": "DESPESA",
            "occurred_on": "2026-09-24",
            "category": categoria,
        },
        {
            "description": "Receita usada no filtro",
            "amount": 300.00,
            "transaction_type": "RECEITA",
            "occurred_on": "2026-09-24",
            "category": categoria,
        },
    ]

    for transacao in transacoes:
        resposta_criacao = client.post(
            "/transactions",
            json=transacao,
        )
        assert resposta_criacao.status_code == 201

    resposta = client.get(
        "/transactions",
        params={
            "transaction_type": "DESPESA",
            "category": categoria,
        },
    )

    assert resposta.status_code == 200
    assert resposta.json()
    assert all(
        transacao["transaction_type"] == "DESPESA"
        and transacao["category"] == categoria
        for transacao in resposta.json()
    )

def test_deve_paginar_transacoes():
    categoria = f"Pagina-{uuid4().hex[:8]}"

    for descricao, data in [
        ("Primeira transação da página", "2026-09-23"),
        ("Segunda transação da página", "2026-09-24"),
    ]:
        criacao = client.post(
            "/transactions",
            json={
                "description": descricao,
                "amount": 50.00,
                "transaction_type": "DESPESA",
                "occurred_on": data,
                "category": categoria,
            },
        )
        assert criacao.status_code == 201

    parametros = {
        "transaction_type": "DESPESA",
        "category": categoria,
        "limit": 1,
    }

    primeira_pagina = client.get(
        "/transactions",
        params={**parametros, "offset": 0},
    )
    segunda_pagina = client.get(
        "/transactions",
        params={**parametros, "offset": 1},
    )

    assert primeira_pagina.status_code == 200
    assert segunda_pagina.status_code == 200
    assert len(primeira_pagina.json()) == 1
    assert len(segunda_pagina.json()) == 1
    assert (
            primeira_pagina.json()[0]["id"]
            != segunda_pagina.json()[0]["id"]
    )

def test_deve_calcular_resumo_financeiro_do_periodo():
    periodo = {
        "start_date": "2026-09-01",
        "end_date": "2026-09-30",
    }

    antes = client.get(
        "/transactions/summary",
        params=periodo,
    )
    assert antes.status_code == 200

    transacoes = [
        {
            "description": "Receita para teste de resumo",
            "amount": 1200.00,
            "transaction_type": "RECEITA",
            "occurred_on": "2026-09-27",
            "category": "Teste resumo",
        },
        {
            "description": "Despesa para teste de resumo",
            "amount": 200.25,
            "transaction_type": "DESPESA",
            "occurred_on": "2026-09-28",
            "category": "Teste resumo",
        },
    ]

    for transacao in transacoes:
        criacao = client.post("/transactions", json=transacao)
        assert criacao.status_code == 201

    depois = client.get(
        "/transactions/summary",
        params=periodo,
    )
    assert depois.status_code == 200

    renda_adicionada = (
            Decimal(str(depois.json()["total_income"]))
            - Decimal(str(antes.json()["total_income"]))
    )
    despesa_adicionada = (
            Decimal(str(depois.json()["total_expenses"]))
            - Decimal(str(antes.json()["total_expenses"]))
    )
    saldo_adicionado = (
            Decimal(str(depois.json()["balance"]))
            - Decimal(str(antes.json()["balance"]))
    )

    assert renda_adicionada == Decimal("1200.00")
    assert despesa_adicionada == Decimal("200.25")
    assert saldo_adicionado == Decimal("999.75")

def test_resumo_de_periodo_sem_transacoes_retorna_totais_zerados():
    resposta = client.get(
        "/transactions/summary",
        params={
            "start_date": "2099-01-01",
            "end_date": "2099-01-31",
        },
    )

    assert resposta.status_code == 200
    assert Decimal(str(resposta.json()["total_income"])) == Decimal("0.00")
    assert Decimal(str(resposta.json()["total_expenses"])) == Decimal("0.00")
    assert Decimal(str(resposta.json()["balance"])) == Decimal("0.00")


def test_resumo_rejeita_data_inicial_posterior_a_data_final():
    resposta = client.get(
        "/transactions/summary",
        params={
            "start_date": "2026-09-30",
            "end_date": "2026-09-01",
        },
    )

    assert resposta.status_code == 422

def test_deve_importar_transacoes_por_csv():
    conteudo = """description,amount,transaction_type,occurred_on,category
Salário importado,5000.00,RECEITA,2026-09-01,Importação
Conta de luz importada,180.50,DESPESA,2026-09-02,Importação
"""

    resposta = client.post(
        "/transactions/import",
        content=conteudo,
        headers={"Content-Type": "text/csv"},
    )

    assert resposta.status_code == 201
    assert resposta.json() == {
        "status": "imported",
        "imported_count": 2,
    }

    listagem = client.get(
        "/transactions",
        params={"category": "Importação"},
    )

    assert listagem.status_code == 200
    assert len(listagem.json()) >= 2
# Finance Automation API

API REST para automação financeira e processamento inicial de folha de pagamento.

## Funcionalidades

- Cadastro de receitas e despesas
- Listagem e filtragem de transações
- Resumo financeiro por período
- Importação de transações via CSV
- Criação de competências de folha de pagamento
- Criação de itens de folha pendentes de aprovação
- Revisão individual de itens com aprovação ou rejeição justificada
- Listagem de itens com filtro por estado de revisão
- Resumo da competência considerando somente itens aprovados
- Fluxo de competência: aberta, enviada para aprovação, aprovada e encerrada
- Bloqueio de inclusão de itens após o encerramento da competência
- Validação de dados com Pydantic
- Persistência com SQLAlchemy
- Execução com PostgreSQL via Docker
- Testes automatizados com Pytest

## Tecnologias

- Python 3.13+
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL
- Docker Compose
- Pytest

## Execução local

Ative o ambiente virtual:

```powershell
.\.venv\Scripts\Activate.ps1
```

Inicie a API:

```powershell
uvicorn app.main:app --reload
```

Documentação interativa:

```text
http://127.0.0.1:8000/docs
```

## Testes

Execute todos os testes com:

```powershell
python -m pytest -q
```

Os testes utilizam automaticamente o banco separado `finance_test.db`, recriado a cada execução por `tests/conftest.py`.

## Integração contínua

O GitHub Actions executa a suíte de testes em cada push para `master` e em pull requests direcionados a `master`. As dependências usadas pelo ambiente de CI estão declaradas em `requirements.txt`.

## Banco de dados

O banco de desenvolvimento local utiliza `finance.db`. Para executar com PostgreSQL, configure a variável `DATABASE_URL` conforme o ambiente e inicie o Docker Compose:

```powershell
docker compose up -d database
```

Arquivos locais de banco, ambientes virtuais e configurações da IDE não são versionados.

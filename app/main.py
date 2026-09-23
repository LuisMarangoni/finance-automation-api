from fastapi import FastAPI, status

from app.schemas import TransactionCreate

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


@app.post("/transactions", status_code=status.HTTP_201_CREATED)
def create_transaction(transaction: TransactionCreate):
    return {
        "status": "received",
        "transaction": transaction,
    }
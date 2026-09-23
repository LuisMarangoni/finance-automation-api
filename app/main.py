from fastapi import FastAPI

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
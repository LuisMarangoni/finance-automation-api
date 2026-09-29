import csv
from io import StringIO

from app.schemas import TransactionCreate


def parse_transactions_csv(content: str) -> list[TransactionCreate]:
    reader = csv.DictReader(StringIO(content))

    required_columns = {
        "description",
        "amount",
        "transaction_type",
        "occurred_on",
        "category",
    }

    if reader.fieldnames is None:
        raise ValueError("CSV must contain a header")

    missing_columns = required_columns - set(reader.fieldnames)

    if missing_columns:
        raise ValueError(
            f"Missing CSV columns: {', '.join(sorted(missing_columns))}"
        )

    return [
        TransactionCreate.model_validate(row)
        for row in reader
    ]
import os
from pathlib import Path


TEST_DATABASE = Path("finance_test.db")

# Garante que os testes nunca usem o banco de desenvolvimento.
os.environ["DATABASE_URL"] = "sqlite:///./finance_test.db"

# Reinicia somente o banco exclusivo dos testes a cada execução.
if TEST_DATABASE.exists():
    TEST_DATABASE.unlink()
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

FIXTURES = Path(__file__).parent / "fixtures"
PATIENTS = [f"patient_0{n}.fasta" for n in range(1, 6)]

def read_fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")

@pytest.fixture(scope="session")
def client() -> TestClient:
    return TestClient(app)

@pytest.fixture
def post_fasta(client):
    """Upload FASTA text to an endpoint as multipart field 'file'."""

    def _post(endpoint: str, text: str, **form_fields):
        files = {"file": ("query.fasta", text.encode("utf-8"), "text/plain")}
        return client.post(endpoint, files=files, data=form_fields)

    return _post
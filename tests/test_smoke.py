from fastapi.testclient import TestClient
from app.main import app

def test_app_starts():
    client = TestClient(app)
    assert client.get("/docs").status_code == 200
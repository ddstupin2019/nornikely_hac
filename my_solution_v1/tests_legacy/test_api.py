from fastapi.testclient import TestClient
from my_solution_v1.main import app

client = TestClient(app)

def test_status():
    response = client.get("/api/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

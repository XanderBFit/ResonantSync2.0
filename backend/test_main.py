from fastapi.testclient import TestClient

# Must import from main after mock setup in conftest if there are global imports
from main import app, verify_token

client = TestClient(app)

# Override verify_token dependency
def override_verify_token():
    return "test-uid-12345"

app.dependency_overrides[verify_token] = override_verify_token

def test_analyze_invalid_file_type():
    file_content = b"fake text data"
    files = {"file": ("test.txt", file_content, "text/plain")}
    response = client.post("/api/analyze", files=files)
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid file type"}

from fastapi.testclient import TestClient
from main import app, verify_token, db
from unittest.mock import MagicMock

client = TestClient(app)

# Mock user IDs
AUTH_UID = "authenticated-user-123"
OTHER_UID = "victim-user-456"

def override_verify_token():
    return AUTH_UID

app.dependency_overrides[verify_token] = override_verify_token

def test_get_vault_authorized_access():
    # Attempt to access AUTH_UID's own vault
    mock_query = MagicMock()
    mock_stream = MagicMock()
    mock_stream.return_value = []

    (db.collection.return_value
       .where.return_value
       .order_by.return_value
       .stream) = mock_stream

    response = client.get(f"/api/vault?uid={AUTH_UID}")

    assert response.status_code == 200
    db.collection.assert_called_with("processedTracks")
    db.collection.return_value.where.assert_called_with("uid", "==", AUTH_UID)

def test_get_vault_idor_vulnerability_blocked():
    # Attempt to access OTHER_UID's vault while authenticated as AUTH_UID
    # This should now return a 403.

    response = client.get(f"/api/vault?uid={OTHER_UID}")

    assert response.status_code == 403
    assert response.json() == {"detail": "Not authorized to access this vault"}

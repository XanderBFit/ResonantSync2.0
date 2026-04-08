from fastapi.testclient import TestClient
import pytest
from main import app
import os
import tempfile

client = TestClient(app)

@pytest.fixture
def mock_downloads(mocker):
    def side_effect(blob, local):
        # Create a dummy file to satisfy os.stat in zip_file.write
        os.makedirs(os.path.dirname(local), exist_ok=True)
        with open(local, "w") as f:
            f.write("dummy content")
        return True
    return mocker.patch("main.download_from_gcs", side_effect=side_effect)

def test_export_zip_limit(mocker, mock_downloads):
    # Mock read_disco_metadata
    mocker.patch("main.read_disco_metadata", return_value={"TIT2": "Test", "TPE1": "Artist"})

    # Create a list of more than 50 IDs
    ids = [f"id{i}" for i in range(55)]
    ids_str = ",".join(ids)

    response = client.get(f"/api/export-zip?fileIds={ids_str}")

    assert response.status_code == 400
    assert "Too many files" in response.json()["detail"]

def test_export_zip_success(mocker, mock_downloads):
    mocker.patch("main.read_disco_metadata", return_value={"TIT2": "Test", "TPE1": "Artist"})

    response = client.get("/api/export-zip?fileIds=id1,id2")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-zip-compressed"
    # FileResponse in recent FastAPI might quote the filename
    assert "ResonantCrab_Sync_Package_" in response.headers["content-disposition"]

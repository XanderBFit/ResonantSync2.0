import pytest
from fastapi.testclient import TestClient
from main import app
import os
import main

client = TestClient(app)

def test_export_zip_limit_enforced():
    # Now that we have a limit (50), 1000 should fail with 400
    large_number = 1000
    ids = ",".join([f"id_{i}" for i in range(large_number)])

    response = client.get(f"/api/export-zip?fileIds={ids}")
    assert response.status_code == 400
    assert "Maximum of 50 files allowed" in response.json()["detail"]

def test_export_zip_success(mocker):
    # Test a successful small export
    ids = "test1,test2"

    # Mock download_from_gcs to return True
    mocker.patch("main.download_from_gcs", return_value=True)
    # Mock read_disco_metadata
    mocker.patch("main.read_disco_metadata", return_value={"TIT2": "Title", "TPE1": "Artist"})

    # We need to mock the zip file writing because we don't have actual files
    # Actually, zip_file.write will fail if the file doesn't exist on disk.
    # Since we used tempfile.TemporaryDirectory and mp3_temp, we should mock those too or just create empty files.

    # Let's mock download_from_gcs to actually create the file
    def mock_download(blob, path):
        with open(path, "w") as f:
            f.write("fake content")
        return True

    mocker.patch("main.download_from_gcs", side_effect=mock_download)

    response = client.get(f"/api/export-zip?fileIds={ids}")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-zip-compressed"
    assert "ResonantCrab_Sync_Package_" in response.headers["content-disposition"]

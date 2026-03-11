import os
import tempfile
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_path_traversal_mitigation_export_zip(mocker):
    # Mock download_from_gcs so it doesn't actually try to download
    mock_download = mocker.patch("main.download_from_gcs", return_value=True)
    # Mock read_disco_metadata so it doesn't fail trying to read a non-existent file
    mock_read_metadata = mocker.patch("main.read_disco_metadata", return_value={"TIT2": "Test", "TPE1": "Artist"})

    # We must patch zipfile.ZipFile so it doesn't fail because the files don't actually exist
    mocker.patch("main.zipfile.ZipFile")

    # Send a request with a path traversal payload
    response = client.get("/api/export-zip?fileIds=../../../etc/passwd")

    assert response.status_code == 200

    # Check what was actually passed to download_from_gcs
    mock_download.assert_called()
    args, kwargs = mock_download.call_args_list[0]
    blob_name = args[0]
    local_path = args[1]

    # We expect "passwd.mp3" not "../../../etc/passwd.mp3"
    assert blob_name == "finalized/passwd.mp3"
    expected_local_path = os.path.join(tempfile.gettempdir(), "passwd_zip.mp3")
    assert local_path == expected_local_path

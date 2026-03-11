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

def test_path_traversal_mitigation_download_audio(mocker):
    # Mock download_from_gcs so it doesn't actually try to download
    mock_download = mocker.patch("main.download_from_gcs", return_value=True)
    # Mock read_disco_metadata so it doesn't fail trying to read a non-existent file
    mock_read_metadata = mocker.patch("main.read_disco_metadata", return_value={"TIT2": "Test", "TPE1": "Artist"})

    # Send a request with a path traversal payload
    response = client.get("/api/download/../../../etc/passwd")

    # The file_id should have been sanitized to "passwd"
    # Wait, the FileResponse will actually fail if the file doesn't exist.
    # We can just check the arguments passed to download_from_gcs!

    mock_download.assert_called_once()
    args, kwargs = mock_download.call_args
    blob_name = args[0]
    local_path = args[1]

    # We expect "passwd.mp3" not "../../../etc/passwd.mp3"
    assert blob_name == "finalized/passwd.mp3"
    import os
    import tempfile
    expected_local_path = os.path.join(tempfile.gettempdir(), "passwd_dl.mp3")
    assert local_path == expected_local_path

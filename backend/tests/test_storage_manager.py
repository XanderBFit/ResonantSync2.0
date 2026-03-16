import pytest
from unittest.mock import MagicMock, patch

# Mock google.cloud.storage.Client before importing storage_manager
with patch("google.cloud.storage.Client"):
    import backend.storage_manager as sm

def test_upload_to_gcs_success(mocker):
    # Setup mock
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob = MagicMock()

    mock_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    # We patch the module-level storage_client
    mocker.patch("backend.storage_manager.storage_client", mock_client)

    # Execute
    result = sm.upload_to_gcs("dummy/path.txt", "dummy_blob.txt")

    # Assert
    assert result is True
    mock_client.bucket.assert_called_once_with(sm.BUCKET_NAME)
    mock_bucket.blob.assert_called_once_with("dummy_blob.txt")
    mock_blob.upload_from_filename.assert_called_once_with("dummy/path.txt")

def test_upload_to_gcs_error(mocker):
    # Setup mock
    mock_client = MagicMock()
    mock_bucket = MagicMock()
    mock_blob = MagicMock()

    mock_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    # Make upload_from_filename raise an Exception
    mock_blob.upload_from_filename.side_effect = Exception("Upload failed")

    mocker.patch("backend.storage_manager.storage_client", mock_client)

    # Execute
    result = sm.upload_to_gcs("dummy/path.txt", "dummy_blob.txt")

    # Assert
    assert not result
    mock_client.bucket.assert_called_once_with(sm.BUCKET_NAME)
    mock_bucket.blob.assert_called_once_with("dummy_blob.txt")
    mock_blob.upload_from_filename.assert_called_once_with("dummy/path.txt")

import pytest
from unittest.mock import MagicMock, patch
from backend.storage_manager import upload_to_gcs, download_from_gcs, blob_exists, find_blob_by_prefix

@patch('backend.storage_manager.storage_client')
def test_upload_to_gcs_success(mock_storage_client):
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_storage_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    result = upload_to_gcs("local/path.mp3", "remote/path.mp3")

    assert result is True
    mock_storage_client.bucket.assert_called_with("resonant-crab-audio-storage-b4")
    mock_bucket.blob.assert_called_with("remote/path.mp3")
    mock_blob.upload_from_filename.assert_called_with("local/path.mp3")

@patch('backend.storage_manager.storage_client')
def test_upload_to_gcs_failure(mock_storage_client):
    mock_storage_client.bucket.side_effect = Exception("Upload failed")

    result = upload_to_gcs("local/path.mp3", "remote/path.mp3")

    assert result is False

@patch('backend.storage_manager.storage_client')
def test_download_from_gcs_success(mock_storage_client):
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_blob.exists.return_value = True
    mock_storage_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    result = download_from_gcs("remote/path.mp3", "local/path.mp3")

    assert result is True
    mock_blob.download_to_filename.assert_called_with("local/path.mp3")

@patch('backend.storage_manager.storage_client')
def test_download_from_gcs_not_found(mock_storage_client):
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_blob.exists.return_value = False
    mock_storage_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    result = download_from_gcs("remote/path.mp3", "local/path.mp3")

    assert result is False
    mock_blob.download_to_filename.assert_not_called()

@patch('backend.storage_manager.storage_client')
def test_download_from_gcs_failure(mock_storage_client):
    mock_storage_client.bucket.side_effect = Exception("Download failed")

    result = download_from_gcs("remote/path.mp3", "local/path.mp3")

    assert result is False

@patch('backend.storage_manager.storage_client')
def test_blob_exists_true(mock_storage_client):
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_blob.exists.return_value = True
    mock_storage_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    result = blob_exists("remote/path.mp3")

    assert result is True

@patch('backend.storage_manager.storage_client')
def test_blob_exists_false(mock_storage_client):
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_blob.exists.return_value = False
    mock_storage_client.bucket.return_value = mock_bucket
    mock_bucket.blob.return_value = mock_blob

    result = blob_exists("remote/path.mp3")

    assert result is False

@patch('backend.storage_manager.storage_client')
def test_blob_exists_failure(mock_storage_client):
    mock_storage_client.bucket.side_effect = Exception("Exists check failed")

    result = blob_exists("remote/path.mp3")

    assert result is False

@patch('backend.storage_manager.storage_client')
def test_find_blob_by_prefix_success(mock_storage_client):
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_blob.name = "remote/path.mp3"
    mock_storage_client.bucket.return_value = mock_bucket
    mock_bucket.list_blobs.return_value = [mock_blob]

    result = find_blob_by_prefix("remote/")

    assert result == "remote/path.mp3"
    mock_bucket.list_blobs.assert_called_with(prefix="remote/")

@patch('backend.storage_manager.storage_client')
def test_find_blob_by_prefix_none(mock_storage_client):
    mock_bucket = MagicMock()
    mock_storage_client.bucket.return_value = mock_bucket
    mock_bucket.list_blobs.return_value = []

    result = find_blob_by_prefix("remote/")

    assert result is None

@patch('backend.storage_manager.storage_client')
def test_find_blob_by_prefix_failure(mock_storage_client):
    mock_storage_client.bucket.side_effect = Exception("Prefix search failed")

    result = find_blob_by_prefix("remote/")

    assert result is None

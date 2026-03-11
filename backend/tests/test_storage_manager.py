import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage_manager import download_from_gcs
from unittest.mock import MagicMock, patch

@patch('storage_manager.storage_client')
def test_download_from_gcs_success(mock_storage_client):
    # Setup mock
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_blob.exists.return_value = True
    mock_bucket.blob.return_value = mock_blob
    mock_storage_client.bucket.return_value = mock_bucket

    # Test
    result = download_from_gcs("test_blob", "test_dest")

    # Assert
    assert result is True
    mock_blob.download_to_filename.assert_called_once_with("test_dest")

@patch('storage_manager.storage_client')
def test_download_from_gcs_not_found(mock_storage_client):
    # Setup mock
    mock_bucket = MagicMock()
    mock_blob = MagicMock()
    mock_blob.exists.return_value = False
    mock_bucket.blob.return_value = mock_blob
    mock_storage_client.bucket.return_value = mock_bucket

    # Test
    result = download_from_gcs("test_blob", "test_dest")

    # Assert
    assert result is False
    mock_blob.download_to_filename.assert_not_called()

@patch('storage_manager.storage_client')
def test_download_from_gcs_exception(mock_storage_client):
    # Setup mock
    mock_bucket = MagicMock()
    mock_bucket.blob.side_effect = Exception("Test Error")
    mock_storage_client.bucket.return_value = mock_bucket

    # Test
    result = download_from_gcs("test_blob", "test_dest")

    # Assert
    assert result is False

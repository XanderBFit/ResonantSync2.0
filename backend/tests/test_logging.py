import pytest
from unittest.mock import patch, MagicMock
import logging
import sys

# Mock external dependencies
sys.modules['mutagen'] = MagicMock()
sys.modules['mutagen.mp3'] = MagicMock()
sys.modules['mutagen.id3'] = MagicMock()
sys.modules['ffmpeg'] = MagicMock()

from backend.metadata_manager import strip_metadata

@patch('backend.metadata_manager.logger')
@patch('backend.metadata_manager.MP3')
def test_strip_metadata_logging(mock_mp3, mock_logger):
    # Setup mock to raise an exception
    mock_mp3.side_effect = Exception("Logging test error")

    # Execute
    result = strip_metadata("fake_path.mp3")

    # Assert
    assert result is False
    mock_logger.error.assert_called_once_with("Failed to strip metadata: Logging test error")

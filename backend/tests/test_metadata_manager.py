import pytest
from unittest.mock import patch, MagicMock
import sys

# Mock external dependencies that might be missing
sys.modules['mutagen'] = MagicMock()
sys.modules['mutagen.mp3'] = MagicMock()
sys.modules['mutagen.id3'] = MagicMock()
sys.modules['ffmpeg'] = MagicMock()

from backend.metadata_manager import strip_metadata, embed_disco_metadata

@patch('backend.metadata_manager.MP3')
def test_strip_metadata_success(mock_mp3):
    # Setup mock
    mock_audio_instance = MagicMock()
    mock_mp3.return_value = mock_audio_instance

    # Execute
    result = strip_metadata("fake_path.mp3")

    # Assert
    assert result is True
    mock_mp3.assert_called_once_with("fake_path.mp3", ID3=sys.modules['mutagen.id3'].ID3)
    mock_audio_instance.delete.assert_called_once()
    mock_audio_instance.save.assert_called_once()

@patch('backend.metadata_manager.MP3')
def test_strip_metadata_failure(mock_mp3):
    # Setup mock to raise an exception
    mock_mp3.side_effect = Exception("Some error")

    # Execute
    result = strip_metadata("fake_path.mp3")

    # Assert
    assert result is False
    mock_mp3.assert_called_once()

@patch('backend.metadata_manager.ID3')
@patch('backend.metadata_manager.TXXX')
def test_embed_disco_metadata_txxx_tags(mock_txxx, mock_id3):
    # Setup mock
    mock_audio_instance = MagicMock()
    mock_id3.return_value = mock_audio_instance

    data = {
        "grouping": "Group A",
        "mood": "Happy",
        "energy": "High",
        "valence": "0.8",
        "danceability": "0.9",
        "instruments": "Guitar",
        "vocalPresence": "Lead"
    }

    # Execute
    result = embed_disco_metadata("fake_path.mp3", data)

    # Assert
    assert result is True

    # Expected TXXX tags
    expected_txxx = [
        ('Grouping', 'Group A'),
        ('Mood', 'Happy'),
        ('Energy', 'High'),
        ('Valence', '0.8'),
        ('Danceability', '0.9'),
        ('Instruments', 'Guitar'),
        ('Vocal Presence', 'Lead')
    ]

    assert mock_txxx.call_count == len(expected_txxx)

    for desc, text in expected_txxx:
        mock_txxx.assert_any_call(encoding=3, desc=desc, text=text)

    assert mock_audio_instance.add.call_count >= len(expected_txxx)
    mock_audio_instance.save.assert_called_once()

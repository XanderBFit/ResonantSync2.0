import pytest
from unittest.mock import patch, MagicMock
import sys

# Mock external dependencies that might be missing
mutagen_mock = MagicMock()
sys.modules['mutagen'] = mutagen_mock

mutagen_mp3_mock = MagicMock()
sys.modules['mutagen.mp3'] = mutagen_mp3_mock

mutagen_id3_mock = MagicMock()
# Define a real exception class for ID3NoHeaderError so it can be caught in except blocks
class ID3NoHeaderError(Exception):
    pass
mutagen_id3_mock.ID3NoHeaderError = ID3NoHeaderError
sys.modules['mutagen.id3'] = mutagen_id3_mock

ffmpeg_mock = MagicMock()
sys.modules['ffmpeg'] = ffmpeg_mock

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
    mock_mp3.assert_called_once_with("fake_path.mp3", ID3=mutagen_id3_mock.ID3)
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
def test_embed_disco_metadata_success(mock_id3):
    # Setup mock
    mock_audio_instance = MagicMock()
    mock_id3.return_value = mock_audio_instance

    data = {
        "title": "Song Title",
        "artist": "Artist Name",
        "album": "Album Name",
        "bpm": 120,
        "key": "C Major",
        "genre": "Pop",
        "isrc": "US1234567890",
        "composer": "Composer Name",
        "publisher": "Publisher Name",
        "oneStop": True,
        "contactName": "Manager",
        "contactEmail": "manager@example.com",
        "contactPhone": "555-1234",
        "comments": "Great song!",
        "grouping": "Fast",
        "mood": "Happy",
        "energy": 8,
        "valence": 0.5,
        "danceability": 0.7,
        "instruments": "Piano",
        "vocalPresence": "Lead Vocal"
    }

    # Execute
    result = embed_disco_metadata("fake_path.mp3", data)

    # Assert
    assert result is True
    # Verify some key tags were added
    # We use ANY for text since it's wrapped in frame classes which we mocked
    assert mock_audio_instance.add.called
    mock_audio_instance.save.assert_called_once_with("fake_path.mp3", v2_version=3)


@patch('backend.metadata_manager.ID3')
def test_embed_disco_metadata_no_header(mock_id3):
    # Setup mock to raise ID3NoHeaderError then succeed
    mock_audio_instance = MagicMock()
    mock_id3.side_effect = [ID3NoHeaderError, mock_audio_instance]

    data = {"title": "New Header Song"}

    # Execute
    result = embed_disco_metadata("fake_path.mp3", data)

    # Assert
    assert result is True
    assert mock_id3.call_count == 2
    # First call with filename, second call without
    mock_id3.assert_any_call("fake_path.mp3")
    mock_id3.assert_any_call()
    mock_audio_instance.save.assert_called_once()


@patch('backend.metadata_manager.ID3')
def test_embed_disco_metadata_failure(mock_id3):
    # Setup mock
    mock_audio_instance = MagicMock()
    mock_id3.return_value = mock_audio_instance
    mock_audio_instance.save.side_effect = Exception("Save failed")

    data = {"title": "Failing Song"}

    # Execute
    result = embed_disco_metadata("fake_path.mp3", data)

    # Assert
    assert result is False
    mock_audio_instance.save.assert_called_once()

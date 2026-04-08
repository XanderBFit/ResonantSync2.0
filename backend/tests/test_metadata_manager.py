import pytest
from unittest.mock import patch, MagicMock, call
import sys

# Define a proper Exception for ID3NoHeaderError
class MockID3NoHeaderError(Exception):
    pass

# Setup mutagen.id3 mock
mutagen_id3 = MagicMock()
mutagen_id3.ID3NoHeaderError = MockID3NoHeaderError

# Mock ID3 frames
for frame in ['TIT2', 'TPE1', 'TALB', 'TBPM', 'TKEY', 'TCON', 'COMM', 'TSRC', 'TPUB', 'TCOM', 'TXXX', 'ID3']:
    setattr(mutagen_id3, frame, MagicMock())

sys.modules['mutagen'] = MagicMock()
sys.modules['mutagen.mp3'] = MagicMock()
sys.modules['mutagen.id3'] = mutagen_id3
sys.modules['ffmpeg'] = MagicMock()

from backend.metadata_manager import strip_metadata, embed_disco_metadata, read_disco_metadata

@patch('backend.metadata_manager.MP3')
def test_strip_metadata_success(mock_mp3):
    # Setup mock
    mock_audio_instance = MagicMock()
    mock_mp3.return_value = mock_audio_instance

    # Execute
    result = strip_metadata("fake_path.mp3")

    # Assert
    assert result is True
    mock_mp3.assert_called_once_with("fake_path.mp3", ID3=mutagen_id3.ID3)
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
        "title": "Test Title",
        "artist": "Test Artist",
        "album": "Test Album",
        "bpm": 120,
        "key": "Am",
        "genre": "Electronic",
        "isrc": "US1234567890",
        "composer": "Test Composer",
        "publisher": "Test Publisher",
        "oneStop": True,
        "contactName": "John Doe",
        "contactEmail": "john@example.com",
        "contactPhone": "555-1234",
        "comments": "Great track!",
        "grouping": "Test Grouping",
        "mood": "Happy",
        "energy": "High",
        "valence": "Positive",
        "danceability": "High",
        "instruments": "Synth, Drums",
        "vocalPresence": "Vocals"
    }

    # Execute
    result = embed_disco_metadata("fake_path.mp3", data)

    # Assert
    assert result is True
    mock_id3.assert_called_once_with("fake_path.mp3")

    # Verify some standard tags
    mutagen_id3.TIT2.assert_called_with(encoding=3, text="Test Title")
    mutagen_id3.TPE1.assert_called_with(encoding=3, text="Test Artist")
    mutagen_id3.TBPM.assert_called_with(encoding=3, text="120")

    # Verify publisher with One-Stop
    mutagen_id3.TPUB.assert_called_with(encoding=3, text="ONE-STOP (Test Publisher)")

    # Verify TXXX tags
    mutagen_id3.TXXX.assert_any_call(encoding=3, desc='Grouping', text="Test Grouping")
    mutagen_id3.TXXX.assert_any_call(encoding=3, desc='Mood', text="Happy")

    mock_audio_instance.save.assert_called_once_with("fake_path.mp3", v2_version=3)

@patch('backend.metadata_manager.ID3')
def test_embed_disco_metadata_no_header(mock_id3):
    # Setup mock to raise ID3NoHeaderError on first call, then return instance on second (new ID3())
    mock_audio_instance = MagicMock()
    mock_id3.side_effect = [MockID3NoHeaderError(), mock_audio_instance]

    data = {"title": "New Header"}

    # Execute
    result = embed_disco_metadata("fake_path.mp3", data)

    # Assert
    assert result is True
    assert mock_id3.call_count == 2
    mock_id3.assert_has_calls([call("fake_path.mp3"), call()])
    mock_audio_instance.add.assert_called()
    mock_audio_instance.save.assert_called_once()

@patch('backend.metadata_manager.ID3')
def test_embed_disco_metadata_failure(mock_id3):
    # Setup mock to raise a generic exception
    mock_id3.side_effect = Exception("Write error")

    # Execute
    result = embed_disco_metadata("fake_path.mp3", {})

    # Assert
    assert result is False

@patch('backend.metadata_manager.ID3')
def test_read_disco_metadata_success(mock_id3):
    # Setup mock audio with some frames
    mock_audio_instance = MagicMock()

    # Mocking audio.items()
    # Frames in mutagen often have a .text attribute which is a list
    mock_tit2 = MagicMock()
    mock_tit2.text = ["Read Title"]

    mock_txxx = MagicMock()
    mock_txxx.desc = "Mood"
    mock_txxx.text = ["Chill"]

    mock_comm = MagicMock()
    mock_comm.text = ["Comment info"]

    mock_audio_instance.items.return_value = [
        ("TIT2", mock_tit2),
        ("TXXX:Mood", mock_txxx),
        ("COMM", mock_comm)
    ]
    mock_id3.return_value = mock_audio_instance

    # Execute
    result = read_disco_metadata("fake_path.mp3")

    # Assert
    assert result == {
        "TIT2": "Read Title",
        "TXXX:Mood": "Chill",
        "COMM": "Comment info"
    }

@patch('backend.metadata_manager.ID3')
def test_read_disco_metadata_no_header(mock_id3):
    # Setup mock to raise ID3NoHeaderError
    mock_id3.side_effect = MockID3NoHeaderError()

    # Execute
    result = read_disco_metadata("fake_path.mp3")

    # Assert
    assert result == {}

import pytest
from unittest.mock import patch, MagicMock
import sys

# Mock external dependencies that might be missing
# ID3NoHeaderError must be an actual Exception class to be used in try/except
class ID3NoHeaderError(Exception):
    pass

id3_mock = MagicMock()
id3_mock.ID3NoHeaderError = ID3NoHeaderError
sys.modules['mutagen'] = MagicMock()
sys.modules['mutagen.mp3'] = MagicMock()
sys.modules['mutagen.id3'] = id3_mock
sys.modules['ffmpeg'] = MagicMock()

from backend.metadata_manager import strip_metadata, read_disco_metadata, embed_disco_metadata

@patch('backend.metadata_manager.MP3')
def test_strip_metadata_success(mock_mp3):
    # Setup mock
    mock_audio_instance = MagicMock()
    mock_mp3.return_value = mock_audio_instance

    # Execute
    result = strip_metadata("fake_path.mp3")

    # Assert
    assert result is True
    mock_mp3.assert_called_once_with("fake_path.mp3", ID3=id3_mock.ID3)
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
def test_read_disco_metadata_no_header(mock_id3):
    # Setup mock to raise ID3NoHeaderError
    mock_id3.side_effect = ID3NoHeaderError("No header")

    # Execute
    result = read_disco_metadata("fake_path.mp3")

    # Assert
    assert result == {}
    mock_id3.assert_called_once_with("fake_path.mp3")

@patch('backend.metadata_manager.ID3')
def test_read_disco_metadata_success(mock_id3):
    # Setup mock ID3 instance with frames
    mock_instance = MagicMock()

    # Mock frames
    frame_tit2 = MagicMock()
    frame_tit2.text = ["Test Title"]

    frame_txxx = MagicMock()
    frame_txxx.desc = "Mood"
    frame_txxx.text = ["Chill"]

    frame_comm = MagicMock()
    frame_comm.text = ["Contact Info"]

    mock_instance.items.return_value = [
        ("TIT2", frame_tit2),
        ("TXXX:Mood", frame_txxx),
        ("COMM:Sync & Contact Info:eng", frame_comm)
    ]

    mock_id3.return_value = mock_instance

    # Execute
    result = read_disco_metadata("fake_path.mp3")

    # Assert
    assert result == {
        "TIT2": "Test Title",
        "TXXX:Mood": "Chill",
        "COMM": "Contact Info"
    }
    mock_id3.assert_called_once_with("fake_path.mp3")

@patch('backend.metadata_manager.ID3')
@patch('backend.metadata_manager.TIT2')
@patch('backend.metadata_manager.TPE1')
@patch('backend.metadata_manager.TXXX')
@patch('backend.metadata_manager.COMM')
@patch('backend.metadata_manager.TPUB')
def test_embed_disco_metadata_success(mock_tpub, mock_comm, mock_txxx, mock_tpe1, mock_tit2, mock_id3):
    # Setup mock ID3
    mock_instance = MagicMock()
    mock_id3.return_value = mock_instance

    data = {
        "title": "Song Title",
        "artist": "Artist Name",
        "mood": "Happy",
        "publisher": "Pub Co",
        "oneStop": True,
        "contactName": "John",
        "contactEmail": "john@example.com",
        "contactPhone": "123"
    }

    # Execute
    result = embed_disco_metadata("fake_path.mp3", data)

    # Assert
    assert result is True
    mock_id3.assert_called_once_with("fake_path.mp3")

    # Check if add was called with expected frames
    # Using call_count because multiple TXXX might be added if more data was provided
    assert mock_instance.add.call_count >= 4

    mock_tit2.assert_called_with(encoding=3, text="Song Title")
    mock_tpe1.assert_called_with(encoding=3, text="Artist Name")
    mock_txxx.assert_any_call(encoding=3, desc='Mood', text='Happy')
    mock_tpub.assert_called_with(encoding=3, text="ONE-STOP (Pub Co)")

    # Check COMM
    mock_comm.assert_called_once()
    args, kwargs = mock_comm.call_args
    assert kwargs['encoding'] == 3
    assert "Contact: John / john@example.com / 123" in kwargs['text']

    mock_instance.save.assert_called_once_with("fake_path.mp3", v2_version=3)

@patch('backend.metadata_manager.ID3')
def test_embed_disco_metadata_failure(mock_id3):
    # Setup mock to raise an exception
    mock_id3.side_effect = Exception("Save failed")

    # Execute
    result = embed_disco_metadata("fake_path.mp3", {})

    # Assert
    assert result is False

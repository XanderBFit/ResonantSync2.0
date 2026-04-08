import pytest
from unittest.mock import patch, MagicMock, call
import sys

# Define a concrete exception for mutagen
class ID3NoHeaderError(Exception):
    pass

# Mock external dependencies
mutagen_id3_mock = MagicMock()
mutagen_id3_mock.ID3NoHeaderError = ID3NoHeaderError

# Mock all the frame classes used in metadata_manager
frames = ['ID3', 'TIT2', 'TPE1', 'TALB', 'TBPM', 'TKEY', 'TCON', 'COMM', 'TSRC', 'TPUB', 'TCOM', 'TXXX']
for frame in frames:
    setattr(mutagen_id3_mock, frame, MagicMock())

sys.modules['mutagen'] = MagicMock()
sys.modules['mutagen.mp3'] = MagicMock()
sys.modules['mutagen.id3'] = mutagen_id3_mock
sys.modules['ffmpeg'] = MagicMock()

from backend.metadata_manager import strip_metadata, embed_disco_metadata, read_disco_metadata, downmix_to_mp3

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

@patch('backend.metadata_manager.ffmpeg')
def test_downmix_to_mp3_success(mock_ffmpeg):
    # Setup mock
    mock_stream = MagicMock()
    mock_ffmpeg.input.return_value = mock_stream
    mock_ffmpeg.output.return_value = mock_stream

    # Execute
    result = downmix_to_mp3("input.wav", "output.mp3")

    # Assert
    assert result is True
    mock_ffmpeg.input.assert_called_once_with("input.wav")
    mock_ffmpeg.output.assert_called_once_with(mock_stream, "output.mp3", audio_bitrate='320k', format='mp3')
    mock_ffmpeg.run.assert_called_once_with(mock_stream, overwrite_output=True, quiet=True)

@patch('backend.metadata_manager.ffmpeg')
def test_downmix_to_mp3_failure(mock_ffmpeg):
    # Setup mock
    mock_ffmpeg.input.side_effect = Exception("FFmpeg error")

    # Execute
    result = downmix_to_mp3("input.wav", "output.mp3")

    # Assert
    assert result is False

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
    # Setup mock frames
    mock_tit2 = MagicMock()
    mock_tit2.text = ["Test Title"]

    mock_txxx_grouping = MagicMock()
    mock_txxx_grouping.desc = "Grouping"
    mock_txxx_grouping.text = ["Test Grouping"]

    mock_comm = MagicMock()
    mock_comm.text = ["Test Comment"]

    mock_audio_instance = MagicMock()
    mock_audio_instance.items.return_value = [
        ("TIT2", mock_tit2),
        ("TXXX:Grouping", mock_txxx_grouping),
        ("COMM:Sync & Contact Info:eng", mock_comm)
    ]
    mock_id3.return_value = mock_audio_instance

    # Execute
    result = read_disco_metadata("fake_path.mp3")

    # Assert
    assert result == {
        "TIT2": "Test Title",
        "TXXX:Grouping": "Test Grouping",
        "COMM": "Test Comment"
    }

@patch('backend.metadata_manager.ID3')
@patch('backend.metadata_manager.TIT2')
@patch('backend.metadata_manager.TPE1')
@patch('backend.metadata_manager.TPUB')
@patch('backend.metadata_manager.COMM')
@patch('backend.metadata_manager.TXXX')
def test_embed_disco_metadata_success(mock_txxx, mock_comm, mock_tpub, mock_tpe1, mock_tit2, mock_id3):
    # Setup mock
    mock_audio_instance = MagicMock()
    mock_id3.return_value = mock_audio_instance

    data = {
        "title": "Title",
        "artist": "Artist",
        "publisher": "Publisher",
        "oneStop": True,
        "grouping": "Grouping",
        "comments": "Comments",
        "contactName": "Name",
        "contactEmail": "Email",
        "contactPhone": "Phone"
    }

    # Execute
    result = embed_disco_metadata("fake_path.mp3", data)

    # Assert
    assert result is True
    mock_id3.assert_called_with("fake_path.mp3")
    mock_tit2.assert_called_once_with(encoding=3, text="Title")
    mock_tpe1.assert_called_once_with(encoding=3, text="Artist")
    mock_tpub.assert_called_once_with(encoding=3, text="ONE-STOP (Publisher)")
    mock_comm.assert_called_once()
    assert mock_txxx.call_count == 1
    mock_audio_instance.save.assert_called_once_with("fake_path.mp3", v2_version=3)

@patch('backend.metadata_manager.ID3')
def test_embed_disco_metadata_new_id3(mock_id3):
    # Setup mock: first call raises NoHeaderError, second (new ID3) succeeds
    mock_id3.side_effect = [ID3NoHeaderError(), MagicMock()]

    data = {"title": "Title"}

    # Execute
    result = embed_disco_metadata("fake_path.mp3", data)

    # Assert
    assert result is True
    assert mock_id3.call_count == 2
    mock_id3.assert_has_calls([call("fake_path.mp3"), call()])

@patch('backend.metadata_manager.ID3')
def test_embed_disco_metadata_failure(mock_id3):
    # Setup mock
    mock_audio_instance = MagicMock()
    mock_audio_instance.save.side_effect = Exception("Save failed")
    mock_id3.return_value = mock_audio_instance

    data = {"title": "Title"}

    # Execute
    result = embed_disco_metadata("fake_path.mp3", data)

    # Assert
    assert result is False

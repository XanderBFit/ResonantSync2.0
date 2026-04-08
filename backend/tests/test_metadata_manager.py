import pytest
from unittest.mock import patch, MagicMock, call
import sys

# Mock external dependencies that might be missing
# Create the exception classes needed for the mocks
class ID3NoHeaderError(Exception):
    pass

mutagen_id3 = MagicMock()
mutagen_id3.ID3NoHeaderError = ID3NoHeaderError
sys.modules['mutagen'] = MagicMock()
sys.modules['mutagen.mp3'] = MagicMock()
sys.modules['mutagen.id3'] = mutagen_id3
sys.modules['ffmpeg'] = MagicMock()

from backend.metadata_manager import strip_metadata, downmix_to_mp3, embed_disco_metadata, read_disco_metadata

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

@patch('backend.metadata_manager.ID3')
def test_read_disco_metadata_success(mock_id3):
    # Setup mock frames
    mock_tit2 = MagicMock()
    mock_tit2.text = ["Test Title"]

    mock_txxx_mood = MagicMock()
    mock_txxx_mood.desc = "Mood"
    mock_txxx_mood.text = ["Dark"]

    mock_comm = MagicMock()
    mock_comm.text = ["Some comments"]

    mock_audio_instance = MagicMock()
    mock_audio_instance.items.return_value = [
        ("TIT2", mock_tit2),
        ("TXXX:Mood", mock_txxx_mood),
        ("COMM", mock_comm)
    ]
    mock_id3.return_value = mock_audio_instance

    # Execute
    result = read_disco_metadata("test.mp3")

    # Assert
    assert result == {
        "TIT2": "Test Title",
        "TXXX:Mood": "Dark",
        "COMM": "Some comments"
    }
    mock_id3.assert_called_once_with("test.mp3")

@patch('backend.metadata_manager.ID3')
def test_read_disco_metadata_no_header(mock_id3):
    # Setup mock to raise ID3NoHeaderError
    mock_id3.side_effect = ID3NoHeaderError()

    # Execute
    result = read_disco_metadata("test.mp3")

    # Assert
    assert result == {}
    mock_id3.assert_called_once_with("test.mp3")

@patch('backend.metadata_manager.ffmpeg')
def test_downmix_to_mp3_success(mock_ffmpeg):
    # Setup mocks
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
    # Setup mocks to raise exception
    mock_ffmpeg.run.side_effect = Exception("FFmpeg error")

    # Execute
    result = downmix_to_mp3("input.wav", "output.mp3")

    # Assert
    assert result is False
    mock_ffmpeg.run.assert_called_once()

@patch('backend.metadata_manager.ID3')
@patch('backend.metadata_manager.TIT2')
@patch('backend.metadata_manager.TPE1')
@patch('backend.metadata_manager.TALB')
@patch('backend.metadata_manager.TBPM')
@patch('backend.metadata_manager.TKEY')
@patch('backend.metadata_manager.TCON')
@patch('backend.metadata_manager.TSRC')
@patch('backend.metadata_manager.TCOM')
@patch('backend.metadata_manager.TPUB')
@patch('backend.metadata_manager.COMM')
@patch('backend.metadata_manager.TXXX')
def test_embed_disco_metadata_success(
    mock_txxx, mock_comm, mock_tpub, mock_tcom, mock_tsrc,
    mock_tcon, mock_tkey, mock_tbpm, mock_talb, mock_tpe1, mock_tit2, mock_id3
):
    # Setup mocks
    mock_audio_instance = MagicMock()
    mock_id3.return_value = mock_audio_instance

    data = {
        "title": "Test Title",
        "artist": "Test Artist",
        "album": "Test Album",
        "bpm": 120,
        "key": "Cm",
        "genre": "Cinematic",
        "isrc": "US-XXX-XX-XXXXX",
        "composer": "Test Composer",
        "publisher": "Test Publisher",
        "oneStop": True,
        "contactName": "John Doe",
        "contactEmail": "john@example.com",
        "contactPhone": "1234567890",
        "comments": "Test Comments",
        "grouping": "Test Grouping",
        "mood": "Dark",
        "energy": "High",
        "valence": "Low",
        "danceability": "0.5",
        "instruments": "Drums",
        "vocalPresence": "None"
    }

    # Execute
    result = embed_disco_metadata("test.mp3", data)

    # Assert
    assert result is True
    mock_id3.assert_called_once_with("test.mp3")

    # Verify standard tags
    mock_tit2.assert_called_once_with(encoding=3, text="Test Title")
    mock_tpe1.assert_called_once_with(encoding=3, text="Test Artist")
    mock_talb.assert_called_once_with(encoding=3, text="Test Album")
    mock_tbpm.assert_called_once_with(encoding=3, text="120")
    mock_tkey.assert_called_once_with(encoding=3, text="Cm")
    mock_tcon.assert_called_once_with(encoding=3, text="Cinematic")
    mock_tsrc.assert_called_once_with(encoding=3, text="US-XXX-XX-XXXXX")
    mock_tcom.assert_called_once_with(encoding=3, text="Test Composer")

    # Verify Publisher with One-Stop
    mock_tpub.assert_called_once_with(encoding=3, text="ONE-STOP (Test Publisher)")

    # Verify Comments
    expected_contact_info = "Contact: John Doe / john@example.com / 1234567890"
    expected_comments = "Test Comments | " + expected_contact_info
    mock_comm.assert_called_once_with(encoding=3, lang='eng', desc='Sync & Contact Info', text=expected_comments)

    # Verify Custom TXXX Tags
    mock_txxx.assert_has_calls([
        call(encoding=3, desc='Grouping', text='Test Grouping'),
        call(encoding=3, desc='Mood', text='Dark'),
        call(encoding=3, desc='Energy', text='High'),
        call(encoding=3, desc='Valence', text='Low'),
        call(encoding=3, desc='Danceability', text='0.5'),
        call(encoding=3, desc='Instruments', text='Drums'),
        call(encoding=3, desc='Vocal Presence', text='None')
    ], any_order=True)

    # Verify save
    mock_audio_instance.save.assert_called_once_with("test.mp3", v2_version=3)

@patch('backend.metadata_manager.ID3')
def test_embed_disco_metadata_no_header(mock_id3):
    # Setup mock to raise ID3NoHeaderError on first call, then return instance on second call
    mock_id3.side_effect = [ID3NoHeaderError(), MagicMock()]

    data = {"title": "New Title"}

    # Execute
    result = embed_disco_metadata("test.mp3", data)

    # Assert
    assert result is True
    assert mock_id3.call_count == 2 # Once with path, once without

@patch('backend.metadata_manager.ID3')
def test_embed_disco_metadata_failure(mock_id3):
    # Setup mock to raise general exception
    mock_id3.side_effect = Exception("General error")

    data = {"title": "Error Title"}

    # Execute
    result = embed_disco_metadata("test.mp3", data)

    # Assert
    assert result is False

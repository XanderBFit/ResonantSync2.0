import sys
import os
import pytest
import numpy as np
from unittest.mock import MagicMock

# Add the backend directory to sys.path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audio_analyzer import measure_lufs, analyze_audio_file
from unittest.mock import patch

@patch('pyloudnorm.Meter')
@patch('librosa.load')
def test_measure_lufs_mono_success(mock_load, mock_meter):
    """Test LUFS measurement for a mono audio file."""
    # Mock librosa.load to return a 1D array (mono)
    mock_data = np.array([0.1, 0.2, 0.3])
    mock_rate = 44100
    mock_load.return_value = (mock_data, mock_rate)

    # Mock pyloudnorm.Meter
    mock_meter_instance = MagicMock()
    mock_meter_instance.integrated_loudness.return_value = -14.234
    mock_meter.return_value = mock_meter_instance

    result = measure_lufs("dummy_path.wav")

    # Check return value is rounded to 1 decimal place
    assert result == -14.2

    # Check that integrated_loudness was called with the correct shape (samples, channels)
    # The original array was shape (3,), so it should become (3, 1)
    args, _ = mock_meter_instance.integrated_loudness.call_args
    assert args[0].shape == (3, 1)

@patch('pyloudnorm.Meter')
@patch('librosa.load')
def test_measure_lufs_stereo_success(mock_load, mock_meter):
    """Test LUFS measurement for a stereo audio file."""
    # Mock librosa.load to return a 2D array (stereo: channels, samples)
    mock_data = np.array([[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]])
    mock_rate = 48000
    mock_load.return_value = (mock_data, mock_rate)

    # Mock pyloudnorm.Meter
    mock_meter_instance = MagicMock()
    mock_meter_instance.integrated_loudness.return_value = -10.56
    mock_meter.return_value = mock_meter_instance

    result = measure_lufs("dummy_path.wav")

    # Check return value is rounded to 1 decimal place
    assert result == -10.6

    # The original array was shape (2, 3), so it should become (3, 2)
    args, _ = mock_meter_instance.integrated_loudness.call_args
    assert args[0].shape == (3, 2)

@patch('pyloudnorm.Meter')
@patch('librosa.load')
def test_measure_lufs_silence(mock_load, mock_meter):
    """Test that silence or infinite LUFS value returns None."""
    mock_data = np.array([0.0, 0.0, 0.0])
    mock_rate = 44100
    mock_load.return_value = (mock_data, mock_rate)

    mock_meter_instance = MagicMock()
    mock_meter_instance.integrated_loudness.return_value = -np.inf
    mock_meter.return_value = mock_meter_instance

    result = measure_lufs("dummy_path.wav")

    assert result is None

@patch('pyloudnorm.Meter')
@patch('librosa.load')
def test_measure_lufs_nan(mock_load, mock_meter):
    """Test that NaN LUFS value returns None."""
    mock_data = np.array([0.0, 0.0, 0.0])
    mock_rate = 44100
    mock_load.return_value = (mock_data, mock_rate)

    mock_meter_instance = MagicMock()
    mock_meter_instance.integrated_loudness.return_value = np.nan
    mock_meter.return_value = mock_meter_instance

    result = measure_lufs("dummy_path.wav")

    assert result is None

@patch('librosa.load')
def test_measure_lufs_exception(mock_load):
    """Test that an exception during measurement gracefully returns None."""
    # Make librosa.load raise an exception
    mock_load.side_effect = Exception("File not found")

    result = measure_lufs("dummy_path.wav")

    assert result is None

# --- analyze_audio_file Tests ---

@patch('audio_analyzer.measure_lufs')
def test_analyze_audio_file_no_local_analysis(mock_lufs):
    """Test analyze_audio_file when local_analysis is None."""
    mock_lufs.return_value = -12.5

    result = analyze_audio_file("dummy_path.wav")

    assert result == {"energy": "0.5", "lufs": -12.5}

@patch('audio_analyzer.measure_lufs')
def test_analyze_audio_file_with_local_analysis_missing_energy(mock_lufs):
    """Test analyze_audio_file adds energy if missing."""
    mock_lufs.return_value = -10.0
    local_analysis = {"tempo": 120}

    result = analyze_audio_file("dummy_path.wav", local_analysis)

    assert result == {"tempo": 120, "energy": "0.5", "lufs": -10.0}
    # Ensure local_analysis wasn't mutated
    assert local_analysis == {"tempo": 120}

@patch('audio_analyzer.measure_lufs')
def test_analyze_audio_file_with_local_analysis_has_energy(mock_lufs):
    """Test analyze_audio_file preserves existing energy."""
    mock_lufs.return_value = -11.0
    local_analysis = {"energy": "0.8", "tempo": 130}

    result = analyze_audio_file("dummy_path.wav", local_analysis)

    assert result == {"energy": "0.8", "tempo": 130, "lufs": -11.0}

@patch('audio_analyzer.measure_lufs')
def test_analyze_audio_file_lufs_fallback(mock_lufs):
    """Test analyze_audio_file falls back to -14.0 if measure_lufs returns None."""
    mock_lufs.return_value = None
    local_analysis = {"energy": "0.6"}

    result = analyze_audio_file("dummy_path.wav", local_analysis)

    assert result == {"energy": "0.6", "lufs": -14.0}

@patch('audio_analyzer.measure_lufs')
def test_analyze_audio_file_exception(mock_lufs):
    """Test analyze_audio_file gracefully handles exceptions and returns None."""
    # We can force an exception by making local_analysis something un-copyable,
    # but the easiest way is mocking measure_lufs to raise an exception.
    mock_lufs.side_effect = Exception("Measurement failed")

    result = analyze_audio_file("dummy_path.wav", {"energy": "0.9"})

    assert result is None

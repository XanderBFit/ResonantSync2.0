import sys
import os
import pytest
import numpy as np
from unittest.mock import MagicMock

# Add the backend directory to sys.path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from audio_analyzer import measure_lufs, analyze_audio_file

def test_measure_lufs_mono_success(mocker):
    """Test LUFS measurement for a mono audio file."""
    # Mock librosa.load to return a 1D array (mono)
    mock_data = np.array([0.1, 0.2, 0.3])
    mock_rate = 44100
    mocker.patch('librosa.load', return_value=(mock_data, mock_rate))

    # Mock pyloudnorm.Meter
    mock_meter_instance = MagicMock()
    mock_meter_instance.integrated_loudness.return_value = -14.234
    mocker.patch('pyloudnorm.Meter', return_value=mock_meter_instance)

    result = measure_lufs("dummy_path.wav")

    # Check return value is rounded to 1 decimal place
    assert result == -14.2

    # Check that integrated_loudness was called with the correct shape (samples, channels)
    # The original array was shape (3,), so it should become (3, 1)
    args, _ = mock_meter_instance.integrated_loudness.call_args
    assert args[0].shape == (3, 1)

def test_measure_lufs_stereo_success(mocker):
    """Test LUFS measurement for a stereo audio file."""
    # Mock librosa.load to return a 2D array (stereo: channels, samples)
    mock_data = np.array([[0.1, 0.2, 0.3], [0.1, 0.2, 0.3]])
    mock_rate = 48000
    mocker.patch('librosa.load', return_value=(mock_data, mock_rate))

    # Mock pyloudnorm.Meter
    mock_meter_instance = MagicMock()
    mock_meter_instance.integrated_loudness.return_value = -10.56
    mocker.patch('pyloudnorm.Meter', return_value=mock_meter_instance)

    result = measure_lufs("dummy_path.wav")

    # Check return value is rounded to 1 decimal place
    assert result == -10.6

    # The original array was shape (2, 3), so it should become (3, 2)
    args, _ = mock_meter_instance.integrated_loudness.call_args
    assert args[0].shape == (3, 2)

def test_measure_lufs_silence(mocker):
    """Test that silence or infinite LUFS value returns None."""
    mock_data = np.array([0.0, 0.0, 0.0])
    mock_rate = 44100
    mocker.patch('librosa.load', return_value=(mock_data, mock_rate))

    mock_meter_instance = MagicMock()
    mock_meter_instance.integrated_loudness.return_value = -np.inf
    mocker.patch('pyloudnorm.Meter', return_value=mock_meter_instance)

    result = measure_lufs("dummy_path.wav")

    assert result is None

def test_measure_lufs_nan(mocker):
    """Test that NaN LUFS value returns None."""
    mock_data = np.array([0.0, 0.0, 0.0])
    mock_rate = 44100
    mocker.patch('librosa.load', return_value=(mock_data, mock_rate))

    mock_meter_instance = MagicMock()
    mock_meter_instance.integrated_loudness.return_value = np.nan
    mocker.patch('pyloudnorm.Meter', return_value=mock_meter_instance)

    result = measure_lufs("dummy_path.wav")

    assert result is None

def test_measure_lufs_exception(mocker):
    """Test that an exception during measurement gracefully returns None."""
    # Make librosa.load raise an exception
    mocker.patch('librosa.load', side_effect=Exception("File not found"))

    result = measure_lufs("dummy_path.wav")

    assert result is None

# --- analyze_audio_file Tests ---

def test_analyze_audio_file_no_local_analysis(mocker):
    """Test analyze_audio_file when local_analysis is None."""
    mocker.patch('audio_analyzer.measure_lufs', return_value=-12.5)

    result = analyze_audio_file("dummy_path.wav")

    assert result == {"energy": "0.5", "lufs": -12.5}

def test_analyze_audio_file_with_local_analysis_missing_energy(mocker):
    """Test analyze_audio_file adds energy if missing."""
    mocker.patch('audio_analyzer.measure_lufs', return_value=-10.0)
    local_analysis = {"tempo": 120}

    result = analyze_audio_file("dummy_path.wav", local_analysis)

    assert result == {"tempo": 120, "energy": "0.5", "lufs": -10.0}
    # Ensure local_analysis wasn't mutated
    assert local_analysis == {"tempo": 120}

def test_analyze_audio_file_with_local_analysis_has_energy(mocker):
    """Test analyze_audio_file preserves existing energy."""
    mocker.patch('audio_analyzer.measure_lufs', return_value=-11.0)
    local_analysis = {"energy": "0.8", "tempo": 130}

    result = analyze_audio_file("dummy_path.wav", local_analysis)

    assert result == {"energy": "0.8", "tempo": 130, "lufs": -11.0}

def test_analyze_audio_file_lufs_fallback(mocker):
    """Test analyze_audio_file falls back to -14.0 if measure_lufs returns None."""
    mocker.patch('audio_analyzer.measure_lufs', return_value=None)
    local_analysis = {"energy": "0.6"}

    result = analyze_audio_file("dummy_path.wav", local_analysis)

    assert result == {"energy": "0.6", "lufs": -14.0}

def test_analyze_audio_file_exception(mocker):
    """Test analyze_audio_file gracefully handles exceptions and returns None."""
    # We can force an exception by making local_analysis something un-copyable,
    # but the easiest way is mocking measure_lufs to raise an exception.
    mocker.patch('audio_analyzer.measure_lufs', side_effect=Exception("Measurement failed"))

    result = analyze_audio_file("dummy_path.wav", {"energy": "0.9"})

    assert result is None

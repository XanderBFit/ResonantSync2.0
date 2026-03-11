import pytest
from unittest.mock import patch, MagicMock
import sys

# Mock all external dependencies
sys.modules['librosa'] = MagicMock()
sys.modules['numpy'] = MagicMock()
sys.modules['pyloudnorm'] = MagicMock()

from backend.audio_analyzer import analyze_audio_file

def test_analyze_audio_file_no_local_analysis():
    with patch('backend.audio_analyzer.measure_lufs') as mock_measure:
        mock_measure.return_value = -12.0
        result = analyze_audio_file("fake_path", None)
        assert result["energy"] == "0.5"
        assert result["lufs"] == -12.0

def test_analyze_audio_file_with_local_analysis():
    local_data = {"energy": "0.8", "other": "value"}
    with patch('backend.audio_analyzer.measure_lufs') as mock_measure:
        mock_measure.return_value = -12.0
        result = analyze_audio_file("fake_path", local_data)
        assert result["energy"] == "0.8"
        assert result["other"] == "value"
        assert result["lufs"] == -12.0

def test_analyze_audio_file_energy_fallback():
    local_data = {"other": "value"}
    with patch('backend.audio_analyzer.measure_lufs') as mock_measure:
        mock_measure.return_value = -12.0
        result = analyze_audio_file("fake_path", local_data)
        assert result["energy"] == "0.5"
        assert result["other"] == "value"

def test_analyze_audio_file_lufs_fallback():
    with patch('backend.audio_analyzer.measure_lufs') as mock_measure:
        mock_measure.return_value = None
        result = analyze_audio_file("fake_path", None)
        assert result["lufs"] == -14.0

def test_analyze_audio_file_lufs_success():
    with patch('backend.audio_analyzer.measure_lufs') as mock_measure:
        mock_measure.return_value = -10.0
        result = analyze_audio_file("fake_path", None)
        assert result["lufs"] == -10.0

def test_analyze_audio_file_exception():
    mock_local = MagicMock()
    mock_local.copy.side_effect = Exception("Copy failed")
    result = analyze_audio_file("fake_path", mock_local)
    assert result is None

import pytest
import unittest.mock
from unittest.mock import MagicMock, patch
import sys

# Ensure backend can be imported
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock reportlab since it might not be installed in the environment
mock_canvas = MagicMock()
sys.modules['reportlab'] = MagicMock()
sys.modules['reportlab.lib'] = MagicMock()
sys.modules['reportlab.lib.pagesizes'] = MagicMock()
sys.modules['reportlab.lib.pagesizes'].letter = (612, 792)
sys.modules['reportlab.pdfgen'] = MagicMock()
sys.modules['reportlab.pdfgen'].canvas = mock_canvas

from one_sheet_generator import generate_one_sheet

@pytest.fixture
def mock_reportlab_canvas():
    with patch('one_sheet_generator.canvas.Canvas') as mock:
        yield mock

def test_generate_one_sheet_success(mock_reportlab_canvas):
    """Test happy path with all data fields populated."""
    data = {
        'title': 'Test Song',
        'artist': 'Test Artist',
        'bpm': '120',
        'key': 'C',
        'scale': 'Major',
        'energy': '0.8',
        'mood': 'Happy',
        'genre': 'Pop',
        'vocalPresence': 'Lead',
        'instruments': ['Drums', 'Guitar'],
        'oneStop': True,
        'publisher': 'Test Pub',
        'composer': 'Test Writer',
        'isrc': 'US-ABC-12-34567',
        'comments': 'Great track for a commercial.',
        'contactName': 'John Doe',
        'contactEmail': 'john@example.com',
        'contactPhone': '123-456-7890'
    }

    mock_canvas_instance = MagicMock()
    mock_reportlab_canvas.return_value = mock_canvas_instance

    result = generate_one_sheet("fake/path.mp3", data, "output.pdf")

    assert result is True
    mock_reportlab_canvas.assert_called_once_with("output.pdf", pagesize=(612, 792))
    mock_canvas_instance.save.assert_called_once()
    # Verify some key calls to draw text/rects
    mock_canvas_instance.drawString.assert_any_call(40, 792 - 60, "TEST SONG")

def test_generate_one_sheet_partial_data(mock_reportlab_canvas):
    """Verify default values when data dictionary is missing keys."""
    data = {} # Empty data

    mock_canvas_instance = MagicMock()
    mock_reportlab_canvas.return_value = mock_canvas_instance

    result = generate_one_sheet("fake/path.mp3", data, "output.pdf")

    assert result is True
    # Verify default title
    mock_canvas_instance.drawString.assert_any_call(40, 792 - 60, "UNTITLED TRACK")

def test_generate_one_sheet_complex_types(mock_reportlab_canvas):
    """Verify logic for instruments as a list and oneStop boolean."""
    data = {
        'instruments': ['Bass', 'Synth'],
        'oneStop': False
    }

    mock_canvas_instance = MagicMock()
    mock_reportlab_canvas.return_value = mock_canvas_instance

    result = generate_one_sheet("fake/path.mp3", data, "output.pdf")

    assert result is True
    # Verify instruments joined by comma
    mock_canvas_instance.drawString.assert_any_call(40, unittest.mock.ANY, "BASS, SYNTH")
    # Verify status for oneStop=False
    mock_canvas_instance.drawString.assert_any_call(140, unittest.mock.ANY, "CLEARANCE REQUIRED")

def test_generate_one_sheet_long_comments(mock_reportlab_canvas):
    """Verify the naive word wrap logic for long comment strings."""
    # A long string that should trigger word wrap
    long_comment = "This is a very long comment that should definitely trigger the word wrap logic in the one sheet generator because it exceeds the expected width limit."
    data = {'comments': long_comment}

    mock_canvas_instance = MagicMock()
    mock_reportlab_canvas.return_value = mock_canvas_instance

    result = generate_one_sheet("fake/path.mp3", data, "output.pdf")

    assert result is True
    # Check that drawString was called multiple times for the comment section
    # The first line should be drawn, and then subsequent lines.
    assert mock_canvas_instance.drawString.call_count > 10 # Lots of calls in total

def test_generate_one_sheet_failure(mock_reportlab_canvas):
    """Verify that the function returns False and catches exceptions."""
    mock_reportlab_canvas.side_effect = Exception("PDF generation failed")

    result = generate_one_sheet("fake/path.mp3", {}, "output.pdf")

    assert result is False

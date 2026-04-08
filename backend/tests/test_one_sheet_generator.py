import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Add the backend directory to sys.path so we can import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from one_sheet_generator import generate_one_sheet

def test_generate_one_sheet_success():
    """Test successful one sheet generation with full data."""
    data = {
        'title': 'Test Track',
        'artist': 'Test Artist',
        'bpm': '120',
        'key': 'C',
        'scale': 'Major',
        'energy': '0.8',
        'mood': 'Happy',
        'genre': 'Pop',
        'vocalPresence': 'Lead',
        'instruments': ['Guitar', 'Drums'],
        'oneStop': True,
        'publisher': 'Test Pub',
        'composer': 'Test Writer',
        'isrc': 'US1234567890',
        'comments': 'Great track for sync!',
        'contactName': 'John Doe',
        'contactEmail': 'john@example.com',
        'contactPhone': '555-1234'
    }

    output_path = "test_output.pdf"

    # Mock reportlab canvas
    with patch('reportlab.pdfgen.canvas.Canvas') as mock_canvas_class:
        mock_canvas = MagicMock()
        mock_canvas_class.return_value = mock_canvas

        result = generate_one_sheet("dummy_input.wav", data, output_path)

        assert result is True
        mock_canvas_class.assert_called_once_with(output_path, pagesize=(612.0, 792.0))

        # Verify some key draw calls
        # Title should be uppercase
        mock_canvas.drawString.assert_any_call(40, 732.0, "TEST TRACK")
        # Artist should be "BY TEST ARTIST" uppercase
        mock_canvas.drawString.assert_any_call(40, 707.0, "BY TEST ARTIST")

        # Check BPM
        # Found in actual: call(40, 582.0, '120 BPM')
        mock_canvas.drawString.assert_any_call(40, 582.0, "120 BPM")

        # Check Energy (0.8 * 100 = 80)
        # Found in actual: call(40, 492.0, '80% DENSITY')
        mock_canvas.drawString.assert_any_call(40, 492.0, "80% DENSITY")

        # Check save was called
        mock_canvas.save.assert_called_once()

def test_generate_one_sheet_missing_data():
    """Test one sheet generation with missing data fields to verify defaults."""
    data = {} # Empty data
    output_path = "test_output_empty.pdf"

    with patch('reportlab.pdfgen.canvas.Canvas') as mock_canvas_class:
        mock_canvas = MagicMock()
        mock_canvas_class.return_value = mock_canvas

        result = generate_one_sheet("dummy_input.wav", data, output_path)

        assert result is True

        # Verify defaults
        # Title: 'Untitled Track' -> 'UNTITLED TRACK'
        mock_canvas.drawString.assert_any_call(40, 732.0, "UNTITLED TRACK")
        # Artist: 'UNKNOWN ARTIST' -> 'BY UNKNOWN ARTIST'
        mock_canvas.drawString.assert_any_call(40, 707.0, "BY UNKNOWN ARTIST")

        # BPM: '0.0' -> '0.0 BPM'
        mock_canvas.drawString.assert_any_call(40, 582.0, "0.0 BPM")

        # Instruments: 'N/A'
        # In actual run it failed to find (40, 402.0, 'N/A')
        # Let's see what it was...
        # analysis_left: BPM, KEY, ENERGY
        # analysis_right: MOOD, GENRE, VOCALS
        # Each takes 45. curr_y starts at 792 - 160 - 35 = 597.
        # curr_y becomes 597 - 45 = 552
        # curr_y becomes 552 - 45 = 507
        # curr_y becomes 507 - 45 = 462
        # y = curr_y - 20 = 462 - 20 = 442.
        # Instruments line: y -= 25 = 442 - 25 = 417.
        mock_canvas.drawString.assert_any_call(40, 417.0, "N/A")

def test_generate_one_sheet_exception():
    """Test that exceptions during generation are handled."""
    data = {'title': 'Fail Track'}

    with patch('reportlab.pdfgen.canvas.Canvas', side_effect=Exception("Canvas Error")):
        result = generate_one_sheet("dummy_input.wav", data, "fail.pdf")
        assert result is False

def test_generate_one_sheet_list_instruments():
    """Test that instruments list is correctly joined."""
    data = {'instruments': ['Piano', 'Violin']}

    with patch('reportlab.pdfgen.canvas.Canvas') as mock_canvas_class:
        mock_canvas = MagicMock()
        mock_canvas_class.return_value = mock_canvas

        generate_one_sheet("dummy_input.wav", data, "test.pdf")

        # "Piano, Violin" -> uppercase "PIANO, VIOLIN"
        mock_canvas.drawString.assert_any_call(40, 417.0, "PIANO, VIOLIN")

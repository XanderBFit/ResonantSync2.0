import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Mock reportlab before importing anything else
sys.modules['reportlab'] = MagicMock()
sys.modules['reportlab.lib'] = MagicMock()
sys.modules['reportlab.lib.pagesizes'] = MagicMock()
sys.modules['reportlab.pdfgen'] = MagicMock()
sys.modules['reportlab.pdfgen.canvas'] = MagicMock()

# Set up the letter constant
import reportlab.lib.pagesizes
reportlab.lib.pagesizes.letter = (100, 792) # Small width to force wrapping

# Now we can import the module to test
# We need to make sure backend is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import one_sheet_generator
one_sheet_generator.letter = (100, 792)

from one_sheet_generator import generate_one_sheet

class TestOneSheetGenerator(unittest.TestCase):
    @patch('one_sheet_generator.canvas.Canvas')
    def test_generate_one_sheet_wrapping(self, mock_canvas_class):
        mock_canvas = MagicMock()
        mock_canvas_class.return_value = mock_canvas

        data = {
            'comments': 'This is a long comment that should definitely be wrapped into multiple lines based on the width of the page.',
            'title': 'Test Title',
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
            'composer': 'Test Comp',
            'isrc': 'US123',
            'contactName': 'Test Name',
            'contactEmail': 'test@example.com',
            'contactPhone': '1234567890'
        }

        # Call the function
        result = generate_one_sheet('dummy_path', data, 'output.pdf')

        self.assertTrue(result)

        # Extract all drawString calls
        draw_string_calls = [call.args for call in mock_canvas.drawString.call_args_list]

        # Find the comment strings
        # We look for parts of the comment
        comment_calls = [args[2] for args in draw_string_calls if any(word in args[2] for word in ['This', 'long', 'wrapped', 'multiple', 'lines'])]

        self.assertTrue(len(comment_calls) > 1, f"Expected multiple lines for long comment, got {len(comment_calls)}")

    @patch('one_sheet_generator.canvas.Canvas')
    def test_generate_one_sheet_error_handling(self, mock_canvas_class):
        mock_canvas_class.side_effect = Exception("PDF Creation Failed")

        data = {'title': 'Test'}
        result = generate_one_sheet('dummy_path', data, 'output.pdf')

        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main()

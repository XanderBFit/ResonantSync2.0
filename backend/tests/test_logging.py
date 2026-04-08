import unittest
from unittest.mock import patch, MagicMock
from one_sheet_generator import generate_one_sheet

class TestLogging(unittest.TestCase):
    @patch('one_sheet_generator.canvas.Canvas')
    @patch('one_sheet_generator.logger')
    def test_generate_one_sheet_logging(self, mock_logger, mock_canvas):
        # Setup mock to raise an exception
        mock_canvas.side_effect = Exception("Test Exception")

        # Call the function
        result = generate_one_sheet("test.mp3", {}, "output.pdf")

        # Verify result is False
        self.assertFalse(result)

        # Verify logger.error was called
        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args
        self.assertIn("Error generating Cinematic One-Sheet: Test Exception", args[0])

if __name__ == '__main__':
    unittest.main()

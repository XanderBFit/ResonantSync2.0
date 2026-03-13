import os
import pytest
from one_sheet_generator import generate_one_sheet

def test_generate_one_sheet_success(tmp_path):
    output_path = os.path.join(tmp_path, "test_output.pdf")
    data = {
        "title": "Test Title",
        "artist": "Test Artist",
        "bpm": 120,
        "key": "C",
        "scale": "Major",
        "energy": 0.8,
        "mood": "Happy",
        "genre": "Pop",
        "vocalPresence": "Instrumental",
        "instruments": ["Piano", "Guitar"],
        "oneStop": True,
        "publisher": "Test Publisher",
        "composer": "Test Composer",
        "isrc": "US1234567890",
        "comments": "This is a test comment. It should be long enough to test the naive word wrap functionality in the one-sheet generator. It just keeps going and going and going and going.",
        "contactName": "Test Contact",
        "contactEmail": "test@test.com",
        "contactPhone": "123-456-7890"
    }

    result = generate_one_sheet("dummy.wav", data, output_path)

    assert result is True
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0

def test_generate_one_sheet_missing_fields(tmp_path):
    output_path = os.path.join(tmp_path, "test_output_missing.pdf")
    data = {} # Empty dictionary, all fields missing

    result = generate_one_sheet("dummy.wav", data, output_path)

    # Should handle all defaults without throwing unhandled exceptions
    assert result is True
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0

def test_generate_one_sheet_edge_cases(tmp_path):
    output_path = os.path.join(tmp_path, "test_output_edge.pdf")
    data = {
        "title": 12345, # Non-string title
        "artist": None, # None artist
        "bpm": "120.5", # String BPM
        "energy": "0.5", # String energy
        "instruments": "Just a string, not a list", # String instruments
        "comments": "", # Empty comment
    }

    result = generate_one_sheet("dummy.wav", data, output_path)

    assert result is True
    assert os.path.exists(output_path)
    assert os.path.getsize(output_path) > 0

def test_generate_one_sheet_invalid_energy(tmp_path):
    output_path = os.path.join(tmp_path, "test_output_invalid_energy.pdf")
    data = {
        "energy": "not_a_number" # Will cause ValueError in float()
    }

    result = generate_one_sheet("dummy.wav", data, output_path)

    # The try/except block in the function should catch the ValueError
    # and return False
    assert result is False
    assert not os.path.exists(output_path)

def test_generate_one_sheet_invalid_path():
    data = {}
    # Passing an invalid path (e.g., directory that doesn't exist)
    # to cause an IOError when saving the canvas
    result = generate_one_sheet("dummy.wav", data, "/invalid/path/that/does/not/exist.pdf")

    assert result is False

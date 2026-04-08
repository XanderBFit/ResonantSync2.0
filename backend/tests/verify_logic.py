import sys
from unittest.mock import MagicMock

# Define Mock Classes
class MockFirestore:
    class Query:
        DESCENDING = "descending"

def setup_mocks():
    mock_modules = [
        'fastapi',
        'fastapi.middleware.cors',
        'fastapi.security',
        'fastapi.responses',
        'fastapi.staticfiles',
        'google.cloud',
        'google.cloud.firestore',
        'google.cloud.storage',
        'firebase_admin',
        'firebase_admin.auth',
        'librosa',
        'numpy',
        'ffmpeg',
        'audio_analyzer',
        'metadata_manager',
        'one_sheet_generator',
        'storage_manager',
    ]

    for mod in mock_modules:
        m = MagicMock()
        sys.modules[mod] = m
        if mod == 'google.cloud.firestore':
            m.Query = MockFirestore.Query

    # Mock dependencies used in main.py
    sys.modules['google.cloud'].firestore = sys.modules['google.cloud.firestore']
    sys.modules['firebase_admin'].auth = sys.modules['firebase_admin.auth']

# Patch app.get etc to not overwrite our functions
def test_get_vault_logic():
    setup_mocks()

    # Pre-patch FastAPI before importing main
    import fastapi
    mock_app = MagicMock()
    fastapi.FastAPI.return_value = mock_app

    # Now import main
    import main

    # Manually re-assign get_vault if it got mocked
    # Actually if main.py defines it, it should be there.

    # Setup mock docs
    mock_doc1 = MagicMock()
    mock_doc1.id = "id1"
    mock_doc1.to_dict.return_value = {"uid": "user1", "name": "track1"}

    mock_doc2 = MagicMock()
    mock_doc2.id = "id2"
    mock_doc2.to_dict.return_value = {"uid": "user1", "name": "track2"}

    mock_stream = [mock_doc1, mock_doc2]

    # Mock the db call
    main.db.collection.return_value.where.return_value.order_by.return_value.stream.return_value = mock_stream

    # Call the function
    import asyncio

    async def run_test():
        results = await main.get_vault("user1", "user1")

        expected = [
            {"uid": "user1", "name": "track1", "id": "id1"},
            {"uid": "user1", "name": "track2", "id": "id2"}
        ]

        print(f"Results: {results}")
        assert results == expected
        print("Test passed!")

    asyncio.run(run_test())

if __name__ == "__main__":
    test_get_vault_logic()

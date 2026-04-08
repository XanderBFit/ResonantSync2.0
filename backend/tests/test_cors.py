from fastapi.testclient import TestClient
import os
import sys
from unittest.mock import MagicMock

# Mocking missing modules for test environment
sys.modules["audio_analyzer"] = MagicMock()
sys.modules["metadata_manager"] = MagicMock()
sys.modules["storage_manager"] = MagicMock()
sys.modules["one_sheet_generator"] = MagicMock()
sys.modules["google.cloud"] = MagicMock()
sys.modules["firebase_admin"] = MagicMock()
sys.modules["librosa"] = MagicMock()
sys.modules["numpy"] = MagicMock()
sys.modules["ffmpeg"] = MagicMock()
sys.modules["reportlab"] = MagicMock()
sys.modules["reportlab.lib"] = MagicMock()
sys.modules["reportlab.lib.pagesizes"] = MagicMock()
sys.modules["reportlab.pdfgen"] = MagicMock()

# Now import app. Note: main.py uses os.getenv at module level,
# so we might need to reload it if we want to test different env vars in the same process.
# But for a simple check of the defaults:
from main import app

client = TestClient(app)

def test_cors_default_allowed_origin():
    # Test one of the default allowed origins
    origin = "http://localhost:5173"
    response = client.get("/", headers={"Origin": origin})
    # If the origin is allowed, the ACAO header is returned
    assert response.headers.get("access-control-allow-origin") == origin

def test_cors_disallowed_origin():
    # Test an origin that is not in the allowed list
    origin = "http://malicious-site.com"
    response = client.get("/", headers={"Origin": origin})
    # For disallowed origins, FastAPI's CORSMiddleware does not include the ACAO header
    assert "access-control-allow-origin" not in response.headers

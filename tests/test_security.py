import sys
from unittest.mock import MagicMock

# Create a minimal mock for FastAPI and its decorators
class MockApp:
    def post(self, *args, **kwargs):
        def decorator(func):
            func._route_info = ('POST', args[0], kwargs)
            return func
        return decorator
    def get(self, *args, **kwargs):
        def decorator(func):
            func._route_info = ('GET', args[0], kwargs)
            return func
        return decorator
    def delete(self, *args, **kwargs):
        def decorator(func):
            func._route_info = ('DELETE', args[0], kwargs)
            return func
        return decorator
    def add_middleware(self, *args, **kwargs): pass
    def mount(self, *args, **kwargs): pass

fastapi_mock = MagicMock()
fastapi_mock.FastAPI.return_value = MockApp()
fastapi_mock.Depends = lambda x: x

modules_to_mock = [
    "fastapi", "fastapi.middleware.cors", "fastapi.responses", "fastapi.staticfiles",
    "google", "google.cloud", "google.cloud.firestore", "firebase_admin",
    "firebase_admin.credentials", "firebase_admin.auth", "librosa", "numpy",
    "soundfile", "ffmpeg", "audio_analyzer", "metadata_manager",
    "one_sheet_generator", "storage_manager"
]

for mod in modules_to_mock:
    if mod == "fastapi":
        sys.modules[mod] = fastapi_mock
    else:
        sys.modules[mod] = MagicMock()

# Re-import main after mocking
if 'main' in sys.modules:
    del sys.modules['main']

import unittest
import inspect

class TestSecurity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.append("./backend")
        import main
        cls.main = main

    def test_create_pitch_auth(self):
        print("\n--- Checking /api/pitches ---")
        sig = inspect.signature(self.main.create_pitch)
        print(f"Signature: {sig}")
        # With our MockApp and Depends = lambda x: x,
        # the default value should be the verify_token function itself
        has_auth = any(p.default == self.main.verify_token for p in sig.parameters.values())
        print(f"Secured with verify_token: {has_auth}")
        self.assertTrue(has_auth, "/api/pitches is not secured")

    def test_get_vault_auth(self):
        print("\n--- Checking /api/vault ---")
        # Check source for ownership check
        source = inspect.getsource(self.main.get_vault)
        has_ownership_check = "if uid != _auth_uid:" in source
        print(f"Has ownership check: {has_ownership_check}")
        self.assertTrue(has_ownership_check, "/api/vault missing ownership check")

    def test_generate_promos_auth(self):
        print("\n--- Checking /api/promos/{file_id} ---")
        sig = inspect.signature(self.main.generate_promos)
        print(f"Signature: {sig}")
        has_auth = any(p.default == self.main.verify_token for p in sig.parameters.values())
        print(f"Secured with verify_token: {has_auth}")

        source = inspect.getsource(self.main.generate_promos)
        has_ownership_check = 'doc.to_dict().get("uid") != uid' in source
        print(f"Has ownership check: {has_ownership_check}")

        self.assertTrue(has_auth, "/api/promos/{file_id} is not secured")
        self.assertTrue(has_ownership_check, "/api/promos/{file_id} missing ownership check")

if __name__ == "__main__":
    unittest.main()

import sys
from unittest.mock import MagicMock
import os
import importlib

def run_test(env_val, expected_origins):
    # Reset sys.modules to allow re-importing main
    if "main" in sys.modules:
        del sys.modules["main"]

    # Mocking
    sys.modules["fastapi"] = MagicMock()
    sys.modules["fastapi.middleware.cors"] = MagicMock()
    sys.modules["fastapi.security"] = MagicMock()
    sys.modules["fastapi.responses"] = MagicMock()
    sys.modules["fastapi.staticfiles"] = MagicMock()
    sys.modules["fastapi.testclient"] = MagicMock()
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

    if env_val is None:
        if "ALLOWED_ORIGINS" in os.environ:
            del os.environ["ALLOWED_ORIGINS"]
    else:
        os.environ["ALLOWED_ORIGINS"] = env_val

    import main
    importlib.reload(main)
    app = main.app

    # Get the arguments of the first call to add_middleware
    call_found = False
    for call in app.add_middleware.call_args_list:
        args, kwargs = call
        if "allow_origins" in kwargs:
            if kwargs["allow_origins"] == expected_origins:
                call_found = True
                break

    if not call_found:
        # Debugging output if test fails
        actual = [kwargs.get("allow_origins") for _, kwargs in app.add_middleware.call_args_list]
        raise AssertionError(f"Expected origins {expected_origins} not found in add_middleware calls. Actual: {actual}")

if __name__ == "__main__":
    # Test with env var
    run_test("http://origin1.com,http://origin2.com", ["http://origin1.com", "http://origin2.com"])
    print("Test passed: Environment variable version.")

    # Test with env var and spaces
    run_test("http://origin1.com,  http://origin2.com ", ["http://origin1.com", "http://origin2.com"])
    print("Test passed: Environment variable version with spaces.")

    # Test default
    default_origins = [
        "http://localhost:5173",
        "https://striking-scout-489504-b4.web.app",
        "https://striking-scout-489504-b4.firebaseapp.com"
    ]
    run_test(None, default_origins)
    print("Test passed: Default version.")

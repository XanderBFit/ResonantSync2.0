import sys
import os
from unittest.mock import MagicMock

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''

# Mock dependencies that might be missing in some environments
mock_modules = [
    'google',
    'google.cloud',
    'google.cloud.firestore',
    'google.cloud.storage',
    'firebase_admin',
]

for module in mock_modules:
    sys.modules[module] = MagicMock()

# Mock specific classes/functions if needed
import google.cloud.firestore
import google.cloud.storage
import firebase_admin

google.cloud.firestore.Client = MagicMock()
google.cloud.storage.Client = MagicMock()
firebase_admin.initialize_app = MagicMock()

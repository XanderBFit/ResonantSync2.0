import sys
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = ''

from unittest.mock import MagicMock
import google.cloud.firestore
import google.cloud.storage
import firebase_admin

# Mock firebase and google cloud stuff before any imports
google.cloud.firestore.Client = MagicMock()
google.cloud.storage.Client = MagicMock()
firebase_admin.initialize_app = MagicMock()

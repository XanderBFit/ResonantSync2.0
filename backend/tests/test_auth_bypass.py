from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import pytest
import os

# Set environment variables before importing app
os.environ["GCS_BUCKET"] = "test-bucket"

from main import app, verify_token, db

client = TestClient(app)

def test_embed_metadata_auth_impersonation():
    # 1. Setup Mocking
    authenticated_uid = "real-user-123"
    impersonated_uid = "victim-user-456"

    # Override verify_token dependency to simulate an authenticated user
    app.dependency_overrides[verify_token] = lambda: authenticated_uid

    # Mock GCS operations
    with patch("main.find_blob_by_prefix", return_value="raw/test-file.wav"), \
         patch("main.download_from_gcs", return_value=True), \
         patch("main.downmix_to_mp3", return_value=True), \
         patch("main.embed_disco_metadata", return_value=True), \
         patch("main.generate_one_sheet", return_value=None), \
         patch("main.upload_to_gcs", return_value=True), \
         patch("main.shutil.copy", return_value=True):

        # Mock Firestore db.collection("processedTracks").document(fileId).set(track_doc)
        mock_doc_ref = MagicMock()
        with patch.object(db, "collection", return_value=MagicMock(return_value=MagicMock(document=MagicMock(return_value=mock_doc_ref)))):
            # Use the actual db client and patch its methods
            with patch.object(db, "collection") as mock_collection:
                mock_collection.return_value.document.return_value.set = MagicMock()

                # 2. Act: Call the endpoint with a malicious uid in the form data
                response = client.post(
                    "/api/embed",
                    data={
                        "fileId": "test-file-id",
                        "metadata": '{"TIT2": "Test Track"}',
                        "uid": impersonated_uid  # Maliciously trying to set a different owner
                    }
                )

                # 3. Assert
                assert response.status_code == 200

                # Get the track_doc passed to .set()
                # db.collection("processedTracks").document(fileId).set(track_doc)
                args, kwargs = mock_collection.return_value.document.return_value.set.call_args
                track_doc = args[0]

                # Verify that the stored UID is the authenticated one, not the impersonated one
                print(f"\nUID in stored doc: {track_doc['uid']}")
                print(f"Authenticated UID: {authenticated_uid}")

                assert track_doc["uid"] == authenticated_uid, "Security Fix Failed: Impersonation still possible!"

    # Cleanup
    app.dependency_overrides.clear()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, Response, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import logging
import tempfile
import os
import shutil
import json
import uuid
import zipfile
import io
import librosa
import numpy as np
import ffmpeg
from audio_analyzer import analyze_audio_file
from metadata_manager import strip_metadata, embed_disco_metadata, read_disco_metadata, downmix_to_mp3
from one_sheet_generator import generate_one_sheet
from storage_manager import upload_to_gcs, download_from_gcs, find_blob_by_prefix, blob_exists
from google.cloud import firestore
import firebase_admin
from firebase_admin import auth as firebase_auth

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Firebase Admin with Application Default Credentials (uses Cloud Run service account)
if not firebase_admin._apps:
    firebase_admin.initialize_app()

db = firestore.Client()
app = FastAPI(title="ResonantCrab API", description="DISCO-Compatible Audio Metadata Engine")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev only. Should be restricted in prod.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temp storage for processing
UPLOAD_DIR = tempfile.gettempdir()


security = HTTPBearer(auto_error=False)

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    Validates Firebase ID token from Authorization: Bearer <token> header.
    Returns the user's UID on success.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = credentials.credentials
    try:
        decoded = firebase_auth.verify_id_token(token)
        return decoded["uid"]
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

@app.post("/api/analyze")
def analyze_audio(file: UploadFile = File(...), localAnalysis: str = Form(None), uid: str = Depends(verify_token)):
    """
    Accepts an audio file, uploads to GCS, strips metadata, and merges local Essentia.js analysis.
    Returns a unique fileId and the analyzed data.
    """
    if not file.filename.lower().endswith(('.mp3', '.wav', '.aiff')):
        raise HTTPException(status_code=400, detail="Invalid file type")

    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1].lower()
    raw_blob_name = f"raw/{file_id}{ext}"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = os.path.join(temp_dir, f"input{ext}")
        
        # 1. Save upload to local temp
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # 2. Strip metadata locally
        strip_metadata(temp_path)
        
        # 3. Upload cleaned raw file to GCS
        if not upload_to_gcs(temp_path, raw_blob_name):
            raise HTTPException(status_code=500, detail="Failed to persist file to GCS")

        # 4. Analyze Audio
        local_data = None
        if localAnalysis:
            try:
                local_data = json.loads(localAnalysis)
            except Exception:
                pass

        analysis_data = analyze_audio_file(temp_path, local_data)
        
        if analysis_data is None:
            raise HTTPException(status_code=500, detail="Audio analysis failed")

    # Merge analysis data with initial knowns
    analysis_data["title"] = os.path.splitext(file.filename)[0]
    analysis_data["artist"] = "Unknown Artist"
    analysis_data["album"] = ""
    analysis_data["fileId"] = file_id 

    return analysis_data


@app.post("/api/embed")
def embed_metadata(
    fileId: str = Form(...),
    metadata: str = Form(...),
    uid: str = Form(None),
    _uid: str = Depends(verify_token)
):
    """
    Pulls raw file from GCS, embeds metadata, generates One-Sheet, and uploads results back to GCS.
    """
    try:
        data = json.loads(metadata)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON metadata")

    # 1. Locate raw file in GCS
    raw_blob_name = find_blob_by_prefix(f"raw/{fileId}")
    if not raw_blob_name:
        raise HTTPException(status_code=404, detail="Original file not found in GCS.")

    ext = os.path.splitext(raw_blob_name)[1].lower()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        local_raw_path = os.path.join(temp_dir, f"raw{ext}")
        local_mp3_path = os.path.join(temp_dir, "final.mp3")
        local_pdf_path = os.path.join(temp_dir, "onesheet.pdf")

        # 2. Download from GCS
        if not download_from_gcs(raw_blob_name, local_raw_path):
            raise HTTPException(status_code=500, detail="Failed to fetch file from GCS")

        # 3. Transcode if necessary
        if ext != '.mp3':
            if not downmix_to_mp3(local_raw_path, local_mp3_path):
                raise HTTPException(status_code=500, detail="Transcoding failed")
        else:
            shutil.copy(local_raw_path, local_mp3_path)

        # 4. Embed Metadata
        if not embed_disco_metadata(local_mp3_path, data):
            raise HTTPException(status_code=500, detail="Metadata embedding failed")

        # 5. Generate One-Sheet
        generate_one_sheet(local_mp3_path, data, local_pdf_path)

        # 6. Upload results to GCS (finalized/ directory)
        final_mp3_blob = f"finalized/{fileId}.mp3"
        final_pdf_blob = f"finalized/{fileId}_OneSheet.pdf"
        
        upload_to_gcs(local_mp3_path, final_mp3_blob)
        upload_to_gcs(local_pdf_path, final_pdf_blob)

        # 7. Persistence: Store in Firestore if UID is provided
        if uid:
            track_doc = {
                "uid": uid,
                "fileId": fileId,
                "metadata": data,
                "downloadUrl": f"/api/download/{fileId}",
                "oneSheetUrl": f"/api/onesheet/{fileId}",
                "isMaster": ext != '.mp3',
                "masterUrl": f"/api/master/{fileId}/{ext.replace('.', '')}" if ext != '.mp3' else None,
                "createdAt": firestore.SERVER_TIMESTAMP
            }
            db.collection("processedTracks").document(fileId).set(track_doc)

    res = {
        "downloadUrl": f"/api/download/{fileId}",
        "oneSheetUrl": f"/api/onesheet/{fileId}"
    }

    if ext != '.mp3':
        res["masterUrl"] = f"/api/master/{fileId}/{ext.replace('.', '')}"

    return res

@app.get("/api/vault")
async def get_vault(uid: str, _auth_uid: str = Depends(verify_token)):
    try:
        docs = db.collection("processedTracks").where("uid", "==", uid).order_by("createdAt", direction=firestore.Query.DESCENDING).stream()
        results = []
        for d in docs:
            data = d.to_dict()
            data['id'] = d.id
            results.append(data)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/vault/{file_id}")
async def delete_track(file_id: str, uid: str = Depends(verify_token)):
    """
    Removes a track from Firestore and deletes all associated GCS blobs.
    """
    file_id = os.path.basename(file_id)
    try:
        doc_ref = db.collection("processedTracks").document(file_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Track not found")
        track = doc.to_dict()
        # Verify ownership
        if track.get("uid") != uid:
            raise HTTPException(status_code=403, detail="Not authorized to delete this track")
        # Delete from Firestore
        doc_ref.delete()
        # Delete GCS blobs (best-effort)
        from google.cloud import storage
        client = storage.Client()
        bucket_name = os.environ.get("GCS_BUCKET", "resonant-crab-audio")
        bucket = client.bucket(bucket_name)
        for prefix in [f"raw/{file_id}", f"finalized/{file_id}", f"promos/{file_id}"]:
            for blob in bucket.list_blobs(prefix=prefix):
                blob.delete()
        return {"status": "deleted", "fileId": file_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pitches")
async def create_pitch(data: dict):
    # data: { uid, title, clientName, trackIds }
    try:
        data['createdAt'] = firestore.SERVER_TIMESTAMP
        doc_ref = db.collection("pitches").add(data)
        return {"pitchId": doc_ref[1].id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pitches/{pitch_id}")
async def get_pitch(pitch_id: str):
    pitch_id = os.path.basename(pitch_id)
    try:
        doc = db.collection("pitches").document(pitch_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Pitch not found")
        
        pitch_data = doc.to_dict()
        track_ids = pitch_data.get('trackIds', [])
        
        # Hydrate tracks
        tracks = []
        for tid in track_ids:
            tdoc = db.collection("processedTracks").document(tid).get()
            if tdoc.exists:
                tdata = tdoc.to_dict()
                tdata['id'] = tdoc.id
                tracks.append(tdata)
        
        pitch_data['tracks'] = tracks
        return pitch_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/download/{file_id}")
async def download_audio(file_id: str):
    file_id = os.path.basename(file_id)
    blob_name = f"finalized/{file_id}.mp3"
    local_path = os.path.join(tempfile.gettempdir(), f"{file_id}_dl.mp3")
    
    if not download_from_gcs(blob_name, local_path):
        raise HTTPException(status_code=404, detail="MP3 not found in GCS")
        
    tags = read_disco_metadata(local_path)
    title = tags.get("TIT2", "Unknown Title").replace("/", "-")
    artist = tags.get("TPE1", "Unknown Artist").replace("/", "-")
    formatted_name = f"{title} - {artist} - (RTag).mp3"
    
    return FileResponse(local_path, media_type="audio/mpeg", filename=formatted_name)

@app.get("/api/master/{file_id}/{ext}")
async def download_master(file_id: str, ext: str):
    file_id = os.path.basename(file_id)
    ext = os.path.basename(ext)
    blob_name = f"raw/{file_id}.{ext}"
    local_path = os.path.join(tempfile.gettempdir(), f"{file_id}_master.{ext}")
    
    if not download_from_gcs(blob_name, local_path):
        raise HTTPException(status_code=404, detail="Master file not found in GCS")
        
    # Attempt to get meta from MP3 twin for naming
    title = "Unknown Title"
    artist = "Unknown Artist"
    mp3_blob = f"finalized/{file_id}.mp3"
    mp3_temp = os.path.join(tempfile.gettempdir(), f"{file_id}_meta.mp3")
    
    if download_from_gcs(mp3_blob, mp3_temp):
        tags = read_disco_metadata(mp3_temp)
        title = tags.get("TIT2", title).replace("/", "-")
        artist = tags.get("TPE1", artist).replace("/", "-")
        
    formatted_name = f"{title} - {artist} - Master.{ext}"
    return FileResponse(local_path, media_type=f"audio/{ext}", filename=formatted_name)

@app.get("/api/onesheet/{file_id}")
async def download_onesheet(file_id: str):
    file_id = os.path.basename(file_id)
    blob_name = f"finalized/{file_id}_OneSheet.pdf"
    local_path = os.path.join(tempfile.gettempdir(), f"{file_id}_sheet.pdf")
    
    if not download_from_gcs(blob_name, local_path):
        raise HTTPException(status_code=404, detail="One-Sheet not found in GCS")
        
    return FileResponse(local_path, media_type="application/pdf", filename=f"{file_id}_OneSheet.pdf")

@app.get("/api/tags/{file_id}")
async def get_tags(file_id: str):
    file_id = os.path.basename(file_id)
    blob_name = f"finalized/{file_id}.mp3"
    local_path = os.path.join(tempfile.gettempdir(), f"{file_id}_tagcheck.mp3")
    
    if not download_from_gcs(blob_name, local_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return read_disco_metadata(local_path)

@app.get("/api/export-zip")
async def export_zip(fileIds: str):
    """
    Packages a list of fileIds into a single ZIP file containing MP3s and One-Sheets.
    fileIds should be a comma-separated string.
    """
    ids = fileIds.split(',')
    
    # Create an in-memory ZIP file
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for fid in ids:
            fid = os.path.basename(fid.strip())
            if not fid:
                continue
            # 1. Add MP3
            mp3_blob = f"finalized/{fid}.mp3"
            mp3_temp = os.path.join(tempfile.gettempdir(), f"{fid}_zip.mp3")
            if download_from_gcs(mp3_blob, mp3_temp):
                tags = read_disco_metadata(mp3_temp)
                title = tags.get("TIT2", "Unknown").replace("/", "-")
                artist = tags.get("TPE1", "Unknown").replace("/", "-")
                zip_file.write(mp3_temp, f"{title} - {artist}.mp3")
            
            # 2. Add PDF
            pdf_blob = f"finalized/{fid}_OneSheet.pdf"
            pdf_temp = os.path.join(tempfile.gettempdir(), f"{fid}_zip.pdf")
            if download_from_gcs(pdf_blob, pdf_temp):
                zip_file.write(pdf_temp, f"{title} - {artist} - OneSheet.pdf")

    zip_buffer.seek(0)
    
    # Generate batch name based on first file or timestamp
    batch_name = f"ResonantCrab_Sync_Package_{uuid.uuid4().hex[:6]}.zip"
    
    return Response(
        zip_buffer.getvalue(),
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename={batch_name}"}
    )
@app.post("/api/promos/{file_id}")
async def generate_promos(file_id: str, uid: str = Depends(verify_token)):
    """
    Finds the most energetic section of a track and generates 15s, 30s, and 60s promo cuts.
    """
    file_id = os.path.basename(file_id)
    with tempfile.TemporaryDirectory() as temp_dir:
        # 1. Download the finalized MP3
        mp3_blob = f"finalized/{file_id}.mp3"
        local_mp3 = os.path.join(temp_dir, "master.mp3")
        if not download_from_gcs(mp3_blob, local_mp3):
            raise HTTPException(status_code=404, detail="Finalized track not found in GCS")

        # 2. Analyze energy to find peak section
        audio, sr = librosa.load(local_mp3, sr=None, mono=True)
        duration = librosa.get_duration(y=audio, sr=sr)

        # Calculate RMS over 1-second hops
        hop = int(sr)  # 1 second
        rms = librosa.feature.rms(y=audio, hop_length=hop)[0]
        # Find center of peak sustained energy (smoothed)
        smoothed = np.convolve(rms, np.ones(5)/5, mode='same')
        peak_frame = int(np.argmax(smoothed))
        peak_sec = peak_frame  # 1 frame = 1 second with hop=sr

        # 3. Read tags for naming
        tags = read_disco_metadata(local_mp3)
        title = tags.get("TIT2", "Track").replace("/", "-")
        artist = tags.get("TPE1", "Artist").replace("/", "-")

        result = {}

        for cut_sec in [15, 30, 60]:
            half = cut_sec / 2
            start = max(0.0, peak_sec - half)
            end = start + cut_sec

            # Clamp to track end
            if end > duration:
                end = duration
                start = max(0.0, end - cut_sec)

            if (end - start) < 5:  # Skip if less than 5s available
                continue

            out_path = os.path.join(temp_dir, f"{cut_sec}s.mp3")
            try:
                (
                    ffmpeg
                    .input(local_mp3, ss=start, to=end)
                    .output(out_path, acodec='libmp3lame', audio_bitrate='320k', loglevel='error')
                    .overwrite_output()
                    .run()
                )
            except Exception as e:
                logger.error(f"ffmpeg cut failed for {cut_sec}s: {e}")
                continue

            blob_name = f"promos/{file_id}_{cut_sec}s.mp3"
            if upload_to_gcs(out_path, blob_name):
                result[f"{cut_sec}s"] = f"/api/promo-download/{file_id}/{cut_sec}"

    if not result:
        raise HTTPException(status_code=500, detail="Failed to generate any promo cuts")

    return result


@app.get("/api/promo-download/{file_id}/{cut_sec}")
async def download_promo(file_id: str, cut_sec: int):
    """
    Streams a promo cut MP3 for download.
    """
    file_id = os.path.basename(file_id)
    blob_name = f"promos/{file_id}_{cut_sec}s.mp3"
    local_path = os.path.join(tempfile.gettempdir(), f"{file_id}_{cut_sec}s_dl.mp3")
    if not download_from_gcs(blob_name, local_path):
        raise HTTPException(status_code=404, detail=f"{cut_sec}s promo not found")
    tags = read_disco_metadata(local_path)
    title = tags.get("TIT2", "Track").replace("/", "-")
    artist = tags.get("TPE1", "Artist").replace("/", "-")
    return FileResponse(local_path, media_type="audio/mpeg", filename=f"{title} - {artist} - {cut_sec}s Promo.mp3")


# Serve the frontend statically
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

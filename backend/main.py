from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import tempfile
import os
import shutil
import json
import uuid

from audio_analyzer import analyze_audio_file
from metadata_manager import strip_metadata, embed_disco_metadata, read_disco_metadata
from one_sheet_generator import generate_one_sheet

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

@app.post("/api/analyze")
async def analyze_audio(file: UploadFile = File(...), localAnalysis: str = Form(None)):
    """
    Accepts an audio file, stores it locally, strips metadata, and merges local Essentia.js analysis.
    Returns a unique fileId and the analyzed data.
    """
    if not file.filename.lower().endswith(('.mp3', '.wav', '.aiff')):
        raise HTTPException(status_code=400, detail="Invalid file type")

    file_id = str(uuid.uuid4())
    ext = os.path.splitext(file.filename)[1]
    safe_filename = f"{file_id}{ext}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)

    # 1. Save file to temp directory
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 2. Strip existing metadata to provide a clean slate
    strip_metadata(file_path)

    # 3. Analyze Audio
    local_data = None
    if localAnalysis:
        try:
            local_data = json.loads(localAnalysis)
        except Exception:
            pass

    analysis_data = analyze_audio_file(file_path, local_data)
    
    if analysis_data is None:
        raise HTTPException(status_code=500, detail="Audio analysis failed")

    # Merge analysis data with initial knowns
    analysis_data["title"] = os.path.splitext(file.filename)[0]
    analysis_data["artist"] = "Unknown Artist"
    analysis_data["album"] = ""
    analysis_data["fileId"] = file_id # Send back ID to map the file

    return analysis_data


@app.post("/api/embed")
async def embed_metadata(
    fileId: str = Form(...),
    metadata: str = Form(...) 
):
    """
    Accepts customized DISCO-compliant metadata from the frontend,
    embeds it into the stripped audio file, and generates a One-Sheet PDF.
    Returns download links.
    """
    try:
        data = json.loads(metadata)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON metadata")

    # Find the original file
    # We don't track extensions in DB for this demo, so we check which one exists
    base_path = os.path.join(UPLOAD_DIR, fileId)
    file_path = None
    for ext in ['.mp3', '.wav', '.aiff']:
        if os.path.exists(base_path + ext):
            file_path = base_path + ext
            break
            
    if not file_path:
        raise HTTPException(status_code=404, detail="Original uploaded file not found.")

    # In a full app, we would use ffmpeg to make sure the final output is 320kbps MP3 here,
    # but for this demo, if it's already an MP3 we just write tags to it. Mutagen strictly works best with MP3s.
    # We will assume MP3 for the embedding step. If it isn't an MP3, Mutagen ID3 will fail.
    # NOTE: ffmpeg conversion is omitted for demo simplicity.
    if not file_path.endswith('.mp3'):
        raise HTTPException(status_code=400, detail="For this demo, please upload MP3 files only so Mutagen can embed ID3 tags.")

    # 1. Embed ID3 tags
    success = embed_disco_metadata(file_path, data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to embed metadata")

    # 2. Generate PDF One-Sheet
    pdf_path = os.path.join(UPLOAD_DIR, f"{fileId}_OneSheet.pdf")
    generate_one_sheet(file_path, data, pdf_path)

    return {
        "downloadUrl": f"http://localhost:8000/api/download/{fileId}",
        "oneSheetUrl": f"http://localhost:8000/api/onesheet/{fileId}"
    }

@app.get("/api/download/{file_id}")
async def download_audio(file_id: str):
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.mp3")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
        
    # Read metadata to format the filename
    tags = read_disco_metadata(file_path)
    title = tags.get("TIT2", "Unknown Title").replace("/", "-")
    artist = tags.get("TPE1", "Unknown Artist").replace("/", "-")
    formatted_name = f"{title} - {artist} - (RTag).mp3"
    
    return FileResponse(file_path, media_type="audio/mpeg", filename=formatted_name)

@app.get("/api/onesheet/{file_id}")
async def download_onesheet(file_id: str):
    pdf_path = os.path.join(UPLOAD_DIR, f"{file_id}_OneSheet.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="One-Sheet not found")
        
    original_mp3 = os.path.join(UPLOAD_DIR, f"{file_id}.mp3")
    title = "Unknown Title"
    artist = "Unknown Artist"
    if os.path.exists(original_mp3):
        tags = read_disco_metadata(original_mp3)
        title = tags.get("TIT2", title).replace("/", "-")
        artist = tags.get("TPE1", artist).replace("/", "-")
        
    formatted_name = f"{title} - {artist} - OneSheet.pdf"
    return FileResponse(pdf_path, media_type="application/pdf", filename=formatted_name)

@app.get("/api/tags/{file_id}")
async def get_tags(file_id: str):
    """
    Scans the actual embedded tags from the MP3 file on disk.
    """
    file_path = os.path.join(UPLOAD_DIR, f"{file_id}.mp3")
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    
    return read_disco_metadata(file_path)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

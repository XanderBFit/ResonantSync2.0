from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TBPM, TKEY, TCON, COMM, TSRC, TPUB, TCOM, TXXX, ID3NoHeaderError
import ffmpeg
import logging

logger = logging.getLogger(__name__)

def downmix_to_mp3(input_path: str, output_path: str):
    """
    Downmixes any audio file to a 320kbps MP3 copy using ffmpeg.
    """
    try:
        stream = ffmpeg.input(input_path)
        stream = ffmpeg.output(stream, output_path, audio_bitrate='320k', format='mp3')
        ffmpeg.run(stream, overwrite_output=True, quiet=True)
        return True
    except Exception as e:
        logger.error(f"FFmpeg conversion failed: {e}")
        return False


def strip_metadata(file_path: str):
    """
    Removes all existing metadata (ID3 tags) from an MP3 file.
    """
    try:
        audio = MP3(file_path, ID3=ID3)
        audio.delete()
        audio.save()
        return True
    except Exception as e:
        logger.error(f"Failed to strip metadata: {e}")
        # If no ID3 header exists, that's fine too.
        return False

def embed_disco_metadata(file_path: str, data: dict):
    """
    Embeds strict DISCO-compliant ID3 tags into the MP3 file.
    """
    try:
        try:
            audio = ID3(file_path)
        except ID3NoHeaderError:
            audio = ID3()
            
        # Core standard tags
        if data.get("title"): audio.add(TIT2(encoding=3, text=data["title"]))
        if data.get("artist"): audio.add(TPE1(encoding=3, text=data["artist"]))
        if data.get("album"): audio.add(TALB(encoding=3, text=data["album"]))
        if data.get("bpm"): audio.add(TBPM(encoding=3, text=str(data["bpm"])))
        if data.get("key"): audio.add(TKEY(encoding=3, text=data["key"]))
        if data.get("genre"): audio.add(TCON(encoding=3, text=data["genre"]))
        
        # Sync & Publishing (DISCO Heavy)
        if data.get("isrc"): audio.add(TSRC(encoding=3, text=data["isrc"]))
        if data.get("composer"): audio.add(TCOM(encoding=3, text=data["composer"]))
        if data.get("publisher"): 
            pub_text = data["publisher"]
            if data.get("oneStop"):
                pub_text = "ONE-STOP (" + pub_text + ")"
            audio.add(TPUB(encoding=3, text=pub_text))
            
        # Comments for Sync Terms / Story / Contact
        contact_info = f"Contact: {data.get('contactName', '')} / {data.get('contactEmail', '')} / {data.get('contactPhone', '')}"
        comments_text = data.get("comments", "") + " | " + contact_info
        audio.add(COMM(encoding=3, lang='eng', desc='Sync & Contact Info', text=comments_text))
        
        # User Defined Explicit Custom Tags (Grouping, Mood, Instruments, Energy, Valence, Danceability)
        if data.get("grouping"): audio.add(TXXX(encoding=3, desc='Grouping', text=str(data["grouping"])))
        if data.get("mood"): audio.add(TXXX(encoding=3, desc='Mood', text=str(data["mood"])))
        if data.get("energy"): audio.add(TXXX(encoding=3, desc='Energy', text=str(data["energy"])))
        if data.get("valence"): audio.add(TXXX(encoding=3, desc='Valence', text=str(data["valence"])))
        if data.get("danceability"): audio.add(TXXX(encoding=3, desc='Danceability', text=str(data["danceability"])))
        if data.get("instruments"): audio.add(TXXX(encoding=3, desc='Instruments', text=str(data["instruments"])))
        if data.get("vocalPresence"): audio.add(TXXX(encoding=3, desc='Vocal Presence', text=str(data["vocalPresence"])))

        audio.save(file_path, v2_version=3) # Saving as v2.3 for best cross-compatibility (DISCO/iTunes)
        return True
    except Exception as e:
        logger.error(f"Failed to embed metadata: {e}")
        return False

def read_disco_metadata(file_path: str) -> dict:
    """
    Reads back the ID3v2 tags from the MP3 file for verification.
    """
    try:
        audio = ID3(file_path)
    except ID3NoHeaderError:
        return {}
    
    data = {}
    for key, frame in audio.items():
        if key.startswith("TXXX"):
            data[f"TXXX:{frame.desc}"] = str(frame.text[0])
        elif key.startswith("COMM"):
            data["COMM"] = str(frame.text[0])
        elif hasattr(frame, 'text') and frame.text:
            data[key] = str(frame.text[0])
            
    return data

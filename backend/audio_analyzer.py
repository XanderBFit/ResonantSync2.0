import logging
import librosa
import numpy as np

logger = logging.getLogger(__name__)

def measure_lufs(file_path: str) -> float | None:
    """
    Measures integrated loudness in LUFS using ITU-R BS.1770 via pyloudnorm.
    Returns the LUFS value as a float, or None on failure.
    """
    try:
        import pyloudnorm as pyln
        # Load audio as float32, preserving stereo if available
        data, rate = librosa.load(file_path, sr=None, mono=False)
        # pyloudnorm expects shape (samples, channels)
        if data.ndim == 1:
            data = data[:, np.newaxis]
        else:
            data = data.T  # (channels, samples) -> (samples, channels)
        meter = pyln.Meter(rate)
        loudness = meter.integrated_loudness(data)
        # Guard against -inf (silence) or pathological values
        if not np.isfinite(loudness):
            return None
        return round(float(loudness), 1)
    except Exception as e:
        logger.error(f"LUFS measurement failed: {e}")
        return None

def analyze_audio_file(file_path: str, local_analysis: dict = None) -> dict:
    """
    Takes local Essentia.js analysis and merges it with LUFS measurement and other server-side metrics.
    """
    try:
        result = local_analysis.copy() if local_analysis else {}

        # Ensure core fields exist
        if "energy" not in result:
            result["energy"] = "0.5"

        # Real integrated loudness measurement (replaces the client-side mock)
        lufs = measure_lufs(file_path)
        result["lufs"] = lufs if lufs is not None else -14.0  # Fallback to streaming target

        return result

    except Exception as e:
        logger.error(f"Error analyzing audio: {e}")
        return None

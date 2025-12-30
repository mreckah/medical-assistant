import whisper
import os
import torch

# --- CONFIGURATION & FFMPEG SETUP ---
# We must help Python find your 'bin' folder containing ffmpeg.exe
# This assumes 'bin' is in your main backend folder.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Goes up one level from 'models'
BIN_DIR = os.path.join(BASE_DIR, "bin")

if os.path.exists(os.path.join(BIN_DIR, "ffmpeg.exe")):
    print(f"[Audio] Found local FFmpeg in: {BIN_DIR}")
    # Add to system PATH for this session only
    os.environ["PATH"] += os.pathsep + BIN_DIR
else:
    print(f"[Audio] Warning: Could not find 'bin/ffmpeg.exe' at {BIN_DIR}. Audio might fail.")

# --- MODEL SETTINGS ---
MODEL_TYPE = "base"
_model = None
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_audio_model():
    """
    Loads the Whisper model into memory once at startup.
    """
    global _model
    print(f"[Audio] Loading Whisper model ('{MODEL_TYPE}') on {_device}...")
    try:
        _model = whisper.load_model(MODEL_TYPE, device=_device)
        print("[Audio] Whisper model loaded successfully.")
    except Exception as e:
        print(f"[Audio] Error loading Whisper: {e}")
        _model = None


def transcribe_audio(file_path: str) -> str:
    """
    Takes an audio file path and returns the text content.
    """
    global _model

    # DEBUG 1: Check if model exists
    if _model is None:
        print("[ERROR] Whisper model is NOT loaded. Check startup logs.")
        return ""

    # DEBUG 2: Check if file exists
    if not os.path.exists(file_path):
        print(f"[ERROR] Audio file not found at: {file_path}")
        return ""

    try:
        print(f"[Audio] Starting transcription for {file_path}...")

        # Whisper handles opening and processing the file internally
        result = _model.transcribe(file_path)
        text = result["text"].strip()

        print(f"[Audio] Success! Text: '{text}'")
        return text

    except Exception as e:
        # DEBUG 3: Print the actual crash error
        print(f"[CRITICAL ERROR] Transcription failed: {e}")
        return ""
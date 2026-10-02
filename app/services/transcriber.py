import whisper
from pathlib import Path
from app.config import settings

# Load model lazily (cached after first load)
_model = None


def _get_model():
    global _model
    if _model is None:
        _model = whisper.load_model(settings.whisper_model)
    return _model


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio file to text using Whisper.
    Returns the full transcript as a string.
    """
    model = _get_model()
    result = model.transcribe(str(audio_path))
    return result["text"].strip()

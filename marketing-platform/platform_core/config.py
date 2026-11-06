"""Configurazione della piattaforma, letta dal file .env."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
# override=True: i valori del .env vincono su variabili già presenti nel terminale
load_dotenv(BASE_DIR / ".env", override=True)

# Cartella dei contenuti sull'hard disk esterno (es. /Volumes/NomeDisco/Contenuti)
MEDIA_DIR = Path(os.getenv("MEDIA_DIR", "")).expanduser() if os.getenv("MEDIA_DIR") else None

# Dati locali della piattaforma (anteprime, trascrizioni, piano editoriale)
DATA_DIR = Path(os.getenv("DATA_DIR", BASE_DIR / "data")).expanduser()
THUMBS_DIR = DATA_DIR / "thumbs"
TRANSCRIPTS_DIR = DATA_DIR / "transcripts"
for _d in (DATA_DIR, THUMBS_DIR, TRANSCRIPTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Europe/Rome"))

# Claude
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
# nomi diversi da quelli che usa Claude Code, così non si mescolano con il terminale
CLAUDE_MODEL = os.getenv("MODELLO_CLAUDE", "claude-opus-5-5")
CLAUDE_EFFORT = os.getenv("EFFORT_CLAUDE", "medium")
CLAUDE_API_URL = os.getenv("CLAUDE_API_URL", "https://api.anthropic.com")

# Trascrizione (faster-whisper): tiny, base, small, medium, large-v3
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "small")
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "it")

# Buffer
BUFFER_API_KEY = os.getenv("BUFFER_API_KEY", "")
BUFFER_API_URL = os.getenv("BUFFER_API_URL", "https://api.buffer.com")
BUFFER_ORG_ID = os.getenv("BUFFER_ORG_ID", "")
# Categoria YouTube (22 = Persone e blog, 27 = Istruzione)
YOUTUBE_CATEGORY_ID = os.getenv("YOUTUBE_CATEGORY_ID", "22")
# Con DRY_RUN=1 la piattaforma NON pubblica: salva solo cosa avrebbe inviato a Buffer
DRY_RUN = os.getenv("DRY_RUN", "1") == "1"

# Cloudinary (link pubblici per i file): cloudinary://API_KEY:API_SECRET@CLOUD_NAME
CLOUDINARY_URL = os.getenv("CLOUDINARY_URL", "")
CLOUDINARY_FOLDER = os.getenv("CLOUDINARY_FOLDER", "marketing-platform")

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "8765"))

VIDEO_EXT = {".mp4", ".mov", ".m4v"}
IMAGE_EXT = {".jpg", ".jpeg", ".png"}


def whisper_available() -> bool:
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        return False
    return True


def status() -> dict:
    """Controlla cosa è configurato, per mostrarlo nell'interfaccia."""
    return {
        "media_dir": str(MEDIA_DIR) if MEDIA_DIR else None,
        "media_dir_ok": bool(MEDIA_DIR and MEDIA_DIR.is_dir()),
        "ffmpeg": shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None,
        "whisper": whisper_available(),
        "claude": bool(ANTHROPIC_API_KEY),
        "buffer": bool(BUFFER_API_KEY and BUFFER_ORG_ID),
        "cloudinary": bool(CLOUDINARY_URL),
        "dry_run": DRY_RUN,
        "model": CLAUDE_MODEL,
    }

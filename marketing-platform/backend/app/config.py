"""Impostazioni della piattaforma.

Si modificano dall'interfaccia (pagina Impostazioni) e vengono salvate solo su questo Mac, in
~/Library/Application Support/MarketingPlatform/impostazioni.json. Le variabili d'ambiente
servono solo per i test.

Il resto del codice legge i valori come attributi del modulo (config.MEDIA_DIR, config.DRY_RUN...):
vengono riletti ogni volta, quindi una modifica dall'interfaccia vale subito.
"""

from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

BASE_DIR = Path(__file__).resolve().parent.parent          # .../backend
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
DEFAULT_STYLE_FILE = Path(__file__).resolve().parent / "stile_predefinito.md"
try:
    APP_VERSION = (BASE_DIR.parent / "VERSION").read_text("utf-8").strip()  # letta all'avvio
except OSError:
    APP_VERSION = "sviluppo"

DATA_DIR = Path(
    os.getenv("MP_DATA_DIR", Path.home() / "Library" / "Application Support" / "MarketingPlatform")
).expanduser()
THUMBS_DIR = DATA_DIR / "anteprime"
TRANSCRIPTS_DIR = DATA_DIR / "trascrizioni"
for _d in (DATA_DIR, THUMBS_DIR, TRANSCRIPTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

SETTINGS_FILE = DATA_DIR / "impostazioni.json"
STYLE_FILE = DATA_DIR / "stile.md"

HOST = "127.0.0.1"
PORT = int(os.getenv("MP_PORT", "8765"))
TIMEZONE = ZoneInfo("Europe/Rome")

VIDEO_EXT = {".mp4", ".mov", ".m4v"}
IMAGE_EXT = {".jpg", ".jpeg", ".png"}

# chiave -> (valore predefinito, è un segreto?)
FIELDS: dict[str, tuple[Any, bool]] = {
    "media_dir": ("", False),
    "claude_engine": ("claude_code", False),   # claude_code (abbonamento) | api (chiave a consumo)
    "anthropic_api_key": ("", True),
    "claude_model": ("claude-opus-5-5", False),
    "claude_effort": ("medium", False),
    "buffer_api_key": ("", True),
    "buffer_org_id": ("6ad06d28221b43577939e3bd", False),
    "cloudinary_url": ("", True),
    "youtube_category_id": ("22", False),
    "whisper_model": ("small", False),
    "dry_run": (True, False),
}

# nomi usati dal codice -> chiave delle impostazioni
_ALIASES = {
    "MEDIA_DIR": "media_dir",
    "ANTHROPIC_API_KEY": "anthropic_api_key",
    "CLAUDE_MODEL": "claude_model",
    "CLAUDE_EFFORT": "claude_effort",
    "BUFFER_API_KEY": "buffer_api_key",
    "BUFFER_ORG_ID": "buffer_org_id",
    "CLOUDINARY_URL": "cloudinary_url",
    "YOUTUBE_CATEGORY_ID": "youtube_category_id",
    "WHISPER_MODEL": "whisper_model",
    "DRY_RUN": "dry_run",
}

# valori fissi o solo per i test
BUFFER_API_URL = os.getenv("MP_BUFFER_API_URL", "https://api.buffer.com")
CLAUDE_API_URL = os.getenv("MP_CLAUDE_API_URL", "https://api.anthropic.com")
CLOUDINARY_FOLDER = "marketing-platform"
WHISPER_LANGUAGE = "it"

_lock = threading.Lock()
_cache: dict[str, Any] | None = None


def _load() -> dict[str, Any]:
    global _cache
    with _lock:
        if _cache is None:
            data: dict[str, Any] = {}
            if SETTINGS_FILE.exists():
                try:
                    data = json.loads(SETTINGS_FILE.read_text("utf-8"))
                except json.JSONDecodeError:
                    data = {}
            # solo per i test: MP_<CHIAVE> nell'ambiente
            for key in FIELDS:
                env = os.getenv(f"MP_{key.upper()}")
                if env is not None:
                    data[key] = env
            _cache = data
        return dict(_cache)


def get(key: str) -> Any:
    default, _ = FIELDS[key]
    value = _load().get(key, default)
    if key == "dry_run":
        return value if isinstance(value, bool) else str(value).lower() in ("1", "true", "si", "sì")
    return value


def save(changes: dict[str, Any]) -> None:
    """Salva le impostazioni. Un segreto lasciato vuoto non viene cancellato."""
    global _cache
    current = _load()
    for key, value in changes.items():
        if key not in FIELDS:
            continue
        _, secret = FIELDS[key]
        if secret and (value is None or value == ""):
            continue
        if isinstance(value, str):
            value = value.strip()
        current[key] = value
    with _lock:
        SETTINGS_FILE.write_text(json.dumps(current, ensure_ascii=False, indent=1), "utf-8")
        try:
            SETTINGS_FILE.chmod(0o600)  # leggibile solo dal tuo utente
        except OSError:
            pass
        _cache = current


def clear_secret(key: str) -> None:
    global _cache
    current = _load()
    current.pop(key, None)
    with _lock:
        SETTINGS_FILE.write_text(json.dumps(current, ensure_ascii=False, indent=1), "utf-8")
        _cache = current


def _mask(value: str) -> str:
    return f"••••{value[-4:]}" if len(value) > 8 else ("••••" if value else "")


def public_settings() -> dict[str, Any]:
    """Impostazioni per l'interfaccia: i segreti si vedono solo mascherati."""
    out: dict[str, Any] = {}
    for key, (_, secret) in FIELDS.items():
        value = get(key)
        out[key] = {"impostato": bool(value), "anteprima": _mask(value)} if secret else value
    return out


def media_root() -> Path | None:
    value = get("media_dir")
    return Path(value).expanduser() if value else None


def style_text() -> str:
    if STYLE_FILE.exists():
        return STYLE_FILE.read_text("utf-8")
    return DEFAULT_STYLE_FILE.read_text("utf-8")


def save_style(text: str) -> None:
    STYLE_FILE.write_text(text, "utf-8")


def whisper_available() -> bool:
    try:
        import faster_whisper  # noqa: F401
    except ImportError:
        return False
    return True


def status() -> dict:
    root = media_root()
    cloud = get("cloudinary_url")
    return {
        "media_dir": str(root) if root else None,
        "media_dir_ok": bool(root and root.is_dir()),
        "whisper": whisper_available(),
        "claude": bool(get("anthropic_api_key")),
        "buffer": bool(get("buffer_api_key") and get("buffer_org_id")),
        "cloudinary": bool(cloud and cloud.startswith("cloudinary://")),
        "dry_run": get("dry_run"),
        "model": get("claude_model"),
    }


def __getattr__(name: str) -> Any:
    """config.MEDIA_DIR, config.DRY_RUN... letti ogni volta dalle impostazioni."""
    if name == "MEDIA_DIR":
        return media_root()
    if name in _ALIASES:
        return get(_ALIASES[name])
    raise AttributeError(name)

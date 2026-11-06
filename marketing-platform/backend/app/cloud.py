"""Caricamento dei file su Cloudinary per avere il link pubblico che Buffer richiede."""

from __future__ import annotations

import json
import os
import threading

from . import config, library

_UPLOADS_FILE = config.DATA_DIR / "uploads.json"
_lock = threading.Lock()


def _load() -> dict:
    if _UPLOADS_FILE.exists():
        return json.loads(_UPLOADS_FILE.read_text("utf-8"))
    return {}


def public_url(clip_id: str) -> str:
    """Carica la clip (una volta sola) e restituisce il suo link pubblico."""
    if not config.CLOUDINARY_URL:
        raise RuntimeError("Inserisci i dati di Cloudinary nelle Impostazioni")
    import cloudinary
    import cloudinary.uploader

    src = library.path_of(clip_id)
    stamp = f"{src.stat().st_mtime}:{src.stat().st_size}"
    with _lock:
        uploads = _load()
        cached = uploads.get(clip_id)
        if cached and cached.get("stamp") == stamp:
            return cached["url"]

    os.environ["CLOUDINARY_URL"] = config.CLOUDINARY_URL  # impostato dalla pagina Impostazioni
    cloudinary.reset_config()
    cloudinary.config(secure=True)
    is_video = src.suffix.lower() in config.VIDEO_EXT
    result = cloudinary.uploader.upload_large(
        str(src),
        resource_type="video" if is_video else "image",
        folder=config.CLOUDINARY_FOLDER,
        public_id=f"{clip_id}-{src.stem}"[:120],
        overwrite=True,
        chunk_size=20_000_000,
    )
    url = result["secure_url"]
    with _lock:
        uploads = _load()
        uploads[clip_id] = {"url": url, "stamp": stamp, "public_id": result.get("public_id")}
        _UPLOADS_FILE.write_text(json.dumps(uploads, indent=1), "utf-8")
    return url

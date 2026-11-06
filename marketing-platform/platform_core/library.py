"""Libreria dei contenuti: legge le clip dalla cartella dell'hard disk esterno."""

from __future__ import annotations

import hashlib
import json
import subprocess
import threading
from pathlib import Path

from . import config

_META_FILE = config.DATA_DIR / "meta.json"
_lock = threading.Lock()


def _clip_id(rel_path: str) -> str:
    return hashlib.sha1(rel_path.encode("utf-8")).hexdigest()[:12]


def _load_meta() -> dict:
    if _META_FILE.exists():
        try:
            return json.loads(_META_FILE.read_text("utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _save_meta(meta: dict) -> None:
    _META_FILE.write_text(json.dumps(meta, ensure_ascii=False, indent=1), "utf-8")


def _probe(path: Path) -> dict:
    """Durata e dimensioni con ffprobe (vuoto se ffprobe manca o fallisce)."""
    try:
        out = subprocess.run(
            [
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height:format=duration",
                "-of", "json", str(path),
            ],
            capture_output=True, text=True, timeout=30, check=True,
        ).stdout
        data = json.loads(out)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return {}
    stream = (data.get("streams") or [{}])[0]
    duration = data.get("format", {}).get("duration")
    return {
        "width": stream.get("width"),
        "height": stream.get("height"),
        "duration": round(float(duration), 1) if duration else None,
    }


def _media_root() -> Path:
    if not config.MEDIA_DIR or not config.MEDIA_DIR.is_dir():
        raise FileNotFoundError(
            "Cartella dei contenuti non trovata. Collega l'hard disk e controlla MEDIA_DIR nel file .env"
        )
    return config.MEDIA_DIR


def scan() -> list[dict]:
    """Elenca video e immagini nella cartella dei contenuti (sottocartelle incluse)."""
    root = _media_root()
    with _lock:
        meta = _load_meta()
        clips = []
        changed = False
        for path in sorted(root.rglob("*")):
            rel = path.relative_to(root)
            # salta file nascosti e i file "._" che macOS crea sui dischi esterni
            if any(part.startswith(".") for part in rel.parts):
                continue
            ext = path.suffix.lower()
            if ext not in config.VIDEO_EXT | config.IMAGE_EXT or not path.is_file():
                continue
            rel_str = rel.as_posix()
            cid = _clip_id(rel_str)
            st = path.stat()
            entry = meta.get(cid)
            if not entry or entry.get("mtime") != st.st_mtime or entry.get("size") != st.st_size:
                entry = {
                    "rel_path": rel_str,
                    "mtime": st.st_mtime,
                    "size": st.st_size,
                    **_probe(path),
                }
                if ext not in config.VIDEO_EXT:
                    entry["duration"] = None
                meta[cid] = entry
                changed = True
            clips.append(
                {
                    "id": cid,
                    "name": path.name,
                    "folder": rel.parent.as_posix() if rel.parent.as_posix() != "." else "",
                    "rel_path": rel_str,
                    "kind": "video" if ext in config.VIDEO_EXT else "image",
                    "size_mb": round(st.st_size / 1_000_000, 1),
                    "duration": entry.get("duration"),
                    "width": entry.get("width"),
                    "height": entry.get("height"),
                    "mtime": st.st_mtime,
                    "transcribed": (config.TRANSCRIPTS_DIR / f"{cid}.json").exists(),
                }
            )
        if changed:
            _save_meta(meta)
    clips.sort(key=lambda c: c["mtime"], reverse=True)
    return clips


def get(clip_id: str) -> dict:
    for clip in scan():
        if clip["id"] == clip_id:
            return clip
    raise KeyError(f"Clip {clip_id} non trovata")


def path_of(clip_id: str) -> Path:
    """Percorso reale del file, verificando che stia dentro la cartella dei contenuti."""
    root = _media_root().resolve()
    with _lock:
        entry = _load_meta().get(clip_id)
    if not entry:
        scan()
        with _lock:
            entry = _load_meta().get(clip_id)
    if not entry:
        raise KeyError(f"Clip {clip_id} non trovata")
    path = (root / entry["rel_path"]).resolve()
    if root not in path.parents or not path.is_file():
        raise KeyError(f"Clip {clip_id} non trovata")
    return path


def thumbnail(clip_id: str) -> Path:
    """Anteprima JPG della clip (creata la prima volta con ffmpeg)."""
    thumb = config.THUMBS_DIR / f"{clip_id}.jpg"
    if thumb.exists():
        return thumb
    src = path_of(clip_id)
    is_video = src.suffix.lower() in config.VIDEO_EXT
    cmd = ["ffmpeg", "-y", "-loglevel", "error"]
    if is_video:
        cmd += ["-ss", "1"]
    cmd += ["-i", str(src), "-frames:v", "1", "-vf", "scale=360:-2", str(thumb)]
    subprocess.run(cmd, capture_output=True, timeout=60)
    if not thumb.exists() and is_video:
        # clip più corta di 1 secondo: prendi il primo fotogramma
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
               "-frames:v", "1", "-vf", "scale=360:-2", str(thumb)]
        subprocess.run(cmd, capture_output=True, timeout=60)
    if not thumb.exists():
        raise RuntimeError("Impossibile creare l'anteprima (ffmpeg è installato?)")
    return thumb

"""Libreria dei contenuti: legge le clip direttamente dalla cartella dell'hard disk esterno.

Durata, dimensioni e anteprime si ricavano con PyAV e Pillow: non serve installare ffmpeg.
"""

from __future__ import annotations

import hashlib
import json
import threading
from pathlib import Path

from . import config

_META_FILE = config.DATA_DIR / "libreria.json"
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
    """Durata e dimensioni del file (vuoto se non leggibile)."""
    try:
        if path.suffix.lower() in config.IMAGE_EXT:
            from PIL import Image

            with Image.open(path) as img:
                return {"width": img.width, "height": img.height, "duration": None}
        import av

        with av.open(str(path)) as container:
            stream = container.streams.video[0]
            duration = container.duration / av.time_base if container.duration else None
            width, height = stream.codec_context.width, stream.codec_context.height
            return {
                "width": width,
                "height": height,
                "duration": round(duration, 1) if duration else None,
            }
    except Exception:  # noqa: BLE001 - un file danneggiato non deve bloccare la libreria
        return {}


def _root() -> Path:
    root = config.media_root()
    if not root:
        raise FileNotFoundError("Scegli la cartella dei contenuti nelle Impostazioni")
    if not root.is_dir():
        raise FileNotFoundError(
            f"Non trovo la cartella {root}. L'hard disk è collegato?"
        )
    return root


def scan() -> list[dict]:
    """Elenca video e immagini nella cartella dei contenuti (sottocartelle incluse)."""
    root = _root()
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
            cid = _clip_id(f"{root}::{rel_str}")
            st = path.stat()
            entry = meta.get(cid)
            if not entry or entry.get("mtime") != st.st_mtime or entry.get("size") != st.st_size:
                entry = {
                    "root": str(root),
                    "rel_path": rel_str,
                    "mtime": st.st_mtime,
                    "size": st.st_size,
                    **_probe(path),
                }
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
    root = _root().resolve()
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
    """Anteprima JPG della clip, creata la prima volta."""
    thumb = config.THUMBS_DIR / f"{clip_id}.jpg"
    if thumb.exists():
        return thumb
    src = path_of(clip_id)
    from PIL import Image

    if src.suffix.lower() in config.IMAGE_EXT:
        with Image.open(src) as img:
            img = img.convert("RGB")
            img.thumbnail((480, 480))
            img.save(thumb, "JPEG", quality=82)
        return thumb

    import av

    with av.open(str(src)) as container:
        stream = container.streams.video[0]
        # prova a saltare al secondo 1 (evita il fotogramma nero iniziale)
        try:
            if container.duration and container.duration / av.time_base > 1.5:
                container.seek(int(av.time_base), any_frame=False)
        except av.AVError:
            pass
        frame = next(container.decode(stream), None)
        if frame is None:
            container.seek(0)
            frame = next(container.decode(stream), None)
        if frame is None:
            raise RuntimeError("Impossibile leggere un fotogramma dal video")
        img = frame.to_image()
        img.thumbnail((480, 480))
        img.save(thumb, "JPEG", quality=82)
    return thumb


def browse(path: str | None) -> dict:
    """Sfoglia le cartelle del Mac per scegliere quella dei contenuti."""
    if not path:
        roots = []
        volumes = Path("/Volumes")
        if volumes.is_dir():
            roots += [
                {"name": f"💽 {p.name}", "path": str(p)}
                for p in sorted(volumes.iterdir())
                if p.is_dir() and not p.name.startswith(".")
            ]
        home = Path.home()
        roots.append({"name": "🏠 Inizio", "path": str(home)})
        for name in ("Desktop", "Documents", "Movies", "Downloads"):
            if (home / name).is_dir():
                roots.append({"name": f"📁 {name}", "path": str(home / name)})
        return {"path": None, "parent": None, "folders": roots}
    current = Path(path).expanduser()
    if not current.is_dir():
        raise FileNotFoundError(f"Cartella non trovata: {current}")
    try:
        children = sorted(
            (p for p in current.iterdir() if p.is_dir() and not p.name.startswith(".")),
            key=lambda p: p.name.lower(),
        )
    except PermissionError:
        raise PermissionError(
            "Il Mac non permette di leggere questa cartella. Apri Impostazioni di Sistema → "
            "Privacy e sicurezza → Accesso completo al disco"
        ) from None
    videos = sum(
        1 for p in current.iterdir()
        if p.is_file() and p.suffix.lower() in config.VIDEO_EXT | config.IMAGE_EXT
        and not p.name.startswith(".")
    )
    parent = str(current.parent) if current.parent != current else None
    return {
        "path": str(current),
        "parent": parent,
        "files_here": videos,
        "folders": [{"name": p.name, "path": str(p)} for p in children],
    }

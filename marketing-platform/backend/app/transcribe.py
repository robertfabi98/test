"""Trascrizione delle clip con Whisper, in locale sul Mac (gratis, nessun upload)."""

from __future__ import annotations

import json
import threading

from . import config, library

_model = None
_model_lock = threading.Lock()


def _get_model():
    global _model
    with _model_lock:
        if _model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise RuntimeError(
                    "La trascrizione non è disponibile: riapri l'app Marketing Platform per completare l'installazione"
                ) from exc
            _model = WhisperModel(config.WHISPER_MODEL, device="cpu", compute_type="int8")
        return _model


def _fmt_srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def cached(clip_id: str) -> dict | None:
    path = config.TRANSCRIPTS_DIR / f"{clip_id}.json"
    if path.exists():
        return json.loads(path.read_text("utf-8"))
    return None


def transcribe(clip_id: str) -> dict:
    """Trascrive la clip (o restituisce la trascrizione già fatta)."""
    existing = cached(clip_id)
    if existing:
        return existing
    src = library.path_of(clip_id)
    if src.suffix.lower() not in config.VIDEO_EXT:
        raise ValueError("Si possono trascrivere solo i video")
    model = _get_model()
    segments, info = model.transcribe(
        str(src), language=config.WHISPER_LANGUAGE or None, vad_filter=True
    )
    segs = [
        {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
        for s in segments
    ]
    result = {
        "clip_id": clip_id,
        "language": info.language,
        "text": " ".join(s["text"] for s in segs).strip(),
        "segments": segs,
    }
    (config.TRANSCRIPTS_DIR / f"{clip_id}.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), "utf-8"
    )
    # sottotitoli .srt, pronti per la fase 2 (editor)
    srt = "\n".join(
        f"{i}\n{_fmt_srt_time(s['start'])} --> {_fmt_srt_time(s['end'])}\n{s['text']}\n"
        for i, s in enumerate(segs, 1)
    )
    (config.TRANSCRIPTS_DIR / f"{clip_id}.srt").write_text(srt, "utf-8")
    return result

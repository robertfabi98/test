"""Piano editoriale: le proposte di Claude restano in attesa finché non le confermi tu."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import datetime

from . import buffer_api, cloud, config, library

_PLAN_FILE = config.DATA_DIR / "piano.json"
_lock = threading.Lock()

STATUS_PENDING = "da_confermare"
STATUS_SCHEDULED = "programmato"
STATUS_SIMULATED = "simulato"
STATUS_PARTIAL = "parziale"
STATUS_ERROR = "errore"
STATUS_CANCELLED = "annullato"


def _load() -> list[dict]:
    if _PLAN_FILE.exists():
        return json.loads(_PLAN_FILE.read_text("utf-8"))
    return []


def _save(items: list[dict]) -> None:
    _PLAN_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=1), "utf-8")


def _parse_due(value: str) -> str:
    """Accetta una data ISO; senza fuso orario usa quello del .env. Deve essere nel futuro."""
    try:
        dt = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Data non valida: {value!r} (formato atteso 2026-11-10T18:30)") from exc
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=config.TIMEZONE)
    if dt <= datetime.now(config.TIMEZONE):
        raise ValueError("La data di pubblicazione deve essere nel futuro")
    return dt.astimezone(config.TIMEZONE).isoformat(timespec="seconds")


def list_items() -> list[dict]:
    with _lock:
        items = _load()
    return sorted(items, key=lambda i: i.get("due_at", ""))


def get_item(item_id: str) -> dict:
    for item in list_items():
        if item["id"] == item_id:
            return item
    raise KeyError(f"Proposta {item_id} non trovata")


def add_proposal(clip_id: str, due_at: str, posts: list[dict], note: str = "") -> dict:
    clip = library.get(clip_id)
    channels = {c["id"]: c for c in buffer_api.list_channels()}
    clean_posts = []
    for p in posts:
        channel = channels.get(p["canale_id"])
        if not channel:
            raise ValueError(f"Canale {p['canale_id']} sconosciuto")
        if channel["service"] == "youtube" and clip["kind"] != "video":
            raise ValueError("YouTube accetta solo video")
        clean_posts.append(
            {
                "channel_id": channel["id"],
                "channel_name": channel["name"],
                "service": channel["service"],
                "text": p["testo"].strip(),
                "title": (p.get("titolo") or "").strip(),
                "due_at": _parse_due(p.get("data_ora") or due_at),
                "buffer_post_id": None,
                "error": None,
            }
        )
    if not clean_posts:
        raise ValueError("Nessun post nella proposta")
    item = {
        "id": uuid.uuid4().hex[:8],
        "clip_id": clip_id,
        "clip_name": clip["name"],
        "clip_kind": clip["kind"],
        "due_at": min(p["due_at"] for p in clean_posts),
        "note": note,
        "status": STATUS_PENDING,
        "created_at": datetime.now(config.TIMEZONE).isoformat(timespec="seconds"),
        "posts": clean_posts,
    }
    with _lock:
        items = _load()
        items.append(item)
        _save(items)
    return item


def update_item(item_id: str, posts: list[dict]) -> dict:
    """Modifiche fatte a mano dall'interfaccia (testi, titolo, data) prima della conferma."""
    with _lock:
        items = _load()
        item = next((i for i in items if i["id"] == item_id), None)
        if not item:
            raise KeyError(f"Proposta {item_id} non trovata")
        if item["status"] != STATUS_PENDING:
            raise ValueError("Si possono modificare solo le proposte da confermare")
        by_channel = {p["channel_id"]: p for p in posts}
        for p in item["posts"]:
            edit = by_channel.get(p["channel_id"])
            if edit:
                p["text"] = edit.get("text", p["text"]).strip()
                p["title"] = edit.get("title", p["title"]).strip()
                if edit.get("due_at"):
                    p["due_at"] = _parse_due(edit["due_at"])
        item["due_at"] = min(p["due_at"] for p in item["posts"])
        _save(items)
    return item


def cancel(item_id: str) -> dict:
    with _lock:
        items = _load()
        item = next((i for i in items if i["id"] == item_id), None)
        if not item:
            raise KeyError(f"Proposta {item_id} non trovata")
        if item["status"] != STATUS_PENDING:
            raise ValueError("Si possono annullare solo le proposte da confermare")
        item["status"] = STATUS_CANCELLED
        _save(items)
    return item


def confirm(item_id: str) -> dict:
    """Carica il file su Cloudinary e programma ogni post su Buffer."""
    item = get_item(item_id)
    retry_ok = (STATUS_PENDING, STATUS_PARTIAL, STATUS_ERROR) + (() if config.DRY_RUN else (STATUS_SIMULATED,))
    if item["status"] not in retry_ok:
        raise ValueError("Questa proposta è già stata gestita")

    channels = {c["id"]: c for c in buffer_api.list_channels()}
    media_url = None
    upload_error = None
    if not config.DRY_RUN:
        try:
            media_url = cloud.public_url(item["clip_id"])
        except Exception as exc:  # noqa: BLE001 - mostriamo l'errore nell'interfaccia
            upload_error = f"Caricamento su Cloudinary non riuscito: {exc}"

    for post in item["posts"]:
        if post.get("buffer_post_id"):
            continue  # già programmato in un tentativo precedente
        channel = channels.get(post["channel_id"]) or {
            "id": post["channel_id"], "name": post["channel_name"], "service": post["service"]
        }
        try:
            post_input = buffer_api.build_post_input(
                channel=channel,
                text=post["text"],
                media_url=media_url or "https://example.com/DRY_RUN",
                media_kind=item["clip_kind"],
                due_at=post["due_at"],
                title=post.get("title", ""),
            )
            if config.DRY_RUN:
                post["dry_run_input"] = post_input
                post["error"] = None
                continue
            if upload_error:
                raise RuntimeError(upload_error)
            created = buffer_api.create_post(post_input)
            post["buffer_post_id"] = created["id"]
            post["error"] = None
        except Exception as exc:  # noqa: BLE001
            post["error"] = str(exc)

    if config.DRY_RUN:
        status = STATUS_SIMULATED
    else:
        ok = [p for p in item["posts"] if p.get("buffer_post_id")]
        status = (
            STATUS_SCHEDULED if len(ok) == len(item["posts"])
            else STATUS_PARTIAL if ok else STATUS_ERROR
        )
    item["status"] = status
    item["media_url"] = media_url
    item["confirmed_at"] = datetime.now(config.TIMEZONE).isoformat(timespec="seconds")

    with _lock:
        items = _load()
        items = [item if i["id"] == item_id else i for i in items]
        _save(items)
    return item

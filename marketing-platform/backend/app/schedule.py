"""Programmazione: unisce le proposte della piattaforma e i post già in coda su Buffer."""

from __future__ import annotations

from datetime import datetime

from . import buffer_api, config, plan


def calendar() -> dict:
    """Tutti gli elementi da mostrare nel calendario, ordinati per data."""
    entries: list[dict] = []
    known_buffer_ids: set[str] = set()

    for item in plan.list_items():
        if item["status"] == plan.STATUS_CANCELLED:
            continue
        for p in item["posts"]:
            if p.get("buffer_post_id"):
                known_buffer_ids.add(p["buffer_post_id"])
            entries.append(
                {
                    "source": "piattaforma",
                    "item_id": item["id"],
                    "status": item["status"],
                    "service": p["service"],
                    "channel_name": p["channel_name"],
                    "title": item["clip_name"],
                    "text": p["text"],
                    "due_at": p["due_at"],
                }
            )

    buffer_error = None
    if config.BUFFER_API_KEY:
        try:
            channels = {c["id"]: c for c in buffer_api.list_channels()}
            for p in buffer_api.list_posts(statuses=["scheduled", "error"], limit=100, newest_first=False):
                if p["id"] in known_buffer_ids:
                    continue
                ch = channels.get(p.get("channelId"), {})
                entries.append(
                    {
                        "source": "buffer",
                        "item_id": None,
                        "buffer_post_id": p["id"],
                        "status": "errore" if p.get("status") == "error" else "in_coda_buffer",
                        "service": p.get("channelService") or ch.get("service", ""),
                        "channel_name": ch.get("name", ""),
                        "title": (p.get("text") or "").split("\n")[0][:80] or "Post senza testo",
                        "text": p.get("text") or "",
                        "due_at": _local(p.get("dueAt")),
                    }
                )
        except Exception as exc:  # noqa: BLE001 - il calendario funziona anche senza Buffer
            buffer_error = str(exc)

    entries = [e for e in entries if e["due_at"]]
    entries.sort(key=lambda e: e["due_at"])
    return {"entries": entries, "buffer_error": buffer_error}


def _local(ts: str | None) -> str | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone(config.TIMEZONE).isoformat(
            timespec="minutes"
        )
    except ValueError:
        return None

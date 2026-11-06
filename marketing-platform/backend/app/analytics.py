"""Analytics per piattaforma, calcolate dai dati dei post pubblicati che Buffer fornisce."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta, timezone

from . import buffer_api, config

# metriche sommate fra i post
_SUM = ["views", "reach", "reactions", "comments", "shares", "saves", "follows", "totalTimeWatched", "impressions", "clicks"]

LABELS = {
    "views": "Visualizzazioni",
    "reach": "Copertura",
    "reactions": "Mi piace",
    "comments": "Commenti",
    "shares": "Condivisioni",
    "saves": "Salvataggi",
    "follows": "Nuovi follower",
    "totalTimeWatched": "Tempo di visione (min)",
    "averageTimeWatched": "Visione media (sec)",
    "engagementRate": "Engagement medio (%)",
    "impressions": "Impressioni",
    "clicks": "Clic",
}

_cache: dict[tuple, tuple[float, dict]] = {}
_lock = threading.Lock()
_TTL = 600  # i dati di Buffer si aggiornano una volta al giorno: 10 minuti di cache bastano


def _parse(ts: str | None) -> datetime | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except ValueError:
        return None


def _metrics(post: dict) -> dict[str, float]:
    return {m["type"]: float(m["value"]) for m in post.get("metrics") or [] if m.get("value") is not None}


def _summarize(posts: list[dict]) -> dict:
    totals: dict[str, float] = {}
    present: set[str] = set()
    for p in posts:
        for k, v in p["metrics"].items():
            present.add(k)
            if k in _SUM:
                totals[k] = totals.get(k, 0) + v
    # engagement: media semplice dei post; visione media: pesata sulle visualizzazioni
    rates = [p["metrics"]["engagementRate"] for p in posts if "engagementRate" in p["metrics"]]
    if rates:
        totals["engagementRate"] = round(sum(rates) / len(rates), 2)
    rows = [(p["metrics"]["averageTimeWatched"], p["metrics"].get("views") or 1)
            for p in posts if "averageTimeWatched" in p["metrics"]]
    if rows:
        totals["averageTimeWatched"] = round(sum(v * w for v, w in rows) / sum(w for _, w in rows), 2)
    interactions = sum(totals.get(k, 0) for k in ("reactions", "comments", "shares", "saves"))
    if present & {"reactions", "comments", "shares", "saves"}:
        totals["interactions"] = interactions
    totals["posts"] = len(posts)
    return {k: (round(v, 2) if isinstance(v, float) else v) for k, v in totals.items()}


def channel_report(channel_id: str, days: int, refresh: bool = False) -> dict:
    key = (channel_id, days)
    with _lock:
        hit = _cache.get(key)
        if hit and not refresh and time.time() - hit[0] < _TTL:
            return hit[1]

    channels = {c["id"]: c for c in buffer_api.list_channels()}
    channel = channels.get(channel_id)
    if not channel:
        raise KeyError(f"Canale {channel_id} non trovato")

    since = datetime.now(timezone.utc) - timedelta(days=days)
    raw = buffer_api.list_posts(statuses=["sent"], channel_ids=[channel_id], limit=200, with_metrics=True)
    posts = []
    for p in raw:
        sent = _parse(p.get("sentAt") or p.get("dueAt"))
        if not sent or sent < since:
            continue
        thumb = next((a.get("thumbnail") for a in p.get("assets") or [] if a.get("thumbnail")), None)
        posts.append(
            {
                "id": p["id"],
                "text": (p.get("text") or "").strip(),
                "sent_at": sent.astimezone(config.TIMEZONE).isoformat(timespec="minutes"),
                "link": p.get("externalLink"),
                "thumbnail": thumb,
                "metrics": _metrics(p),
            }
        )
    posts.sort(key=lambda p: p["sent_at"])

    # periodo precedente di pari durata, per il confronto
    prev_since = since - timedelta(days=days)
    previous = [
        {"metrics": _metrics(p)}
        for p in raw
        if (d := _parse(p.get("sentAt") or p.get("dueAt"))) and prev_since <= d < since
    ]

    report = {
        "channel": channel,
        "days": days,
        "totals": _summarize(posts),
        "previous": _summarize(previous) if previous else None,
        "posts": posts,
        "labels": LABELS,
        "updated_at": datetime.now(config.TIMEZONE).isoformat(timespec="minutes"),
    }
    with _lock:
        _cache[key] = (time.time(), report)
    return report


def overview(days: int, refresh: bool = False) -> list[dict]:
    out = []
    for ch in buffer_api.list_channels():
        try:
            r = channel_report(ch["id"], days, refresh)
            out.append({"channel": ch, "totals": r["totals"], "previous": r["previous"], "error": None})
        except Exception as exc:  # noqa: BLE001 - un canale in errore non blocca gli altri
            out.append({"channel": ch, "totals": None, "previous": None, "error": str(exc)})
    return out

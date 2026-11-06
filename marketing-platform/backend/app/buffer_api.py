"""Collegamento a Buffer.

Modo principale: il server MCP ufficiale di Buffer (accesso dal browser, nessuna chiave) - vedi buffer_mcp.py.
Alternativa: l'API GraphQL con una chiave personale (Impostazioni → Avanzate).
"""

from __future__ import annotations

import json

import requests

from . import buffer_mcp, config

# Campi che nello schema GraphQL di Buffer sono enum (vanno scritti senza virgolette)
_ENUM_KEYS = {"schedulingType", "mode", "type", "field", "direction", "status"}


def _literal(value, key: str | None = None) -> str:
    """Converte un dict Python in un letterale GraphQL, come negli esempi di Buffer."""
    if isinstance(value, dict):
        inner = ", ".join(f"{k}: {_literal(v, k)}" for k, v in value.items() if v is not None)
        return "{ " + inner + " }"
    if isinstance(value, list):
        return "[" + ", ".join(_literal(v, key) for v in value) + "]"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if key in _ENUM_KEYS:
        if not str(value).isidentifier():
            raise ValueError(f"Valore non valido per {key}: {value!r}")
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)

# Canali già collegati al tuo Buffer, usati se l'API non risponde
FALLBACK_CHANNELS = [
    {"id": "6ad06d43778b240e2f14bb94", "name": "iamrobertfabi_", "service": "instagram"},
    {"id": "6ad06d59778b240e2f14c051", "name": "iamrobertfabi", "service": "tiktok"},
    {"id": "6ad06d6e778b240e2f14c13c", "name": "Robert Fabi", "service": "youtube"},
]

_channels_cache: list[dict] | None = None


class BufferError(RuntimeError):
    pass


def mode() -> str | None:
    """"mcp" se Buffer è collegato con l'accesso dal browser, "api" se c'è una chiave, altrimenti None."""
    if buffer_mcp.connected():
        return "mcp"
    if config.BUFFER_API_KEY:
        return "api"
    return None


def available() -> bool:
    return mode() is not None


def _mcp(tool: str, args: dict):
    try:
        return buffer_mcp.call(tool, args)
    except buffer_mcp.BufferMCPError as exc:
        raise BufferError(str(exc)) from None


def _gql(query: str, variables: dict | None = None) -> dict:
    if not config.BUFFER_API_KEY:
        raise BufferError("Inserisci la chiave di Buffer nelle Impostazioni")
    resp = requests.post(
        config.BUFFER_API_URL,
        json={"query": query, "variables": variables or {}},
        headers={"Authorization": f"Bearer {config.BUFFER_API_KEY}"},
        timeout=60,
    )
    try:
        body = resp.json()
    except ValueError:
        raise BufferError(f"Risposta non valida da Buffer (HTTP {resp.status_code})") from None
    if body.get("errors"):
        raise BufferError("; ".join(e.get("message", str(e)) for e in body["errors"]))
    if resp.status_code >= 400:
        raise BufferError(f"Errore Buffer HTTP {resp.status_code}")
    return body["data"]


def list_channels(refresh: bool = False) -> list[dict]:
    global _channels_cache
    if _channels_cache is not None and not refresh:
        return _channels_cache
    try:
        if mode() == "mcp":
            data = _mcp("list_channels", {"organizationId": config.BUFFER_ORG_ID})
        else:
            org = _literal({"organizationId": config.BUFFER_ORG_ID})
            data = _gql(f"query GetChannels {{ channels(input: {org}) {{ id name service }} }}")["channels"]
        _channels_cache = [
            {"id": c["id"], "name": c.get("name") or c.get("displayName"), "service": c["service"]}
            for c in data
            if not c.get("isDisconnected")
        ]
    except (BufferError, requests.RequestException, KeyError, TypeError):
        _channels_cache = None
        return FALLBACK_CHANNELS
    return _channels_cache


def build_post_input(
    *, channel: dict, text: str, media_url: str, media_kind: str, due_at: str,
    title: str = "", ig_type: str = "",
) -> dict:
    """Costruisce l'input di createPost come richiesto da Buffer per ogni social."""
    service = channel["service"]
    if media_kind == "video":
        asset = {"video": {"url": media_url}}
    else:
        asset = {"image": {"url": media_url, "metadata": {"altText": title or text[:120]}}}

    post: dict = {
        "channelId": channel["id"],
        "text": text,
        "schedulingType": "automatic",
        "mode": "customScheduled",
        "dueAt": due_at,
        "assets": [asset],
    }
    if service == "instagram":
        # un singolo video nel feed va pubblicato come reel
        kind = ig_type or ("reel" if media_kind == "video" else "post")
        post["metadata"] = {"instagram": {"type": kind, "shouldShareToFeed": True}}
    elif service == "youtube":
        if media_kind != "video":
            raise BufferError("YouTube accetta solo video")
        post["metadata"] = {
            "youtube": {"title": (title or text)[:100], "categoryId": config.YOUTUBE_CATEGORY_ID}
        }
    elif service == "tiktok" and title:
        post["metadata"] = {"tiktok": {"title": title}}
    elif service == "facebook":
        post["metadata"] = {"facebook": {"type": "reel" if media_kind == "video" else "post"}}
    return post


def create_post(post_input: dict) -> dict:
    if mode() == "mcp":
        created = _mcp("create_post", post_input) or {}
        post = created.get("post", created) if isinstance(created, dict) else {}
        if not post.get("id"):
            raise BufferError(str(created) or "Buffer non ha creato il post")
        return post
    query = (
        f"mutation CreatePost {{ createPost(input: {_literal(post_input)}) {{"
        " ... on PostActionSuccess { post { id status dueAt } }"
        " ... on MutationError { message } } }"
    )
    data = _gql(query)
    result = data.get("createPost") or {}
    if "post" in result:
        return result["post"]
    raise BufferError(result.get("message", "Buffer non ha creato il post"))


# ---------- lettura dei post (analytics e calendario) ----------

# Dal più completo al più semplice: se Buffer non riconosce un campo, si riprova con meno campi.
_POST_FIELDS = [
    "id text status channelId channelService dueAt sentAt externalLink "
    "assets { thumbnail } metrics { type name value unit }",
    "id text status channelId channelService dueAt sentAt externalLink metrics { type name value unit }",
    "id text status channelId dueAt sentAt",
]


def list_posts(
    *, statuses: list[str], channel_ids: list[str] | None = None, limit: int = 100,
    with_metrics: bool = False, newest_first: bool = True,
) -> list[dict]:
    """Post dell'organizzazione con lo stato indicato (sent, scheduled, draft, error...)."""
    if mode() == "mcp":
        args: dict = {
            "organizationId": config.BUFFER_ORG_ID,
            "status": statuses,
            "includeMetrics": with_metrics,
            "sort": [{"field": "dueAt", "direction": "desc" if newest_first else "asc"}],
        }
        if channel_ids:
            args["channelIds"] = channel_ids
        try:
            return buffer_mcp.call_pages("list_posts", args, limit)
        except buffer_mcp.BufferMCPError as exc:
            raise BufferError(str(exc)) from None
    filt: dict = {"status": statuses}
    if channel_ids:
        filt["channelIds"] = channel_ids
    fields_options = _POST_FIELDS if with_metrics else [
        f.replace(" metrics { type name value unit }", "") for f in _POST_FIELDS[1:]
    ]
    sort = [{"field": "dueAt", "direction": "desc" if newest_first else "asc"}]
    attempts = [(f, True) for f in fields_options] + [(fields_options[-1], False)]

    last_error: Exception | None = None
    for fields, with_sort in attempts:
        posts: list[dict] = []
        cursor = None
        try:
            while len(posts) < limit:
                args: dict = {"organizationId": config.BUFFER_ORG_ID, "filter": filt}
                if with_sort:
                    args["sort"] = sort
                after = f", after: {json.dumps(cursor)}" if cursor else ""
                query = (
                    f"query GetPosts {{ posts(first: {min(50, limit - len(posts))}{after}, "
                    f"input: {_literal(args)}) {{ edges {{ node {{ {fields} }} }} "
                    f"pageInfo {{ hasNextPage endCursor }} }} }}"
                )
                data = _gql(query)["posts"]
                posts += [e["node"] for e in data.get("edges", [])]
                page = data.get("pageInfo") or {}
                if not page.get("hasNextPage") or not page.get("endCursor"):
                    break
                cursor = page["endCursor"]
            return posts
        except BufferError as exc:
            last_error = exc
            msg = str(exc).lower()
            if not any(w in msg for w in ("field", "cannot query", "sort", "argument", "unknown")):
                raise
    raise last_error or BufferError("Impossibile leggere i post da Buffer")

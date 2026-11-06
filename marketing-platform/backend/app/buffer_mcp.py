"""Collegamento a Buffer tramite il server MCP ufficiale (https://mcp.buffer.com/mcp).

Niente chiave API: la prima volta si apre il browser, accedi a Buffer e approvi l'accesso.
I token vengono salvati solo su questo Mac e rinnovati in automatico.
"""

from __future__ import annotations

import asyncio
import json
import os
import threading
import webbrowser
from typing import Any, Awaitable, Callable

from . import config

MCP_URL = os.getenv("MP_BUFFER_MCP_URL", "https://mcp.buffer.com/mcp")
REDIRECT_URI = f"http://localhost:{config.PORT}/oauth/buffer/callback"
_TOKENS_FILE = config.DATA_DIR / "buffer_mcp.json"
_TIMEOUT = 90


class BufferMCPError(RuntimeError):
    pass


# ---------- token salvati sul Mac ----------

def _read() -> dict:
    if _TOKENS_FILE.exists():
        try:
            return json.loads(_TOKENS_FILE.read_text("utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _write(data: dict) -> None:
    _TOKENS_FILE.write_text(json.dumps(data, indent=1), "utf-8")
    try:
        _TOKENS_FILE.chmod(0o600)
    except OSError:
        pass


class _FileStorage:
    async def get_tokens(self):
        from mcp.shared.auth import OAuthToken

        raw = _read().get("tokens")
        return OAuthToken.model_validate(raw) if raw else None

    async def set_tokens(self, tokens) -> None:
        data = _read()
        data["tokens"] = tokens.model_dump(mode="json", exclude_none=True)
        _write(data)

    async def get_client_info(self):
        from mcp.shared.auth import OAuthClientInformationFull

        raw = _read().get("client")
        return OAuthClientInformationFull.model_validate(raw) if raw else None

    async def set_client_info(self, client_info) -> None:
        data = _read()
        data["client"] = client_info.model_dump(mode="json", exclude_none=True)
        _write(data)


def connected() -> bool:
    return bool(_read().get("tokens"))


def disconnect() -> None:
    if _TOKENS_FILE.exists():
        _TOKENS_FILE.unlink()


# ---------- ciclo asincrono dedicato ----------

_loop = asyncio.new_event_loop()
threading.Thread(target=_loop.run_forever, daemon=True, name="buffer-mcp").start()

_login = {"state": "idle", "url": None, "error": None}
_callback: asyncio.Future | None = None


def login_status() -> dict:
    return {**_login, "connected": connected()}


async def _redirect(url: str) -> None:
    if _login["state"] != "in_attesa":
        # token scaduti e non rinnovabili: serve un nuovo accesso dalle Impostazioni
        raise BufferMCPError("Il collegamento con Buffer è scaduto: ricollegalo nelle Impostazioni")
    _login["url"] = url
    try:
        webbrowser.open(url)
    except Exception:  # noqa: BLE001 - l'interfaccia mostra comunque il link
        pass


async def _wait_callback():
    from mcp.client.auth import AuthorizationCodeResult

    global _callback
    _callback = _loop.create_future()
    try:
        code, state = await asyncio.wait_for(_callback, timeout=300)
    except asyncio.TimeoutError:
        raise BufferMCPError("Accesso a Buffer non completato in tempo, riprova") from None
    return AuthorizationCodeResult(code=code, state=state)


def oauth_callback(code: str | None, state: str | None, error: str | None) -> None:
    """Chiamata dalla pagina a cui Buffer rimanda dopo l'accesso."""
    fut = _callback
    if fut is None or fut.done():
        return
    if error or not code:
        _loop.call_soon_threadsafe(fut.set_exception, BufferMCPError(f"Accesso negato: {error or 'nessun codice'}"))
    else:
        _loop.call_soon_threadsafe(fut.set_result, (code, state))


def _provider():
    from mcp.client.auth import OAuthClientProvider
    from mcp.shared.auth import OAuthClientMetadata

    metadata = OAuthClientMetadata(
        client_name="Marketing Platform",
        redirect_uris=[REDIRECT_URI],
        grant_types=["authorization_code", "refresh_token"],
        response_types=["code"],
        token_endpoint_auth_method="none",
    )
    return OAuthClientProvider(
        server_url=MCP_URL,
        client_metadata=metadata,
        storage=_FileStorage(),
        redirect_handler=_redirect,
        callback_handler=_wait_callback,
    )


async def _with_session(fn: Callable[[Any], Awaitable[Any]]) -> Any:
    import httpx2
    from mcp.client.session import ClientSession
    from mcp.client.streamable_http import streamable_http_client

    async with httpx2.AsyncClient(auth=_provider(), timeout=httpx2.Timeout(60, read=120)) as http:
        async with streamable_http_client(MCP_URL, http_client=http) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                return await fn(session)


def _run(coro, timeout: float = _TIMEOUT):
    future = asyncio.run_coroutine_threadsafe(coro, _loop)
    try:
        return future.result(timeout=timeout)
    except BaseExceptionGroup as group:  # errori dentro i task group di MCP: mostra il primo
        first = group.exceptions[0]
        while isinstance(first, BaseExceptionGroup):
            first = first.exceptions[0]
        raise BufferMCPError(str(first)) from None


def _parse(result) -> Any:
    texts = [c.text for c in result.content if getattr(c, "type", "") == "text"]
    if result.is_error:
        raise BufferMCPError(texts[0] if texts else "Errore da Buffer")
    if not texts:
        return None
    try:
        return json.loads(texts[0])
    except json.JSONDecodeError:
        return texts[0]


# ---------- funzioni usate dalla piattaforma ----------

def call(tool: str, args: dict) -> Any:
    """Chiama uno strumento del server MCP di Buffer (es. list_channels)."""
    if not connected():
        raise BufferMCPError("Collega Buffer nelle Impostazioni")

    async def go(session):
        return _parse(await session.call_tool(tool, args))

    return _run(_with_session(go))


def call_pages(tool: str, args: dict, limit: int) -> list[dict]:
    """Strumenti a pagine (list_posts): segue i cursori fino a `limit` elementi, in una sola sessione."""
    if not connected():
        raise BufferMCPError("Collega Buffer nelle Impostazioni")

    async def go(session):
        nodes: list[dict] = []
        cursor = None
        while len(nodes) < limit:
            page_args = {**args, "first": min(50, limit - len(nodes))}
            if cursor:
                page_args["after"] = cursor
            data = _parse(await session.call_tool(tool, page_args)) or {}
            nodes += [e["node"] for e in data.get("edges", [])]
            info = data.get("pageInfo") or {}
            if not info.get("hasNextPage") or not info.get("endCursor"):
                break
            cursor = info["endCursor"]
        return nodes

    return _run(_with_session(go), timeout=_TIMEOUT * 2)


def start_login() -> None:
    """Avvia l'accesso: si apre il browser sulla pagina di Buffer."""
    if _login["state"] == "in_attesa":
        return
    _login.update(state="in_attesa", url=None, error=None)

    async def go():
        try:
            account = await _with_session(lambda s: s.call_tool("get_account", {}))
            data = _parse(account) or {}
            orgs = data.get("organizations") or []
            if orgs and not config.get("buffer_org_id"):
                config.save({"buffer_org_id": orgs[0]["id"]})
            elif orgs and config.get("buffer_org_id") not in {o["id"] for o in orgs}:
                config.save({"buffer_org_id": orgs[0]["id"]})
            _login.update(state="collegato", url=None, error=None)
        except BaseException as exc:  # noqa: BLE001
            err = exc
            while isinstance(err, BaseExceptionGroup):
                err = err.exceptions[0]
            _login.update(state="errore", url=None, error=str(err) or err.__class__.__name__)

    asyncio.run_coroutine_threadsafe(go(), _loop)

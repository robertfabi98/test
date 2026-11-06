"""Backend della Marketing Platform (API per l'interfaccia React)."""

from __future__ import annotations

import os
import threading
import time
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from . import agent, analytics, buffer_api, buffer_mcp, claude_code, config, library, plan, schedule, transcribe

app = FastAPI(title="Marketing Platform", docs_url=None, redoc_url=None, openapi_url=None)

_ALLOWED_HOSTS = {f"127.0.0.1:{config.PORT}", f"localhost:{config.PORT}", "127.0.0.1", "localhost", "testserver"}


@app.middleware("http")
async def local_only(request: Request, call_next):
    """La piattaforma risponde solo al tuo Mac.

    - Host controllato: blocca i siti che provano a raggiungerla con trucchi DNS.
    - Le modifiche richiedono l'intestazione X-MP: un altro sito aperto nel browser
      non può inviarla, quindi non può pubblicare o cambiare impostazioni al posto tuo.
    """
    if request.headers.get("host", "") not in _ALLOWED_HOSTS:
        return JSONResponse({"detail": "Host non consentito"}, status_code=403)
    if request.method not in ("GET", "HEAD", "OPTIONS") and request.headers.get("x-mp") != "1":
        return JSONResponse({"detail": "Richiesta non consentita"}, status_code=403)
    return await call_next(request)


def _fail(exc: Exception) -> HTTPException:
    if isinstance(exc, KeyError):
        return HTTPException(404, str(exc).strip("'\""))
    return HTTPException(400, str(exc))


# ---------- stato e impostazioni ----------

@app.get("/api/ping")
def ping():
    return {"ok": True, "app": "marketing-platform", "version": config.APP_VERSION}


@app.get("/api/stato")
def stato():
    st = config.status()
    st["buffer"] = buffer_api.available()
    st["buffer_mode"] = buffer_api.mode()
    st["claude_engine"] = config.get("claude_engine")
    if st["claude_engine"] == "api":
        st["claude"] = bool(config.get("anthropic_api_key"))
    else:
        cc = claude_code.status()
        st["claude"] = cc["installed"] and cc["logged_in"] is not False
    return st


# ---------- collegamenti senza chiavi: Claude Code e Buffer via MCP ----------

@app.get("/api/claude-code")
def cc_status(verifica: bool = False):
    return claude_code.status(check_login=verifica)


@app.post("/api/claude-code/installa")
def cc_install():
    claude_code.install()
    return claude_code.status()


@app.post("/api/claude-code/accedi")
def cc_login():
    try:
        claude_code.open_login()
    except Exception as exc:  # noqa: BLE001
        raise _fail(exc) from None
    return claude_code.status()


@app.get("/api/buffer")
def buffer_status():
    return {**buffer_mcp.login_status(), "mode": buffer_api.mode(), "org_id": config.get("buffer_org_id")}


@app.post("/api/buffer/collega")
def buffer_connect():
    buffer_mcp.start_login()
    return buffer_mcp.login_status()


@app.post("/api/buffer/scollega")
def buffer_disconnect():
    buffer_mcp.disconnect()
    buffer_api.list_channels(refresh=True)
    return buffer_mcp.login_status()


@app.get("/oauth/buffer/callback")
def buffer_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    from fastapi.responses import HTMLResponse

    buffer_mcp.oauth_callback(code, state, error)
    msg = "Buffer è collegato. Puoi chiudere questa scheda e tornare alla Marketing Platform." if code else \
        "Accesso a Buffer non riuscito. Torna alla Marketing Platform e riprova."
    return HTMLResponse(
        f"<!doctype html><meta charset=utf-8><title>Buffer</title>"
        f"<body style='font-family:-apple-system,sans-serif;display:grid;place-items:center;height:90vh'>"
        f"<p style='font-size:18px'>{msg}</p><script>setTimeout(()=>window.close(),2500)</script></body>"
    )


@app.get("/api/impostazioni")
def settings_get():
    return config.public_settings()


class SettingsIn(BaseModel):
    media_dir: str | None = None
    anthropic_api_key: str | None = None
    claude_engine: str | None = None
    claude_model: str | None = None
    claude_effort: str | None = None
    buffer_api_key: str | None = None
    buffer_org_id: str | None = None
    cloudinary_url: str | None = None
    youtube_category_id: str | None = None
    whisper_model: str | None = None
    dry_run: bool | None = None


@app.put("/api/impostazioni")
def settings_put(body: SettingsIn):
    changes: dict[str, Any] = {k: v for k, v in body.model_dump().items() if v is not None}
    if "claude_engine" in changes and changes["claude_engine"] not in ("claude_code", "api"):
        raise HTTPException(400, "Motore non valido")
    if "claude_effort" in changes and changes["claude_effort"] not in ("low", "medium", "high"):
        raise HTTPException(400, "Livello non valido")
    if "cloudinary_url" in changes and changes["cloudinary_url"] and not changes["cloudinary_url"].startswith(
        "cloudinary://"
    ):
        raise HTTPException(400, "Il dato di Cloudinary deve iniziare con cloudinary://")
    if changes.get("media_dir"):
        from pathlib import Path

        if not Path(changes["media_dir"]).expanduser().is_dir():
            raise HTTPException(400, "Cartella non trovata")
    config.save(changes)
    if "buffer_api_key" in changes or "buffer_org_id" in changes:
        buffer_api.list_channels(refresh=True)
    return config.public_settings()


@app.delete("/api/impostazioni/{key}")
def settings_clear(key: str):
    if key not in config.FIELDS or not config.FIELDS[key][1]:
        raise HTTPException(400, "Impostazione non valida")
    config.clear_secret(key)
    return config.public_settings()


@app.get("/api/cartelle")
def folders(path: str | None = None):
    try:
        return library.browse(path)
    except Exception as exc:  # noqa: BLE001
        raise _fail(exc) from None


@app.get("/api/stile")
def style_get():
    return {"testo": config.style_text()}


class StyleIn(BaseModel):
    testo: str


@app.put("/api/stile")
def style_put(body: StyleIn):
    if not body.testo.strip():
        raise HTTPException(400, "Lo stile non può essere vuoto")
    config.save_style(body.testo)
    return {"testo": config.style_text()}


@app.post("/api/stile/ripristina")
def style_reset():
    if config.STYLE_FILE.exists():
        config.STYLE_FILE.unlink()
    return {"testo": config.style_text()}


# ---------- libreria ----------

@app.get("/api/clip")
def clip_list():
    try:
        return library.scan()
    except Exception as exc:  # noqa: BLE001
        raise _fail(exc) from None


@app.get("/api/clip/{clip_id}/anteprima")
def clip_thumb(clip_id: str):
    try:
        return FileResponse(library.thumbnail(clip_id), media_type="image/jpeg")
    except Exception as exc:  # noqa: BLE001
        raise _fail(exc) from None


@app.get("/api/clip/{clip_id}/file")
def clip_file(clip_id: str):
    try:
        return FileResponse(library.path_of(clip_id))
    except Exception as exc:  # noqa: BLE001
        raise _fail(exc) from None


@app.get("/api/clip/{clip_id}/trascrizione")
def clip_transcript(clip_id: str):
    return transcribe.cached(clip_id) or {}


@app.post("/api/clip/{clip_id}/trascrivi")
def clip_transcribe(clip_id: str):
    try:
        return transcribe.transcribe(clip_id)
    except Exception as exc:  # noqa: BLE001
        raise _fail(exc) from None


# ---------- canali, chat, piano ----------

@app.get("/api/canali")
def channels():
    return buffer_api.list_channels(refresh=True)


class ChatIn(BaseModel):
    messaggio: str


@app.get("/api/chat")
def chat_history():
    return agent.session.transcript


@app.post("/api/chat")
def chat(body: ChatIn):
    if not body.messaggio.strip():
        raise HTTPException(400, "Messaggio vuoto")
    try:
        return agent.session.send(body.messaggio.strip())
    except Exception as exc:  # noqa: BLE001
        raise _fail(exc) from None


@app.post("/api/chat/nuova")
def chat_reset():
    agent.session.reset()
    return {"ok": True}


@app.get("/api/piano")
def plan_list():
    return plan.list_items()


class PostEdit(BaseModel):
    channel_id: str
    text: str
    title: str = ""
    due_at: str = ""


class PlanEdit(BaseModel):
    posts: list[PostEdit]


@app.put("/api/piano/{item_id}")
def plan_update(item_id: str, body: PlanEdit):
    try:
        return plan.update_item(item_id, [p.model_dump() for p in body.posts])
    except Exception as exc:  # noqa: BLE001
        raise _fail(exc) from None


@app.post("/api/piano/{item_id}/conferma")
def plan_confirm(item_id: str):
    try:
        return plan.confirm(item_id)
    except Exception as exc:  # noqa: BLE001
        raise _fail(exc) from None


@app.post("/api/piano/{item_id}/annulla")
def plan_cancel(item_id: str):
    try:
        return plan.cancel(item_id)
    except Exception as exc:  # noqa: BLE001
        raise _fail(exc) from None


# ---------- analytics e programmazione ----------

@app.get("/api/analytics")
def analytics_overview(giorni: int = 30, aggiorna: bool = False):
    if not buffer_api.available():
        raise HTTPException(400, "Collega Buffer nelle Impostazioni per vedere le analytics")
    return analytics.overview(max(1, min(giorni, 365)), aggiorna)


@app.get("/api/analytics/{channel_id}")
def analytics_channel(channel_id: str, giorni: int = 30, aggiorna: bool = False):
    if not buffer_api.available():
        raise HTTPException(400, "Collega Buffer nelle Impostazioni per vedere le analytics")
    try:
        return analytics.channel_report(channel_id, max(1, min(giorni, 365)), aggiorna)
    except Exception as exc:  # noqa: BLE001
        raise _fail(exc) from None


@app.get("/api/calendario")
def calendar():
    return schedule.calendar()


# ---------- spegnimento ----------

@app.post("/api/spegni")
def shutdown():
    """Chiude la piattaforma (pulsante "Chiudi" nell'interfaccia)."""
    threading.Thread(target=lambda: (time.sleep(0.5), os._exit(0)), daemon=True).start()
    return {"ok": True}


# ---------- interfaccia (frontend React già compilato) ----------

if (config.FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=config.FRONTEND_DIST / "assets"), name="assets")


@app.get("/{full_path:path}")
def spa(full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(404, "Non trovato")
    target = (config.FRONTEND_DIST / full_path).resolve()
    if full_path and config.FRONTEND_DIST.resolve() in target.parents and target.is_file():
        return FileResponse(target)
    index = config.FRONTEND_DIST / "index.html"
    if not index.exists():
        return JSONResponse({"detail": "Interfaccia non trovata (frontend/dist mancante)"}, status_code=500)
    return FileResponse(index, headers={"Cache-Control": "no-cache"})


def run() -> None:
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="warning")


if __name__ == "__main__":
    run()

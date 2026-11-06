"""Marketing Platform: avvia con `python app.py` e apri http://127.0.0.1:8765"""

from __future__ import annotations

import threading
import webbrowser

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from platform_core import agent, buffer_api, config, library, plan, transcribe

app = FastAPI(title="Marketing Platform")
STATIC_DIR = config.BASE_DIR / "static"


def _fail(exc: Exception) -> HTTPException:
    if isinstance(exc, KeyError):
        return HTTPException(404, str(exc).strip("'\""))
    return HTTPException(400, str(exc))


@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/stato")
def stato():
    return config.status()


@app.get("/api/clip")
def clip_list():
    try:
        return library.scan()
    except Exception as exc:  # noqa: BLE001
        raise _fail(exc) from None


@app.get("/api/clip/{clip_id}/thumb")
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


@app.post("/api/chat/reset")
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


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    url = f"http://{config.HOST}:{config.PORT}"
    print(f"\n  Marketing Platform attiva su {url}\n  (chiudi con Ctrl+C)\n")
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host=config.HOST, port=config.PORT, log_level="warning")

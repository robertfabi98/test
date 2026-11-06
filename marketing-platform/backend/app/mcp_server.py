"""Server MCP della piattaforma: espone libreria, trascrizioni, analytics e piano a Claude Code.

Viene avviato da Claude Code (claude -p) a ogni messaggio della chat. Ogni azione fatta viene
annotata in un file, così l'interfaccia può mostrare cosa ha fatto Claude.
"""

from __future__ import annotations

import json
import os

from mcp.server.mcpserver import MCPServer
from pydantic import BaseModel, Field

from . import config, tools

server = MCPServer("piattaforma", instructions="Strumenti della Marketing Platform di Robert Fabi.")
_ACTIONS_DIR = config.DATA_DIR / "azioni"
_ACTIONS_DIR.mkdir(exist_ok=True)


def _run(name: str, args: dict) -> str:
    run_id = os.getenv("MP_RUN_ID", "")
    try:
        output, label = tools.run_tool(name, args)
    except Exception as exc:  # noqa: BLE001 - l'errore torna a Claude, che lo spiega
        output, label = f"Errore: {exc}", f"Errore in {name}: {exc}"
    if run_id.isalnum():
        with open(_ACTIONS_DIR / f"{run_id}.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({"label": label}, ensure_ascii=False) + "\n")
    return output


def _desc(name: str) -> str:
    return next(t["description"] for t in tools.TOOLS if t["name"] == name)


class PostProposto(BaseModel):
    canale_id: str = Field(description="id restituito da elenca_canali")
    testo: str = Field(description="Caption o descrizione completa")
    titolo: str = Field(default="", description="Titolo (obbligatorio per YouTube, altrimenti vuoto)")
    data_ora: str = Field(default="", description="Data e ora ISO specifica per questo canale, o vuoto")


@server.tool(description=_desc("elenca_clip"))
def elenca_clip(cerca: str = "") -> str:
    return _run("elenca_clip", {"cerca": cerca})


@server.tool(description=_desc("trascrivi_clip"))
def trascrivi_clip(clip_id: str) -> str:
    return _run("trascrivi_clip", {"clip_id": clip_id})


@server.tool(description=_desc("elenca_canali"))
def elenca_canali() -> str:
    return _run("elenca_canali", {})


@server.tool(description=_desc("leggi_piano"))
def leggi_piano() -> str:
    return _run("leggi_piano", {})


@server.tool(description=_desc("leggi_analytics"))
def leggi_analytics(canale_id: str, giorni: int = 30) -> str:
    return _run("leggi_analytics", {"canale_id": canale_id, "giorni": giorni})


@server.tool(description=_desc("proponi_programmazione"))
def proponi_programmazione(clip_id: str, data_ora: str, post: list[PostProposto], note: str = "") -> str:
    return _run(
        "proponi_programmazione",
        {"clip_id": clip_id, "data_ora": data_ora, "post": [p.model_dump() for p in post], "note": note},
    )


if __name__ == "__main__":
    server.run("stdio")

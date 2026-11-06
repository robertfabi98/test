"""La chat: Claude legge la libreria, trascrive le clip, scrive i testi e prepara il piano.

Claude non pubblica mai da solo: crea proposte che tu confermi con un clic nel pannello "Piano".
"""

from __future__ import annotations

import json
import threading
from datetime import datetime

import anthropic

from . import buffer_api, config, library, plan, transcribe

_STYLE_FILE = config.BASE_DIR / "brand" / "stile.md"

SYSTEM_PROMPT = """Sei il social media manager personale di Robert Fabi e lavori dentro la sua \
piattaforma di marketing. Robert è un consulente di marketing e personal branding per professionisti \
e piccole imprese; i suoi contenuti sono clip video brevi (reel, TikTok, YouTube Shorts).

Cosa fai:
- Trovi le clip nella libreria (elenca_clip) e, per capire cosa dice Robert, le trascrivi (trascrivi_clip).
- Scrivi titoli, descrizioni e hashtag partendo dalla trascrizione, nello stile descritto sotto.
- Prepari il piano di pubblicazione con proponi_programmazione. Le proposte NON vengono pubblicate: \
Robert le controlla e le conferma nel pannello "Piano". Diglielo quando ne crei una.

Regole per i testi:
- Instagram: prima riga = gancio che funziona anche da titolo, poi riga vuota, 2-4 frasi brevi, \
una call to action, 2-4 hashtag in fondo.
- TikTok: stesso messaggio, più asciutto, massimo 2-3 frasi più gli hashtag.
- YouTube: campo titolo obbligatorio (massimo 90 caratteri, niente clickbait); la descrizione \
riprende il testo di Instagram.
- Scrivi solo ciò che la clip dice davvero: non inventare dati, risultati o promesse.

Regole per il piano:
- Usa sempre date future, nel fuso orario Europe/Rome, in formato ISO (es. 2026-11-10T18:30:00+01:00). \
L'ora attuale è indicata all'inizio di ogni messaggio di Robert.
- Se Robert non indica giorno e ora, proponi tu un orario sensato e spiega perché in una riga.
- Prima di proporre, controlla il piano esistente (leggi_piano) per non sovrapporre due contenuti \
nello stesso giorno sullo stesso canale.
- Se una richiesta non è chiara (quale clip, quali canali), chiedi invece di indovinare.

Rispondi in italiano, in modo diretto e breve.
"""

TOOLS = [
    {
        "name": "elenca_clip",
        "description": "Elenca le clip (video e immagini) presenti nella cartella dei contenuti "
        "sull'hard disk, dalle più recenti. Restituisce id, nome, cartella, durata, formato e se "
        "esiste già una trascrizione.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "cerca": {
                    "type": "string",
                    "description": "Parte del nome o della cartella da cercare; stringa vuota per tutte.",
                }
            },
            "required": ["cerca"],
            "additionalProperties": False,
        },
    },
    {
        "name": "trascrivi_clip",
        "description": "Restituisce la trascrizione dell'audio di un video (la crea con Whisper se non "
        "esiste ancora; può richiedere qualche minuto per le clip lunghe).",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {"clip_id": {"type": "string"}},
            "required": ["clip_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "elenca_canali",
        "description": "Elenca i canali social collegati a Buffer (id, nome, servizio).",
        "strict": True,
        "input_schema": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
    },
    {
        "name": "leggi_piano",
        "description": "Legge il piano editoriale: proposte da confermare e post già programmati.",
        "strict": True,
        "input_schema": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
    },
    {
        "name": "proponi_programmazione",
        "description": "Crea una proposta di pubblicazione per una clip su uno o più canali. La proposta "
        "resta in attesa finché Robert non la conferma nel pannello Piano: non pubblica nulla.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "clip_id": {"type": "string"},
                "data_ora": {
                    "type": "string",
                    "description": "Data e ora ISO 8601 con fuso orario, usata per i post senza data_ora propria.",
                },
                "post": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "canale_id": {"type": "string", "description": "id restituito da elenca_canali"},
                            "testo": {"type": "string", "description": "Caption o descrizione completa"},
                            "titolo": {
                                "type": "string",
                                "description": "Titolo (obbligatorio per YouTube, altrimenti stringa vuota)",
                            },
                            "data_ora": {
                                "type": "string",
                                "description": "Data e ora specifica per questo canale, o stringa vuota",
                            },
                        },
                        "required": ["canale_id", "testo", "titolo", "data_ora"],
                        "additionalProperties": False,
                    },
                },
                "note": {"type": "string", "description": "Perché questa scelta di orario/canali (breve)"},
            },
            "required": ["clip_id", "data_ora", "post", "note"],
            "additionalProperties": False,
        },
    },
]


def _style() -> str:
    if _STYLE_FILE.exists():
        return _STYLE_FILE.read_text("utf-8")
    return ""


def _run_tool(name: str, args: dict) -> tuple[str, str]:
    """Esegue uno strumento. Restituisce (risultato per Claude, descrizione per l'interfaccia)."""
    if name == "elenca_clip":
        query = (args.get("cerca") or "").lower()
        clips = [
            {k: c[k] for k in ("id", "name", "folder", "kind", "duration", "width", "height", "transcribed")}
            for c in library.scan()
            if not query or query in c["rel_path"].lower()
        ]
        return json.dumps(clips[:60], ensure_ascii=False), f"Ho letto la libreria ({len(clips)} file)"
    if name == "trascrivi_clip":
        clip = library.get(args["clip_id"])
        result = transcribe.transcribe(args["clip_id"])
        return (
            json.dumps({"clip": clip["name"], "testo": result["text"]}, ensure_ascii=False),
            f"Ho trascritto «{clip['name']}»",
        )
    if name == "elenca_canali":
        return json.dumps(buffer_api.list_channels(), ensure_ascii=False), "Ho letto i canali"
    if name == "leggi_piano":
        items = [
            {
                "id": i["id"], "clip": i["clip_name"], "stato": i["status"],
                "post": [{"canale": p["channel_name"], "servizio": p["service"], "data_ora": p["due_at"]}
                         for p in i["posts"]],
            }
            for i in plan.list_items()
            if i["status"] != plan.STATUS_CANCELLED
        ]
        return json.dumps(items, ensure_ascii=False), "Ho controllato il piano"
    if name == "proponi_programmazione":
        item = plan.add_proposal(args["clip_id"], args["data_ora"], args["post"], args.get("note", ""))
        return (
            json.dumps({"proposta_id": item["id"], "stato": item["status"]}, ensure_ascii=False),
            f"Ho preparato una proposta per «{item['clip_name']}» (da confermare)",
        )
    raise ValueError(f"Strumento sconosciuto: {name}")


def _explain(exc: anthropic.APIError) -> str:
    if isinstance(exc, anthropic.AuthenticationError):
        return "Chiave ANTHROPIC_API_KEY non valida"
    if isinstance(exc, anthropic.RateLimitError):
        return "Troppe richieste a Claude, riprova tra un minuto"
    if isinstance(exc, anthropic.APIConnectionError):
        return "Claude non raggiungibile: controlla la connessione"
    if isinstance(exc, anthropic.APIStatusError) and exc.status_code >= 500:
        return "Claude è momentaneamente non disponibile, riprova tra poco"
    return f"Errore da Claude: {getattr(exc, 'message', exc)}"


class ChatSession:
    """Una conversazione con Claude. La cronologia resta in memoria finché non la azzeri."""

    MAX_STEPS = 20

    def __init__(self) -> None:
        self.messages: list[dict] = []
        self.transcript: list[dict] = []  # versione leggibile per l'interfaccia
        self._lock = threading.Lock()
        self._client: anthropic.Anthropic | None = None

    def _get_client(self) -> anthropic.Anthropic:
        if self._client is None:
            if not config.ANTHROPIC_API_KEY:
                raise RuntimeError("Manca ANTHROPIC_API_KEY nel file .env")
            self._client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY, base_url=config.CLAUDE_API_URL)
        return self._client

    def reset(self) -> None:
        with self._lock:
            self.messages = []
            self.transcript = []

    def _system(self) -> list[dict]:
        text = SYSTEM_PROMPT
        style = _style()
        if style:
            text += "\n\n# Stile di Robert\n\n" + style
        # testo stabile: viene messo in cache e costa meno dalla seconda richiesta
        return [{"type": "text", "text": text, "cache_control": {"type": "ephemeral"}}]

    def send(self, user_text: str) -> dict:
        with self._lock:
            client = self._get_client()
            now = datetime.now(config.TIMEZONE).strftime("%A %d/%m/%Y %H:%M (%z)")
            start = len(self.messages)
            self.messages.append({"role": "user", "content": f"[Ora attuale: {now}]\n{user_text}"})
            self.transcript.append({"role": "user", "text": user_text})

            actions: list[str] = []
            reply_parts: list[str] = []
            for _ in range(self.MAX_STEPS):
                try:
                    response = client.beta.messages.create(
                        model=config.CLAUDE_MODEL,
                        max_tokens=16000,
                        system=self._system(),
                        tools=TOOLS,
                        messages=self.messages,
                        thinking={"type": "adaptive"},
                        output_config={"effort": config.CLAUDE_EFFORT},
                        # se un modello rifiuta per errore, l'API riprova da sola con un altro modello
                        betas=["server-side-fallback-2026-07-01"],
                        fallbacks="default",
                    )
                except anthropic.APIError as exc:
                    # annulla tutto il turno, così la cronologia resta coerente
                    del self.messages[start:]
                    self.transcript.pop()
                    raise RuntimeError(_explain(exc)) from None

                self.messages.append({"role": "assistant", "content": response.content})
                reply_parts += [b.text for b in response.content if b.type == "text" and b.text.strip()]

                if response.stop_reason == "refusal":
                    reply_parts.append("(Claude non ha completato questa richiesta.)")
                    break
                if response.stop_reason == "pause_turn":
                    continue
                if response.stop_reason != "tool_use":
                    if response.stop_reason == "max_tokens":
                        reply_parts.append("(Risposta interrotta perché troppo lunga.)")
                    break

                results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    try:
                        output, label = _run_tool(block.name, dict(block.input))
                        actions.append(label)
                        results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
                    except Exception as exc:  # noqa: BLE001 - l'errore torna a Claude, che lo spiega
                        actions.append(f"Errore in {block.name}: {exc}")
                        results.append(
                            {"type": "tool_result", "tool_use_id": block.id, "content": str(exc), "is_error": True}
                        )
                # tutti i risultati in un unico messaggio
                self.messages.append({"role": "user", "content": results})
            else:
                reply_parts.append("(Mi sono fermato: troppi passaggi in una sola richiesta.)")

            reply = "\n\n".join(reply_parts).strip() or "Fatto."
            self.transcript.append({"role": "assistant", "text": reply, "actions": actions})
            return {"reply": reply, "actions": actions}


session = ChatSession()

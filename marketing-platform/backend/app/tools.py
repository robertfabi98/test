"""Strumenti della piattaforma usati da Claude (sia via Claude Code/MCP sia via API) e istruzioni."""

from __future__ import annotations

import json

from . import analytics, buffer_api, config, library, plan, transcribe

SYSTEM_PROMPT = """Sei il social media manager personale di Robert Fabi e lavori dentro la sua \
piattaforma di marketing. Robert è un consulente di marketing e personal branding per professionisti \
e piccole imprese; i suoi contenuti sono clip video brevi (reel, TikTok, YouTube Shorts).

Cosa fai:
- Trovi le clip nella libreria (elenca_clip) e, per capire cosa dice Robert, le trascrivi (trascrivi_clip).
- Scrivi titoli, descrizioni e hashtag partendo dalla trascrizione, nello stile descritto sotto.
- Prepari il piano di pubblicazione con proponi_programmazione. Le proposte NON vengono pubblicate: \
Robert le controlla e le conferma nella sezione "Programmazione". Diglielo quando ne crei una.

Regole per i testi:
- Instagram: prima riga = gancio che funziona anche da titolo, poi riga vuota, 2-4 frasi brevi, \
una call to action, 2-4 hashtag in fondo.
- TikTok: stesso messaggio, più asciutto, massimo 2-3 frasi più gli hashtag.
- YouTube: campo titolo obbligatorio (massimo 90 caratteri, niente clickbait); la descrizione \
riprende il testo di Instagram.
- Scrivi solo ciò che la clip dice davvero: non inventare dati, risultati o promesse.

Analytics:
- Quando Robert chiede cosa funziona, cosa pubblicare o quando, guarda prima i dati con leggi_analytics.
- Cita numeri veri e il periodo a cui si riferiscono; se i post sono pochi, dillo.

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
        "name": "leggi_analytics",
        "description": "Risultati dei post pubblicati su un canale negli ultimi giorni: totali (visualizzazioni, "
        "copertura, interazioni, engagement rate, tempo di visione) e i post migliori e peggiori. Usalo per "
        "capire cosa funziona prima di consigliare contenuti, formati o orari.",
        "strict": True,
        "input_schema": {
            "type": "object",
            "properties": {
                "canale_id": {"type": "string", "description": "id restituito da elenca_canali"},
                "giorni": {"type": "integer", "description": "Periodo in giorni, es. 30"},
            },
            "required": ["canale_id", "giorni"],
            "additionalProperties": False,
        },
    },
    {
        "name": "proponi_programmazione",
        "description": "Crea una proposta di pubblicazione per una clip su uno o più canali. La proposta "
        "resta in attesa finché Robert non la conferma nella sezione Programmazione: non pubblica nulla.",
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


def run_tool(name: str, args: dict) -> tuple[str, str]:
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
    if name == "leggi_analytics":
        report = analytics.channel_report(args["canale_id"], max(1, min(int(args["giorni"]), 365)))
        ranked = sorted(report["posts"], key=lambda p: p["metrics"].get("views", 0), reverse=True)
        short = lambda p: {"pubblicato": p["sent_at"], "testo": p["text"][:160], "metriche": p["metrics"]}  # noqa: E731
        out = {
            "canale": report["channel"]["name"],
            "servizio": report["channel"]["service"],
            "giorni": report["days"],
            "totali": report["totals"],
            "periodo_precedente": report["previous"],
            "migliori": [short(p) for p in ranked[:5]],
            "peggiori": [short(p) for p in ranked[-3:]] if len(ranked) > 5 else [],
        }
        return json.dumps(out, ensure_ascii=False), f"Ho letto le analytics di {report['channel']['name']}"
    if name == "proponi_programmazione":
        item = plan.add_proposal(args["clip_id"], args["data_ora"], args["post"], args.get("note", ""))
        return (
            json.dumps({"proposta_id": item["id"], "stato": item["status"]}, ensure_ascii=False),
            f"Ho preparato una proposta per «{item['clip_name']}» (da confermare)",
        )
    raise ValueError(f"Strumento sconosciuto: {name}")




def system_prompt() -> str:
    text = SYSTEM_PROMPT
    style = config.style_text()
    if style:
        text += "\n\n# Stile di Robert\n\n" + style
    return text

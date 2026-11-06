"""La chat: Claude legge la libreria, trascrive le clip, scrive i testi e prepara il piano.

Claude non pubblica mai da solo: crea proposte che tu confermi con un clic nella sezione "Programmazione".
"""

from __future__ import annotations

import json
import threading
from datetime import datetime

import anthropic

from . import claude_code, config, tools

def _explain(exc: anthropic.APIError) -> str:
    if isinstance(exc, anthropic.AuthenticationError):
        return "La chiave di Claude non è valida: controllala nelle Impostazioni"
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
        self._client_key = ""
        self._cc_session: str | None = None  # sessione di Claude Code (per continuare la conversazione)

    def _get_client(self) -> anthropic.Anthropic:
        key = config.ANTHROPIC_API_KEY
        if not key:
            raise RuntimeError("Inserisci la chiave di Claude nelle Impostazioni")
        if self._client is None or self._client_key != key:
            self._client = anthropic.Anthropic(api_key=key, base_url=config.CLAUDE_API_URL)
            self._client_key = key
        return self._client

    def reset(self) -> None:
        with self._lock:
            self.messages = []
            self.transcript = []
            self._cc_session = None

    def _system(self) -> list[dict]:
        # testo stabile: viene messo in cache e costa meno dalla seconda richiesta
        return [{"type": "text", "text": tools.system_prompt(), "cache_control": {"type": "ephemeral"}}]

    def send(self, user_text: str) -> dict:
        if config.get("claude_engine") == "api":
            return self._send_api(user_text)
        return self._send_claude_code(user_text)

    def _send_claude_code(self, user_text: str) -> dict:
        with self._lock:
            now = datetime.now(config.TIMEZONE).strftime("%A %d/%m/%Y %H:%M (%z)")
            self.transcript.append({"role": "user", "text": user_text})
            try:
                reply, session_id, actions = claude_code.ask(
                    f"[Ora attuale: {now}]\n{user_text}", self._cc_session
                )
            except Exception:
                self.transcript.pop()
                raise
            self._cc_session = session_id or self._cc_session
            reply = reply or "Fatto."
            self.transcript.append({"role": "assistant", "text": reply, "actions": actions})
            return {"reply": reply, "actions": actions}

    def _send_api(self, user_text: str) -> dict:
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
                        tools=tools.TOOLS,
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
                        output, label = tools.run_tool(block.name, dict(block.input))
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

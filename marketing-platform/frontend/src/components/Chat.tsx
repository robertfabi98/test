import { useEffect, useRef, useState } from "react";
import { api, type ChatEntry } from "../api";

function Bubble({ entry }: { entry: ChatEntry & { error?: boolean } }) {
  // grassetto **così** come in chat
  const parts = entry.text.split(/(\*\*[^*]+\*\*)/g);
  return (
    <div className={`msg ${entry.role} ${entry.error ? "error" : ""}`}>
      {parts.map((p, i) =>
        p.startsWith("**") && p.endsWith("**") ? <strong key={i}>{p.slice(2, -2)}</strong> : <span key={i}>{p}</span>,
      )}
      {entry.actions && entry.actions.length > 0 && (
        <div className="actions">
          {entry.actions.map((a, i) => (
            <span key={i}>• {a}</span>
          ))}
        </div>
      )}
    </div>
  );
}

export default function Chat({
  draft,
  onDraftUsed,
  claudeReady,
  goToSettings,
  onWork,
}: {
  draft: string;
  onDraftUsed: () => void;
  claudeReady: boolean;
  goToSettings: () => void;
  onWork: (actions: string[]) => void;
}) {
  const [messages, setMessages] = useState<(ChatEntry & { error?: boolean })[]>([]);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const listRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    api.chatHistory().then(setMessages).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (draft) {
      setText(draft);
      onDraftUsed();
      inputRef.current?.focus();
    }
  }, [draft, onDraftUsed]);

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages, busy]);

  const send = async () => {
    const message = text.trim();
    if (!message || busy) return;
    setText("");
    setBusy(true);
    setMessages((m) => [...m, { role: "user", text: message }]);
    try {
      const res = await api.chat(message);
      setMessages((m) => [...m, { role: "assistant", text: res.reply, actions: res.actions }]);
      onWork(res.actions);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", text: (e as Error).message, error: true }]);
    } finally {
      setBusy(false);
    }
  };

  const reset = async () => {
    await api.newChat();
    setMessages([]);
  };

  return (
    <section className="panel">
      <div className="panel-head">
        <h2>Chat con Claude</h2>
        <button className="ghost small" onClick={reset} disabled={busy}>
          Nuova chat
        </button>
      </div>
      <div className="messages" ref={listRef}>
        {!claudeReady && (
          <div className="notice">
            Claude non è ancora collegato.{" "}
            <button className="link" onClick={goToSettings}>
              Inserisci la chiave nelle Impostazioni
            </button>
          </div>
        )}
        {messages.length === 0 && (
          <div className="msg assistant intro">
            Ciao Robert. Scegli una clip dalla libreria oppure scrivimi cosa vuoi fare, per esempio:{" "}
            <em>«Prendi le ultime 3 clip della cartella Reel novembre e distribuiscile la prossima settimana su Instagram e TikTok»</em>.
            Preparo le proposte, tu le confermi nel Piano.
          </div>
        )}
        {messages.map((m, i) => (
          <Bubble key={i} entry={m} />
        ))}
        {busy && <div className="msg assistant thinking">Sto lavorando…</div>}
      </div>
      <form
        className="chat-form"
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
      >
        <textarea
          ref={inputRef}
          rows={3}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              send();
            }
          }}
          placeholder="Scrivi a Claude… (Invio per inviare, Maiusc+Invio per andare a capo)"
        />
        <button type="submit" disabled={busy || !text.trim()}>
          Invia
        </button>
      </form>
    </section>
  );
}

import { useCallback, useEffect, useRef, useState } from "react";
import { linksApi, type BufferLink, type ClaudeCodeStatus } from "../api";

// Claude tramite Claude Code: usa l'abbonamento Claude, nessuna chiave.
export function ConnectClaude({ onChange }: { onChange?: () => void }) {
  const [st, setSt] = useState<ClaudeCodeStatus | null>(null);
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const timer = useRef<number>();

  const load = useCallback(async (verify = false) => {
    try {
      const s = await linksApi.claudeCode(verify);
      setSt(s);
      setError("");
      return s;
    } catch (e) {
      setError((e as Error).message);
      return null;
    }
  }, []);

  useEffect(() => {
    load();
    return () => window.clearInterval(timer.current);
  }, [load]);

  const run = async (label: string, fn: () => Promise<unknown>) => {
    setBusy(label);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy("");
      onChange?.();
    }
  };

  const install = () =>
    run("Installo Claude Code…", async () => {
      await linksApi.installClaudeCode();
      // aspetto la fine dell'installazione
      await new Promise<void>((resolve) => {
        timer.current = window.setInterval(async () => {
          const s = await load();
          if (s && !s.installing) {
            window.clearInterval(timer.current);
            resolve();
          }
        }, 3000);
      });
    });

  const verify = () => run("Verifico…", () => load(true));

  let state: [string, string];
  if (!st) state = ["Controllo…", ""];
  else if (!st.installed) state = ["Da installare", "no"];
  else if (st.logged_in === true) state = ["Collegato", "ok"];
  else if (st.logged_in === false) state = ["Accesso da fare", "no"];
  else state = ["Installato", "warn"];

  return (
    <div className="connect">
      <div className="connect-head">
        <div>
          <strong>Claude</strong> <span className="muted">· tramite Claude Code, con il tuo abbonamento</span>
        </div>
        <span className={`pill ${state[1]}`}>{state[0]}</span>
      </div>
      <p className="muted small">
        Nessuna chiave API e nessun costo extra: la chat usa Claude Code con il tuo account Claude (lo stesso che usi in
        VS Code). L'uso conta nei limiti del tuo abbonamento.
      </p>
      {st?.error && <div className="notice small">{st.error}</div>}
      {error && <div className="notice small">{error}</div>}
      <div className="row wrap">
        {st && !st.installed && (
          <button disabled={!!busy || st.installing} onClick={install}>
            {busy || (st.installing ? "Installo…" : "Installa Claude Code")}
          </button>
        )}
        {st?.installed && st.logged_in !== true && (
          <button disabled={!!busy} onClick={() => run("Apro il Terminale…", linksApi.loginClaudeCode)}>
            Accedi a Claude
          </button>
        )}
        {st?.installed && (
          <button className="ghost" disabled={!!busy} onClick={verify}>
            {busy === "Verifico…" ? busy : "Verifica collegamento"}
          </button>
        )}
      </div>
      {st?.installed && st.logged_in !== true && (
        <p className="muted small">
          «Accedi a Claude» apre il Terminale con Claude Code: alla prima apertura ti chiede di accedere con il tuo account
          (si apre il browser). Quando vedi il messaggio di benvenuto chiudi il Terminale e premi «Verifica collegamento».
          Se usi già Claude Code in VS Code, probabilmente l'accesso è già fatto: prova prima «Verifica».
        </p>
      )}
    </div>
  );
}

// Buffer tramite il server MCP ufficiale: accesso dal browser, nessuna chiave.
export function ConnectBuffer({ onChange }: { onChange?: () => void }) {
  const [st, setSt] = useState<BufferLink | null>(null);
  const [error, setError] = useState("");
  const timer = useRef<number>();

  const load = useCallback(async () => {
    try {
      const s = await linksApi.buffer();
      setSt(s);
      return s;
    } catch (e) {
      setError((e as Error).message);
      return null;
    }
  }, []);

  useEffect(() => {
    load();
    return () => window.clearInterval(timer.current);
  }, [load]);

  const connect = async () => {
    setError("");
    try {
      setSt(await linksApi.connectBuffer());
      window.clearInterval(timer.current);
      timer.current = window.setInterval(async () => {
        const s = await load();
        if (s && s.state !== "in_attesa") {
          window.clearInterval(timer.current);
          onChange?.();
        }
      }, 2000);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const disconnect = async () => {
    if (!confirm("Scollegare Buffer dalla piattaforma?")) return;
    setSt(await linksApi.disconnectBuffer().then(() => linksApi.buffer()));
    onChange?.();
  };

  const linked = st?.mode === "mcp";
  const state: [string, string] = !st
    ? ["Controllo…", ""]
    : linked
      ? ["Collegato", "ok"]
      : st.mode === "api"
        ? ["Collegato con chiave", "ok"]
        : st.state === "in_attesa"
          ? ["In attesa dell'accesso", "warn"]
          : ["Da collegare", "no"];

  return (
    <div className="connect">
      <div className="connect-head">
        <div>
          <strong>Buffer</strong> <span className="muted">· tramite il server MCP ufficiale</span>
        </div>
        <span className={`pill ${state[1]}`}>{state[0]}</span>
      </div>
      <p className="muted small">
        Nessuna chiave: accedi a Buffer nel browser e approvi l'accesso. Servono per analytics, calendario e
        programmazione dei post.
      </p>
      {st?.state === "errore" && st.error && <div className="notice small">{st.error}</div>}
      {error && <div className="notice small">{error}</div>}
      {st?.state === "in_attesa" && (
        <div className="notice small">
          Si è aperta la pagina di Buffer nel browser: accedi e approva. Se non la vedi,{" "}
          {st.url ? (
            <a href={st.url} target="_blank" rel="noreferrer">
              aprila da qui
            </a>
          ) : (
            "attendi qualche secondo"
          )}
          .
        </div>
      )}
      <div className="row wrap">
        {!linked && (
          <button disabled={st?.state === "in_attesa"} onClick={connect}>
            {st?.state === "in_attesa" ? "In attesa…" : "Accedi con Buffer"}
          </button>
        )}
        {linked && (
          <button className="ghost" onClick={disconnect}>
            Scollega
          </button>
        )}
      </div>
    </div>
  );
}

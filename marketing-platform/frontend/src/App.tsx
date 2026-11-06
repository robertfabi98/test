import { useCallback, useEffect, useState } from "react";
import { api, type Status } from "./api";
import Setup from "./pages/Setup";
import Workspace from "./pages/Workspace";
import SettingsPage from "./pages/SettingsPage";
import StylePage from "./pages/StylePage";

type Page = "lavoro" | "stile" | "impostazioni";

export default function App() {
  const [status, setStatus] = useState<Status | null>(null);
  const [error, setError] = useState("");
  const [page, setPage] = useState<Page>("lavoro");
  const [setupDone, setSetupDone] = useState(() => localStorage.getItem("mp-setup") === "ok");
  const [closed, setClosed] = useState(false);

  const refresh = useCallback(async () => {
    try {
      setStatus(await api.status());
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  if (closed) {
    return (
      <div className="center-screen">
        <div className="card narrow">
          <h1>Marketing Platform chiusa</h1>
          <p className="muted">Per riaprirla fai doppio clic sull'app Marketing Platform.</p>
        </div>
      </div>
    );
  }

  if (!status) {
    return (
      <div className="center-screen">
        <p className="muted">{error ? `Non riesco a contattare la piattaforma: ${error}` : "Avvio…"}</p>
      </div>
    );
  }

  if (!setupDone && !status.media_dir) {
    return (
      <Setup
        onDone={() => {
          localStorage.setItem("mp-setup", "ok");
          setSetupDone(true);
          refresh();
        }}
      />
    );
  }

  const close = async () => {
    if (!confirm("Chiudere la Marketing Platform?")) return;
    try {
      await api.shutdown();
    } finally {
      setClosed(true);
    }
  };

  const pills: [string, boolean][] = [
    ["Hard disk", status.media_dir_ok],
    ["Claude", status.claude],
    ["Buffer", status.buffer],
    ["Cloudinary", status.cloudinary],
    ["Trascrizione", status.whisper],
  ];

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">Marketing Platform</div>
        <nav className="tabs">
          {(
            [
              ["lavoro", "Lavoro"],
              ["stile", "Il mio stile"],
              ["impostazioni", "Impostazioni"],
            ] as [Page, string][]
          ).map(([key, label]) => (
            <button key={key} className={`tab ${page === key ? "active" : ""}`} onClick={() => setPage(key)}>
              {label}
            </button>
          ))}
        </nav>
        <div className="status">
          {pills.map(([label, ok]) => (
            <span key={label} className={`pill ${ok ? "ok" : "no"}`} title={ok ? "Collegato" : "Da configurare"}>
              {label}
            </span>
          ))}
          {status.dry_run ? (
            <span className="pill warn" title="Le conferme non inviano niente a Buffer">
              Modalità prova
            </span>
          ) : (
            <span className="pill ok">Pubblicazione attiva</span>
          )}
          <button className="ghost small" onClick={close} title="Chiudi la piattaforma">
            Chiudi
          </button>
        </div>
      </header>

      {page === "lavoro" && <Workspace status={status} goToSettings={() => setPage("impostazioni")} />}
      {page === "stile" && <StylePage />}
      {page === "impostazioni" && <SettingsPage onSaved={refresh} />}
    </div>
  );
}

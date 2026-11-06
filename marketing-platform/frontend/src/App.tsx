import { useCallback, useEffect, useState } from "react";
import { api, APP_VERSION, type Status } from "./api";
import Setup from "./pages/Setup";
import AnalyticsPage from "./pages/AnalyticsPage";
import SchedulePage from "./pages/SchedulePage";
import CreatePage from "./pages/CreatePage";
import SettingsPage from "./pages/SettingsPage";

type Section = "analytics" | "programmazione" | "creazione" | "impostazioni";

const NAV: { key: Section; label: string; hint: string; icon: JSX.Element }[] = [
  {
    key: "analytics",
    label: "Analytics",
    hint: "Risultati per piattaforma",
    icon: (
      <svg viewBox="0 0 20 20" aria-hidden="true">
        <path d="M3 17V9M8 17V4M13 17v-6M18 17V7" />
      </svg>
    ),
  },
  {
    key: "programmazione",
    label: "Programmazione",
    hint: "Calendario e gestione",
    icon: (
      <svg viewBox="0 0 20 20" aria-hidden="true">
        <rect x="2.5" y="4" width="15" height="13" rx="2" />
        <path d="M2.5 8h15M6.5 2v4M13.5 2v4" />
      </svg>
    ),
  },
  {
    key: "creazione",
    label: "Creazione",
    hint: "Libreria e chat con Claude",
    icon: (
      <svg viewBox="0 0 20 20" aria-hidden="true">
        <path d="M10 2.5l1.8 4.7 4.7 1.8-4.7 1.8L10 15.5l-1.8-4.7L3.5 9l4.7-1.8z" />
        <path d="M16 14l.7 1.8 1.8.7-1.8.7L16 19l-.7-1.8-1.8-.7 1.8-.7z" />
      </svg>
    ),
  },
  {
    key: "impostazioni",
    label: "Impostazioni",
    hint: "Collegamenti, cartella, stile",
    icon: (
      <svg viewBox="0 0 20 20" aria-hidden="true">
        <circle cx="10" cy="10" r="2.8" />
        <path d="M10 1.8v2.4M10 15.8v2.4M1.8 10h2.4M15.8 10h2.4M4.2 4.2l1.7 1.7M14.1 14.1l1.7 1.7M4.2 15.8l1.7-1.7M14.1 5.9l1.7-1.7" />
      </svg>
    ),
  },
];

export default function App() {
  const [status, setStatus] = useState<Status | null>(null);
  const [error, setError] = useState("");
  const [section, setSection] = useState<Section>(
    () => (localStorage.getItem("mp-section") as Section | null) ?? "creazione",
  );
  const [setupDone, setSetupDone] = useState(() => localStorage.getItem("mp-setup") === "ok");
  const [closed, setClosed] = useState(false);
  const [draft, setDraft] = useState("");
  const [oldEngine, setOldEngine] = useState(false);

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
    // dopo un aggiornamento il motore vecchio può essere ancora acceso: va riavviato
    api
      .ping()
      .then((p) => setOldEngine(p.version !== APP_VERSION))
      .catch(() => undefined);
  }, [refresh]);

  const go = (s: Section) => {
    setSection(s);
    try {
      localStorage.setItem("mp-section", s);
    } catch {
      /* non importante */
    }
  };

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

  if (oldEngine) {
    return (
      <div className="center-screen">
        <div className="card narrow">
          <h1>Aggiornamento da completare</h1>
          <p>
            Hai scaricato una nuova versione, ma è ancora acceso il motore di quella vecchia. Chiudi la piattaforma e
            riaprila con doppio clic sull'app: la prima volta ci mette circa un minuto.
          </p>
          <button
            onClick={async () => {
              try {
                await api.shutdown();
              } finally {
                setOldEngine(false);
                setClosed(true);
              }
            }}
          >
            Chiudi ora
          </button>
        </div>
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

  const links: [string, boolean][] = [
    ["Hard disk", status.media_dir_ok],
    ["Claude", status.claude],
    ["Buffer", status.buffer],
    ["Cloudinary", status.cloudinary],
  ];
  const missing = links.filter(([, ok]) => !ok).map(([l]) => l);

  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          Marketing Platform
        </div>
        <nav className="nav">
          {NAV.map((n) => (
            <button key={n.key} className={`nav-item ${section === n.key ? "active" : ""}`} onClick={() => go(n.key)}>
              {n.icon}
              <span>
                <span className="nav-label">{n.label}</span>
                <span className="nav-hint">{n.hint}</span>
              </span>
            </button>
          ))}
        </nav>
        <div className="sidebar-foot">
          {status.dry_run ? (
            <button className="mode warn" onClick={() => go("impostazioni")} title="Le conferme non inviano niente a Buffer">
              ● Modalità prova
            </button>
          ) : (
            <span className="mode ok">● Pubblicazione attiva</span>
          )}
          <div className="links">
            {links.map(([label, ok]) => (
              <span key={label} className="link-status">
                <span className={`dot ${ok ? "ok" : "no"}`} />
                {label}
              </span>
            ))}
          </div>
          {missing.length > 0 && (
            <button className="link small" onClick={() => go("impostazioni")}>
              Completa i collegamenti
            </button>
          )}
          <button className="ghost small" onClick={close}>
            Chiudi l'app
          </button>
        </div>
      </aside>

      <div className="content">
        {section === "analytics" && (
          <AnalyticsPage
            buffer={status.buffer}
            goToSettings={() => go("impostazioni")}
            askClaude={(prompt) => {
              setDraft(prompt);
              go("creazione");
            }}
          />
        )}
        {section === "programmazione" && <SchedulePage dryRun={status.dry_run} goToCreate={() => go("creazione")} />}
        {section === "creazione" && (
          <CreatePage
            status={status}
            draft={draft}
            setDraft={setDraft}
            goToSettings={() => go("impostazioni")}
            goToSchedule={() => go("programmazione")}
          />
        )}
        {section === "impostazioni" && <SettingsPage onSaved={refresh} status={status} />}
      </div>
    </div>
  );
}

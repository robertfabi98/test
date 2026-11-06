import { useCallback, useEffect, useState } from "react";
import { analyticsApi, api, fmtDate, SERVICE_LABEL, type CalendarEntry, type PlanItem } from "../api";
import WeekCalendar from "../components/WeekCalendar";
import { PendingCard } from "../components/Plan";

// Programmazione e gestione: calendario + proposte da confermare + post in arrivo.
export default function SchedulePage({ dryRun, goToCreate }: { dryRun: boolean; goToCreate: () => void }) {
  const [entries, setEntries] = useState<CalendarEntry[]>([]);
  const [bufferError, setBufferError] = useState<string | null>(null);
  const [items, setItems] = useState<PlanItem[]>([]);
  const [weekStart, setWeekStart] = useState(new Date());
  const [focus, setFocus] = useState<string | null>(null);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      const [cal, plan] = await Promise.all([analyticsApi.calendar(), api.plan()]);
      setEntries(cal.entries);
      setBufferError(cal.buffer_error);
      setItems(plan);
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const pending = items.filter((i) => ["da_confermare", "parziale", "errore", "simulato"].includes(i.status));
  const now = Date.now();
  const upcoming = entries.filter(
    (e) => new Date(e.due_at).getTime() >= now && (e.status === "programmato" || e.status === "in_coda_buffer"),
  );

  const open = (e: CalendarEntry) => {
    setWeekStart(new Date(e.due_at));
    if (e.item_id) {
      setFocus(e.item_id);
      setTimeout(() => document.getElementById(`item-${e.item_id}`)?.scrollIntoView({ behavior: "smooth", block: "center" }), 50);
    }
  };

  return (
    <div className="page">
      <div className="page-inner xwide">
        <div className="page-head">
          <h1>Programmazione</h1>
          <div className="row">
            <button className="ghost" onClick={load}>
              ↻ Aggiorna
            </button>
            <button onClick={goToCreate}>+ Crea un contenuto</button>
          </div>
        </div>
        {error && <div className="notice">{error}</div>}
        {bufferError && <div className="notice small">Non riesco a leggere la coda di Buffer: {bufferError}</div>}

        <section className="card">
          <WeekCalendar entries={entries} weekStart={weekStart} setWeekStart={setWeekStart} onOpen={open} />
        </section>

        <div className="schedule-cols">
          <section>
            <h2 className="section-title">
              Da confermare <span className="count">{pending.length}</span>
            </h2>
            {pending.length === 0 ? (
              <div className="card empty">
                Nessuna proposta in attesa.{" "}
                <button className="link" onClick={goToCreate}>
                  Chiedi a Claude di prepararne una
                </button>
              </div>
            ) : (
              <div className="stack">
                {pending.map((i) => (
                  <div key={i.id} id={`item-${i.id}`} className={focus === i.id ? "focus-ring" : ""}>
                    <PendingCard item={i} dryRun={dryRun} onChanged={load} />
                  </div>
                ))}
              </div>
            )}
          </section>

          <section>
            <h2 className="section-title">
              In arrivo <span className="count">{upcoming.length}</span>
            </h2>
            <div className="card">
              {upcoming.length === 0 ? (
                <div className="empty">Nessun post programmato.</div>
              ) : (
                <ul className="upcoming">
                  {upcoming.map((e, i) => (
                    <li key={i}>
                      <span className={`dot ch-${e.service}`} />
                      <span className="upcoming-main">
                        <strong>{e.title}</strong>
                        <span className="muted small">
                          {SERVICE_LABEL[e.service] ?? e.service} · {fmtDate(e.due_at)}
                          {e.source === "buffer" ? " · da Buffer" : ""}
                        </span>
                      </span>
                    </li>
                  ))}
                </ul>
              )}
              <a className="small" href="https://publish.buffer.com" target="_blank" rel="noreferrer">
                Apri Buffer per modificare o eliminare i post già in coda →
              </a>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}

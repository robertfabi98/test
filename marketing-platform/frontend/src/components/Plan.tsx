import { useCallback, useEffect, useState } from "react";
import { api, fmtDate, toLocalInput, type PlanItem, type PlanPost } from "../api";

const STATUS: Record<PlanItem["status"], [string, string]> = {
  da_confermare: ["Da confermare", "warn"],
  programmato: ["Programmato su Buffer", "ok"],
  simulato: ["Prova (non inviato)", "warn"],
  parziale: ["Programmato in parte", "no"],
  errore: ["Errore", "no"],
  annullato: ["Annullato", ""],
};

type Edit = { channel_id: string; text: string; title: string; due_at: string };

function toEdits(item: PlanItem): Edit[] {
  return item.posts.map((p) => ({ channel_id: p.channel_id, text: p.text, title: p.title, due_at: toLocalInput(p.due_at) }));
}

function editsForApi(edits: Edit[]) {
  // datetime-local è nell'ora del Mac: lo converto in ISO con fuso
  return edits.map((e) => ({ ...e, due_at: e.due_at ? new Date(e.due_at).toISOString() : "" }));
}

function PendingCard({ item, dryRun, onChanged }: { item: PlanItem; dryRun: boolean; onChanged: () => void }) {
  const [edits, setEdits] = useState<Edit[]>(() => toEdits(item));
  const [busy, setBusy] = useState("");
  const [error, setError] = useState("");
  const editable = item.status === "da_confermare";
  const dirty = JSON.stringify(edits) !== JSON.stringify(toEdits(item));

  useEffect(() => setEdits(toEdits(item)), [item]);

  const run = async (label: string, fn: () => Promise<unknown>) => {
    setBusy(label);
    setError("");
    try {
      await fn();
      onChanged();
    } catch (e) {
      setError((e as Error).message);
      onChanged();
    } finally {
      setBusy("");
    }
  };

  const confirmItem = () =>
    run("Carico e programmo…", async () => {
      if (editable && dirty) await api.updatePlan(item.id, editsForApi(edits));
      const res = await api.confirmPlan(item.id);
      if (res.status === "simulato") {
        alert("Modalità prova: niente è stato inviato a Buffer. Quando sei pronto, attiva “Pubblica davvero” nelle Impostazioni.");
      }
    });

  const set = (i: number, patch: Partial<Edit>) => setEdits((all) => all.map((e, j) => (j === i ? { ...e, ...patch } : e)));
  const [label, cls] = STATUS[item.status];

  return (
    <div className="plan-card">
      <div className="plan-head">
        <div className="plan-title">{item.clip_name}</div>
        <span className={`pill ${cls}`}>{label}</span>
      </div>
      {item.note && <div className="muted small">{item.note}</div>}
      {item.posts.map((p: PlanPost, i) => (
        <div className="post" key={p.channel_id}>
          <div className="row spread">
            <span className="service">
              {p.service} · {p.channel_name}
            </span>
            {p.buffer_post_id && <span className="pill ok">programmato</span>}
          </div>
          <input
            type="datetime-local"
            value={edits[i]?.due_at ?? ""}
            disabled={!editable}
            onChange={(e) => set(i, { due_at: e.target.value })}
          />
          {p.service === "youtube" && (
            <input
              placeholder="Titolo"
              value={edits[i]?.title ?? ""}
              disabled={!editable}
              onChange={(e) => set(i, { title: e.target.value })}
            />
          )}
          <textarea
            rows={5}
            value={edits[i]?.text ?? ""}
            disabled={!editable}
            onChange={(e) => set(i, { text: e.target.value })}
          />
          {p.error && <div className="err">{p.error}</div>}
        </div>
      ))}
      {error && <div className="notice small">{error}</div>}
      <div className="row wrap">
        {item.status === "simulato" && dryRun ? (
          <span className="muted small">Provato in modalità prova. Attiva “Pubblica davvero” nelle Impostazioni per programmarlo.</span>
        ) : (
          <button disabled={!!busy} onClick={confirmItem}>
            {busy || ({ da_confermare: "Conferma e programma", simulato: "Programma davvero" } as Record<string, string>)[item.status] || "Riprova"}
          </button>
        )}
        {editable && (
          <button className="ghost" disabled={!dirty || !!busy} onClick={() => run("Salvo…", () => api.updatePlan(item.id, editsForApi(edits)))}>
            Salva modifiche
          </button>
        )}
        {editable && (
          <button
            className="danger"
            disabled={!!busy}
            onClick={() => confirm("Annullare questa proposta?") && run("Annullo…", () => api.cancelPlan(item.id))}
          >
            Annulla
          </button>
        )}
      </div>
    </div>
  );
}

export default function Plan({ version, dryRun }: { version: number; dryRun: boolean }) {
  const [items, setItems] = useState<PlanItem[]>([]);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    try {
      setItems(await api.plan());
      setError("");
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, version]);

  const pending = items.filter((i) => ["da_confermare", "parziale", "errore", "simulato"].includes(i.status));
  const done = items.filter((i) => i.status === "programmato").reverse();

  return (
    <section className="panel">
      <div className="panel-head">
        <h2>Piano</h2>
        <button className="ghost icon" onClick={load} title="Aggiorna">
          ↻
        </button>
      </div>
      <div className="panel-body plan">
        {error && <div className="notice">{error}</div>}
        <h3>Da confermare</h3>
        {pending.length ? (
          pending.map((i) => <PendingCard key={i.id} item={i} dryRun={dryRun} onChanged={load} />)
        ) : (
          <div className="empty">Nessuna proposta in attesa. Chiedi a Claude di prepararne una.</div>
        )}
        <h3>Programmati</h3>
        {done.length ? (
          done.map((item) => (
            <div className="plan-card" key={item.id}>
              <div className="plan-head">
                <div className="plan-title">{item.clip_name}</div>
                <span className="pill ok">Programmato</span>
              </div>
              {item.posts.map((p) => (
                <div className="post" key={p.channel_id}>
                  <span className="service">
                    {p.service} · {fmtDate(p.due_at)}
                  </span>
                  {p.title && <strong>{p.title}</strong>}
                  <div className="post-text">{p.text}</div>
                </div>
              ))}
            </div>
          ))
        ) : (
          <div className="empty">Ancora niente.</div>
        )}
      </div>
    </section>
  );
}

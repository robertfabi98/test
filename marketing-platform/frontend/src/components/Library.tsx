import { useEffect, useMemo, useState } from "react";
import { api, fmtDuration, type Clip } from "../api";

export default function Library({
  clips,
  loading,
  error,
  onRefresh,
  onClipsChanged,
  onPrepare,
  goToSettings,
}: {
  clips: Clip[];
  loading: boolean;
  error: string;
  onRefresh: () => void;
  onClipsChanged: () => void;
  onPrepare: (clip: Clip) => void;
  goToSettings: () => void;
}) {
  const [query, setQuery] = useState("");
  const [folder, setFolder] = useState("");
  const [selected, setSelected] = useState<Clip | null>(null);

  const folders = useMemo(() => [...new Set(clips.map((c) => c.folder).filter(Boolean))].sort(), [clips]);
  const visible = clips.filter(
    (c) => (!folder || c.folder === folder) && (!query || c.rel_path.toLowerCase().includes(query.toLowerCase())),
  );

  return (
    <section className="panel">
      <div className="panel-head">
        <h2>Libreria</h2>
        <button className="ghost icon" onClick={onRefresh} title="Rileggi l'hard disk">
          ↻
        </button>
      </div>
      <div className="panel-tools">
        <input type="search" placeholder="Cerca…" value={query} onChange={(e) => setQuery(e.target.value)} />
        {folders.length > 0 && (
          <select value={folder} onChange={(e) => setFolder(e.target.value)}>
            <option value="">Tutte le cartelle</option>
            {folders.map((f) => (
              <option key={f} value={f}>
                {f}
              </option>
            ))}
          </select>
        )}
      </div>

      {selected && (
        <ClipDetail
          clip={selected}
          onClose={() => setSelected(null)}
          onPrepare={() => onPrepare(selected)}
          onTranscribed={onClipsChanged}
        />
      )}

      <div className="panel-body">
        {error ? (
          <div className="notice">
            {error}
            <div className="row" style={{ marginTop: 8 }}>
              <button className="ghost small" onClick={onRefresh}>
                Riprova
              </button>
              <button className="ghost small" onClick={goToSettings}>
                Impostazioni
              </button>
            </div>
          </div>
        ) : loading && clips.length === 0 ? (
          <div className="empty">Leggo l'hard disk…</div>
        ) : visible.length === 0 ? (
          <div className="empty">Nessuna clip trovata.</div>
        ) : (
          <div className="clips">
            {visible.map((c) => (
              <button
                key={c.id}
                className={`clip ${selected?.id === c.id ? "selected" : ""}`}
                onClick={() => setSelected(c)}
                title={c.rel_path}
              >
                <img loading="lazy" src={`/api/clip/${c.id}/anteprima`} alt="" />
                <span className="clip-info">
                  <span className="clip-name">{c.name}</span>
                  <span className="tags">
                    <span className="pill">{c.kind === "video" ? fmtDuration(c.duration) : "foto"}</span>
                    {c.transcribed && <span className="pill ok">trascritta</span>}
                  </span>
                </span>
              </button>
            ))}
          </div>
        )}
      </div>
    </section>
  );
}

function ClipDetail({
  clip,
  onClose,
  onPrepare,
  onTranscribed,
}: {
  clip: Clip;
  onClose: () => void;
  onPrepare: () => void;
  onTranscribed: () => void;
}) {
  const [transcript, setTranscript] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setTranscript("");
    setError("");
    api.transcript(clip.id).then((t) => setTranscript(t.text ?? "")).catch(() => undefined);
  }, [clip.id]);

  const transcribe = async () => {
    setBusy(true);
    setError("");
    try {
      const t = await api.transcribe(clip.id);
      setTranscript(t.text ?? "");
      onTranscribed();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="detail">
      <div className="detail-media">
        {clip.kind === "video" ? (
          <video key={clip.id} src={`/api/clip/${clip.id}/file`} controls preload="metadata" />
        ) : (
          <img src={`/api/clip/${clip.id}/file`} alt="" />
        )}
      </div>
      <div className="detail-body">
        <div className="detail-title">{clip.name}</div>
        <div className="muted small">
          {[
            clip.folder,
            clip.kind === "video" ? fmtDuration(clip.duration) : "foto",
            clip.width && clip.height ? `${clip.width}×${clip.height}` : "",
            `${clip.size_mb} MB`,
          ]
            .filter(Boolean)
            .join(" · ")}
        </div>
        <div className="row wrap">
          <button onClick={onPrepare}>Scrivi testi e programma</button>
          {clip.kind === "video" && !transcript && (
            <button className="ghost" disabled={busy} onClick={transcribe}>
              {busy ? "Trascrivo…" : "Trascrivi"}
            </button>
          )}
          <button className="ghost" onClick={onClose}>
            Chiudi
          </button>
        </div>
        {error && <div className="notice small">{error}</div>}
        {transcript && (
          <details>
            <summary>Trascrizione</summary>
            <p className="small transcript">{transcript}</p>
          </details>
        )}
      </div>
    </div>
  );
}

import { useEffect, useState } from "react";
import { api, type FolderList } from "../api";

// Sfoglia le cartelle del Mac (dischi esterni in cima) e sceglie quella dei contenuti.
export default function FolderPicker({
  value,
  onChoose,
}: {
  value: string;
  onChoose: (path: string) => void;
}) {
  const [list, setList] = useState<FolderList | null>(null);
  const [error, setError] = useState("");
  const [manual, setManual] = useState("");

  const open = async (path?: string) => {
    setError("");
    try {
      setList(await api.folders(path));
    } catch (e) {
      setError((e as Error).message);
    }
  };

  useEffect(() => {
    open(value || undefined);
  }, []);

  return (
    <div className="folder-picker">
      <div className="folder-path">
        <span className="muted small">{list?.path ? "Cartella aperta:" : "Scegli da dove partire:"}</span>
        <strong>{list?.path ?? "Dischi e cartelle"}</strong>
      </div>
      {error && <div className="notice">{error}</div>}
      <div className="folder-list">
        {list?.path && (
          <button className="folder-row" onClick={() => open(list.parent ?? undefined)}>
            ⬆︎ Indietro
          </button>
        )}
        {list?.path && (
          <button className="folder-row" onClick={() => open()}>
            ⌂ Dischi e cartelle principali
          </button>
        )}
        {list?.folders.map((f) => (
          <button key={f.path} className="folder-row" onClick={() => open(f.path)}>
            {list.path ? "📁 " : ""}
            {f.name}
          </button>
        ))}
        {list && list.folders.length === 0 && <div className="empty">Nessuna sottocartella.</div>}
      </div>
      {list?.path && (
        <div className="row wrap">
          <button onClick={() => onChoose(list.path!)}>Usa questa cartella</button>
          <span className="muted small">
            {list.files_here ? `${list.files_here} video/foto qui (più quelli nelle sottocartelle)` : ""}
          </span>
        </div>
      )}
      <details className="small">
        <summary>Oppure incolla il percorso</summary>
        <div className="row">
          <input value={manual} onChange={(e) => setManual(e.target.value)} placeholder="/Volumes/NomeDisco/Contenuti" />
          <button className="ghost" onClick={() => manual.trim() && open(manual.trim())}>
            Apri
          </button>
        </div>
        <p className="muted small">
          Nel Finder: tasto destro sulla cartella, tieni premuto Option, scegli “Copia … come nome percorso”.
        </p>
      </details>
    </div>
  );
}

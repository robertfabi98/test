import { useEffect, useState } from "react";
import { api } from "../api";

export default function StylePage({ embedded = false }: { embedded?: boolean }) {
  const [text, setText] = useState("");
  const [saved, setSaved] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .style()
      .then((r) => {
        setText(r.testo);
        setSaved(r.testo);
      })
      .catch((e) => setError(e.message));
  }, []);

  const run = async (fn: () => Promise<{ testo: string }>, ok: string) => {
    setError("");
    setMessage("");
    try {
      const r = await fn();
      setText(r.testo);
      setSaved(r.testo);
      setMessage(ok);
    } catch (e) {
      setError((e as Error).message);
    }
  };

  const body = (
    <>
        {embedded ? <h2>Il mio stile</h2> : <h1>Il mio stile</h1>}
        <p className="muted">
          Claude legge questo testo ogni volta che scrive per te: tono, temi, hashtag, call to action ed esempi di post. Più
          è preciso, più i testi ti somigliano.
        </p>
        {message && <div className="notice ok">{message}</div>}
        {error && <div className="notice">{error}</div>}
        <textarea className="style-editor" value={text} onChange={(e) => setText(e.target.value)} spellCheck />
        <div className="row wrap">
          <button disabled={text === saved} onClick={() => run(() => api.saveStyle(text), "Stile salvato")}>
            Salva
          </button>
          <button
            className="ghost"
            onClick={() => confirm("Tornare allo stile iniziale?") && run(api.resetStyle, "Stile iniziale ripristinato")}
          >
            Ripristina iniziale
          </button>
        </div>
    </>
  );
  if (embedded) return <section className="card">{body}</section>;
  return (
    <div className="page">
      <div className="page-inner wide">{body}</div>
    </div>
  );
}

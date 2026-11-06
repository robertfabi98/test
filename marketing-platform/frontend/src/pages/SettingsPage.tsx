import { useEffect, useState } from "react";
import { api, type Settings } from "../api";
import FolderPicker from "../components/FolderPicker";
import SecretField from "../components/SecretField";

export default function SettingsPage({ onSaved }: { onSaved: () => void }) {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [keys, setKeys] = useState({ anthropic_api_key: "", buffer_api_key: "", cloudinary_url: "" });
  const [form, setForm] = useState({ claude_effort: "medium", youtube_category_id: "22", whisper_model: "small" });
  const [changingFolder, setChangingFolder] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api
      .settings()
      .then((s) => {
        setSettings(s);
        setForm({ claude_effort: s.claude_effort, youtube_category_id: s.youtube_category_id, whisper_model: s.whisper_model });
      })
      .catch((e) => setError(e.message));
  }, []);

  const save = async (changes: Record<string, unknown>, okText = "Salvato") => {
    setError("");
    setMessage("");
    try {
      const s = await api.saveSettings(changes);
      setSettings(s);
      setKeys({ anthropic_api_key: "", buffer_api_key: "", cloudinary_url: "" });
      setMessage(okText);
      onSaved();
    } catch (e) {
      setError((e as Error).message);
    }
  };

  if (!settings) return <div className="page">{error || "Carico…"}</div>;

  return (
    <div className="page">
      <div className="page-inner">
        <h1>Impostazioni</h1>
        {message && <div className="notice ok">{message}</div>}
        {error && <div className="notice">{error}</div>}

        <section className="card">
          <h2>Cartella dei contenuti</h2>
          <p>
            <strong>{settings.media_dir || "Nessuna cartella scelta"}</strong>
          </p>
          {changingFolder ? (
            <FolderPicker
              value={settings.media_dir}
              onChoose={(path) => {
                setChangingFolder(false);
                save({ media_dir: path }, "Cartella aggiornata");
              }}
            />
          ) : (
            <button className="ghost" onClick={() => setChangingFolder(true)}>
              Cambia cartella
            </button>
          )}
        </section>

        <section className="card">
          <h2>Pubblicazione</h2>
          <label className="switch">
            <input
              type="checkbox"
              checked={!settings.dry_run}
              onChange={(e) => {
                if (e.target.checked && !confirm("Da ora le conferme programmeranno davvero i post su Buffer. Procedere?")) return;
                save({ dry_run: !e.target.checked }, e.target.checked ? "Pubblicazione attiva" : "Modalità prova attiva");
              }}
            />
            <span>
              <strong>Pubblica davvero</strong>
              <br />
              <span className="muted small">
                Spento = modalità prova: le conferme mostrano cosa verrebbe inviato a Buffer, senza pubblicare.
              </span>
            </span>
          </label>
        </section>

        <section className="card">
          <h2>Collegamenti</h2>
          <SecretField
            label="Chiave di Claude"
            help="Da"
            link="https://console.anthropic.com/settings/keys"
            linkLabel="console.anthropic.com"
            current={settings.anthropic_api_key}
            value={keys.anthropic_api_key}
            onChange={(v) => setKeys({ ...keys, anthropic_api_key: v })}
            placeholder="sk-ant-…"
          />
          <SecretField
            label="Chiave di Buffer"
            help="Da"
            link="https://publish.buffer.com/settings/api"
            linkLabel="publish.buffer.com/settings/api"
            current={settings.buffer_api_key}
            value={keys.buffer_api_key}
            onChange={(v) => setKeys({ ...keys, buffer_api_key: v })}
          />
          <SecretField
            label="Cloudinary (API environment variable)"
            help="Dashboard → API Keys:"
            link="https://console.cloudinary.com/"
            linkLabel="console.cloudinary.com"
            current={settings.cloudinary_url}
            value={keys.cloudinary_url}
            onChange={(v) => setKeys({ ...keys, cloudinary_url: v })}
            placeholder="cloudinary://…"
          />
          <button
            disabled={!Object.values(keys).some((v) => v.trim())}
            onClick={() =>
              save(Object.fromEntries(Object.entries(keys).filter(([, v]) => v.trim())), "Chiavi salvate")
            }
          >
            Salva chiavi
          </button>
        </section>

        <section className="card">
          <h2>Avanzate</h2>
          <label className="field">
            <span className="field-label">Quanto ragiona Claude</span>
            <select value={form.claude_effort} onChange={(e) => setForm({ ...form, claude_effort: e.target.value })}>
              <option value="low">Veloce (costa meno)</option>
              <option value="medium">Equilibrato (consigliato)</option>
              <option value="high">Accurato (costa di più)</option>
            </select>
          </label>
          <label className="field">
            <span className="field-label">Precisione della trascrizione</span>
            <select value={form.whisper_model} onChange={(e) => setForm({ ...form, whisper_model: e.target.value })}>
              <option value="base">Veloce</option>
              <option value="small">Equilibrata (consigliata)</option>
              <option value="medium">Precisa (più lenta)</option>
            </select>
          </label>
          <label className="field">
            <span className="field-label">Categoria YouTube</span>
            <select
              value={form.youtube_category_id}
              onChange={(e) => setForm({ ...form, youtube_category_id: e.target.value })}
            >
              <option value="22">Persone e blog</option>
              <option value="27">Istruzione</option>
              <option value="28">Scienza e tecnologia</option>
            </select>
          </label>
          <button className="ghost" onClick={() => save(form)}>
            Salva
          </button>
        </section>
      </div>
    </div>
  );
}

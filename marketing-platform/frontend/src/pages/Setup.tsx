import { useEffect, useState } from "react";
import { api, type Settings } from "../api";
import FolderPicker from "../components/FolderPicker";
import SecretField from "../components/SecretField";

const STEPS = ["Cartella", "Claude", "Buffer", "Cloudinary", "Fatto"];

// Configurazione guidata al primo avvio: un passo alla volta, si può saltare e completare dopo.
export default function Setup({ onDone }: { onDone: () => void }) {
  const [step, setStep] = useState(0);
  const [settings, setSettings] = useState<Settings | null>(null);
  const [value, setValue] = useState("");
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.settings().then(setSettings).catch((e) => setError(e.message));
  }, []);

  const save = async (changes: Record<string, unknown>) => {
    setSaving(true);
    setError("");
    try {
      setSettings(await api.saveSettings(changes));
      setValue("");
      setStep((s) => s + 1);
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const skip = () => {
    setValue("");
    setError("");
    setStep((s) => s + 1);
  };

  return (
    <div className="center-screen">
      <div className="card setup">
        <div className="steps">
          {STEPS.map((s, i) => (
            <span key={s} className={`step ${i === step ? "current" : i < step ? "done" : ""}`}>
              {i + 1}. {s}
            </span>
          ))}
        </div>

        {step === 0 && (
          <>
            <h1>Benvenuto nella tua Marketing Platform</h1>
            <p>
              Collega l'hard disk esterno e scegli la cartella dove salvi i video finiti. La piattaforma li legge da lì:
              non devi caricare niente a mano.
            </p>
            <FolderPicker value={settings?.media_dir ?? ""} onChoose={(path) => save({ media_dir: path })} />
          </>
        )}

        {step === 1 && (
          <>
            <h1>Collega Claude</h1>
            <p>Claude scrive titoli e descrizioni e prepara il piano di pubblicazione. Serve una chiave API (si paga a consumo).</p>
            <SecretField
              label="Chiave di Claude"
              help="Crea la chiave e incollala qui:"
              link="https://console.anthropic.com/settings/keys"
              linkLabel="console.anthropic.com"
              current={settings?.anthropic_api_key}
              value={value}
              onChange={setValue}
              placeholder="sk-ant-…"
            />
          </>
        )}

        {step === 2 && (
          <>
            <h1>Collega Buffer</h1>
            <p>Buffer pubblica i post su Instagram, TikTok e YouTube agli orari che confermi.</p>
            <SecretField
              label="Chiave di Buffer"
              help="Creala nelle impostazioni API di Buffer:"
              link="https://publish.buffer.com/settings/api"
              linkLabel="publish.buffer.com/settings/api"
              current={settings?.buffer_api_key}
              value={value}
              onChange={setValue}
            />
          </>
        )}

        {step === 3 && (
          <>
            <h1>Collega Cloudinary</h1>
            <p>
              Buffer ha bisogno di un link pubblico al video. Cloudinary lo crea: la piattaforma ci carica da sola i file
              quando confermi un post. Il piano gratuito basta per iniziare.
            </p>
            <SecretField
              label="API environment variable"
              help="Dashboard di Cloudinary → API Keys → copia “API environment variable” (inizia con cloudinary://)."
              link="https://console.cloudinary.com/"
              linkLabel="console.cloudinary.com"
              current={settings?.cloudinary_url}
              value={value}
              onChange={setValue}
              placeholder="cloudinary://…"
            />
          </>
        )}

        {step === 4 && (
          <>
            <h1>Tutto pronto</h1>
            <p>
              La piattaforma parte in <strong>modalità prova</strong>: quando confermi un post ti mostra cosa invierebbe a
              Buffer, senza pubblicare niente. Quando sei pronto, disattivala nelle Impostazioni.
            </p>
            <p className="muted">Puoi cambiare cartella e chiavi in qualsiasi momento dalla pagina Impostazioni.</p>
          </>
        )}

        {error && <div className="notice">{error}</div>}

        <div className="row wrap setup-actions">
          {step >= 1 && step <= 3 && (
            <>
              <button
                disabled={saving || !value.trim()}
                onClick={() =>
                  save({ [["anthropic_api_key", "buffer_api_key", "cloudinary_url"][step - 1]]: value.trim() })
                }
              >
                {saving ? "Salvo…" : "Salva e continua"}
              </button>
              <button className="ghost" onClick={skip}>
                Salta per ora
              </button>
            </>
          )}
          {step === 0 && (
            <button className="ghost" onClick={skip}>
              Salta per ora
            </button>
          )}
          {step === 4 && <button onClick={onDone}>Inizia</button>}
        </div>
      </div>
    </div>
  );
}

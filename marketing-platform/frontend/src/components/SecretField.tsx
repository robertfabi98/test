import type { Secret } from "../api";

// Campo per una chiave: mostra solo le ultime cifre di quella salvata.
export default function SecretField({
  label,
  help,
  link,
  linkLabel,
  current,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  help: string;
  link: string;
  linkLabel: string;
  current?: Secret;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <label className="field">
      <span className="field-label">
        {label}{" "}
        {current?.impostato ? (
          <span className="pill ok">salvata {current.anteprima}</span>
        ) : (
          <span className="pill no">mancante</span>
        )}
      </span>
      <input
        type="password"
        autoComplete="off"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={current?.impostato ? "Lascia vuoto per non cambiarla" : placeholder}
      />
      <span className="muted small">
        {help}{" "}
        <a href={link} target="_blank" rel="noreferrer">
          {linkLabel}
        </a>
      </span>
    </label>
  );
}

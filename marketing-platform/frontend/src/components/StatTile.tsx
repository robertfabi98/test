import { fmtNumber } from "../api";

// Riquadro con un numero: etichetta, valore e variazione rispetto al periodo precedente.
export default function StatTile({
  label,
  value,
  previous,
  decimals = 0,
  suffix = "",
}: {
  label: string;
  value: number | undefined;
  previous?: number | undefined;
  decimals?: number;
  suffix?: string;
}) {
  let delta: { text: string; up: boolean } | null = null;
  if (value != null && previous != null && previous > 0) {
    const pct = ((value - previous) / previous) * 100;
    if (Math.abs(pct) >= 0.5) delta = { text: `${pct > 0 ? "+" : ""}${fmtNumber(pct, 0)}%`, up: pct > 0 };
  }
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-value">
        {fmtNumber(value, decimals)}
        {value != null && suffix}
      </div>
      {delta ? (
        <div className={`stat-delta ${delta.up ? "up" : "down"}`}>
          {delta.up ? "▲" : "▼"} {delta.text} <span className="muted">vs periodo prima</span>
        </div>
      ) : (
        <div className="stat-delta muted">&nbsp;</div>
      )}
    </div>
  );
}

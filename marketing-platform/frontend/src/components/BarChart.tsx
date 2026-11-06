import { useEffect, useRef, useState } from "react";
import { fmtNumber } from "../api";

export type Bar = { key: string; label: string; date: string; value: number };

// Grafico a barre di una sola serie (es. visualizzazioni per post), con tooltip su ogni barra.
export default function BarChart({ bars, unit }: { bars: Bar[]; unit: string }) {
  const [hover, setHover] = useState<{ bar: Bar; x: number; y: number } | null>(null);
  const wrap = useRef<HTMLDivElement>(null);
  const [W, setW] = useState(720);

  // il grafico usa la larghezza reale: i testi restano sempre della stessa misura
  useEffect(() => {
    const el = wrap.current;
    if (!el) return;
    const ro = new ResizeObserver(([e]) => setW(Math.max(280, Math.round(e.contentRect.width))));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  if (bars.length === 0)
    return (
      <div className="chart" ref={wrap}>
        <div className="empty">Nessun post pubblicato nel periodo.</div>
      </div>
    );

  const H = 220;
  const pad = { top: 12, right: 8, bottom: 26, left: 44 };
  const innerW = W - pad.left - pad.right;
  const innerH = H - pad.top - pad.bottom;
  const max = Math.max(...bars.map((b) => b.value), 1);
  // scala "pulita": 1, 2, 5 × 10^n
  const raw = max / 3;
  const pow = 10 ** Math.floor(Math.log10(raw));
  const step = [1, 2, 5, 10].map((m) => m * pow).find((s) => s >= raw) ?? raw;
  const top = Math.ceil(max / step) * step;
  const ticks = Array.from({ length: Math.round(top / step) + 1 }, (_, i) => i * step);
  const slot = innerW / bars.length;
  const gap = Math.min(2 + slot * 0.25, 10);
  const barW = Math.max(slot - gap, 2);
  const y = (v: number) => pad.top + innerH - (v / top) * innerH;
  const r = Math.min(4, barW / 2);

  const show = (bar: Bar, cx: number, cy: number) => setHover({ bar, x: cx, y: cy });

  const labelEvery = Math.ceil(bars.length / Math.max(2, Math.floor(innerW / 90)));

  return (
    <div className="chart" ref={wrap}>
      <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`} role="img" aria-label={`${unit} per post`} onPointerLeave={() => setHover(null)}>
        {ticks.map((t) => (
          <g key={t}>
            <line className="grid" x1={pad.left} x2={W - pad.right} y1={y(t)} y2={y(t)} />
            <text className="axis" x={pad.left - 6} y={y(t) + 4} textAnchor="end">
              {fmtNumber(t)}
            </text>
          </g>
        ))}
        {bars.map((b, i) => {
          const x = pad.left + i * slot + gap / 2;
          const h = Math.max(innerH - (y(b.value) - pad.top), b.value > 0 ? 1 : 0);
          const yTop = pad.top + innerH - h;
          const rr = Math.min(r, h);
          // angoli arrotondati solo in alto, base appoggiata all'asse
          const d = `M${x},${pad.top + innerH} V${yTop + rr} Q${x},${yTop} ${x + rr},${yTop} H${x + barW - rr} Q${x + barW},${yTop} ${x + barW},${yTop + rr} V${pad.top + innerH} Z`;
          return (
            <g key={b.key}>
              {/* area di aggancio più grande della barra */}
              <rect
                x={pad.left + i * slot}
                y={pad.top}
                width={slot}
                height={innerH}
                fill="transparent"
                tabIndex={0}
                aria-label={`${b.date}: ${fmtNumber(b.value)} ${unit}`}
                onPointerMove={() => show(b, x + barW / 2, yTop)}
                onFocus={() => show(b, x + barW / 2, yTop)}
                onBlur={() => setHover(null)}
              />
              <path d={d} className={`bar ${hover?.bar.key === b.key ? "active" : ""}`} pointerEvents="none" />
              {i % labelEvery === 0 && (
                <text className="axis" x={x + barW / 2} y={H - 8} textAnchor="middle">
                  {b.date}
                </text>
              )}
            </g>
          );
        })}
        <line className="baseline" x1={pad.left} x2={W - pad.right} y1={pad.top + innerH} y2={pad.top + innerH} />
      </svg>
      {hover && (
        <div className="tooltip" style={{ left: hover.x, top: hover.y }}>
          <div className="tooltip-date">{hover.bar.date}</div>
          <div className="tooltip-value">
            {fmtNumber(hover.bar.value)} {unit}
          </div>
          <div className="tooltip-text">{hover.bar.label}</div>
        </div>
      )}
    </div>
  );
}

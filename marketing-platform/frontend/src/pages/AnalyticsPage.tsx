import { useEffect, useMemo, useState } from "react";
import {
  analyticsApi,
  fmtNumber,
  SERVICE_LABEL,
  type ChannelOverview,
  type ChannelReport,
  type AnalyticsPost,
} from "../api";
import StatTile from "../components/StatTile";
import BarChart from "../components/BarChart";

const PERIODS = [7, 30, 90];
const SORTS: [string, string][] = [
  ["views", "Visualizzazioni"],
  ["engagementRate", "Engagement"],
  ["interactions", "Interazioni"],
  ["sent_at", "Più recenti"],
];

function interactions(p: AnalyticsPost) {
  const m = p.metrics;
  return (m.reactions ?? 0) + (m.comments ?? 0) + (m.shares ?? 0) + (m.saves ?? 0);
}

function shortDate(iso: string) {
  return new Date(iso).toLocaleDateString("it-IT", { day: "2-digit", month: "short" });
}

export default function AnalyticsPage({
  buffer,
  goToSettings,
  askClaude,
}: {
  buffer: boolean;
  goToSettings: () => void;
  askClaude: (prompt: string) => void;
}) {
  const [days, setDays] = useState(30);
  const [tab, setTab] = useState<string>("panoramica");
  const [overview, setOverview] = useState<ChannelOverview[] | null>(null);
  const [report, setReport] = useState<ChannelReport | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [sort, setSort] = useState("views");

  const load = async (refresh = false) => {
    if (!buffer) return;
    setLoading(true);
    setError("");
    try {
      if (tab === "panoramica") setOverview(await analyticsApi.overview(days, refresh));
      else setReport(await analyticsApi.channel(tab, days, refresh));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (buffer) analyticsApi.overview(days).then(setOverview).catch((e) => setError(e.message));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [buffer]);

  useEffect(() => {
    setReport(null);
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, days]);

  const channels = overview?.map((o) => o.channel) ?? [];

  if (!buffer) {
    return (
      <div className="page">
        <div className="page-inner">
          <h1>Analytics</h1>
          <div className="notice">
            Per vedere i risultati dei tuoi post collega Buffer.{" "}
            <button className="link" onClick={goToSettings}>
              Vai alle Impostazioni
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-inner xwide">
        <div className="page-head">
          <h1>Analytics</h1>
          <div className="row wrap">
            <div className="segmented" role="group" aria-label="Periodo">
              {PERIODS.map((d) => (
                <button key={d} className={d === days ? "active" : ""} onClick={() => setDays(d)}>
                  {d} giorni
                </button>
              ))}
            </div>
            <button className="ghost" disabled={loading} onClick={() => load(true)}>
              {loading ? "Aggiorno…" : "↻ Aggiorna"}
            </button>
          </div>
        </div>

        <div className="subtabs">
          <button className={tab === "panoramica" ? "active" : ""} onClick={() => setTab("panoramica")}>
            Panoramica
          </button>
          {channels.map((c) => (
            <button key={c.id} className={tab === c.id ? "active" : ""} onClick={() => setTab(c.id)}>
              <span className={`dot ch-${c.service}`} />
              {SERVICE_LABEL[c.service] ?? c.service}
            </button>
          ))}
        </div>

        {error && <div className="notice">{error}</div>}

        {tab === "panoramica" ? (
          <Overview data={overview} days={days} openChannel={setTab} />
        ) : report ? (
          <ChannelView report={report} sort={sort} setSort={setSort} askClaude={askClaude} />
        ) : (
          !error && <div className="empty">Carico i dati da Buffer…</div>
        )}

        <p className="muted small">
          Dati forniti da Buffer, aggiornati circa una volta al giorno. Confronto con i {days} giorni precedenti.
        </p>
      </div>
    </div>
  );
}

function Overview({
  data,
  days,
  openChannel,
}: {
  data: ChannelOverview[] | null;
  days: number;
  openChannel: (id: string) => void;
}) {
  if (!data) return <div className="empty">Carico i dati da Buffer…</div>;
  return (
    <div className="overview-grid">
      {data.map((o) => (
        <section className="card" key={o.channel.id}>
          <div className="row spread">
            <h2>
              <span className={`dot ch-${o.channel.service}`} />
              {SERVICE_LABEL[o.channel.service] ?? o.channel.service}
              <span className="muted">&nbsp;· {o.channel.name}</span>
            </h2>
            <button className="ghost small" onClick={() => openChannel(o.channel.id)}>
              Dettagli →
            </button>
          </div>
          {o.error ? (
            <div className="notice small">{o.error}</div>
          ) : (
            <div className="stats">
              <StatTile label={`Post (${days} gg)`} value={o.totals?.posts} previous={o.previous?.posts} />
              <StatTile label="Visualizzazioni" value={o.totals?.views} previous={o.previous?.views} />
              <StatTile label="Interazioni" value={o.totals?.interactions} previous={o.previous?.interactions} />
              <StatTile
                label="Engagement medio"
                value={o.totals?.engagementRate}
                previous={o.previous?.engagementRate}
                decimals={2}
                suffix="%"
              />
            </div>
          )}
        </section>
      ))}
    </div>
  );
}

function ChannelView({
  report,
  sort,
  setSort,
  askClaude,
}: {
  report: ChannelReport;
  sort: string;
  setSort: (s: string) => void;
  askClaude: (prompt: string) => void;
}) {
  const t = report.totals;
  const p = report.previous ?? {};
  const name = SERVICE_LABEL[report.channel.service] ?? report.channel.service;
  const hasWatch = t.averageTimeWatched != null;

  const bars = report.posts.map((post) => ({
    key: post.id,
    date: shortDate(post.sent_at),
    label: post.text.split("\n")[0].slice(0, 90) || "Post senza testo",
    value: post.metrics.views ?? 0,
  }));

  const sorted = useMemo(() => {
    const rows = [...report.posts];
    rows.sort((a, b) => {
      if (sort === "sent_at") return b.sent_at.localeCompare(a.sent_at);
      if (sort === "interactions") return interactions(b) - interactions(a);
      return (b.metrics[sort] ?? 0) - (a.metrics[sort] ?? 0);
    });
    return rows;
  }, [report.posts, sort]);

  return (
    <>
      <div className="stats wide">
        <StatTile label="Post pubblicati" value={t.posts} previous={p.posts} />
        <StatTile label="Visualizzazioni" value={t.views} previous={p.views} />
        <StatTile label="Copertura" value={t.reach} previous={p.reach} />
        <StatTile label="Interazioni" value={t.interactions} previous={p.interactions} />
        <StatTile label="Engagement medio" value={t.engagementRate} previous={p.engagementRate} decimals={2} suffix="%" />
        {hasWatch && (
          <StatTile label="Visione media" value={t.averageTimeWatched} previous={p.averageTimeWatched} decimals={1} suffix=" s" />
        )}
        {t.follows != null && <StatTile label="Nuovi follower" value={t.follows} previous={p.follows} />}
      </div>

      <section className="card">
        <div className="row spread wrap">
          <h2>Visualizzazioni per post · {name}</h2>
          <button
            className="ghost small"
            onClick={() =>
              askClaude(
                `Analizza i risultati di ${name} (canale ${report.channel.id}) negli ultimi ${report.days} giorni: cosa funziona meglio, cosa no, e cosa mi consigli di pubblicare e quando nelle prossime due settimane.`,
              )
            }
          >
            ✨ Chiedi a Claude cosa funziona
          </button>
        </div>
        <BarChart bars={bars} unit="visualizzazioni" />
      </section>

      <section className="card">
        <div className="row spread wrap">
          <h2>Post del periodo</h2>
          <label className="row small">
            Ordina per
            <select value={sort} onChange={(e) => setSort(e.target.value)} style={{ width: "auto" }}>
              {SORTS.map(([k, l]) => (
                <option key={k} value={k}>
                  {l}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="table-wrap">
          <table className="table">
            <thead>
              <tr>
                <th>Post</th>
                <th>Data</th>
                <th className="num">Visual.</th>
                <th className="num">Copertura</th>
                <th className="num">Mi piace</th>
                <th className="num">Commenti</th>
                <th className="num">Condiv.</th>
                <th className="num">Salv.</th>
                <th className="num">Eng.</th>
                {hasWatch && <th className="num">Visione</th>}
              </tr>
            </thead>
            <tbody>
              {sorted.map((post) => (
                <tr key={post.id}>
                  <td className="post-cell">
                    {post.thumbnail && <img src={post.thumbnail} alt="" loading="lazy" />}
                    <span>
                      {post.link ? (
                        <a href={post.link} target="_blank" rel="noreferrer">
                          {post.text.split("\n")[0].slice(0, 70) || "Apri il post"}
                        </a>
                      ) : (
                        post.text.split("\n")[0].slice(0, 70) || "Post senza testo"
                      )}
                    </span>
                  </td>
                  <td className="nowrap">{shortDate(post.sent_at)}</td>
                  <td className="num">{fmtNumber(post.metrics.views)}</td>
                  <td className="num">{fmtNumber(post.metrics.reach)}</td>
                  <td className="num">{fmtNumber(post.metrics.reactions)}</td>
                  <td className="num">{fmtNumber(post.metrics.comments)}</td>
                  <td className="num">{fmtNumber(post.metrics.shares)}</td>
                  <td className="num">{fmtNumber(post.metrics.saves)}</td>
                  <td className="num">
                    {post.metrics.engagementRate != null ? `${fmtNumber(post.metrics.engagementRate, 1)}%` : "–"}
                  </td>
                  {hasWatch && (
                    <td className="num">
                      {post.metrics.averageTimeWatched != null ? `${fmtNumber(post.metrics.averageTimeWatched, 1)} s` : "–"}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </>
  );
}

import { SERVICE_LABEL, type CalendarEntry } from "../api";

const DAY = 24 * 60 * 60 * 1000;

function startOfWeek(d: Date) {
  const x = new Date(d.getFullYear(), d.getMonth(), d.getDate());
  const wd = (x.getDay() + 6) % 7; // lunedì = 0
  return new Date(x.getTime() - wd * DAY);
}

const STATUS_LABEL: Record<string, string> = {
  da_confermare: "da confermare",
  simulato: "prova",
  programmato: "programmato",
  in_coda_buffer: "in coda su Buffer",
  parziale: "in parte",
  errore: "errore",
};

// Calendario di una settimana: ogni post è una scheda con colore e nome del canale.
export default function WeekCalendar({
  entries,
  weekStart,
  setWeekStart,
  onOpen,
}: {
  entries: CalendarEntry[];
  weekStart: Date;
  setWeekStart: (d: Date) => void;
  onOpen: (entry: CalendarEntry) => void;
}) {
  const start = startOfWeek(weekStart);
  const days = Array.from({ length: 7 }, (_, i) => new Date(start.getTime() + i * DAY));
  const today = new Date().toDateString();
  const end = new Date(start.getTime() + 7 * DAY);
  const inWeek = entries.filter((e) => {
    const d = new Date(e.due_at);
    return d >= start && d < end;
  });

  const title = `${days[0].toLocaleDateString("it-IT", { day: "numeric", month: "long" })} – ${days[6].toLocaleDateString(
    "it-IT",
    { day: "numeric", month: "long", year: "numeric" },
  )}`;

  return (
    <div className="calendar">
      <div className="row spread wrap">
        <h2>{title}</h2>
        <div className="row">
          <button className="ghost small" onClick={() => setWeekStart(new Date(start.getTime() - 7 * DAY))}>
            ← Settimana prima
          </button>
          <button className="ghost small" onClick={() => setWeekStart(new Date())}>
            Oggi
          </button>
          <button className="ghost small" onClick={() => setWeekStart(new Date(start.getTime() + 7 * DAY))}>
            Settimana dopo →
          </button>
        </div>
      </div>
      <div className="week">
        {days.map((d) => {
          const items = inWeek
            .filter((e) => new Date(e.due_at).toDateString() === d.toDateString())
            .sort((a, b) => a.due_at.localeCompare(b.due_at));
          return (
            <div key={d.toISOString()} className={`day ${d.toDateString() === today ? "today" : ""}`}>
              <div className="day-head">
                <span>{d.toLocaleDateString("it-IT", { weekday: "short" })}</span>
                <strong>{d.getDate()}</strong>
              </div>
              <div className="day-items">
                {items.map((e, i) => (
                  <button
                    key={i}
                    className={`event ch-border-${e.service} st-${e.status}`}
                    onClick={() => onOpen(e)}
                    title={e.text}
                  >
                    <span className="event-time">
                      {new Date(e.due_at).toLocaleTimeString("it-IT", { hour: "2-digit", minute: "2-digit" })}
                    </span>
                    <span className="event-channel">
                      <span className={`dot ch-${e.service}`} />
                      {SERVICE_LABEL[e.service] ?? e.service}
                    </span>
                    <span className="event-title">{e.title}</span>
                    <span className="event-status">{STATUS_LABEL[e.status] ?? e.status}</span>
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

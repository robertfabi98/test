// Collegamento con il backend locale.

export type Status = {
  media_dir: string | null;
  media_dir_ok: boolean;
  whisper: boolean;
  claude: boolean;
  buffer: boolean;
  cloudinary: boolean;
  dry_run: boolean;
  model: string;
};

export type Secret = { impostato: boolean; anteprima: string };

export type Settings = {
  media_dir: string;
  anthropic_api_key: Secret;
  claude_model: string;
  claude_effort: string;
  buffer_api_key: Secret;
  buffer_org_id: string;
  cloudinary_url: Secret;
  youtube_category_id: string;
  whisper_model: string;
  dry_run: boolean;
};

export type Clip = {
  id: string;
  name: string;
  folder: string;
  rel_path: string;
  kind: "video" | "image";
  size_mb: number;
  duration: number | null;
  width: number | null;
  height: number | null;
  mtime: number;
  transcribed: boolean;
};

export type Transcript = { text?: string };

export type ChatEntry = { role: "user" | "assistant"; text: string; actions?: string[] };

export type PlanPost = {
  channel_id: string;
  channel_name: string;
  service: string;
  text: string;
  title: string;
  due_at: string;
  buffer_post_id: string | null;
  error: string | null;
};

export type PlanItem = {
  id: string;
  clip_id: string;
  clip_name: string;
  clip_kind: string;
  due_at: string;
  note: string;
  status: "da_confermare" | "programmato" | "simulato" | "parziale" | "errore" | "annullato";
  posts: PlanPost[];
};

export type FolderList = {
  path: string | null;
  parent: string | null;
  files_here?: number;
  folders: { name: string; path: string }[];
};

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  const res = await fetch(path, {
    method,
    headers: { "Content-Type": "application/json", "X-MP": "1" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    /* risposta vuota */
  }
  if (!res.ok) {
    const detail = (data as { detail?: unknown } | null)?.detail;
    throw new Error(typeof detail === "string" ? detail : `Errore ${res.status}`);
  }
  return data as T;
}

export const api = {
  status: () => request<Status>("GET", "/api/stato"),
  settings: () => request<Settings>("GET", "/api/impostazioni"),
  saveSettings: (changes: Record<string, unknown>) => request<Settings>("PUT", "/api/impostazioni", changes),
  folders: (path?: string) =>
    request<FolderList>("GET", `/api/cartelle${path ? `?path=${encodeURIComponent(path)}` : ""}`),
  style: () => request<{ testo: string }>("GET", "/api/stile"),
  saveStyle: (testo: string) => request<{ testo: string }>("PUT", "/api/stile", { testo }),
  resetStyle: () => request<{ testo: string }>("POST", "/api/stile/ripristina"),
  clips: () => request<Clip[]>("GET", "/api/clip"),
  transcript: (id: string) => request<Transcript>("GET", `/api/clip/${id}/trascrizione`),
  transcribe: (id: string) => request<Transcript>("POST", `/api/clip/${id}/trascrivi`),
  chatHistory: () => request<ChatEntry[]>("GET", "/api/chat"),
  chat: (messaggio: string) => request<{ reply: string; actions: string[] }>("POST", "/api/chat", { messaggio }),
  newChat: () => request("POST", "/api/chat/nuova"),
  plan: () => request<PlanItem[]>("GET", "/api/piano"),
  updatePlan: (id: string, posts: { channel_id: string; text: string; title: string; due_at: string }[]) =>
    request<PlanItem>("PUT", `/api/piano/${id}`, { posts }),
  confirmPlan: (id: string) => request<PlanItem>("POST", `/api/piano/${id}/conferma`),
  cancelPlan: (id: string) => request<PlanItem>("POST", `/api/piano/${id}/annulla`),
  shutdown: () => request("POST", "/api/spegni"),
};

export function fmtDuration(sec: number | null): string {
  if (sec == null) return "";
  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function fmtDate(iso: string): string {
  if (!iso) return "";
  return new Date(iso).toLocaleString("it-IT", {
    weekday: "short",
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

// ISO con fuso -> valore per <input type="datetime-local"> (ora del Mac)
export function toLocalInput(iso: string): string {
  const d = new Date(iso);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

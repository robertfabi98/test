"use strict";

const $ = (id) => document.getElementById(id);
const state = { clips: [], selected: null, busy: false, dryRun: true };

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  let body = null;
  try { body = await res.json(); } catch { /* risposta vuota */ }
  if (!res.ok) throw new Error((body && body.detail) || `Errore ${res.status}`);
  return body;
}

function esc(text) {
  const d = document.createElement("div");
  d.textContent = text ?? "";
  return d.innerHTML;
}

function fmtDuration(sec) {
  if (sec == null) return "";
  const m = Math.floor(sec / 60), s = Math.round(sec % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

function fmtDate(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleString("it-IT", {
    weekday: "short", day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit",
  });
}

// ISO con fuso -> valore per <input type="datetime-local"> (ora locale del Mac)
function toLocalInput(iso) {
  const d = new Date(iso);
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

/* ---------- Stato configurazione ---------- */
async function loadStatus() {
  try {
    const s = await api("/api/stato");
    state.dryRun = s.dry_run;
    const pills = [
      ["Disco", s.media_dir_ok],
      ["ffmpeg", s.ffmpeg],
      ["Whisper", s.whisper],
      ["Claude", s.claude],
      ["Buffer", s.buffer],
      ["Cloudinary", s.cloudinary],
    ].map(([label, ok]) => `<span class="pill ${ok ? "ok" : "no"}">${label}</span>`);
    pills.push(
      s.dry_run
        ? `<span class="pill warn" title="DRY_RUN=1 nel .env: nessun post viene inviato a Buffer">Modalità prova</span>`
        : `<span class="pill ok">Pubblicazione attiva</span>`
    );
    $("status").innerHTML = pills.join("");
  } catch (e) {
    $("status").innerHTML = `<span class="pill no">${esc(e.message)}</span>`;
  }
}

/* ---------- Libreria ---------- */
async function loadClips() {
  $("library-error").classList.add("hidden");
  try {
    state.clips = await api("/api/clip");
    renderClips();
  } catch (e) {
    $("clips").innerHTML = "";
    $("library-error").textContent = e.message;
    $("library-error").classList.remove("hidden");
  }
}

function renderClips() {
  const q = $("search").value.trim().toLowerCase();
  const clips = state.clips.filter((c) => !q || c.rel_path.toLowerCase().includes(q));
  if (!clips.length) {
    $("clips").innerHTML = `<div class="empty">Nessuna clip trovata.</div>`;
    return;
  }
  $("clips").innerHTML = clips.map((c) => `
    <div class="clip ${state.selected?.id === c.id ? "selected" : ""}" data-id="${c.id}" title="${esc(c.rel_path)}">
      <img loading="lazy" src="/api/clip/${c.id}/thumb" alt="">
      <div class="info">
        <div class="name">${esc(c.name)}</div>
        <div class="tags">
          ${c.kind === "video" ? `<span class="pill">${fmtDuration(c.duration)}</span>` : `<span class="pill">foto</span>`}
          ${c.transcribed ? `<span class="pill ok">trascritta</span>` : ""}
        </div>
      </div>
    </div>`).join("");
}

async function selectClip(id) {
  const clip = state.clips.find((c) => c.id === id);
  if (!clip) return;
  state.selected = clip;
  renderClips();
  $("detail").classList.remove("hidden");
  $("detail-title").textContent = clip.name;
  $("detail-meta").textContent = [
    clip.folder, clip.kind === "video" ? fmtDuration(clip.duration) : "foto",
    clip.width && clip.height ? `${clip.width}×${clip.height}` : "", `${clip.size_mb} MB`,
  ].filter(Boolean).join(" · ");
  $("detail-media").innerHTML = clip.kind === "video"
    ? `<video src="/api/clip/${clip.id}/file" controls preload="metadata"></video>`
    : `<img src="/api/clip/${clip.id}/file" alt="">`;
  $("btn-transcribe").classList.toggle("hidden", clip.kind !== "video");
  showTranscript(await api(`/api/clip/${clip.id}/trascrizione`).catch(() => ({})));
}

function showTranscript(t) {
  const box = $("transcript-box");
  if (t && t.text) {
    $("transcript-text").textContent = t.text;
    box.classList.remove("hidden");
  } else {
    box.classList.add("hidden");
  }
}

async function transcribeSelected() {
  const clip = state.selected;
  if (!clip) return;
  const btn = $("btn-transcribe");
  btn.disabled = true;
  btn.textContent = "Trascrivo…";
  try {
    showTranscript(await api(`/api/clip/${clip.id}/trascrivi`, { method: "POST" }));
    $("transcript-box").open = true;
    clip.transcribed = true;
    renderClips();
  } catch (e) {
    alert(e.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Trascrivi";
  }
}

/* ---------- Chat ---------- */
function addMessage(role, text, actions = [], extraClass = "") {
  const el = document.createElement("div");
  el.className = `msg ${role} ${extraClass}`;
  el.innerHTML = esc(text).replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
  if (actions.length) {
    el.innerHTML += `<div class="actions">${actions.map((a) => `<span>• ${esc(a)}</span>`).join("")}</div>`;
  }
  $("messages").appendChild(el);
  $("messages").scrollTop = $("messages").scrollHeight;
  return el;
}

async function loadChat() {
  const history = await api("/api/chat").catch(() => []);
  history.forEach((m) => addMessage(m.role, m.text, m.actions || []));
}

async function sendChat(text) {
  if (state.busy || !text.trim()) return;
  state.busy = true;
  $("chat-send").disabled = true;
  addMessage("user", text);
  const waiting = addMessage("assistant", "Sto lavorando…", [], "thinking");
  try {
    const res = await api("/api/chat", { method: "POST", body: JSON.stringify({ messaggio: text }) });
    waiting.remove();
    addMessage("assistant", res.reply, res.actions);
    if (res.actions.some((a) => a.includes("proposta") || a.includes("trascritto"))) {
      loadPlan();
      loadClips();
    }
  } catch (e) {
    waiting.remove();
    addMessage("assistant", e.message, [], "error");
  } finally {
    state.busy = false;
    $("chat-send").disabled = false;
  }
}

/* ---------- Piano ---------- */
const STATUS_LABEL = {
  da_confermare: ["Da confermare", "warn"],
  programmato: ["Programmato su Buffer", "ok"],
  simulato: ["Prova (non inviato)", "warn"],
  parziale: ["Programmato in parte", "no"],
  errore: ["Errore", "no"],
  annullato: ["Annullato", ""],
};

async function loadPlan() {
  let items = [];
  try {
    items = await api("/api/piano");
  } catch (e) {
    $("plan").innerHTML = `<div class="empty">${esc(e.message)}</div>`;
    return;
  }
  const pending = items.filter((i) => ["da_confermare", "parziale", "errore", "simulato"].includes(i.status));
  const done = items.filter((i) => i.status === "programmato").reverse();
  let html = `<h3>Da confermare</h3>`;
  html += pending.length ? pending.map(renderPending).join("") : `<div class="empty">Nessuna proposta in attesa.</div>`;
  html += `<h3>Programmati</h3>`;
  html += done.length ? done.map(renderDone).join("") : `<div class="empty">Ancora niente.</div>`;
  $("plan").innerHTML = html;
}

function statusPill(status) {
  const [label, cls] = STATUS_LABEL[status] || [status, ""];
  return `<span class="pill ${cls}">${label}</span>`;
}

function renderPending(item) {
  const editable = item.status === "da_confermare";
  return `
    <div class="card" data-item="${item.id}">
      <div class="head"><div class="title">${esc(item.clip_name)}</div>${statusPill(item.status)}</div>
      ${item.note ? `<div class="muted small">${esc(item.note)}</div>` : ""}
      ${item.posts.map((p) => `
        <div class="post" data-channel="${p.channel_id}">
          <div class="row" style="justify-content:space-between">
            <span class="service">${esc(p.service)} · ${esc(p.channel_name)}</span>
            ${p.buffer_post_id ? `<span class="pill ok">programmato</span>` : ""}
          </div>
          <input type="datetime-local" class="f-date" value="${toLocalInput(p.due_at)}" ${editable ? "" : "disabled"}>
          ${p.service === "youtube" ? `<input class="f-title" placeholder="Titolo" value="${esc(p.title)}" ${editable ? "" : "disabled"}>` : ""}
          <textarea class="f-text" rows="5" ${editable ? "" : "disabled"}>${esc(p.text)}</textarea>
          ${p.error ? `<div class="err">${esc(p.error)}</div>` : ""}
        </div>`).join("")}
      <div class="row wrap">
        ${item.status === "simulato" && state.dryRun
          ? `<span class="muted small">Provato in modalità prova. Con DRY_RUN=0 nel .env potrai programmarlo davvero.</span>`
          : `<button data-action="confirm">${{ da_confermare: "Conferma e programma", simulato: "Programma davvero" }[item.status] || "Riprova"}</button>`}
        ${editable ? `<button class="ghost" data-action="save">Salva modifiche</button>` : ""}
        ${editable ? `<button class="danger" data-action="cancel">Annulla</button>` : ""}
      </div>
    </div>`;
}

function renderDone(item) {
  return `
    <div class="card">
      <div class="head"><div class="title">${esc(item.clip_name)}</div>${statusPill(item.status)}</div>
      ${item.posts.map((p) => `
        <div class="post">
          <span class="service">${esc(p.service)} · ${fmtDate(p.due_at)}</span>
          ${p.title ? `<div><strong>${esc(p.title)}</strong></div>` : ""}
          <div class="txt">${esc(p.text)}</div>
        </div>`).join("")}
    </div>`;
}

function collectEdits(card) {
  return [...card.querySelectorAll(".post")].map((el) => {
    const date = el.querySelector(".f-date").value;
    return {
      channel_id: el.dataset.channel,
      text: el.querySelector(".f-text").value,
      title: el.querySelector(".f-title")?.value || "",
      // datetime-local è nell'ora del Mac: lo converto in ISO con fuso
      due_at: date ? new Date(date).toISOString() : "",
    };
  });
}

async function onPlanClick(ev) {
  const btn = ev.target.closest("button[data-action]");
  if (!btn) return;
  const card = btn.closest(".card");
  const id = card.dataset.item;
  const action = btn.dataset.action;
  btn.disabled = true;
  try {
    if (action === "save") {
      await api(`/api/piano/${id}`, { method: "PUT", body: JSON.stringify({ posts: collectEdits(card) }) });
    } else if (action === "cancel") {
      if (!confirm("Annullare questa proposta?")) return;
      await api(`/api/piano/${id}/annulla`, { method: "POST" });
    } else if (action === "confirm") {
      if (card.querySelector(".f-text:not([disabled])")) {
        await api(`/api/piano/${id}`, { method: "PUT", body: JSON.stringify({ posts: collectEdits(card) }) });
      }
      btn.textContent = "Carico e programmo…";
      const res = await api(`/api/piano/${id}/conferma`, { method: "POST" });
      if (res.status === "simulato") {
        alert("Modalità prova: niente è stato inviato a Buffer. Per pubblicare davvero imposta DRY_RUN=0 nel file .env.");
      }
    }
    await loadPlan();
  } catch (e) {
    alert(e.message);
    await loadPlan();
  } finally {
    btn.disabled = false;
  }
}

/* ---------- Avvio ---------- */
$("clips").addEventListener("click", (ev) => {
  const card = ev.target.closest(".clip");
  if (card) selectClip(card.dataset.id);
});
$("search").addEventListener("input", renderClips);
$("refresh").addEventListener("click", loadClips);
$("btn-close").addEventListener("click", () => {
  state.selected = null;
  $("detail").classList.add("hidden");
  renderClips();
});
$("btn-transcribe").addEventListener("click", transcribeSelected);
$("btn-plan").addEventListener("click", () => {
  const c = state.selected;
  if (!c) return;
  $("chat-input").value =
    `Prepara titolo, descrizioni e hashtag per «${c.name}» (id ${c.id}) e proponimi quando pubblicarla su Instagram, TikTok e YouTube.`;
  $("chat-input").focus();
});
$("chat-form").addEventListener("submit", (ev) => {
  ev.preventDefault();
  const text = $("chat-input").value;
  $("chat-input").value = "";
  sendChat(text);
});
$("chat-input").addEventListener("keydown", (ev) => {
  if (ev.key === "Enter" && !ev.shiftKey) {
    ev.preventDefault();
    $("chat-form").requestSubmit();
  }
});
$("chat-reset").addEventListener("click", async () => {
  await api("/api/chat/reset", { method: "POST" });
  $("messages").querySelectorAll(".msg:not(.intro)").forEach((m) => m.remove());
});
$("plan").addEventListener("click", onPlanClick);
$("plan-refresh").addEventListener("click", loadPlan);

loadStatus().then(loadPlan);
loadClips();
loadChat();

import os
import time
from datetime import datetime, timezone, timedelta
import requests

CLICKUP_TOKEN = os.environ["CLICKUP_TOKEN"]
CLICKUP_SPACE_ID = os.environ["CLICKUP_SPACE_ID"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

BASE_URL = "https://api.clickup.com/api/v2"
HEADERS = {"Authorization": CLICKUP_TOKEN}

DAYS_IT = ["Lunedì", "Martedì", "Mercoledì", "Giovedì", "Venerdì", "Sabato", "Domenica"]
MONTHS_IT = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno",
             "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]


def get_folders(space_id: str) -> list:
    resp = requests.get(f"{BASE_URL}/space/{space_id}/folder", headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("folders", [])


def get_lists(folder_id: str) -> list:
    resp = requests.get(f"{BASE_URL}/folder/{folder_id}/list", headers=HEADERS)
    resp.raise_for_status()
    return resp.json().get("lists", [])


def get_tasks_from_list(list_id: str) -> list:
    tasks, page = [], 0
    while True:
        resp = requests.get(
            f"{BASE_URL}/list/{list_id}/task",
            headers=HEADERS,
            params={"include_closed": "false", "subtasks": "true", "page": page},
        )
        resp.raise_for_status()
        data = resp.json()
        tasks.extend(data.get("tasks", []))
        if data.get("last_page"):
            break
        page += 1
        time.sleep(0.3)
    return tasks


def get_tasks(folder_id: str) -> list:
    all_tasks = []
    for lst in get_lists(folder_id):
        all_tasks.extend(get_tasks_from_list(lst["id"]))
        time.sleep(0.2)
    return all_tasks


def fmt_due(due_ms) -> str | None:
    if not due_ms:
        return None
    dt = datetime.fromtimestamp(int(due_ms) / 1000, tz=timezone.utc)
    return dt.strftime("%d/%m")


def due_within_3(due_ms) -> bool:
    if not due_ms:
        return False
    now = datetime.now(timezone.utc)
    due = datetime.fromtimestamp(int(due_ms) / 1000, tz=timezone.utc)
    return timedelta(0) <= (due - now) <= timedelta(days=3)


def send_telegram(text: str) -> None:
    resp = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": TELEGRAM_CHAT_ID, "text": text,
              "parse_mode": "Markdown", "disable_web_page_preview": True},
    )
    resp.raise_for_status()
    time.sleep(0.5)


def classify(status: str) -> str:
    s = status.lower().strip()
    if any(k in s for k in ("lavorazion", "progress", "in corso", "working")):
        return "progress"
    if any(k in s for k in ("revision", "review", "approvazion")):
        return "review"
    if any(k in s for k in ("da fare", "to do", "todo", "open", "aperto", "nuovo", "new")):
        return "todo"
    return "todo"  # default per status non riconosciuti


def build_client_message(folder_name: str, tasks: list) -> str:
    review, due_soon = [], []

    for task in tasks:
        name = task.get("name", "").strip()
        status = task.get("status", {}).get("status", "")
        due_ms = task.get("due_date")
        due_str = fmt_due(due_ms)

        if classify(status) == "review":
            line = f"  • {name}"
            if due_str:
                line += f" — {due_str}"
            review.append(line)

        if due_within_3(due_ms):
            suffix = f" — {due_str}" if due_str else ""
            due_soon.append(f"  • {name}{suffix}")

    if not review and not due_soon:
        return ""

    lines = [f"📁 *{folder_name}*", f"_{len(tasks)} task totali_"]

    if review:
        lines += ["", "🔵 *In revisione* _(richiede la tua attenzione)_"] + review
    if due_soon:
        lines += ["", "🔴 *In scadenza (3 giorni)*"] + due_soon

    return "\n".join(lines)


def main():
    now = datetime.now(tz=timezone(timedelta(hours=2)))  # CEST
    date_str = f"{DAYS_IT[now.weekday()]} {now.day} {MONTHS_IT[now.month - 1]} {now.year}"

    send_telegram(f"📊 *Report Aloha Ltd*\n_{date_str}_")

    folders = get_folders(CLICKUP_SPACE_ID)

    totals = {"tasks": 0, "review": 0, "due_soon": 0}

    for folder in folders:
        tasks = get_tasks(folder["id"])
        if not tasks:
            continue

        msg = build_client_message(folder["name"], tasks)
        if msg:
            send_telegram(msg)

        totals["tasks"] += len(tasks)
        for task in tasks:
            status = task.get("status", {}).get("status", "")
            if classify(status) == "review":
                totals["review"] += 1
            if due_within_3(task.get("due_date")):
                totals["due_soon"] += 1

    send_telegram(
        f"📈 *Riepilogo workspace*\n"
        f"Task totali aperti: *{totals['tasks']}*\n"
        f"🔵 In revisione: *{totals['review']}*\n"
        f"🔴 In scadenza (3 gg): *{totals['due_soon']}*"
    )


if __name__ == "__main__":
    main()

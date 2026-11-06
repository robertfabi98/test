"""Chat con Claude tramite Claude Code: usa il tuo abbonamento Claude, nessuna chiave API.

Ogni messaggio avvia `claude -p` (modalità senza interfaccia) collegato al server MCP della
piattaforma (mcp_server.py). Claude Code può usare solo quegli strumenti.
"""

from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import sys
import threading
import uuid
from pathlib import Path

from . import config, tools

_WORKDIR = config.DATA_DIR / "claude"          # cartella vuota: Claude non vede altri file
_WORKDIR.mkdir(exist_ok=True)
_ACTIONS_DIR = config.DATA_DIR / "azioni"
_ACTIONS_DIR.mkdir(exist_ok=True)
_INSTALL_LOG = config.DATA_DIR / "installazione_claude.log"

_EXTRA_PATH = [
    str(Path.home() / ".local" / "bin"),
    str(Path.home() / ".claude" / "local"),
    "/opt/homebrew/bin",
    "/usr/local/bin",
    str(Path.home() / ".npm-global" / "bin"),
    "/usr/bin",
    "/bin",
]

# strumenti di Claude Code che qui non servono (file, terminale, web)
_BLOCKED = [
    "Bash", "Edit", "Write", "MultiEdit", "NotebookEdit", "Read", "Glob", "Grep", "LS",
    "WebFetch", "WebSearch", "Task", "TodoWrite",
]


def _env() -> dict:
    env = dict(os.environ)
    env["PATH"] = os.pathsep.join(_EXTRA_PATH + env.get("PATH", "").split(os.pathsep))
    # niente chiave API: Claude Code usa l'accesso del tuo abbonamento
    env.pop("ANTHROPIC_API_KEY", None)
    return env


def find_cli() -> str | None:
    """Trova il comando `claude` (installazione ufficiale, Homebrew, npm o estensione di VS Code)."""
    custom = os.getenv("MP_CLAUDE_CLI")
    if custom:
        return custom if os.access(custom, os.X_OK) else None
    found = shutil.which("claude", path=_env()["PATH"])
    if found:
        return found
    home = str(Path.home())
    patterns = [
        f"{home}/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude",
        f"{home}/.vscode/extensions/anthropic.claude-code-*/resources/*/claude",
        f"{home}/.cursor/extensions/anthropic.claude-code-*/resources/native-binary/claude",
    ]
    for pattern in patterns:
        hits = sorted(glob.glob(pattern), reverse=True)
        for hit in hits:
            if os.access(hit, os.X_OK):
                return hit
    return None


_status_cache: dict = {}


def status(check_login: bool = False) -> dict:
    """installato? accesso fatto? (il controllo dell'accesso fa una piccola richiesta a Claude)"""
    cli = find_cli()
    out = {"installed": bool(cli), "path": cli, "logged_in": _status_cache.get("logged_in"),
           "error": _status_cache.get("error"), "installing": _install_state["running"]}
    if cli and check_login:
        try:
            res = _run_cli(cli, "Rispondi solo con la parola OK.", None, with_tools=False, timeout=120)
            ok = not res.get("is_error")
            _status_cache.update(logged_in=ok, error=None if ok else _explain(res.get("result", "")))
        except Exception as exc:  # noqa: BLE001
            _status_cache.update(logged_in=False, error=str(exc))
        out.update(logged_in=_status_cache["logged_in"], error=_status_cache["error"])
    return out


def _explain(text: str) -> str:
    low = text.lower()
    if "login" in low or "log in" in low or "auth" in low or "api key" in low:
        return "Claude Code non ha ancora fatto l'accesso al tuo account: premi «Accedi a Claude»"
    if "limit" in low or "usage" in low:
        return "Hai raggiunto il limite di utilizzo del tuo abbonamento Claude: riprova più tardi"
    return text.strip()[:400] or "Claude Code non ha risposto"


def _mcp_config(run_id: str) -> Path:
    env = {k: v for k, v in os.environ.items() if k.startswith("MP_")}
    env.update(MP_RUN_ID=run_id, PYTHONPATH=str(config.BASE_DIR), MP_DATA_DIR=str(config.DATA_DIR))
    cfg = {
        "mcpServers": {
            "piattaforma": {"command": sys.executable, "args": ["-m", "app.mcp_server"], "env": env}
        }
    }
    path = _WORKDIR / f"mcp-{run_id}.json"
    path.write_text(json.dumps(cfg), "utf-8")
    return path


def _run_cli(cli: str, prompt: str, session_id: str | None, *, with_tools: bool = True,
             run_id: str | None = None, timeout: int = 900) -> dict:
    cmd = [cli, "-p", prompt, "--output-format", "json"]
    cfg_path = None
    if with_tools:
        run_id = run_id or uuid.uuid4().hex
        cfg_path = _mcp_config(run_id)
        cmd += [
            "--mcp-config", str(cfg_path), "--strict-mcp-config",
            "--tools", "",                       # nessuno strumento integrato (file, terminale, web)
            "--allowedTools", "mcp__piattaforma",
            "--disallowedTools", *_BLOCKED,
            "--append-system-prompt", tools.system_prompt()
            + "\n\nUsa solo gli strumenti mcp__piattaforma__*. Non hai accesso a file o terminale.",
        ]
    if session_id:
        cmd += ["--resume", session_id]
    try:
        proc = subprocess.run(
            cmd, cwd=_WORKDIR, env=_env(), capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("Claude Code ci sta mettendo troppo: riprova con una richiesta più semplice") from None
    finally:
        if cfg_path:
            cfg_path.unlink(missing_ok=True)
    out = proc.stdout.strip()
    try:
        # l'ultima riga JSON è il risultato
        data = json.loads(out.splitlines()[-1]) if out else {}
    except (json.JSONDecodeError, IndexError):
        data = {}
    if not data:
        raise RuntimeError(_explain(proc.stderr or out or "Claude Code non ha risposto"))
    return data


def read_actions(run_id: str) -> list[str]:
    path = _ACTIONS_DIR / f"{run_id}.jsonl"
    if not path.exists():
        return []
    labels = [json.loads(line)["label"] for line in path.read_text("utf-8").splitlines() if line.strip()]
    path.unlink(missing_ok=True)
    return labels


def ask(prompt: str, session_id: str | None) -> tuple[str, str | None, list[str]]:
    """Manda un messaggio a Claude Code. Restituisce (risposta, id sessione, azioni)."""
    cli = find_cli()
    if not cli:
        raise RuntimeError("Claude Code non è installato: vai in Impostazioni → Collegamenti")
    run_id = uuid.uuid4().hex
    data = _run_cli(cli, prompt, session_id, run_id=run_id)
    actions = read_actions(run_id)
    if data.get("is_error"):
        raise RuntimeError(_explain(str(data.get("result", ""))))
    _status_cache.update(logged_in=True, error=None)
    return str(data.get("result", "")).strip(), data.get("session_id"), actions


# ---------- installazione e accesso (dai pulsanti delle Impostazioni) ----------

_install_state = {"running": False}


def install() -> None:
    """Installa Claude Code con l'installer ufficiale (in ~/.local/bin, senza password)."""
    if _install_state["running"] or find_cli():
        return
    _install_state["running"] = True

    def go():
        try:
            with open(_INSTALL_LOG, "w", encoding="utf-8") as log:
                subprocess.run(
                    ["/bin/bash", "-c", "curl -fsSL https://claude.ai/install.sh | bash"],
                    stdout=log, stderr=subprocess.STDOUT, env=_env(), timeout=900,
                )
        finally:
            _install_state["running"] = False

    threading.Thread(target=go, daemon=True).start()


def open_login() -> None:
    """Apre il Terminale con Claude Code: al primo avvio chiede di accedere con il tuo account."""
    cli = find_cli()
    if not cli:
        raise RuntimeError("Installa prima Claude Code")
    script = f'tell application "Terminal" to do script "{cli}"\ntell application "Terminal" to activate'
    subprocess.run(["osascript", "-e", script], check=False)
    _status_cache.update(logged_in=None, error=None)

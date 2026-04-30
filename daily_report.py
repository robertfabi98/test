#!/usr/bin/env python3
"""
Routine giornaliera - aggiorna il foglio Google Sheets con il resoconto del giorno.

Setup (una sola volta):
  1. Vai su https://console.cloud.google.com
  2. Crea un progetto → Abilita "Google Sheets API" e "Google Drive API"
  3. Crea credenziali "Service Account" → scarica il JSON → salvalo come credentials.json
  4. Apri il foglio Google Sheets → condividilo con l'email del service account (colonna "client_email" nel JSON)
  5. pip install gspread google-auth

Uso:
  python3 daily_report.py
  (poi incolla il resoconto e premi Invio + Ctrl+D)

  oppure da file:
  python3 daily_report.py resoconto.txt
"""

import re
import sys
import os
from datetime import datetime

def _import_gspread():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
        return gspread, Credentials
    except ImportError:
        print("ERRORE: Installa le dipendenze con: pip install gspread google-auth")
        sys.exit(1)

SPREADSHEET_ID = "1jhMMrKHO5yW367TYjJaXi2ScdXFPQiOEynahr1SBABo"
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

MONTH_IT = {
    "GENNAIO": 1, "FEBBRAIO": 2, "MARZO": 3, "APRILE": 4,
    "MAGGIO": 5, "GIUGNO": 6, "LUGLIO": 7, "AGOSTO": 8,
    "SETTEMBRE": 9, "OTTOBRE": 10, "NOVEMBRE": 11, "DICEMBRE": 12,
}

MONTH_SHEET_NAMES = {
    1: "GENNAIO", 2: "FEBBRAIO", 3: "MARZO", 4: "APRILE",
    5: "MAGGIO", 6: "GIUGNO", 7: "LUGLIO", 8: "AGOSTO",
    9: "SETTEMBRE", 10: "OTTOBRE", 11: "NOVEMBRE", 12: "DICEMBRE",
}

# Mappa: chiave normalizzata del report → etichetta esatta nella riga del foglio
ENTRATE_ROW_LABELS = {
    "incasso pos mattina": "POS BAR / Mattina",
    "incasso mattina":     "Fondo Cassa / Mattina",
    "incasso pos sera":    "POS BAR / Sera",
    "incasso sera":        "Fondo Cassa / Sera",
    "entrata f":           "Entrata F",
    "entrata n":           "Entrata N",
}

SPESE_ROW_LABELS = {
    "ninni":         "Ninni",
    "teresa":        "Teresa",
    "granarolo":     "Granarolo",
    "galbani":       "Galbani",
    "pelucco":       "Pelucco",
    "san carlo":     "San Carlo",
    "latte":         "Latte",
    "cornetti":      "Cornetti",
    "caffe":         "Caffe",
    "caffè":         "Caffe",
    "sammontana":    "Sammontana",
    "d'orazio":      "D'orazio",
    "dorazio":       "D'orazio",
    "salvati":       "Salvati",
    "preziosi":      "Preziosi",
    "spesa":         "Spesa",
    "torres":        "Torres",
    "paffone":       "Paffone",
    "luca":          "Luca",
    "nicole":        "Nicole",
    "affitto":       "Affitto bar/Dipendenti/Aloha",
    "cassa fiscale": "Cassa Fiscale",
    "strumentazione":"Strumentazione",
    "allarme":       "Allarme",
    "bollette":      "Bollette",
    "manutenzione":  "Manutenzione",
    "offerte":       "Offerte",
    "banca":         "Banca",
    "lottomatica":   "Lottomatica",
    "utenze":        "Utenze",
    "pierluigi":     "Pierluigi",
    "soletti":       "Soletti",
    "f24":           "F24",
}


def parse_value(raw: str) -> float:
    """Converte una stringa numero (es. '169.7' o '169,7') in float."""
    return float(raw.strip().replace(",", "."))


def parse_report(text: str) -> dict:
    """
    Analizza il testo del resoconto giornaliero.
    Restituisce un dict con:
      - 'data': datetime
      - 'entrate': {label_foglio: valore}
      - 'spese': {label_foglio: valore}
      - 'borselli': {'SF': valore, 'SN': valore}  (non aggiornato sul foglio, solo log)
      - 'non_riconosciuti': lista di righe non parsate
    """
    result = {
        "data": None,
        "entrate": {},
        "spese": {},
        "borselli": {},
        "non_riconosciuti": [],
    }

    lines = [l.strip() for l in text.splitlines()]

    # --- Data ---
    for line in lines:
        m = re.search(r"Data[:\s]+(\d{1,2})\s+([A-Z]+)\s+(\d{4})", line, re.IGNORECASE)
        if m:
            day = int(m.group(1))
            month = MONTH_IT.get(m.group(2).upper())
            year = int(m.group(3))
            if month:
                result["data"] = datetime(year, month, day)
            break

    # Parametri generici: "Chiave —> valore" o "Chiave > valore" o "Chiave valore"
    value_pattern = re.compile(
        r"^(.+?)\s*[-—>]+\s*([\d.,]+)\s*$|^(.+?)\s+([\d.,]+)\s*$"
    )

    section = None  # "entrate" | "spese" | "stipendi" | "borselli"

    for line in lines:
        # Salto righe vuote, separatori e la riga della data
        clean = re.sub(r"[—\-]+", "", line).strip()
        if not clean:
            continue
        if re.match(r"^\s*data\s*[:\s]", line, re.IGNORECASE):
            continue

        upper = line.upper()
        m = value_pattern.match(line)

        # Rilevo la sezione solo su righe che NON sono già righe-valore
        if m is None:
            if re.search(r"ENTRAT", upper):
                section = "entrate"
                continue
            if re.search(r"SPES", upper):
                section = "spese"
                continue
            if re.search(r"STIPEND", upper):
                section = "spese"  # stipendi → stessa sezione SERA nel foglio
                continue
            if re.search(r"BORSELL", upper):
                section = "borselli"
                continue
            continue  # riga di testo libero, non valore
        if not m:
            continue

        if m.group(1):
            key_raw = m.group(1).strip()
            val_raw = m.group(2)
        else:
            key_raw = m.group(3).strip()
            val_raw = m.group(4)

        key_norm = key_raw.lower().strip(" :-")

        try:
            value = parse_value(val_raw)
        except ValueError:
            result["non_riconosciuti"].append(line)
            continue

        if section == "borselli":
            if key_norm in ("sf", "s.f."):
                result["borselli"]["SF"] = value
            elif key_norm in ("sn", "s.n."):
                result["borselli"]["SN"] = value
            else:
                result["borselli"][key_raw] = value
            continue

        # Cerca prima nelle entrate, poi nelle spese
        label = None
        if section in ("entrate", None):
            # Prova le chiavi entrate in ordine: quelle più lunghe per prime
            for k in sorted(ENTRATE_ROW_LABELS, key=len, reverse=True):
                if k in key_norm:
                    label = ENTRATE_ROW_LABELS[k]
                    result["entrate"][label] = value
                    break

        if label is None:
            for k in sorted(SPESE_ROW_LABELS, key=len, reverse=True):
                if k in key_norm:
                    label = SPESE_ROW_LABELS[k]
                    result["spese"][label] = value
                    break

        if label is None:
            result["non_riconosciuti"].append(line)

    return result


def col_letter(day: int) -> str:
    """Restituisce la lettera della colonna per il giorno (1→B, 2→C, ...)."""
    # Colonna A = etichette, B = giorno 1, C = giorno 2, ...
    col_index = day + 1  # 1-based: A=1, B=2
    if col_index <= 26:
        return chr(ord('A') + col_index - 1)
    # doppia lettera (es. AA, AB, ...)
    return chr(ord('A') + (col_index - 1) // 26 - 1) + chr(ord('A') + (col_index - 1) % 26)


def update_sheet(parsed: dict, dry_run: bool = False):
    if not parsed["data"]:
        print("ERRORE: Data non trovata nel resoconto.")
        return

    dt: datetime = parsed["data"]
    day = dt.day
    month = dt.month
    year = dt.year
    col = col_letter(day)

    sheet_name = f"{MONTH_SHEET_NAMES[month]} {year}"
    print(f"\nFoglio target: '{sheet_name}' | Giorno: {day} | Colonna: {col}")

    ws = None
    if not dry_run:
        if not os.path.exists(CREDENTIALS_FILE):
            print(f"\nERRORE: File credenziali non trovato: {CREDENTIALS_FILE}")
            print("Consulta le istruzioni nella sezione 'Setup' all'inizio del file.")
            print("\nModalità DRY-RUN attivata automaticamente:\n")
            dry_run = True
        else:
            gspread, Credentials = _import_gspread()
            creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=SCOPES)
            gc = gspread.authorize(creds)
            try:
                sh = gc.open_by_key(SPREADSHEET_ID)
            except gspread.exceptions.SpreadsheetNotFound:
                print("ERRORE: Foglio non trovato. Verifica che il service account abbia accesso.")
                return

            # Cerca il foglio del mese
            try:
                ws = sh.worksheet(sheet_name)
            except gspread.exceptions.WorksheetNotFound:
                titles = [w.title for w in sh.worksheets()]
                match = next((t for t in titles if MONTH_SHEET_NAMES[month] in t.upper()), None)
                if match:
                    ws = sh.worksheet(match)
                    print(f"  (Trovato foglio alternativo: '{match}')")
                else:
                    print(f"ERRORE: Nessun foglio trovato per '{sheet_name}'. Fogli disponibili: {titles}")
                    return

    # Raccoglie tutti gli aggiornamenti
    all_updates = {**parsed["entrate"], **parsed["spese"]}
    updates_done = []
    updates_failed = []

    if dry_run:
        print("\n--- AGGIORNAMENTI (DRY RUN) ---")
    else:
        print("\n--- AGGIORNAMENTI ---")

    for label, value in all_updates.items():
        if dry_run:
            print(f"  [{label}] → colonna {col} = {value}")
            updates_done.append(label)
        else:
            try:
                cell = ws.find(label)
                if cell is None:
                    raise ValueError(f"Etichetta '{label}' non trovata nel foglio")
                col_index = day + 1  # A=1 (labels), B=2 (day 1), ...
                ws.update_cell(cell.row, col_index, value)
                print(f"  ✓ [{label}] riga {cell.row}, col {col} = {value}")
                updates_done.append(label)
            except Exception as e:
                print(f"  ✗ ERRORE [{label}]: {e}")
                updates_failed.append((label, str(e)))

    if parsed["borselli"]:
        print("\n--- BORSELLI (solo log, non scritti sul foglio) ---")
        for k, v in parsed["borselli"].items():
            print(f"  {k}: {v}")

    if parsed["non_riconosciuti"]:
        print("\n--- RIGHE NON RICONOSCIUTE ---")
        for r in parsed["non_riconosciuti"]:
            print(f"  ! {r}")

    print(f"\nRiepilogo: {len(updates_done)} aggiornati, {len(updates_failed)} falliti.")


def main():
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    if args:
        with open(args[0], "r", encoding="utf-8") as f:
            text = f.read()
    else:
        print("Incolla il resoconto giornaliero (poi premi Invio e Ctrl+D):\n")
        text = sys.stdin.read()

    parsed = parse_report(text)

    if parsed["data"]:
        print(f"Data rilevata: {parsed['data'].strftime('%d/%m/%Y')}")
    print(f"Entrate trovate:  {len(parsed['entrate'])}")
    print(f"Spese trovate:    {len(parsed['spese'])}")
    print(f"Borselli trovati: {len(parsed['borselli'])}")

    update_sheet(parsed, dry_run=dry_run)


if __name__ == "__main__":
    main()

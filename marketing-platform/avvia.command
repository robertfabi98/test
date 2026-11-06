#!/bin/bash
# Avvio della Marketing Platform: doppio clic su questo file nel Finder.
# La prima volta installa tutto (qualche minuto), le volte successive parte subito.

cd "$(dirname "$0")" || exit 1

pausa() { echo; read -r -p "Premi Invio per chiudere questa finestra..." _; exit 1; }

echo "== Marketing Platform =="

# 1. Python 3.10 o superiore (preferisce quello di Homebrew)
PY=""
for c in /opt/homebrew/bin/python3 /usr/local/bin/python3 python3; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "ERRORE: serve Python 3.10 o più recente."
  echo "Installa Homebrew da https://brew.sh e poi esegui: brew install python ffmpeg"
  pausa
fi
echo "Python: $("$PY" --version)"

# 2. ffmpeg (per anteprime e durata delle clip)
if ! command -v ffmpeg >/dev/null 2>&1; then
  export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
fi
if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ATTENZIONE: ffmpeg non è installato, le anteprime non funzioneranno."
  echo "Installalo con: brew install ffmpeg"
fi

# 3. Ambiente Python e librerie (solo la prima volta o se cambiano)
if [ ! -x .venv/bin/python ]; then
  echo "Preparo l'ambiente Python (solo la prima volta)..."
  "$PY" -m venv .venv || { echo "ERRORE: impossibile creare l'ambiente Python"; pausa; }
fi
if [ ! -f .venv/.installato ] || [ requirements.txt -nt .venv/.installato ]; then
  echo "Installo le librerie (qualche minuto)..."
  .venv/bin/python -m pip install --upgrade pip >/dev/null
  if ! .venv/bin/python -m pip install -r requirements.txt; then
    echo "ERRORE durante l'installazione delle librerie: copia il messaggio qui sopra e mandalo a Claude."
    pausa
  fi
  echo "Installo Whisper per la trascrizione..."
  .venv/bin/python -m pip install -r requirements-whisper.txt \
    || echo "ATTENZIONE: Whisper non installato. La piattaforma funziona lo stesso, ma senza trascrizione."
  touch .venv/.installato
fi

# 4. File di configurazione
if [ ! -f .env ]; then
  cp .env.example .env
  echo
  echo "Ho creato il file .env: scrivi il percorso della cartella dell'hard disk accanto a MEDIA_DIR"
  echo "e le chiavi che hai già. Poi salva e fai di nuovo doppio clic su avvia.command."
  open -e .env 2>/dev/null || true
  pausa
fi

# 5. Porta già occupata? Forse la piattaforma è già aperta
PORT=$(grep -E '^PORT=' .env | cut -d= -f2); PORT=${PORT:-8765}
if lsof -iTCP:"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "La piattaforma sembra già accesa: apro il browser."
  open "http://127.0.0.1:$PORT"
  exit 0
fi

echo
echo "Avvio... non chiudere questa finestra finché usi la piattaforma."
.venv/bin/python app.py || { echo; echo "La piattaforma si è fermata con un errore: copia il messaggio qui sopra e mandalo a Claude."; pausa; }

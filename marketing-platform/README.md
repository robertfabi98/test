# Marketing Platform

La tua agenzia di marketing personale, sul tuo Mac.

La piattaforma legge le clip direttamente dall'hard disk esterno. Claude le trascrive, scrive titoli e descrizioni nel tuo stile e prepara il piano di pubblicazione. Tu controlli e confermi con un clic. A quel punto la piattaforma carica il file su Cloudinary e lo programma su Buffer, senza nessun upload a mano.

```
Hard disk ──► Libreria ──► Chat con Claude ──► Piano (tu confermi) ──► Cloudinary ──► Buffer ──► Instagram / TikTok / YouTube
```

**Fase 1 (questa versione):** libreria dal disco, trascrizione, testi coerenti con il tuo stile, programmazione su Buffer.
**Prossime fasi:** editor in chat (tagli, formato 9:16, sottotitoli), analisi dei risultati.

---

## Installazione (una volta sola)

Apri il Terminale (o il terminale di VS Code) ed esegui questi comandi uno alla volta.

**1. Strumenti di base.** Se non hai Homebrew, installalo prima da https://brew.sh

```bash
brew install python ffmpeg
```

**2. Scarica il progetto** (se l'hai già scaricato, entra nella cartella e usa `git pull`)

```bash
git clone https://github.com/robertfabi98/test.git
```

```bash
cd test/marketing-platform
```

**3. Ambiente Python e librerie**

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```

```bash
pip install -r requirements.txt
```

**4. File di configurazione**

```bash
cp .env.example .env
```

Poi apri `.env` in VS Code e compila i valori (vedi sotto). Il file `.env` contiene le tue chiavi: resta solo sul tuo Mac e non viene mai caricato su GitHub.

## Le chiavi da inserire nel file `.env`

| Voce | Dove la trovi |
|---|---|
| `MEDIA_DIR` | La cartella dei contenuti sull'hard disk. Nel Finder: tasto destro sulla cartella, tieni premuto **Option** e scegli "Copia … come nome percorso". Di solito è `/Volumes/NomeDisco/...` |
| `ANTHROPIC_API_KEY` | https://console.anthropic.com/settings/keys (si paga a consumo) |
| `BUFFER_API_KEY` | https://publish.buffer.com/settings/api |
| `CLOUDINARY_URL` | Account gratuito su https://cloudinary.com → Dashboard → API Keys → "API environment variable" |

`BUFFER_ORG_ID` è già compilato con la tua organizzazione Buffer.

## Avvio

Ogni volta che vuoi usarla:

```bash
cd test/marketing-platform && source .venv/bin/activate && python app.py
```

Si apre il browser su http://127.0.0.1:8765. In alto vedi lo stato di ogni collegamento (verde = ok). Per chiuderla premi `Ctrl+C` nel terminale.

## Come si usa

1. **Libreria** (a sinistra): ci sono tutte le clip della cartella. Clicca una clip per vederla.
2. **Scrivi testi e programma**: prepara la richiesta in chat. Puoi anche scrivere liberamente, per esempio:
   - *«Prendi le ultime 3 clip della cartella Reel novembre e distribuiscile la prossima settimana su Instagram e TikTok»*
   - *«Scrivi titolo e descrizione per il video sul posizionamento, più diretto e senza emoji»*
3. **Piano** (a destra): Claude crea le proposte. Puoi modificare testi, titoli e orari, poi premi **Conferma e programma**.

Claude non pubblica mai da solo: ogni post passa dalla tua conferma.

## Primo test: modalità prova

Nel file `.env` c'è `DRY_RUN=1`. In questa modalità la conferma **non invia niente** a Buffer. Ti fa vedere cosa verrebbe programmato, così provi tutto senza rischi.

Quando sei pronto a pubblicare davvero, imposta `DRY_RUN=0` e riavvia. Per il primo post reale scegli un orario lontano qualche ora e controlla in Buffer che sia arrivato bene. L'API di Buffer è recente: se risponde con un errore, copialo e lo sistemiamo.

## Il tuo stile

Il file `brand/stile.md` descrive tono, temi, hashtag e contiene esempi dei tuoi post. Claude lo legge a ogni conversazione: modificalo quando vuoi cambiare il modo in cui scrive.

## Da sapere

- **Hard disk:** deve essere collegato quando usi la piattaforma. Le anteprime, le trascrizioni e il piano restano sul Mac, nella cartella `data/`.
- **Trascrizione:** gira sul Mac ed è gratuita. Al primo utilizzo scarica il modello Whisper (qualche centinaio di MB). Puoi scegliere un modello più preciso o più veloce con `WHISPER_MODEL`.
- **Buffer gratuito:** al massimo 10 post in coda.
- **Cloudinary gratuito:** ha un limite di spazio e di dimensione per file. I video lunghi o pesanti potrebbero richiedere un'esportazione più leggera.
- **Musica di tendenza** di Instagram e TikTok: con la pubblicazione automatica non si può aggiungere. L'audio va messo nel montaggio.

## Struttura

```
marketing-platform/
├── app.py                 server locale (avvio)
├── brand/stile.md         il tuo stile, letto da Claude
├── platform_core/
│   ├── library.py         legge le clip dal disco e crea le anteprime
│   ├── transcribe.py      trascrizione con Whisper (+ file .srt)
│   ├── agent.py           la chat con Claude e i suoi strumenti
│   ├── plan.py            proposte, conferma e programmazione
│   ├── cloud.py           caricamento su Cloudinary
│   └── buffer_api.py      collegamento a Buffer
└── static/                l'interfaccia (HTML, CSS, JS)
```

# Marketing Platform

La tua agenzia di marketing personale: un'app per Mac che si apre con doppio clic, senza terminale e senza codice.

- **Libreria:** legge le clip direttamente dall'hard disk esterno, con anteprime e durata.
- **Chat con Claude:** trascrive le clip e scrive titoli, descrizioni e hashtag nel tuo stile. Poi prepara il piano di pubblicazione.
- **Piano:** controlli le proposte, le modifichi e le confermi. La piattaforma carica da sola il file su Cloudinary e lo programma su Buffer per Instagram, TikTok e YouTube.
- **Il mio stile e Impostazioni:** tutto si configura dall'interfaccia. Le chiavi restano solo sul tuo Mac.

```
Hard disk ──► Backend (sul Mac) ◄──► Interfaccia nel browser
                   │
                   ├── Claude (testi e piano)
                   ├── Cloudinary (link pubblico del video)
                   └── Buffer ──► Instagram / TikTok / YouTube
```

---

## Installazione (una volta sola, senza terminale)

1. Scarica e installa **GitHub Desktop**: https://desktop.github.com
2. Aprilo, accedi con il tuo account GitHub e scegli **File → Clone Repository → robertfabi98/test**. Come cartella va bene `Documenti/GitHub`.
3. In alto, su **Current Branch**, scegli `claude/great-ramanujan-uy5xhq`.
4. Clicca **Show in Finder** e apri la cartella `marketing-platform`.
5. Fai **doppio clic su "Marketing Platform"**, l'app con l'icona blu.
   - La prima volta scarica da sola i componenti: ci vogliono alcuni minuti e vedi un avviso in alto a destra. Poi si apre il browser.
   - Se il Mac chiede di accedere ai file dell'hard disk esterno, scegli **Consenti**.
   - Consiglio: trascina l'app nel Dock, così la apri con un clic.

Al primo avvio una **configurazione guidata** ti chiede:
- la cartella dell'hard disk dove salvi i video finiti
- la chiave di Claude: https://console.anthropic.com/settings/keys (si paga a consumo)
- la chiave di Buffer: https://publish.buffer.com/settings/api
- i dati di Cloudinary (gratuito): Dashboard → API Keys → "API environment variable"

Puoi saltare un passaggio e completarlo dopo da **Impostazioni**.

## Uso di tutti i giorni

- **Aprire:** doppio clic su "Marketing Platform".
- **Chiudere:** pulsante **Chiudi** in alto a destra.
- **Aggiornare** quando ci sono novità: in GitHub Desktop premi **Fetch origin** e poi **Pull**. Alla riapertura l'app si aggiorna da sola.

## Come si lavora

1. In **Libreria** clicca una clip e premi **Scrivi testi e programma**. Puoi anche scrivere liberamente in chat, per esempio:
   - *«Prendi le ultime 3 clip della cartella Reel novembre e distribuiscile la prossima settimana su Instagram e TikTok»*
   - *«Riscrivi la descrizione del video sul posizionamento, più diretta e senza emoji»*
2. Claude prepara le proposte nel **Piano**. Puoi cambiare testi, titoli e orari.
3. Premi **Conferma e programma**. Claude non pubblica mai da solo: ogni post passa dalla tua conferma.

### Modalità prova

All'inizio la piattaforma è in **modalità prova**: la conferma mostra cosa verrebbe programmato, ma non invia niente a Buffer. Quando sei pronto vai in **Impostazioni → Pubblica davvero**.

Per il primo post reale scegli un orario lontano qualche ora e controlla in Buffer che sia arrivato bene. L'API di Buffer è recente: se compare un errore, copialo e mandalo a Claude.

## Da sapere

- **Dove stanno i tuoi dati:** impostazioni, chiavi, anteprime, trascrizioni e piano sono nella cartella `Libreria/Application Support/MarketingPlatform` del tuo utente. Restano lì anche quando aggiorni l'app.
- **Se qualcosa non parte:** l'app mostra un messaggio e apre il file `avvio.log`. Mandalo a Claude.
- **Trascrizione:** gira sul Mac ed è gratuita. Al primo utilizzo scarica il modello (qualche centinaio di MB).
- **Limiti dei piani gratuiti:** Buffer accetta al massimo 10 post in coda. Cloudinary ha limiti di spazio e di dimensione per file.
- **Musica di tendenza** di Instagram e TikTok: con la pubblicazione automatica non si può aggiungere. L'audio va messo già nel montaggio.

---

## Per chi sviluppa

```
marketing-platform/
├── Marketing Platform.app   lanciatore per Mac (installa uv + Python 3.12 in ~/.marketing-platform)
├── backend/                 FastAPI: API su 127.0.0.1:8765 e serve l'interfaccia compilata
│   ├── requirements.txt
│   └── app/
│       ├── main.py          rotte API, protezioni (solo localhost + intestazione X-MP), spegnimento
│       ├── config.py        impostazioni salvate da interfaccia
│       ├── library.py       clip dal disco, anteprime (PyAV + Pillow), sfoglia cartelle
│       ├── transcribe.py    Whisper locale (faster-whisper)
│       ├── agent.py         chat con Claude e i suoi strumenti
│       ├── plan.py          proposte, conferma, programmazione
│       ├── cloud.py         caricamento su Cloudinary
│       └── buffer_api.py    API GraphQL di Buffer
└── frontend/                React + Vite + TypeScript (dist/ già compilata e inclusa)
```

Sviluppo: avvia `python -m app.main` dentro `backend/`, poi `npm install && npm run dev` dentro `frontend/` (le chiamate `/api` passano al backend). Dopo ogni modifica al frontend esegui `npm run build` e includi `frontend/dist` nel commit.

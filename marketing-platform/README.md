# Marketing Platform

La tua agenzia di marketing personale: un'app per Mac che si apre con doppio clic, senza terminale e senza codice.

L'app è divisa in quattro sezioni:

- **Analytics:** risultati per piattaforma (Instagram, TikTok, YouTube) su 7, 30 o 90 giorni. Visualizzazioni, copertura, interazioni, engagement e tempo di visione, con il confronto con il periodo precedente, un grafico per post e la tabella dei post. Il pulsante "Chiedi a Claude cosa funziona" passa i dati alla chat.
- **Programmazione:** calendario settimanale con i post in coda su Buffer e le proposte della piattaforma. Le proposte si modificano e si confermano da qui.
- **Creazione:** libreria delle clip lette dall'hard disk, con anteprime e trascrizione, e chat con Claude che scrive titoli, descrizioni e hashtag nel tuo stile e prepara le proposte.
- **Impostazioni:** collegamenti (Claude, Buffer, Cloudinary), cartella dei contenuti, modalità di pubblicazione, il tuo stile e opzioni avanzate. Le chiavi restano solo sul tuo Mac.

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

Al primo avvio una **configurazione guidata** ti chiede, senza nessuna chiave API da pagare:
- **la cartella** dell'hard disk dove salvi i video finiti
- **Claude**, tramite **Claude Code** e il tuo abbonamento Claude, lo stesso account che usi in VS Code. Se Claude Code non è installato c'è il pulsante "Installa Claude Code". "Accedi a Claude" apre il Terminale per fare l'accesso la prima volta.
- **Buffer**, con il pulsante **"Accedi con Buffer"**: si apre il browser, accedi e approvi. Il collegamento passa dal server MCP ufficiale di Buffer.
- **Cloudinary** (facoltativo, gratuito, senza carta di credito): serve solo per pubblicare davvero, perché Buffer vuole un link pubblico al video.

Puoi saltare un passaggio e completarlo dopo da **Impostazioni**.

## Uso di tutti i giorni

- **Aprire:** doppio clic su "Marketing Platform".
- **Chiudere:** pulsante **Chiudi** in alto a destra.
- **Aggiornare** quando ci sono novità: in GitHub Desktop premi **Fetch origin** e poi **Pull**. Alla riapertura l'app si aggiorna da sola.

## Come si lavora

1. In **Creazione** clicca una clip e premi **Scrivi testi e programma**. Puoi anche scrivere liberamente in chat, per esempio:
   - *«Prendi le ultime 3 clip della cartella Reel novembre e distribuiscile la prossima settimana su Instagram e TikTok»*
   - *«Guarda le analytics di TikTok dell'ultimo mese e dimmi quali temi funzionano meglio»*
2. Claude prepara le proposte. Le trovi in **Programmazione**, dove puoi cambiare testi, titoli e orari.
3. Premi **Conferma e programma**. Claude non pubblica mai da solo: ogni post passa dalla tua conferma.
4. In **Analytics** controlli come sono andati i post e chiedi a Claude cosa migliorare.

### Modalità prova

All'inizio la piattaforma è in **modalità prova**: la conferma mostra cosa verrebbe programmato, ma non invia niente a Buffer. Quando sei pronto vai in **Impostazioni → Pubblica davvero**.

Per il primo post reale scegli un orario lontano qualche ora e controlla in Buffer che sia arrivato bene. L'API di Buffer è recente: se compare un errore, copialo e mandalo a Claude.

## Da sapere

- **Dove stanno i tuoi dati:** impostazioni, chiavi, anteprime, trascrizioni e piano sono nella cartella `Libreria/Application Support/MarketingPlatform` del tuo utente. Restano lì anche quando aggiorni l'app.
- **Se qualcosa non parte:** l'app mostra un messaggio e apre il file `avvio.log`. Mandalo a Claude.
- **Trascrizione:** gira sul Mac ed è gratuita. Al primo utilizzo scarica il modello (qualche centinaio di MB).
- **Uso di Claude:** la chat usa Claude Code con il tuo abbonamento, quindi conta nei limiti del tuo piano Claude e non ha costi extra. In Impostazioni → Avanzate puoi passare a una chiave API a consumo, se preferisci.
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
│       ├── agent.py         chat: Claude Code (abbonamento) oppure API con chiave
│       ├── claude_code.py   avvio di `claude -p` collegato al server MCP della piattaforma
│       ├── mcp_server.py    server MCP con gli strumenti della piattaforma (usato da Claude Code)
│       ├── tools.py         strumenti e istruzioni di Claude
│       ├── buffer_mcp.py    client MCP di Buffer con accesso OAuth dal browser
│       ├── plan.py          proposte, conferma, programmazione
│       ├── schedule.py      calendario (proposte + coda di Buffer)
│       ├── analytics.py     analytics per piattaforma dai post di Buffer
│       ├── cloud.py         caricamento su Cloudinary
│       └── buffer_api.py    Buffer: via MCP (predefinito) o API GraphQL con chiave
└── frontend/                React + Vite + TypeScript (dist/ già compilata e inclusa)
```

Sviluppo: avvia `python -m app.main` dentro `backend/`, poi `npm install && npm run dev` dentro `frontend/` (le chiamate `/api` passano al backend). Dopo ogni modifica al frontend esegui `npm run build` e includi `frontend/dist` nel commit.

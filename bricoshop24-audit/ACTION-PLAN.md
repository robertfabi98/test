# Piano d'Azione SEO — BricoShop24.it
**Data:** 23 giugno 2026 | **Health Score attuale:** 38/100 | **Target 90gg:** 58/100

---

## 🚨 FASE 1 — Fix Critici (Settimana 1)

> Questi problemi bloccano tutto il resto. Nessuna altra azione SEO produce effetto finché questi non sono risolti.

| # | Azione | Responsabile | Effort | Impatto |
|---|--------|-------------|--------|---------|
| 1 | **Sbloccare Googlebot nel WAF** — whitelist IP ranges Google (`googlebot.json`) e Bingbot. Validare con GSC "Test Live URL" | Dev/Hosting | 1-2h | 🔴 Critico |
| 2 | **Redirect 301 URL legacy OpenCart** — tutti i pattern `?product_id=X&route=product/product` → slug SEO-friendly | Dev | 4-8h | 🔴 Critico |
| 3 | **Rendere robots.txt e sitemap.xml accessibili (HTTP 200)** da qualsiasi IP | Dev/Hosting | 1h | 🔴 Critico |
| 4 | **Aggiungere P.IVA + REA al footer** (obbligatorio D.Lgs. 70/2003) | Dev | 30min | 🔴 Legale + Trust |
| 5 | **Risolvere www vs non-www** — 301 da `http://bricoshop24.it` e `https://bricoshop24.it` → `https://www.bricoshop24.it` | Dev | 1h | 🔴 Critico |

---

## ⚡ FASE 2 — Quick Wins ad Alto Impatto (Settimane 2–3)

> Massimo ROI per unità di tempo. Effetti visibili in 4–8 settimane.

| # | Azione | Effort | Impatto |
|---|--------|--------|---------|
| 6 | **Organization + AggregateRating schema in homepage** — JSON-LD con nome, indirizzo, telefono, logo, sameAs (Trustpilot, eBay, FB), aggregateRating (4/5, 306 recensioni) | Dev 2h | Stelle SERP, Knowledge Panel |
| 7 | **BreadcrumbList schema** su tutte le pagine categoria e prodotto | Dev 3h | Breadcrumb in SERP, CTR |
| 8 | **Product + Offer schema** sui template prodotto OpenCart — nome, prezzo, disponibilità, immagine, brand | Dev 4h | Rich results prezzo in SERP |
| 9 | **Correggere title tag homepage** → "Bricoshop24 \| Porte Blindate, Arredo Casa e Giardino" (52 char) | SEO 30min | CTR organico |
| 10 | **Portare in homepage/chi-siamo:** Trustpilot 4★ 306 recensioni + eBay 97.4% 19k+ vendite + anni di attività | Content 2h | Conversione + E-E-A-T |
| 11 | **fetchpriority="high" + preload** sull'immagine LCP (hero o primo prodotto above-fold) | Dev 1h | LCP < 2.5s |
| 12 | **Canonical tag** su ogni pagina prodotto che espliciti lo slug pulito (strip parametri UTM/marketplace) | Dev 2h | Duplicate content |

---

## 📝 FASE 3 — Contenuto & Autorità (Mese 2)

> Fondamenta della visibilità organica a lungo termine.

| # | Azione | Effort | Impatto |
|---|--------|--------|---------|
| 13 | **Blocco editoriale 500 parole su /porte-blindate** — tabella prezzi per classe, guida UNI EN 1627, FAQ 4 domande PAA + FAQPage schema | Content 1gg | Ranking "porte blindate online" |
| 14 | **Articolo pillar "Porta Blindata Classe 3 vs Classe 4: guida 2026"** (2.000+ parole, autore nominato, FAQPage schema) | Content 2gg | AI Overview + ranking informazionali |
| 15 | **Creare profilo autore** per il blog — nome, bio, foto, expertise (sicurezza, bricolage) | Content 2h | E-E-A-T Google QRG |
| 16 | **Blocco editoriale 300 parole** su /giardino, /riscaldamento, /climatizzazione | Content 3h/pagina | Ranking categorie secondarie |
| 17 | **WebSite + SearchAction schema** in homepage | Dev 1h | Sitelinks Searchbox SERP |
| 18 | **Article schema** sul template blog (datePublished, author, publisher, image) | Dev 2h | Google Discover, rich results |
| 19 | **llms.txt** su `/llms.txt` con identità brand, categorie, contatti | Dev/SEO 1h | Citabilità AI crawlers |
| 20 | **Disavow siteindices.com e revool.net** in GSC (verificare prima che i link esistano) | SEO 1h | Profilo backlink pulito |

---

## 📈 FASE 4 — Monitoraggio & Iterazione (Mese 3 e ongoing)

| # | Azione |
|---|--------|
| 21 | Configurare Google Search Console — verificare copertura indice, errori crawl, CWV report |
| 22 | Configurare Google Analytics 4 con eventi e-commerce |
| 23 | Avviare campagna link building: pagine fornitore, editoriale (lavorincasa.it, casanoi.it), CCIAA Roma |
| 24 | Integrare BNPL (Scalapay o Klarna) sulle pagine porte blindate — leva conversione per ticket €600–3.000 |
| 25 | Audit mensile crawl con Screaming Frog da IP business (non cloud) — identificare pagine orfane, errori 4xx, redirect chain |
| 26 | A/B test trust bar persistente (Trustpilot rating + 24h delivery + garanzia italiana) su homepage e categorie |
| 27 | Monitorare AI Overview visibility per "porte blindate online", "porta blindata classe 3", "porte blindate acquisto" |

---

## KPI Target (90 giorni)

| Metrica | Ora | Target 90gg |
|---------|-----|-------------|
| SEO Health Score | 38/100 | 58/100 |
| Schema coverage | 0% pagine | 80% pagine prodotto |
| Title tag corretto | Troncato | ≤ 60 char |
| LCP (stima mobile) | > 3s | < 2.5s |
| Pagine indicizzate | Incerto (WAF) | +30% dopo fix WAF |
| Backlink referring domains | ~8 noti | +15 nuovi domini |

---

## Dipendenze Critiche

```
WAF Fix (Task 1)
    ↓
robots.txt / sitemap accessibili (Task 3)
    ↓
GSC attivo e monitorabile
    ↓
Tutte le altre ottimizzazioni producono effetto misurabile
```

> ⚠️ Senza il fix WAF, qualsiasi miglioramento a schema, contenuto o performance è potenzialmente invisibile a Google. Il Task 1 è il prerequisito di tutto.

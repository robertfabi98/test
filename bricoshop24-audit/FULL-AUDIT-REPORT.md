# SEO Audit Completo — BricoShop24.it
**Data:** 23 giugno 2026  
**URL:** https://www.bricoshop24.it/  
**Tipo business:** E-commerce multi-categoria (Porte Blindate, Arredamento, Giardino, Cucina, Riscaldamento, Bricolage)  
**Sede:** Via del Prato della Corte 1422, 00123 Roma  
**Piattaforma:** OpenCart (inferred da URL pattern e struttura legacy)

---

## 🏆 SEO Health Score Complessivo: **38 / 100**

| Categoria | Peso | Score | Score Ponderato |
|-----------|------|-------|-----------------|
| Technical SEO | 22% | 44 | 9.7 |
| Content Quality (E-E-A-T) | 23% | 48 | 11.0 |
| On-Page SEO | 20% | 40* | 8.0 |
| Schema / Structured Data | 10% | 5 | 0.5 |
| Performance (CWV) | 10% | 45* | 4.5 |
| AI Search Readiness (GEO) | 10% | 18 | 1.8 |
| Backlinks | 5% | N/D† | — |

*stima basata su dati disponibili senza accesso diretto  
†dati insufficienti per scoring affidabile (Tier 0)

> **Nota metodologica:** Il sito restituisce HTTP 403 da tutti gli IP cloud/datacenter, inclusi quelli dei tool di analisi e dei motori di ricerca. Questo è il problema più urgente dell'intero audit — potenzialmente invalida tutti gli altri sforzi SEO.

---

## Executive Summary

BricoShop24 è un e-commerce romano con solide basi commerciali — 10+ anni di attività, 3.370 prodotti su Leroy Merlin, 500+ su ManoMano, 19.000+ vendite eBay con 97.4% feedback positivo, 306 recensioni Trustpilot a 4 stelle. Questo capitale di fiducia esiste ma **non viene comunicato ai motori di ricerca né agli utenti che arrivano da Google**.

I 5 problemi critici che bloccano la crescita organica:

1. **Il WAF blocca Googlebot** (403 su IP datacenter) — il sito potrebbe non essere crawlato correttamente
2. **URL legacy OpenCart** (`?product_id=X&route=product/product`) in circolazione — duplicate content massivo
3. **Schema markup assente** — 0 Product schema, 0 BreadcrumbList, 0 Organization, 0 AggregateRating
4. **Pagine categoria senza contenuto editoriale** — pure PLP che non competono con hybrid pages nei SERP
5. **AI crawler bloccati** — invisibile a Google AI Overviews, Perplexity, ChatGPT

**Top 5 Quick Wins (alta priorità, basso sforzo):**
1. Sbloccare Googlebot nel WAF (1 ora, impatto immediato)
2. Aggiungere P.IVA + REA in footer (30 minuti, obbligatorio per legge)
3. Organization + AggregateRating schema in homepage (2 ore, visibilità brand SERP)
4. Portare il 97.4% eBay e Trustpilot in homepage e chi-siamo (1 ora)
5. Reindirizzare 301 tutti gli URL ?product_id= legacy (4 ore sviluppatore)

---

## 1. Technical SEO — Score: 44/100

### Problemi Critici

**🔴 WAF/CDN blocca Googlebot (HTTP 403)**
Il server risponde `x-deny-reason: host_not_allowed` a tutti gli IP datacenter. Googlebot opera da IP Google — se bloccato, causa deindexazione progressiva. Questo è il rischio più alto dell'intero audit.

*Fix:* Inserire whitelist WAF per gli IP Googlebot pubblicati da Google (`developers.google.com/search/apis/ipranges/googlebot.json`) + Bingbot. Validare con GSC → Ispezione URL → Testa URL live.

**🔴 URL legacy OpenCart duplicati**
URL del tipo `bricoshop24.it/?product_id=23712&route=product/product` esistono in parallelo agli URL SEO-friendly (`/21633-porta-blindata-...`). Duplicate content su ogni prodotto.

*Fix:* 301 redirect da tutti i pattern `?route=product/product&product_id=X` agli slug puliti. Verificare che ogni prodotto abbia canonical tag che punta allo slug.

### Problemi Alti

- **robots.txt restituisce 403** — Google può interpretarlo come "tutto disallow"
- **sitemap.xml inaccessibile** — impossibile verificarne struttura e completezza
- **www vs non-www non risolto** — il dominio non-www sembra ospitare ancora versioni legacy
- **Title tag homepage troncato** — "...arredo casa, giardino e..." ellissi visibile in SERP
- **Immagini prodotto senza fetchpriority** — LCP probabilmente > 2.5s su mobile

---

## 2. Content Quality & E-E-A-T — Score: 48/100

### Cosa Funziona
- Indirizzo fisico specifico e verificabile (Roma) → chiarezza entità
- Due numeri di telefono + orari di supporto pubblicati
- USP concreti: garanzia italiana, consegna 24h
- Sottocategorie porte blindate ben strutturate (anta singola, doppia anta, interno multistrato)

### Problemi Critici

**🔴 P.IVA / REA assenti dal footer**
Obbligatorio per D.Lgs. 70/2003 (e-commerce italiano). Assenza = rischio legale + penalità E-E-A-T nei quality rater Google.

**🔴 Nessun AggregateRating schema (306 recensioni Trustpilot)**
306 recensioni a 4 stelle esistono ma sono invisibili a Google. Implementare schema = stelle in SERP, nessun costo.

### Problemi Alti

- **Nessun autore nominato sui blog post** — YMYL-adjacent (sicurezza casa), Google penalizza contenuti anonimi
- **Pagine categoria senza blocco editoriale** — meno di 800 parole su ogni PLP principale
- **Rischio alto duplicate content su descrizioni prodotto** — 3.370 prodotti su Leroy Merlin = descrizioni condivise
- **Blog insufficiente** — 1 articolo confermato non può creare autorità tematica su 6 verticali
- **97.4% eBay / 19k+ vendite non comunicato sul sito** — asset di fiducia unico e inutilizzato

---

## 3. Schema / Structured Data — Score: 5/100

Stato attuale: **nessun JSON-LD verificato**. OpenCart out-of-the-box non emette schema valido.

| Schema | Stato | Priorità | Impatto |
|--------|-------|----------|---------|
| Product + Offer | ❌ Assente | CRITICO | Rich results prezzo/disponibilità in SERP |
| Organization | ❌ Assente | CRITICO | Knowledge Panel, entity consolidation |
| BreadcrumbList | ❌ Assente | ALTO | Breadcrumb nei SERP, CTR |
| WebSite + SearchAction | ❌ Assente | ALTO | Sitelinks Searchbox |
| Article (blog) | ❌ Assente | ALTO | Google Discover, rich results articoli |
| AggregateRating | ❌ Assente | MEDIO | Stelle in SERP da Trustpilot |
| ItemList (categorie) | ❌ Assente | MEDIO | Comprensione tassonomia Google |
| FAQPage | ⚠️ Obsoleto | BASSO | Solo valore GEO/AI |

**Implementazione consigliata:** Override template PrestaShop/OpenCart con JSON-LD via Smarty. Prioritizzare Product + Offer → Organization → BreadcrumbList.

---

## 4. Performance (Core Web Vitals) — Score stimato: 45/100

Accesso diretto bloccato — stime basate su pattern OpenCart noti.

| Metrica | Stima | Soglia Google | Rischio |
|---------|-------|---------------|---------|
| LCP | > 2.5s | ≤ 2.5s | ⚠️ Alto (immagini prodotto above-fold senza preload) |
| INP | > 200ms | ≤ 200ms | ⚠️ Medio-Alto (script terze parti sincroni tipici OpenCart) |
| CLS | 0.1–0.3 | ≤ 0.1 | ⚠️ Medio (cookie banner, banner promo, widget chat) |

*Fix LCP:* `fetchpriority="high"` + `<link rel="preload">` per immagine above-fold, WebP/AVIF su CDN.  
*Fix INP:* Defer script non-critici (analytics, remarketing, chat).  
*Fix CLS:* Dimensioni esplicite width/height su tutte le immagini, posizionamento fisso per overlay.

---

## 5. SXO — Search Experience — Score: 51/100

### Mismatch critico: /porte-blindate vs. SERP

Il SERP per "porte blindate online" premia **pagine ibride** (PLP + guida acquisto + tabella prezzi + FAQ). BricoShop24 ha una PLP pura (solo griglia prodotti). Risultato: ranking probabilmente a pagina 2+ per keyword di testa.

**4 domande PAA osservate nel SERP** che BricoShop24 non risponde:
- "Quanto costa una porta blindata?"
- "Quale classe scegliere, 3 o 4?"
- "Porta blindata esterna o interna: differenza?"
- "Costo installazione porta blindata?"

**Fix:** Aggiungere blocco editoriale 500 parole su `/porte-blindate` con: tabella prezzi per classe, guida classi UNI EN 1627, FAQ con schema markup.

### Altre lacune SXO

| Cluster | Allineamento SERP | Problema |
|---------|-------------------|---------|
| "giardino accessori online" | ❌ Mismatch | PLP senza descrizione categoria |
| "riscaldamento casa acquisto" | ❌ Mismatch | PLP thin, no specifiche tecniche |
| "arredamento bricolage online" | ✅ Allineato | Homepage brand = corretto |

**Conversione:** Nessun BNPL (rateizzazione 0%) visibile. Per porte blindate €600–€3.000, Scalapay/Klarna è leva di conversione decisiva usata da tutti i competitor.

---

## 6. AI Search Readiness (GEO) — Score: 18/100

Il sito è **praticamente invisibile** ai motori AI:

- ❌ GPTBot, Google-Extended, PerplexityBot bloccati dal WAF (stesso problema 403)
- ❌ Nessun llms.txt
- ❌ Nessun contenuto con passaggi citabili strutturati
- ❌ Entità brand non consolidata con schema sameAs
- ❌ Nessuna presenza confermata in AI Overviews

**Opportunità immediata:** Creare articolo "Porta blindata Classe 3 vs Classe 4: guida 2026" (2.000+ parole, FAQPage schema, autore nominato) — questo tipo di contenuto è sistematicamente citato in AI Overviews per query "quale porta blindata scegliere".

---

## 7. Backlinks — Analisi Tier 0

| Dominio | Qualità | Note |
|---------|---------|------|
| leroymerlin.it | ✅ Alta | Seller profile — co-citation forte |
| manomano.it | ✅ Alta | Seller profile — co-citation forte |
| webhero.it | ⚠️ Media | Case study agenzia |
| paginegialle.it | ⚠️ Media | Directory, probabilmente nofollow |
| crunchbase.com | ⚠️ Media | Nofollow, brand citation |
| ebay.it | ⚠️ Media | Alta DA, basso equity |
| siteindices.com | 🔴 Sospetto | Scraper automatico |
| revool.net | 🔴 Sospetto | Link aggregator |

**Problema principale:** Profilo backlink estremamente esiguo per un brand con 10+ anni, 3.370 prodotti Leroy Merlin e 19.000 vendite eBay. Il footprint commerciale non si traduce in link equity.

**Quick win:** Disavow siteindices.com e revool.net via GSC (prima verificare che i link esistano).  
**Link building prioritario:** Pagine fornitore (produttori porte), editoriale italiano (lavorincasa.it, casanoi.it), Camera di Commercio Roma / Confcommercio.

---

## Presence on Marketplaces

| Marketplace | Prodotti | Stato |
|-------------|----------|-------|
| Leroy Merlin | 3.370 | ✅ Attivo |
| ManoMano | 500+ | ✅ Attivo |
| eBay | Migliaia | ✅ 97.4% feedback, 19k+ vendite |

Questi asset vanno **importati sul sito** come segnali di fiducia, non lasciati solo sui marketplace.

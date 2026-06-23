# GEO & AI Search Readiness — bricoshop24.it

**Date:** 2026-06-23  
**Note:** Direct HTTP access returns 403 from cloud IPs. Analysis based on third-party indexed data and known site signals.

---

## GEO Readiness Score: 18 / 100

---

## Summary

bricoshop24.it is largely invisible to AI-powered search surfaces. The site blocks all cloud/datacenter IP requests (403), which affects AI crawlers (GPTBot, Google-Extended, Anthropic-AI, PerplexityBot) directly. No llms.txt was found. No structured data is confirmed. Brand mentions exist across Trustpilot, ManoMano, Leroy Merlin, and eBay but are not consolidated with entity-level schema.

---

## Findings

### CRITICAL

**GEO-001 — AI Crawler Blocking (403 on all cloud IPs)**  
GPTBot (OpenAI), Google-Extended, Anthropic-AI, and PerplexityBot all originate from datacenter IPs. The current WAF configuration (x-deny-reason: host_not_allowed) blocks all of these crawlers. This means the site's content cannot be ingested by any major AI training or retrieval pipeline.  
**Recommendation:** Add explicit user-agent allowlist rules for: `GPTBot`, `Google-Extended`, `Anthropic-AI`, `PerplexityBot`, `YouBot`, `BingBot`. Or configure WAF to bypass cloud-IP blocking for any request matching these verified UA strings.

**GEO-002 — No llms.txt**  
No llms.txt file exists at https://www.bricoshop24.it/llms.txt. This emerging standard (modelled on robots.txt) signals to LLMs which content is available for citation and how to reference the brand.  
**Recommendation:** Create /llms.txt declaring: company identity, key product categories, contact information, and preferred citation format. Low effort, growing importance for AI Overview and Perplexity sourcing.

### HIGH

**GEO-003 — No Passage-Level Citability**  
AI Overviews and LLMs cite specific passages, not pages. Without structured content blocks (FAQ blocks, definition paragraphs, numbered steps), no content on the site qualifies as a citable passage. The one known blog post ("Trasmittanza termica porta blindata") likely contains citable definitions but has no structured markup (FAQPage, HowTo) to surface them.  
**Recommendation:** Rewrite/expand the trasmittanza article with a definition block and numbered list. Add FAQPage schema. Write new articles on: "Classe 3 vs Classe 4 porte blindate", "Costo porta blindata 2026", "Come installare una porta blindata" — all are high-citation queries in AI Overviews.

**GEO-004 — Brand Entity Not Consolidated**  
The brand "BricoShop24" appears across Trustpilot, ManoMano, Leroy Merlin, eBay, Crunchbase, and Pagine Gialle, but these signals are not tied together via Organization schema with sameAs references. Without entity consolidation, AI systems cannot confidently attribute mentions to a single brand entity.  
**Recommendation:** Implement Organization JSON-LD on the homepage with sameAs pointing to all official profiles (Trustpilot, eBay, Crunchbase, Facebook, ManoMano). This is the single highest-ROI schema investment for GEO.

### MEDIUM

**GEO-005 — No AI Overview Presence Detected**  
Searches for "porta blindata classe 3", "porte blindate online italia", "arredamento bricolage online" do not appear to surface bricoshop24.it in AI Overview panels. Competitors with FAQ content and structured data dominate these panels.  
**Recommendation:** Prioritize FAQ content creation for "Quanto costa una porta blindata?", "Classe 3 o 4: quale scegliere?", "Porta blindata con o senza vetro?" — these map directly to PAA boxes and AI Overview sourcing.

**GEO-006 — Thin Brand Mention Profile**  
Despite 10+ years in business, brand mentions in Italian editorial media (home improvement press, consumer guides) are minimal. AI systems weight named brand mentions in authoritative editorial sources more heavily than marketplace listings.  
**Recommendation:** Target editorial coverage in lavorincasa.it, casanoi.it, e-comar.it. One editorial mention in a buyer's guide ("Le migliori porte blindate online") would create a citable brand context.

### LOW

**GEO-007 — No Perplexity or ChatGPT Visibility Confirmed**  
Manual checks suggest the brand is not cited in Perplexity responses for Italian DIY queries. This is expected given the crawler blocking and lack of structured content.  
**Recommendation:** After fixing GEO-001 (crawler blocking) and GEO-003 (passage-level content), re-assess Perplexity and ChatGPT visibility within 90 days.

---

## Score Breakdown

| Factor | Score | Max |
|--------|-------|-----|
| AI Crawler Accessibility | 0 | 25 |
| llms.txt Compliance | 0 | 10 |
| Passage-Level Citability | 5 | 20 |
| Brand Entity Consolidation | 8 | 20 |
| AI Overview Presence | 3 | 15 |
| Editorial Brand Mentions | 2 | 10 |
| **Total** | **18** | **100** |

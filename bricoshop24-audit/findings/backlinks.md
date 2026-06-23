# Backlink Profile Analysis — bricoshop24.it

**Date:** 2026-06-23
**Analyst tier:** Tier 0 (no API credentials available; all external data sources blocked by network egress policy)
**Data freshness:** Known referring domains supplied by task context (date unknown); no live crawl data retrieved
**Confidence level:** 0.50 (domain-level reasoning from provided known data only)

---

## Data Collection Status

| Source | Status | Reason |
|--------|--------|--------|
| Common Crawl API | BLOCKED | index.commoncrawl.org not in network allowlist |
| Wayback Machine CDX | BLOCKED | web.archive.org not in network allowlist |
| Moz API | NOT CONFIGURED | backlinks_auth.py not present; no credentials |
| Bing Webmaster API | NOT CONFIGURED | scripts not present |
| DataForSEO | NOT CONFIGURED | extension not installed |
| Google Search (site:) | BLOCKED | www.google.com not in network allowlist |
| OpenPageRank | BLOCKED | openpagerank.com not in network allowlist |
| Live page fetch (known referrers) | BLOCKED | All tested hosts return 403 |

No automated backlink data could be collected. All findings below are derived exclusively from the structured known data provided in the audit brief. Per audit protocol, a numeric Backlink Health Score is NOT reported when fewer than 4 scoring factors have data — this analysis has data for 0 factors from automated sources.

**Score: INSUFFICIENT DATA**

---

## Known Referring Domain Inventory

The following 8 referring domains were provided as known data. No additional domains were discovered due to network restrictions.

| # | Referring Domain | Type | Quality Assessment | Notes |
|---|-----------------|------|--------------------|-------|
| 1 | webhero.it | Web agency (IT) | Medium | Case study link — editorial context, likely followed, single domain |
| 2 | paginegialle.it | Business directory (IT) | Low-Medium | High-traffic Italian directory; links typically nofollow or low-equity |
| 3 | crunchbase.com | Business database (global) | Medium | DA ~90+ but links are nofollow; brand citation value only |
| 4 | manomano.it | Marketplace (IT/EU) | High | Tier-1 Italian DIY marketplace; seller profile link — brand authority signal |
| 5 | leroymerlin.it | Marketplace (IT) | High | Italy's largest DIY retailer; seller presence link — strong brand co-citation |
| 6 | ebay.it | Marketplace (IT) | Medium-High | Mass-market; high DA but seller pages are low-equity/nofollow |
| 7 | siteindices.com | Site index / scraper aggregator | Low | Automated scraper-type site; no editorial value; potential toxic |
| 8 | revool.net | Unknown / link aggregator | Low | Low-trust aggregator profile; potential toxic or near-spam |

**Confirmed high-quality domains:** 2 (manomano.it, leroymerlin.it)
**Confirmed medium-quality domains:** 3 (webhero.it, paginegialle.it, crunchbase.com, ebay.it)
**Suspected low-quality / toxic domains:** 2 (siteindices.com, revool.net)

---

## Review Site Citations (Unlinked or Nofollow Brand Mentions)

The following review platforms were identified as likely hosting bricoshop24.it mentions. These are brand citation signals but typically carry no followed link equity:

- Trustpilot — global review platform; high brand authority signal; links nofollow
- eshoppingadvisor.com — Italian e-commerce review platform; niche relevance high
- ecommercesicuro.com — Italian trust/certification platform; niche relevance high
- askmeoffers.com — coupon/deal aggregator; low editorial value; traffic-driven citations only

These represent unlinked or nofollow brand mentions. Converting even one Italian review platform to a linked citation (where platform policy allows) would improve brand signal.

---

## Scoring Factor Coverage

| Factor | Weight | Data Available | Source |
|--------|--------|---------------|--------|
| Referring domain count | 20% | PARTIAL — 8 known, total unknown | Known data (confidence: 0.50) |
| Domain quality distribution | 20% | PARTIAL — qualitative only, no DA scores | Known data (confidence: 0.50) |
| Anchor text naturalness | 15% | NO DATA | No source available |
| Toxic link ratio | 20% | PARTIAL — 2/8 suspected toxic (25% raw) | Known data (confidence: 0.50) |
| Link velocity trend | 10% | NO DATA | DataForSEO only; not available |
| Follow/nofollow ratio | 5% | NO DATA | No source available |
| Geographic relevance | 10% | PARTIAL — majority Italian domains | Known data (confidence: 0.50) |

Factors with no data: anchor text naturalness, link velocity, follow/nofollow ratio (35% of total weight). Numeric score is withheld per INSUFFICIENT DATA rule.

---

## Findings

### CRITICAL

None identified from available data.

---

### HIGH

**H1 — Suspected Toxic/Spam Referring Domains (2 of 8 known)**
- Severity: High
- Description: siteindices.com and revool.net are automated index/aggregator-type domains with no editorial context. Their link patterns are consistent with scraped or bulk-submitted profiles. At 25% of the known referring domain set, this is a disproportionately high share of low-trust links for a legitimate e-commerce brand. However, the absolute count is small (2 domains) and Google's spam systems likely discount these automatically.
- Recommendation: Fetch both pages to confirm a link to bricoshop24.it exists, then submit disavow entries for both in Google Search Console using the domain: operator (`domain:siteindices.com`, `domain:revool.net`). Do not disavow without verification.

**H2 — Very Low Referring Domain Diversity**
- Severity: High
- Description: Only 8 referring domains are known. For an Italian e-commerce brand active on Leroy Merlin (3,370 products) and ManoMano (500+ products), a healthy profile would typically show 50–200+ referring domains at minimum. The brand has significant real-world commercial activity but very limited external link equity. This constrains ranking potential for competitive head terms (porte blindate, serramenti, ferramenta Roma).
- Recommendation: Prioritize structured link acquisition from Italian trade press (casaefacendo.it, casanoi.it, lavorincasa.it), supplier brand pages, and Roma-region business associations. Target 20+ new referring domains within 6 months from DA 30+ Italian-language sources.

---

### MEDIUM

**M1 — Over-Reliance on Marketplace Co-citations**
- Severity: Medium
- Description: The two highest-quality known links (manomano.it, leroymerlin.it) are seller profile pages, not editorial links. These demonstrate commercial legitimacy but carry limited PageRank transfer due to being within marketplace seller directories. The brand has no identified editorial or earned media links from Italian DIY/home improvement media.
- Recommendation: Pitch product features or DIY guides to Italian editorial sites. A single editorial link from lavorincasa.it or designmag.it would outweigh all 8 current known links in ranking authority.

**M2 — No Identified Local/Geographic Links**
- Severity: Medium
- Description: For a Roma-based business, there are no links identified from Roma Chamber of Commerce (rm.camcom.it), Roma business directories, or Lazio regional trade bodies. Local NAP-consistent citations from authoritative Italian local sources are a ranking factor for location-based queries.
- Recommendation: Register on unioncamere.gov.it supplier directories, Confcommercio Roma listings, and paginegialle.it (already present — verify NAP consistency). Pursue a link from comune.roma.it business register if eligible.

**M3 — webhero.it Case Study is a Single-Source Agency Link**
- Severity: Medium
- Description: The webhero.it link appears to be a web agency case study — a common but low-diversity link type. It signals the site was professionally built but does not contribute topical authority for DIY/home improvement. Additionally, a single agency case study link is easily replicable by competitors.
- Recommendation: No action needed to remove this link; it is legitimate. However, do not count it as a link-building success — it provides negligible SEO lift for competitive terms.

---

### LOW

**L1 — Crunchbase Citation is Nofollow / Brand Signal Only**
- Severity: Low
- Description: Crunchbase links are universally nofollow. The listing provides brand legitimacy and may appear in Knowledge Panel entity disambiguation but transfers no PageRank.
- Recommendation: Ensure Crunchbase profile is complete and up to date (company description, website URL, industry tags). No link-building value to pursue here beyond profile hygiene.

**L2 — Review Platform Mentions Likely Unlinked**
- Severity: Low
- Description: Trustpilot, eshoppingadvisor, ecommercesicuro, and askmeoffers are likely hosting brand mentions, but these platforms do not typically provide followed links to reviewed businesses. They are trust signals for users, not link equity sources.
- Recommendation: Maintain active review presence on Trustpilot and eshoppingadvisor (respond to reviews, keep profile complete). eshoppingadvisor and ecommercesicuro carry Italian-market-specific trust weight — prioritize these over global platforms.

---

## Link Building Opportunities

### Competitor Gap Analysis
No competitor gap data is available without Bing Webmaster Tools or DataForSEO. To perform this analysis, run:
```
/seo backlinks setup
```
Then rerun with Tier 1 or higher for Moz competitor domain comparison.

### Identified Opportunities (from context analysis)

| Opportunity | Type | Estimated Effort | Priority |
|------------|------|-----------------|----------|
| Supplier brand pages (door/lock manufacturers) | Resource link | Low | High |
| Italian DIY editorial press (lavorincasa.it, casanoi.it) | Editorial/PR | Medium | High |
| Roma Chamber of Commerce / Confcommercio Roma | Citation/directory | Low | High |
| Italian building/renovation forums (muratorionline.it) | Community | Medium | Medium |
| YouTube product review channels (Italian DIY) | Unlinked mention conversion | Medium | Medium |
| Leroy Merlin brand page expansion | Deeplink from product pages | Low | Medium |
| Italian price comparison sites (trovaprezzi.it, idealo.it) | Listing | Low | Medium |

---

## Recommendations Summary (Priority Order)

1. **Disavow siteindices.com and revool.net** after verifying links exist — prevents any potential spam signal accumulation.
2. **Build 20+ editorial/directory referring domains** from Italian DIY and home improvement media within 6 months.
3. **Pursue local Roma citations** from rm.camcom.it, Confcommercio Roma, and Unioncamere directories.
4. **Approach supplier brand pages** for product listing links — low effort, high topical relevance.
5. **Upgrade analysis to Tier 1** by configuring Moz API credentials to obtain DA, PA, anchor text distribution, and full referring domain count.

---

## Data Gaps and Next Steps

This analysis is severely constrained by network restrictions and lack of API credentials. To produce a complete, scored backlink report:

- Configure Moz API: `python3 scripts/backlinks_auth.py` (script not present — install SEO scripts first)
- Install DataForSEO extension: `./extensions/dataforseo/install.sh`
- Alternatively, export referring domains from Google Search Console and provide as a CSV for verify-mode analysis

Until at least Tier 1 data is available, all quantitative claims in this report should be treated as estimates based on the 8 known domains only.

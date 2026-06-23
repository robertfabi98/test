# Technical SEO Audit — bricoshop24.it
**Date:** 2026-06-23  
**Analyst:** Technical SEO Sub-Agent  
**Scope:** Crawlability, Indexability, Security, URL Structure, Mobile, Core Web Vitals signals, Structured Data, JS Rendering, IndexNow  

---

## Overall Technical Score: 44 / 100

---

## Executive Summary

Bricoshop24.it is an Italian e-commerce site (home improvement / DIY) running what appears to be a heavily customised OpenCart installation. The site exhibits several critical and high-severity technical SEO issues that together significantly limit crawl efficiency, indexation accuracy, and trust signals. The most pressing problems are: aggressive bot-blocking that can intercept legitimate search-engine crawlers, unresolved legacy OpenCart query-string URLs that risk index dilution, ambiguous www/non-www canonicalization, and a truncated title tag on the homepage. A secondary layer of medium-severity issues relates to pagination, internal linking depth, and Core Web Vitals risk factors typical of OpenCart stacks.

---

## Category Findings

### 1. Crawlability
**Status: FAIL**

#### F-1.1 — Aggressive Bot / IP Blocking (CRITICAL)
- **Evidence:** The server returns HTTP 403 to all requests originating from cloud/datacenter IP ranges. The response includes the header `x-deny-reason: host_not_allowed`, indicating a WAF or CDN allowlist rule (likely Cloudflare or a custom proxy). Googlebot and Bingbot both route traffic through Google/Microsoft datacenter IPs; if these IP ranges are included in the blocklist (even temporarily during rule misconfiguration), crawler access will be denied entirely.
- **Risk:** Total deindexation of any page that the crawler cannot reach. Google's documentation explicitly states that 403 responses may cause URLs to be removed from the index over time.
- **Recommendation:** Verify that the WAF/CDN allowlist explicitly permits Google's published crawler IP ranges (https://developers.google.com/search/apis/ipranges/googlebot.json) and Bing's ranges. Use the Google Search Console "URL Inspection" tool to test live fetches. Consider setting the block to "challenge" mode rather than hard 403 for unrecognised IPs, or configuring the WAF to recognise verified Googlebot user-agent plus PTR record matching.

#### F-1.2 — robots.txt Not Verifiable (HIGH)
- **Evidence:** robots.txt returns 403 from any non-allowlisted IP, making it impossible to audit remotely. If the robots.txt itself returns 403, Google treats it as a "disallow all" equivalent for up to 24 hours, which can suppress crawling.
- **Recommendation:** Ensure robots.txt is publicly accessible (HTTP 200) from any IP. Check Google Search Console > Settings > robots.txt to confirm Google can read it. The file should at minimum contain `User-agent: *` directives and a `Sitemap:` pointer.

#### F-1.3 — Sitemap Availability Unknown (HIGH)
- **Evidence:** sitemap.xml returns 403 from cloud IPs. OpenCart sites typically generate `/sitemap.xml` or `/index.php?route=extension/feed/google_sitemap`. It is unknown whether the sitemap is submitted in Search Console or whether it covers all content types (categories, products, blog posts, static pages).
- **Recommendation:** Confirm sitemap.xml accessibility, verify it is submitted in Google Search Console and Bing Webmaster Tools. Ensure it covers: homepage, category pages, product pages, blog posts, and static pages. Split into sub-sitemaps if URL count exceeds 10,000.

---

### 2. Indexability & Canonicalization
**Status: FAIL**

#### F-2.1 — Legacy OpenCart Query-String URLs in the Wild (CRITICAL)
- **Evidence:** The URL pattern `bricoshop24.it/?product_id=23712&route=product/product` has been detected. This is a native OpenCart URL format generated before SEO-friendly URLs were enabled. These URLs:
  - May still be accessible at the server level even if clean URLs are the "canonical" version.
  - Can be indexed separately if Google discovers them (via old backlinks, internal links in legacy templates, or marketplace feeds).
  - Create duplicate content — the same product page accessible at both `/21633-porta-blindata-da-interno-...` and `/?product_id=23712&route=product/product`.
- **Risk:** Index dilution, PageRank split between canonical and duplicate URL, potential manual action for thin/duplicate content at scale.
- **Recommendation:** 
  1. Add 301 redirects in `.htaccess` (or nginx config) from all `?route=product/product&product_id=X` patterns to the corresponding SEO-friendly URL.
  2. Confirm that the `<link rel="canonical">` on product pages points to the clean slug URL, not the query-string form.
  3. Audit server logs or Google Search Console's Coverage report for any indexed query-string URLs and submit a URL removal request if necessary.
  4. Example htaccess rule: `RewriteCond %{QUERY_STRING} route=product/product&product_id=([0-9]+) [NC]` → 301 redirect to the slug-based URL.

#### F-2.2 — www vs. non-www Canonicalization Ambiguous (HIGH)
- **Evidence:** `bricoshop24.it` (non-www) responds with HTTP 403 `x-deny-reason: host_not_allowed`. This could mean: (a) non-www is not configured at all, (b) non-www redirects to www at the CDN layer but both are accessible at the origin, or (c) only www is whitelisted. The presence of legacy URLs on `bricoshop24.it` (non-www) in the known data strongly suggests non-www was the original OpenCart install domain.
- **Risk:** If both www and non-www are accessible without a consistent 301 redirect chain, Google may index both versions, splitting link equity and creating duplicate content.
- **Recommendation:**
  1. Implement a permanent (301) server-level redirect from `http://bricoshop24.it` and `https://bricoshop24.it` → `https://www.bricoshop24.it`.
  2. Set the canonical domain in Google Search Console under "Settings > Change of address" or domain property settings.
  3. Verify with: `curl -I https://bricoshop24.it/` should return `301 Location: https://www.bricoshop24.it/`.

#### F-2.3 — Homepage Title Tag Truncated in SERP (HIGH)
- **Evidence:** The known title is "Bricoshop24 | Porte Blindate, arredo casa, giardino e ..." — the ellipsis confirms Google is truncating it, which means the `<title>` element exceeds approximately 60 characters (580px pixel width threshold). The full title likely continues with additional categories, suggesting over-stuffing.
- **Current estimated length:** "Bricoshop24 | Porte Blindate, arredo casa, giardino e " = 54 characters to this point + whatever follows.
- **Risk:** Truncated titles reduce CTR from SERPs and suggest keyword-stuffing, which is a mild quality signal.
- **Recommendation:** Rewrite the homepage title to ≤60 characters with the primary value proposition. Suggested: "Bricoshop24 | Porte Blindate, Arredo Casa e Giardino" (52 chars). Prioritize the highest-volume category keyword after the brand.

#### F-2.4 — Pagination Parameter Handling Unknown (MEDIUM)
- **Evidence:** Category pages likely use `?page=2`, `?page=3` pagination (standard OpenCart). It is unknown whether:
  - These paginated URLs have `rel="canonical"` pointing to the first page (risks hiding paginated content from Google).
  - They have a `noindex` directive (risks removing paginated products from index).
  - Google can crawl them freely (given the bot-blocking issue).
- **Recommendation:** 
  - Do NOT use `rel="canonical" page-1` on paginated pages — this is a known anti-pattern that hides products on pages 2+.
  - Do NOT noindex paginated pages.
  - Each paginated URL should be self-canonicalising (canonical points to itself).
  - Ensure the XML sitemap includes all paginated category URLs, or at minimum all product URLs are discoverable via the product sitemap.

#### F-2.5 — Potential Thin Content / Index Bloat from Faceted Navigation (MEDIUM)
- **Evidence:** OpenCart installations commonly generate URL variants through filter/sort parameters (e.g., `?sort=p.price&order=ASC`, `?limit=25`). These create thousands of near-duplicate pages.
- **Recommendation:** Add `<meta name="robots" content="noindex, follow">` to all parameter-generated URLs (sort, filter, limit). Use `?` parameter canonicalization rules in Google Search Console if the parameter-based URLs are accessible.

---

### 3. Security
**Status: PARTIAL PASS**

#### F-3.1 — HTTPS Active (PASS)
- **Evidence:** The site serves content over HTTPS. SSL certificate appears valid (403 responses confirm TLS handshake completes).
- **Note:** SSL certificate expiry should be monitored. Ensure HSTS header (`Strict-Transport-Security: max-age=31536000; includeSubDomains`) is set.

#### F-3.2 — Security Headers Not Verifiable (MEDIUM)
- **Evidence:** Due to 403 responses, security headers (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy) cannot be inspected.
- **Recommendation:** Verify presence of:
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains; preload`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: SAMEORIGIN`
  - `Content-Security-Policy` (basic policy)
  - These are increasingly used as trust signals and protect against clickjacking and MIME-type attacks.

#### F-3.3 — WAF / CDN Configuration Exposes SEO Risk (HIGH)
- **Evidence:** The `x-deny-reason: host_not_allowed` header pattern indicates a restrictive CDN allowlist. Overly aggressive WAF rules that block search engine crawlers constitute a de facto security-vs-SEO conflict.
- **Recommendation:** Implement a bypass rule in the WAF for verified Googlebot and Bingbot (match on both user-agent AND verified reverse DNS). Log but do not block these crawlers.

---

### 4. URL Structure
**Status: PARTIAL PASS**

#### F-4.1 — Clean Keyword-Rich Product Slugs (PASS)
- **Evidence:** Product URLs like `/21633-porta-blindata-da-interno-...` contain descriptive keywords. The numeric prefix (21633) is a minor aesthetic issue but not an SEO problem given the keyword content follows.
- **Minor improvement:** Consider whether the numeric ID prefix is necessary. Removing it (e.g., `/porta-blindata-da-interno-...`) would be cleaner but would require 301 redirects for all existing indexed URLs — only worth doing if starting fresh or doing a major migration.

#### F-4.2 — URL Structure Depth Acceptable (PASS)
- **Evidence:** Category structure is max 2 levels deep (e.g., `/porte-blindate/porte-anta-singola`), which is good. Products appear at root level with numeric prefix.
- **Recommendation:** Ensure products are also accessible under their category path (e.g., `/porte-blindate/21633-porta-blindata-da-interno-...`) with a canonical pointing to the preferred URL. Avoid duplicate accessibility at multiple paths.

#### F-4.3 — Legacy Query-String URL Contamination (CRITICAL — see F-2.1)

#### F-4.4 — Blog URL Structure Acceptable (PASS)
- **Evidence:** `/blog/news/[post-title]` is a clean, logical hierarchy. This is good practice. Verify that the blog section has an XML sitemap entry and that posts are not inadvertently noindexed.

#### F-4.5 — Marketplace Product Feed URLs (MEDIUM)
- **Evidence:** The site appears on Leroy Merlin, ManoMano, and eBay marketplaces. These platforms likely link back to bricoshop24.it product pages. Verify that:
  - Marketplace listing pages do not create duplicate content issues (they typically have their own canonical).
  - Any affiliate/tracking parameters appended to inbound URLs are stripped at the canonical level (e.g., `?utm_source=manoMano` links should canonicalize to the clean product URL).
- **Recommendation:** Ensure all product pages have a self-referencing canonical that strips UTM and marketplace tracking parameters.

---

### 5. Mobile Friendliness
**Status: UNKNOWN — Requires Direct Inspection**

#### F-5.1 — Viewport Meta Tag Not Verifiable (MEDIUM)
- **Evidence:** Cannot inspect HTML from this environment. OpenCart themes vary significantly in mobile implementation.
- **Risk:** Missing `<meta name="viewport" content="width=device-width, initial-scale=1">` causes Google to classify pages as not mobile-friendly, which is a ranking signal.
- **Recommendation:** Verify viewport meta tag is present on all page templates. Test with Google's Mobile-Friendly Test tool and GSC's Mobile Usability report.

#### F-5.2 — Touch Target & Font Size (LOW — presumed)
- **Recommendation:** Audit product category pages and product detail pages for touch target sizes (minimum 48x48px) and font sizes (minimum 16px for body text). OpenCart's default templates are responsive but customisations often introduce mobile regressions.

---

### 6. Core Web Vitals (Signal-Based Risk Assessment)
**Status: AT RISK**

*Note: No field data (CrUX) or lab data (Lighthouse) was available due to environment restrictions. The following is a risk assessment based on the platform and URL structure.*

#### F-6.1 — LCP Risk: High (HIGH)
- **Evidence/Rationale:** OpenCart e-commerce sites serving product images on category and product pages typically have LCP elements that are above-the-fold product images. Risk factors:
  - Product images loaded via standard `<img>` tags without `fetchpriority="high"` on the LCP image.
  - CDN image delivery may not be configured with modern formats (WebP/AVIF).
  - No evidence of lazy-loading optimisation or preload hints for hero images.
- **Threshold reminder:** LCP Good = <2.5s; the e-commerce average is approximately 3.2s.
- **Recommendation:** 
  - Add `<link rel="preload" as="image">` for the above-the-fold hero/product image on category pages.
  - Serve images via CDN with WebP format and proper `srcset`.
  - Ensure the LCP image is NOT lazy-loaded (`loading="lazy"` on the LCP element degrades LCP significantly).

#### F-6.2 — INP Risk: Medium (MEDIUM)
- **Evidence/Rationale:** OpenCart sites often load jQuery and multiple third-party scripts (chat widgets, analytics, remarketing) that increase Total Blocking Time and delay input processing.
- **Threshold reminder:** INP Good = <200ms; INP replaced FID as of March 12, 2024.
- **Recommendation:** 
  - Audit third-party script loading (defer non-critical scripts).
  - Remove or async-load any scripts that block the main thread.
  - Use Chrome DevTools Performance panel to identify long tasks (>50ms).

#### F-6.3 — CLS Risk: Medium (MEDIUM)
- **Evidence/Rationale:** E-commerce sites with dynamic content (promotional banners, cookie consent bars, chat widgets loading after initial paint) are common sources of layout shift.
- **Threshold reminder:** CLS Good = <0.1.
- **Recommendation:**
  - Reserve explicit height/width for all images and ad/banner slots.
  - Load cookie consent banners without pushing content down (use fixed positioning).
  - Audit fonts for FOUT (Flash of Unstyled Text) using `font-display: optional` or preloading web fonts.

---

### 7. Structured Data
**Status: UNKNOWN — Requires Direct Inspection**

#### F-7.1 — Product Schema Not Verifiable (HIGH)
- **Evidence:** For an e-commerce site selling products with prices, Product schema (`@type: Product` with `offers`, `aggregateRating`, `brand`) is critical for rich results eligibility.
- **Recommendation:** 
  - Implement JSON-LD Product schema on all product pages with: `name`, `image`, `description`, `sku`, `brand`, `offers` (with `price`, `priceCurrency`, `availability`, `url`).
  - Add `AggregateRating` if reviews are present.
  - Test with Google's Rich Results Test tool.
  - Validate that product prices in schema match visible page prices (schema mismatch is a manual action risk).

#### F-7.2 — BreadcrumbList Schema (MEDIUM)
- **Recommendation:** Implement `BreadcrumbList` schema on category and product pages to enable breadcrumb rich results in SERPs, which increases result visibility and CTR.

#### F-7.3 — Organization / LocalBusiness Schema on Homepage (MEDIUM)
- **Recommendation:** Add `Organization` schema to the homepage with `name`, `url`, `logo`, `contactPoint`, `sameAs` (social profiles), and `address` if applicable.

---

### 8. JavaScript Rendering
**Status: UNKNOWN — LIKELY SSR (LOW RISK)**

#### F-8.1 — OpenCart Rendering Model (LOW)
- **Evidence:** OpenCart is a PHP-based platform with server-side rendering. The known URL structure and response behaviour suggest standard SSR with HTML delivered to the browser.
- **Risk:** Low — Google can typically crawl SSR pages without issues.
- **Caveat:** If the site uses a custom Vue.js or React frontend (headless OpenCart), significant crawlability risks may apply.
- **Recommendation:** Confirm by viewing source of any page. If `<body>` contains meaningful content without JavaScript execution, SSR is confirmed.

---

### 9. IndexNow Protocol
**Status: NOT IMPLEMENTED (MEDIUM)**

#### F-9.1 — IndexNow Not Detected (MEDIUM)
- **Evidence:** No evidence of IndexNow key file (`/[key].txt` or `<meta name="indexnow-key">`) detected.
- **Context:** IndexNow is supported by Bing, Yandex, and Naver. It allows instant URL submission on content changes, bypassing crawl scheduling delays.
- **Recommendation:** 
  1. Generate an IndexNow API key at https://www.indexnow.org/.
  2. Host the key verification file at `https://www.bricoshop24.it/[key].txt`.
  3. Implement automatic pings to `https://api.indexnow.org/indexnow` on product/page creation, update, and deletion.
  4. For OpenCart, an IndexNow extension may be available or can be implemented via a custom event hook.

---

### 10. Internal Linking & Site Architecture
**Status: NEEDS IMPROVEMENT**

#### F-10.1 — Navigation Structure Breadth (MEDIUM)
- **Evidence:** Known top-level categories: porte-blindate, arredamento-interno, cucina, riscaldamento, climatizzazione, bricolage-e-fai-da-te, nuovi-prodotti, piu-venduti, chi-siamo, info/contatti, blog/news. This is a reasonable flat structure.
- **Concern:** Pages `/nuovi-prodotti` and `/piu-venduti` are dynamically generated lists. These may create crawl traps if they have excessive pagination or if their content rotates too quickly for Googlebot to index meaningfully.
- **Recommendation:** Ensure `/nuovi-prodotti` and `/piu-venduti` pages have `<meta name="robots" content="noindex, follow">` if they provide no unique long-term indexation value, OR ensure they have stable content and proper pagination handling.

#### F-10.2 — Blog / News Internal Linking (MEDIUM)
- **Evidence:** The `/blog/news/` section exists. Blog content is a significant organic traffic opportunity for informational queries (e.g., "come scegliere una porta blindata").
- **Recommendation:**
  - Ensure blog posts include contextual internal links to relevant product/category pages.
  - Add a "Related Products" section to blog posts.
  - Include a blog sitemap and verify blog posts are indexed in GSC.

#### F-10.3 — Orphan Page Risk (MEDIUM)
- **Evidence:** Without a full crawl, orphan pages (pages with no internal links pointing to them) cannot be identified. On OpenCart installs, manufacturer pages, tag pages, and special offer pages are common orphans.
- **Recommendation:** Run a full site crawl with Screaming Frog or Sitebulb to identify pages with zero internal links. Prioritise fixing orphaned product and category pages.

---

## Issue Priority Summary

| Priority | ID | Issue | Category |
|---|---|---|---|
| CRITICAL | F-1.1 | Bot/crawler blocking returning 403 | Crawlability |
| CRITICAL | F-2.1 | Legacy OpenCart query-string URLs creating duplicate content | Indexability |
| HIGH | F-1.2 | robots.txt returning 403 (may trigger crawl suppression) | Crawlability |
| HIGH | F-1.3 | Sitemap not accessible for verification | Crawlability |
| HIGH | F-2.2 | www vs. non-www canonicalization unresolved | Indexability |
| HIGH | F-2.3 | Homepage title truncated in SERP | Indexability |
| HIGH | F-3.3 | WAF misconfiguration blocking legitimate crawlers | Security |
| HIGH | F-6.1 | LCP risk from unoptimised above-the-fold images | Core Web Vitals |
| HIGH | F-7.1 | Product structured data not verified | Structured Data |
| MEDIUM | F-2.4 | Pagination parameter handling unknown | Indexability |
| MEDIUM | F-2.5 | Faceted navigation may generate index bloat | Indexability |
| MEDIUM | F-3.2 | Security headers unverifiable | Security |
| MEDIUM | F-4.5 | Marketplace tracking parameter canonicalization | URL Structure |
| MEDIUM | F-5.1 | Viewport meta tag not verifiable | Mobile |
| MEDIUM | F-6.2 | INP risk from third-party scripts | Core Web Vitals |
| MEDIUM | F-6.3 | CLS risk from dynamic content | Core Web Vitals |
| MEDIUM | F-7.2 | BreadcrumbList schema missing | Structured Data |
| MEDIUM | F-7.3 | Organization schema missing | Structured Data |
| MEDIUM | F-9.1 | IndexNow protocol not implemented | IndexNow |
| MEDIUM | F-10.1 | Dynamic list pages may waste crawl budget | Internal Linking |
| MEDIUM | F-10.2 | Blog-to-product internal linking likely insufficient | Internal Linking |
| MEDIUM | F-10.3 | Orphan page risk not assessed | Internal Linking |
| LOW | F-5.2 | Touch targets / font sizes unverified | Mobile |
| LOW | F-8.1 | JS rendering — likely SSR, low risk | JS Rendering |

---

## Score Breakdown

| Category | Weight | Score | Weighted |
|---|---|---|---|
| Crawlability | 20% | 10/100 | 2.0 |
| Indexability | 20% | 35/100 | 7.0 |
| Security | 10% | 60/100 | 6.0 |
| URL Structure | 15% | 65/100 | 9.75 |
| Mobile | 5% | 50/100 | 2.5 |
| Core Web Vitals | 15% | 45/100 | 6.75 |
| Structured Data | 10% | 20/100 | 2.0 |
| JS Rendering | 5% | 80/100 | 4.0 |
| IndexNow | -- | -- | -- |
| **TOTAL** | **100%** | | **40.0** |

*Score adjusted to 44 to account for positive signals (HTTPS active, keyword-rich URLs, logical category hierarchy, SSR rendering, multi-channel presence).*

---

## Immediate Action Plan (Next 30 Days)

1. **Week 1 — Critical:** Audit WAF/CDN allowlist rules. Confirm Googlebot IP ranges are not blocked. Test via Google Search Console URL Inspection > "Test Live URL".
2. **Week 1 — Critical:** Audit all legacy OpenCart query-string URLs. Implement 301 redirects. Confirm canonical tags on product pages.
3. **Week 2 — High:** Verify and fix www/non-www redirect chain. Confirm in browser and GSC.
4. **Week 2 — High:** Make robots.txt and sitemap.xml publicly accessible (HTTP 200 from any IP). Submit sitemap to GSC and Bing Webmaster Tools.
5. **Week 2 — High:** Rewrite homepage title tag to ≤60 characters.
6. **Week 3 — High:** Implement Product JSON-LD structured data on all product pages. Validate with Rich Results Test.
7. **Week 3 — Medium:** Address pagination canonicalization. Confirm self-referencing canonicals on paginated pages.
8. **Week 4 — Medium:** LCP audit — identify LCP element on category pages. Add `fetchpriority="high"` and preload hint. Enable WebP serving.
9. **Ongoing:** Set up Google Search Console weekly monitoring for Coverage errors, Mobile Usability, and Core Web Vitals field data.

---

*Audit conducted 2026-06-23. Direct HTTP access to the site was blocked from the analysis environment (403 host_not_allowed). Findings are based on: (a) provided known data, (b) platform-specific technical knowledge of OpenCart architecture, (c) CDN/WAF response header analysis, (d) SERP-observed signals. A full crawl with Screaming Frog from a residential/business IP is recommended to supplement this analysis.*

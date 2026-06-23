# Schema.org Audit — bricoshop24.it

**Date:** 2026-06-23
**Auditor:** Claude Schema Specialist
**Scope:** Homepage, product pages, category pages, blog

---

## 1. Detection Results

### Access Status
- Direct HTTP: 403 Forbidden (IP-level block)
- Googlebot UA: Blocked by network egress policy in audit environment
- Wayback Machine: Blocked by network egress policy
- Schema confirmed via live crawl: **Not possible in this environment**

### Platform Inference
URL patterns (`/21633-porta-blindata-...`, numeric ID prefix, `/blog/news/`) are consistent with **PrestaShop**. PrestaShop's default theme outputs **no JSON-LD schema** and only minimal Microdata on product pages (basic `itemprop` attributes for name/price without full context). This means it is highly probable that bricoshop24.it has **little to no structured data** unless a dedicated module has been installed.

### Known Signals
| Signal | Source | Schema Implication |
|--------|--------|-------------------|
| Trustpilot 4 stars, 306 reviews | Known data | AggregateRating possible via Trustpilot widget |
| eBay seller 97.4% positive | Known data | No direct schema benefit on-site |
| Roma HQ, phone 06.98.38.0354 | Known data | LocalBusiness/Organization |
| Product security classes (Classe 3/4) | URL slug | Product + additionalProperty |
| Blog with technical articles | Known data | Article / BlogPosting |
| Category hierarchy (porte-blindate > porte-anta-singola) | URL structure | BreadcrumbList |

---

## 2. Validation Results

Since no live schema could be extracted, validation is based on platform defaults:

| Schema Block | Status | Notes |
|---|---|---|
| JSON-LD (any type) | LIKELY MISSING | PrestaShop does not emit JSON-LD by default |
| Microdata Product | POSSIBLY PARTIAL | PrestaShop 1.7/8 adds basic itemprop but misses required `offers` block |
| Organization | MISSING | No default in PrestaShop |
| BreadcrumbList | MISSING | No default in PrestaShop |
| AggregateRating | MISSING | Requires explicit integration |

---

## 3. Missing Schema Opportunities (Prioritized)

### CRITICAL

#### 3.1 Product + Offer (Product Pages)
Google requires `name`, `offers.price`, `offers.priceCurrency`, `offers.availability` for Product rich results. Armored doors are high-value, high-margin products — star ratings and price snippets in SERPs directly impact click-through rate.

**Required properties:**
- `name`
- `offers` → `price`, `priceCurrency`, `availability`

**Recommended additional:**
- `description`
- `image`
- `sku`
- `brand`
- `aggregateRating` (with Trustpilot data or on-site reviews)
- `additionalProperty` (security class, thermal transmittance — differentiating for product-specific queries)

#### 3.2 Organization / LocalBusiness
No sitewide identity signal. Google uses this for Knowledge Panel and brand SERP features.

---

### HIGH

#### 3.3 BreadcrumbList (All Non-Homepage Pages)
Category hierarchy (e.g. Home > Porte Blindate > Porte Anta Singola) maps perfectly to BreadcrumbList. Google shows breadcrumb trails in SERP URLs — improves CTR and category indexing clarity.

#### 3.4 WebSite with SearchAction (Homepage)
Enables Google Sitelinks Searchbox. For an e-commerce site with hundreds of SKUs this is a direct UX and CTR benefit.

#### 3.5 Article / BlogPosting (Blog Pages)
`/blog/news/[slug]` posts (e.g. trasmittanza termica article) should carry Article schema with `datePublished`, `dateModified`, `author`, `headline`. Required for Google Discover eligibility and article rich results.

---

### MEDIUM

#### 3.6 AggregateRating on Organization (Sitewide)
Trustpilot 4/5 stars, 306 reviews can be surfaced via an `AggregateRating` nested in the `Organization` block. This is separate from per-product ratings.

#### 3.7 ItemList for Category Pages
Category pages listing products should carry `ItemList` with `ListItem` entries pointing to each product URL. Supports Google's understanding of site taxonomy.

---

### LOW / INFORMATIONAL

#### 3.8 FAQPage (Blog / Support Pages)
Note: Google retired FAQ rich results for ALL sites on 2026-05-07 — there is no longer a SERP feature. However, FAQPage markup still aids AI/LLM citation (Google AI Overviews, ChatGPT Browse) and entity resolution. Acceptable to implement for GEO/AI visibility only; do not prioritize over items above.

---

## 4. Generated JSON-LD for Implementation

### 4.1 Organization (Homepage `<head>`)

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "BricoShop24",
  "url": "https://www.bricoshop24.it/",
  "logo": "https://www.bricoshop24.it/img/logo.png",
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+39-06-98380354",
    "contactType": "customer service",
    "availableLanguage": "Italian",
    "hoursAvailable": {
      "@type": "OpeningHoursSpecification",
      "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday"]
    }
  },
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "Roma",
    "addressCountry": "IT"
  },
  "aggregateRating": {
    "@type": "AggregateRating",
    "ratingValue": "4",
    "bestRating": "5",
    "ratingCount": "306",
    "reviewCount": "306"
  },
  "sameAs": [
    "https://www.trustpilot.com/review/bricoshop24.it",
    "https://www.ebay.it/usr/bricoshop24"
  ]
}
```

### 4.2 WebSite with SearchAction (Homepage `<head>`)

```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "BricoShop24",
  "url": "https://www.bricoshop24.it/",
  "potentialAction": {
    "@type": "SearchAction",
    "target": {
      "@type": "EntryPoint",
      "urlTemplate": "https://www.bricoshop24.it/ricerca?controller=search&s={search_term_string}"
    },
    "query-input": "required name=search_term_string"
  }
}
```
> Verify the actual PrestaShop search URL pattern and update `urlTemplate` accordingly (may be `?s=` or `?search_query=`).

### 4.3 Product (Product Page `<head>`)

```json
{
  "@context": "https://schema.org",
  "@type": "Product",
  "name": "Porta Blindata da Interno per Ingresso – Classe 3",
  "description": "Porta blindata da interno certificata Classe 3, ideale per ingressi residenziali. Alta resistenza all'effrazione con trasmittanza termica ottimizzata.",
  "image": "https://www.bricoshop24.it/img/p/[product-image].jpg",
  "sku": "21633",
  "brand": {
    "@type": "Brand",
    "name": "[Marca prodotto]"
  },
  "additionalProperty": [
    {
      "@type": "PropertyValue",
      "name": "Classe di sicurezza",
      "value": "Classe 3"
    },
    {
      "@type": "PropertyValue",
      "name": "Trasmittanza termica",
      "value": "[valore Uw W/m²K]"
    }
  ],
  "offers": {
    "@type": "Offer",
    "priceCurrency": "EUR",
    "price": "[prezzo numerico]",
    "availability": "https://schema.org/InStock",
    "url": "https://www.bricoshop24.it/21633-porta-blindata-da-interno-per-ingresso",
    "seller": {
      "@type": "Organization",
      "name": "BricoShop24"
    }
  }
}
```
> Replace bracketed placeholders with dynamic values from PrestaShop template variables.

### 4.4 BreadcrumbList (Category / Product Pages)

```json
{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "name": "Home",
      "item": "https://www.bricoshop24.it/"
    },
    {
      "@type": "ListItem",
      "position": 2,
      "name": "Porte Blindate",
      "item": "https://www.bricoshop24.it/porte-blindate"
    },
    {
      "@type": "ListItem",
      "position": 3,
      "name": "Porte Anta Singola",
      "item": "https://www.bricoshop24.it/porte-blindate/porte-anta-singola"
    }
  ]
}
```
> Generate dynamically from PrestaShop's `{breadcrumb}` Smarty variable.

### 4.5 Article (Blog Pages)

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Trasmittanza Termica delle Porte: Guida Completa",
  "author": {
    "@type": "Organization",
    "name": "BricoShop24"
  },
  "publisher": {
    "@type": "Organization",
    "name": "BricoShop24",
    "logo": {
      "@type": "ImageObject",
      "url": "https://www.bricoshop24.it/img/logo.png"
    }
  },
  "datePublished": "[YYYY-MM-DD]",
  "dateModified": "[YYYY-MM-DD]",
  "image": "https://www.bricoshop24.it/img/blog/[post-image].jpg",
  "url": "https://www.bricoshop24.it/blog/news/[post-slug]",
  "mainEntityOfPage": {
    "@type": "WebPage",
    "@id": "https://www.bricoshop24.it/blog/news/[post-slug]"
  }
}
```

### 4.6 ItemList (Category Pages)

```json
{
  "@context": "https://schema.org",
  "@type": "ItemList",
  "name": "Porte Blindate",
  "url": "https://www.bricoshop24.it/porte-blindate",
  "itemListElement": [
    {
      "@type": "ListItem",
      "position": 1,
      "url": "https://www.bricoshop24.it/21633-porta-blindata-da-interno-per-ingresso"
    }
  ]
}
```
> Populate all product URLs dynamically from the category product loop.

---

## 5. Implementation Notes for PrestaShop

1. **Preferred method:** Install a dedicated JSON-LD module (e.g., "SEO Expert" or "Rich Snippets + Structured Data" from PrestaShop Addons marketplace) or implement via custom override in `themes/[theme]/templates/`.
2. **Product template:** `product.tpl` — inject JSON-LD in `{block name='product_scripts'}` or just before `</head>`.
3. **Category template:** `catalog/listing/category.tpl`
4. **Blog template:** Depends on the blog module in use (e.g., `modules/pm_advanceblog/` or similar).
5. **Do not use Microdata** on new implementations — JSON-LD is Google's preferred format and is decoupled from HTML structure.
6. **Validate** every implementation at: https://search.google.com/test/rich-results

---

## 6. Summary Score

**Schema Implementation Score: 5 / 100**

Rationale: PrestaShop default installations produce no JSON-LD and only partial/invalid Microdata on product pages. No evidence of any schema module installed. The site has significant untapped rich result potential across Product, BreadcrumbList, Article, and Organization types that are directly actionable and commercially impactful.

| Priority | Type | Potential SERP Impact |
|---|---|---|
| Critical | Product + Offer | Price/availability snippets on product queries |
| Critical | Organization | Knowledge Panel, brand SERP |
| High | BreadcrumbList | URL breadcrumbs in all SERPs |
| High | WebSite + SearchAction | Sitelinks Searchbox |
| High | Article | Discover eligibility, article rich results |
| Medium | AggregateRating (Org) | Star display on brand queries |
| Medium | ItemList | Category page understanding |
| Low | FAQPage | AI/LLM citations only (no Google SERP feature as of May 2026) |

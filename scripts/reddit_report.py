import json
import os
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
import urllib.request

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
ROME_TZ = timezone(timedelta(hours=2))

SOURCES = [
    # Google News RSS — aggrega automaticamente tutti i media e blog italiani
    {"name": "Digital Marketing",   "url": "https://news.google.com/rss/search?q=digital+marketing+italia&hl=it&gl=IT&ceid=IT:it",                  "type": "news"},
    {"name": "Ecommerce Italia",    "url": "https://news.google.com/rss/search?q=ecommerce+italia&hl=it&gl=IT&ceid=IT:it",                           "type": "news"},
    {"name": "PMI & Marketing",     "url": "https://news.google.com/rss/search?q=piccole+medie+imprese+marketing+digitale&hl=it&gl=IT&ceid=IT:it",   "type": "news"},
    {"name": "Social Media Mkt",    "url": "https://news.google.com/rss/search?q=social+media+marketing+italia&hl=it&gl=IT&ceid=IT:it",              "type": "news"},
    # Blog italiani diretti
    {"name": "Ninja Marketing",     "url": "https://www.ninjamarketing.it/feed/",    "type": "news"},
    {"name": "Wired Italia",        "url": "https://www.wired.it/feed/rss",          "type": "news"},
    # YouTube — canali italiani top (digital marketing, business, ecommerce)
    {"name": "Marco Montemagno",    "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCNg4RDHGls-HpbV10kWPlsw", "type": "youtube"},
    {"name": "We Are Marketers",    "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCj4ft9BRkYngTO_qfWGzzdQ", "type": "youtube"},
    {"name": "Mirko Cuneo",         "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCSnw8sw9mzJn4mFpnB36rlw", "type": "youtube"},
    {"name": "Ninja Marketing YT",  "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCqY0bXYGZvRGSzE2WD74ang", "type": "youtube"},
]

KEYWORDS_HIGH = [
    "digital marketing", "email marketing", "seo", "sem", "google ads",
    "facebook ads", "meta ads", "instagram ads", "lead generation",
    "conversion rate", "ecommerce", "e-commerce", "shopify", "woocommerce",
    "small business", "copywriting", "landing page", "funnel", "analytics",
    "content marketing", "social media marketing", "roi", "cpa", "cpc",
    "ctr", "roas", "publishing", "affiliate marketing",
    "marketing automation", "crm", "retargeting", "a/b test",
    "intelligenza artificiale", "ai marketing", "automazione",
]
KEYWORDS_MID = [
    "marketing", "advertising", "campagna", "brand", "vendite", "fatturato",
    "cliente", "audience", "traffico", "organico", "paid", "b2b", "b2c",
    "startup", "imprenditore", "crescita", "strategia", "automazione",
    "influencer", "newsletter", "lancio prodotto", "ricerca di mercato",
    "acquisizione clienti", "retention", "upsell", "cross-sell",
    "digitale", "online", "web", "app", "piattaforma",
]


def parse_date(date_str: str) -> datetime | None:
    if not date_str:
        return None
    try:
        return parsedate_to_datetime(date_str.strip())
    except Exception:
        pass
    try:
        return datetime.fromisoformat(date_str.strip())
    except Exception:
        pass
    return None


def fetch_feed(source: dict) -> list:
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/rss+xml, application/xml, text/xml, */*",
    }
    req = urllib.request.Request(source["url"], headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
    except Exception as e:
        print(f"[WARN] {source['name']}: {e}")
        return []

    try:
        root = ET.fromstring(content)
    except ET.ParseError as e:
        print(f"[WARN] XML parse error {source['name']}: {e}")
        return []

    ATOM = "{http://www.w3.org/2005/Atom}"
    items = []

    # RSS 2.0
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        desc = (item.findtext("description") or "").strip()
        date = parse_date(item.findtext("pubDate") or "")
        if title and link:
            items.append({"title": title, "url": link, "summary": desc[:250], "date": date, "source": source["name"], "type": source["type"]})

    # Atom (YouTube e altri)
    for entry in root.findall(f".//{ATOM}entry"):
        title = (entry.findtext(f"{ATOM}title") or "").strip()
        link_el = entry.find(f"{ATOM}link[@rel='alternate']") or entry.find(f"{ATOM}link")
        link = link_el.get("href", "") if link_el is not None else ""
        published = entry.findtext(f"{ATOM}published") or entry.findtext(f"{ATOM}updated") or ""
        summary = (entry.findtext(f"{ATOM}summary") or entry.findtext(f"{ATOM}content") or "").strip()
        date = parse_date(published)
        if title and link:
            items.append({"title": title, "url": link, "summary": summary[:250], "date": date, "source": source["name"], "type": source["type"]})

    return items


def is_recent(item: dict, hours: int) -> bool:
    date = item.get("date")
    if not date:
        return True
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    try:
        d = date if date.tzinfo else date.replace(tzinfo=timezone.utc)
        return d >= cutoff
    except Exception:
        return True


def relevance_score(item: dict) -> int:
    text = (item.get("title", "") + " " + item.get("summary", "")).lower()
    score = 1
    for kw in KEYWORDS_HIGH:
        if kw in text:
            score += 2
    for kw in KEYWORDS_MID:
        if kw in text:
            score += 1
    return min(score, 10)


def h(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def send_telegram(token: str, chat_id: str, html: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": html, "parse_mode": "HTML", "disable_web_page_preview": True}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
    if not result.get("ok"):
        raise RuntimeError(f"Telegram error: {result}")


def main():
    today_str = datetime.now(ROME_TZ).strftime("%d/%m/%Y")

    send_telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
        f"📊 <b>Report Digitale del {today_str}</b>\n"
        f"Blog, news e YouTube italiani\n"
        f"<i>Digital marketing · Ecommerce · PMI · Social media</i>"
    )
    time.sleep(1)

    all_news: list[dict] = []
    all_youtube: list[dict] = []

    for source in SOURCES:
        print(f"Fetching {source['name']}...")
        items = fetch_feed(source)
        hours = 48 if source["type"] == "news" else 168
        recent = [i for i in items if is_recent(i, hours)]
        if not recent and items:
            recent = items[:3]
        for item in recent:
            item["relevance"] = relevance_score(item)
        if source["type"] == "news":
            all_news.extend(recent)
        else:
            all_youtube.extend(recent)
        time.sleep(1)

    # Deduplica per URL
    seen: set[str] = set()
    unique_news, unique_yt = [], []
    for item in sorted(all_news, key=lambda x: x["relevance"], reverse=True):
        if item["url"] not in seen:
            seen.add(item["url"])
            unique_news.append(item)
    for item in sorted(all_youtube, key=lambda x: x["relevance"], reverse=True):
        if item["url"] not in seen:
            seen.add(item["url"])
            unique_yt.append(item)

    # Sezione news / blog
    if unique_news:
        lines = ["🗞️ <b>Blog &amp; News Italiani</b>\n"]
        for i, item in enumerate(unique_news[:7], 1):
            lines.append(f"{i}. <a href='{item['url']}'>{h(item['title'])}</a>")
            lines.append(f"   📌 {h(item['source'])}  ·  ⭐ {item['relevance']}/10\n")
        send_telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, "\n".join(lines))
    else:
        send_telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, "🗞️ <b>Blog &amp; News</b>\n<i>Nessun articolo trovato.</i>")
    time.sleep(1)

    # Sezione YouTube
    if unique_yt:
        lines = ["📺 <b>YouTube Italiani</b>\n"]
        for i, item in enumerate(unique_yt[:5], 1):
            lines.append(f"{i}. <a href='{item['url']}'>{h(item['title'])}</a>")
            lines.append(f"   📌 {h(item['source'])}  ·  ⭐ {item['relevance']}/10\n")
        send_telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, "\n".join(lines))
    else:
        send_telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, "📺 <b>YouTube</b>\n<i>Nessun video trovato.</i>")
    time.sleep(1)

    # Top 5 complessivo
    top5 = sorted(unique_news[:10] + unique_yt[:5], key=lambda x: x["relevance"], reverse=True)[:5]
    if top5:
        lines = ["🏆 <b>Top 5 per rilevanza al tuo business</b>\n"]
        for i, item in enumerate(top5, 1):
            emoji = "📺" if item["type"] == "youtube" else "🗞️"
            lines.append(f"{i}. {emoji} <a href='{item['url']}'>{h(item['title'])}</a>")
            lines.append(f"   {h(item['source'])}  ·  ⭐ {item['relevance']}/10\n")
        send_telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, "\n".join(lines))

    print("Report inviato su Telegram.")


if __name__ == "__main__":
    main()

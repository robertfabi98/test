import json
import os
import time
from datetime import datetime, timezone, timedelta
import urllib.request

SUBREDDITS = ["marketing", "digital_marketing", "ecommerce", "smallbusiness"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
ROME_TZ = timezone(timedelta(hours=2))  # CEST

KEYWORDS_HIGH = [
    "digital marketing", "email marketing", "seo", "sem", "google ads",
    "facebook ads", "meta ads", "instagram ads", "lead generation",
    "conversion rate", "ecommerce", "e-commerce", "shopify", "woocommerce",
    "small business", "copywriting", "landing page", "funnel", "analytics",
    "content marketing", "social media marketing", "roi", "cpa", "cpc",
    "ctr", "roas", "publishing", "affiliate marketing",
    "marketing automation", "crm", "retargeting", "a/b test",
]
KEYWORDS_MID = [
    "marketing", "advertising", "campaign", "brand", "sales", "revenue",
    "customer", "audience", "traffic", "organic", "paid", "b2b", "b2c",
    "startup", "entrepreneur", "growth", "strategy", "automation",
    "influencer", "newsletter", "product launch", "market research",
    "customer acquisition", "retention", "upsell", "cross-sell",
]


def fetch_posts(subreddit: str, limit: int = 30) -> list:
    url = f"https://www.reddit.com/r/{subreddit}/top.json?t=week&limit={limit}"
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; DailyReportBot/1.0; +https://github.com/robertfabi98/test)",
        "Accept": "application/json",
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
    except Exception as e:
        print(f"[WARN] r/{subreddit}: {e}")
        return []

    cutoff = time.time() - 48 * 3600
    recent = [
        item["data"]
        for item in data["data"]["children"]
        if item["data"]["created_utc"] >= cutoff
        and not item["data"].get("stickied", False)
    ]

    if not recent:
        recent = [
            item["data"]
            for item in data["data"]["children"][:5]
            if not item["data"].get("stickied", False)
        ]

    return sorted(recent, key=lambda p: p["score"], reverse=True)[:5]


def relevance_score(post: dict) -> int:
    text = (post.get("title", "") + " " + post.get("selftext", "")).lower()
    score = 1
    for kw in KEYWORDS_HIGH:
        if kw in text:
            score += 2
    for kw in KEYWORDS_MID:
        if kw in text:
            score += 1
    return min(score, 10)


def summarize(post: dict) -> str:
    selftext = post.get("selftext", "").strip()
    if selftext and len(selftext) > 30:
        return (selftext[:250].rsplit(" ", 1)[0] + "...") if len(selftext) > 250 else selftext
    return ""


def h(text: str) -> str:
    """Escape HTML special characters for Telegram."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def send_telegram(token: str, chat_id: str, html: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": html,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
    if not result.get("ok"):
        raise RuntimeError(f"Telegram error: {result}")


def main():
    today_str = datetime.now(ROME_TZ).strftime("%d/%m/%Y")

    # Intestazione
    send_telegram(
        TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
        f"📊 <b>Report Reddit del {today_str}</b>\n"
        f"Subreddit: r/marketing · r/digital_marketing · r/ecommerce · r/smallbusiness\n"
        f"<i>Post con più engagement nelle ultime 48 ore</i>"
    )
    time.sleep(1)

    all_scored: list[dict] = []

    for subreddit in SUBREDDITS:
        print(f"Recupero post da r/{subreddit}...")
        posts = fetch_posts(subreddit)
        time.sleep(2)

        if not posts:
            send_telegram(
                TELEGRAM_TOKEN, TELEGRAM_CHAT_ID,
                f"📌 <b>r/{subreddit}</b>\n<i>Nessun post trovato.</i>"
            )
            time.sleep(1)
            continue

        lines = [f"📌 <b>r/{subreddit}</b>\n"]
        for i, post in enumerate(posts, 1):
            score = relevance_score(post)
            title = h(post.get("title", ""))
            url = f"https://reddit.com{post['permalink']}"
            upvotes = post.get("score", 0)
            comments = post.get("num_comments", 0)
            summary = h(summarize(post))
            stars = "⭐" * score

            lines.append(f"<b>{i}. <a href='{url}'>{title}</a></b>")
            if summary:
                lines.append(f"<i>{summary}</i>")
            lines.append(f"🔺 {upvotes:,}  💬 {comments:,}  {stars} {score}/10\n")

            all_scored.append({
                "title": post.get("title", ""),
                "url": url,
                "subreddit": subreddit,
                "relevance": score,
                "upvotes": upvotes,
            })

        send_telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, "\n".join(lines))
        time.sleep(1)

    # Top 5 complessivo
    top5 = sorted(all_scored, key=lambda x: (x["relevance"], x["upvotes"]), reverse=True)[:5]
    if top5:
        summary_lines = ["🏆 <b>Top 5 per rilevanza al tuo business:</b>\n"]
        for i, p in enumerate(top5, 1):
            summary_lines.append(
                f"{i}. <a href='{p['url']}'>{h(p['title'])}</a>\n"
                f"   r/{p['subreddit']} · ⭐ {p['relevance']}/10"
            )
        send_telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, "\n".join(summary_lines))

    print("Report inviato su Telegram.")


if __name__ == "__main__":
    main()

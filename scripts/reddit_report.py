import json
import os
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import urllib.request
import urllib.error

SUBREDDITS = ["marketing", "digital_marketing", "ecommerce", "smallbusiness"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
ROME_TZ = timezone(timedelta(hours=2))  # CEST; works for scheduling purposes

# Keyword-based relevance scoring for Robert's business context
KEYWORDS_HIGH = [
    "digital marketing", "email marketing", "seo", "sem", "google ads",
    "facebook ads", "meta ads", "instagram ads", "lead generation",
    "conversion rate", "ecommerce", "e-commerce", "shopify", "woocommerce",
    "small business", "copywriting", "landing page", "funnel", "analytics",
    "content marketing", "social media marketing", "roi", "cpa", "cpc",
    "ctr", "roas", "pmi", "publishing", "affiliate marketing",
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
    req = urllib.request.Request(url, headers={"User-Agent": "RedditDailyReportBot/1.0"})
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

    # fallback: top 3 della settimana se non ci sono post nelle 48h
    if not recent:
        recent = [
            item["data"]
            for item in data["data"]["children"][:3]
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
        return (selftext[:280].rsplit(" ", 1)[0] + "...") if len(selftext) > 280 else selftext
    return post.get("title", "")


def build_report(all_posts: dict[str, list]) -> tuple[str, list]:
    today_str = datetime.now(ROME_TZ).strftime("%d/%m/%Y")
    lines = [
        f"# Report Reddit Giornaliero — {today_str}",
        "",
        f"**Subreddit monitorati:** {', '.join('r/' + s for s in SUBREDDITS)}  ",
        f"**Finestra temporale:** ultime 48 ore  ",
        "",
        "---",
        "",
    ]

    all_scored: list[dict] = []

    for subreddit, posts in all_posts.items():
        lines.append(f"## r/{subreddit}")
        lines.append("")

        if not posts:
            lines.append("*Nessun post trovato nelle ultime 48 ore.*")
            lines.append("")
            continue

        for i, post in enumerate(posts, 1):
            score = relevance_score(post)
            summary = summarize(post)
            url = f"https://reddit.com{post['permalink']}"
            upvotes = post.get("score", 0)
            comments = post.get("num_comments", 0)
            stars = "⭐" * score

            lines += [
                f"### {i}. {post['title']}",
                "",
                f"**Riassunto:** {summary}",
                "",
                f"- 🔺 Upvote: **{upvotes:,}** | 💬 Commenti: **{comments:,}**",
                f"- 📊 Rilevanza per il business: {stars} **({score}/10)**",
                f"- 🔗 [Apri il post]({url})",
                "",
            ]

            all_scored.append({
                "title": post["title"],
                "url": url,
                "subreddit": subreddit,
                "relevance": score,
                "upvotes": upvotes,
            })

    top5 = sorted(all_scored, key=lambda x: (x["relevance"], x["upvotes"]), reverse=True)[:5]

    lines += [
        "---",
        "",
        "## 🏆 Top 5 Post per Rilevanza",
        "",
    ]
    for i, p in enumerate(top5, 1):
        lines.append(
            f"{i}. **[{p['title']}]({p['url']})** "
            f"(r/{p['subreddit']}) — {p['relevance']}/10"
        )

    lines += [
        "",
        "---",
        f"*Report generato automaticamente il {today_str} alle 08:00 (ora italiana)*",
    ]

    return "\n".join(lines), top5


def send_telegram(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
    if not result.get("ok"):
        raise RuntimeError(f"Telegram API error: {result}")


def main():
    all_posts: dict[str, list] = {}
    for subreddit in SUBREDDITS:
        print(f"Recupero post da r/{subreddit}...")
        all_posts[subreddit] = fetch_posts(subreddit)
        time.sleep(2)  # rispetta i rate limit di Reddit

    report_md, top5 = build_report(all_posts)

    today = datetime.now(ROME_TZ).strftime("%Y-%m-%d")
    report_path = Path("research/reports") / f"{today}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report_md, encoding="utf-8")
    print(f"Report salvato: {report_path}")

    today_str = datetime.now(ROME_TZ).strftime("%d/%m/%Y")
    tg_lines = [
        f"📊 *Report Reddit del {today_str}*",
        "",
        "*Top 5 post più rilevanti per il tuo business:*",
        "",
    ]
    for i, p in enumerate(top5, 1):
        tg_lines.append(
            f"{i}\\. [{p['title']}]({p['url']}) "
            f"\\(r/{p['subreddit']}\\) — ⭐ {p['relevance']}/10"
        )
    tg_lines += [
        "",
        f"📁 Report completo: `research/reports/{today}\\.md`",
    ]

    send_telegram(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, "\n".join(tg_lines))
    print("Messaggio Telegram inviato.")


if __name__ == "__main__":
    main()

import json
import html
import re
from datetime import datetime, timezone
from urllib.parse import quote_plus
from zoneinfo import ZoneInfo

import feedparser

SEARCHES = [
    ("chatgpt", "ChatGPT", "ChatGPT OR OpenAI OR GPT-5 OR GPT-4.1 OR OpenAI API"),
    ("claude", "Claude Code", "Claude Code OR Anthropic OR Claude AI OR Claude API"),
    ("gemini", "Gemini", "Gemini AI OR Google Gemini OR Gemini API OR Google AI Studio"),
    ("codex", "Codex / LLM Code", "Codex OR AI coding agent OR GitHub Copilot OR Cursor AI OR coding assistant"),
]

MAX_PER_TOPIC = 8
MAX_TOTAL = 32
LOCAL_TIMEZONE = ZoneInfo("America/New_York")


def clean_summary(text):
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:260]


def normalize_text(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def split_title_and_source(title, entry):
    source = ""
    entry_source = entry.get("source", {})

    if hasattr(entry_source, "get"):
        source = clean_summary(entry_source.get("title", ""))

    if " - " in title:
        headline, inferred_source = title.rsplit(" - ", 1)
        source = source or inferred_source.strip()
        title = headline.strip()

    return title, source or "Unknown source"


def is_low_signal_title(title):
    normalized = normalize_text(title)
    return not normalized or normalized in {"untitled", "no title"}


def build_summary(raw_summary, title, source):
    summary = clean_summary(raw_summary)
    normalized_summary = normalize_text(summary)
    normalized_title = normalize_text(title)

    if not summary or normalized_summary == normalized_title or normalized_title in normalized_summary:
        return f"{source} is reporting this update. Open the article for the full story."

    return summary


def format_entry_time(entry):
    parsed_time = entry.get("published_parsed") or entry.get("updated_parsed")

    if not parsed_time:
        return "Latest", None

    published_at = datetime(*parsed_time[:6], tzinfo=timezone.utc)
    local_time = published_at.astimezone(LOCAL_TIMEZONE)

    return local_time.strftime("%b %d, %I:%M %p ET"), published_at.isoformat()


def categorize(title, fallback_category, fallback_label):
    t = title.lower()

    if any(k in t for k in ["gemini", "google ai", "ai studio"]):
        return "gemini", "Gemini"

    if any(k in t for k in ["claude", "anthropic"]):
        return "claude", "Claude Code"

    if any(k in t for k in ["chatgpt", "openai", "gpt-5", "gpt-4", "gpt"]):
        return "chatgpt", "ChatGPT"

    if any(k in t for k in ["codex", "copilot", "cursor", "coding agent", "ai coding", "developer"]):
        return "codex", "Codex / LLM Code"

    return fallback_category, fallback_label


def google_news_rss(query):
    encoded = quote_plus(query)
    return f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"


articles = []
seen_titles = set()
seen_urls = set()

for fallback_category, fallback_label, query in SEARCHES:
    feed = feedparser.parse(google_news_rss(query))

    for entry in feed.entries[:MAX_PER_TOPIC]:
        raw_title = clean_summary(entry.get("title", "Untitled"))
        title, source = split_title_and_source(raw_title, entry)
        normalized = normalize_text(title)
        url = entry.get("link", "#")

        if is_low_signal_title(title) or normalized in seen_titles or url in seen_urls:
            continue

        seen_titles.add(normalized)
        seen_urls.add(url)

        category, label = categorize(title, fallback_category, fallback_label)
        display_time, published_at = format_entry_time(entry)

        articles.append({
            "category": category,
            "label": label,
            "time": display_time,
            "publishedAt": published_at,
            "source": source,
            "title": title,
            "summary": build_summary(entry.get("summary", ""), title, source),
            "linkText": "Read article →",
            "url": url,
            "difficulty": "News"
        })

articles.sort(key=lambda article: article["publishedAt"] or "", reverse=True)
articles = articles[:MAX_TOTAL]

with open("articles.json", "w", encoding="utf-8") as f:
    json.dump(articles, f, indent=2, ensure_ascii=False)

updated_at_utc = datetime.now(timezone.utc)
eastern_time = updated_at_utc.astimezone(LOCAL_TIMEZONE)

timestamp = {
    "lastUpdated": eastern_time.strftime("%B %d, %Y at %I:%M %p ET"),
    "lastUpdatedUtc": updated_at_utc.isoformat().replace("+00:00", "Z")
}

with open("feed-info.json", "w", encoding="utf-8") as f:
    json.dump(timestamp, f, indent=2)

print(f"Updated {len(articles)} articles at {datetime.now(timezone.utc).isoformat()}")

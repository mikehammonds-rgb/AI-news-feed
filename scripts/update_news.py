import json
import html
import re
from datetime import datetime, timezone
from urllib.parse import quote_plus

import feedparser

SEARCHES = [
    ("chatgpt", "ChatGPT", "ChatGPT OR OpenAI OR GPT-5 OR GPT-4.1 OR OpenAI API"),
    ("claude", "Claude Code", "Claude Code OR Anthropic OR Claude AI OR Claude API"),
    ("gemini", "Gemini", "Gemini AI OR Google Gemini OR Gemini API OR Google AI Studio"),
    ("codex", "Codex / LLM Code", "Codex OR AI coding agent OR GitHub Copilot OR Cursor AI OR coding assistant"),
]

MAX_PER_TOPIC = 8
MAX_TOTAL = 32


def clean_summary(text):
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:260]


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

for fallback_category, fallback_label, query in SEARCHES:
    feed = feedparser.parse(google_news_rss(query))

    for entry in feed.entries[:MAX_PER_TOPIC]:
        title = clean_summary(entry.get("title", "Untitled"))
        normalized = title.lower()

        if normalized in seen_titles:
            continue

        seen_titles.add(normalized)

        category, label = categorize(title, fallback_category, fallback_label)

        articles.append({
            "category": category,
            "label": label,
            "time": "Latest",
            "title": title,
            "summary": clean_summary(entry.get("summary", "")),
            "linkText": "Read article →",
            "url": entry.get("link", "#"),
            "difficulty": "News"
        })

articles = articles[:MAX_TOTAL]

with open("articles.json", "w", encoding="utf-8") as f:
    json.dump(articles, f, indent=2, ensure_ascii=False)

print(f"Updated {len(articles)} articles at {datetime.now(timezone.utc).isoformat()}")

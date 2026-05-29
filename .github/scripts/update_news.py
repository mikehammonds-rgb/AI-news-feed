import json
import feedparser

RSS_URL = (
    "https://news.google.com/rss/search?q="
    "ChatGPT+OR+Gemini+OR+Claude+OR+Anthropic+OR+OpenAI+OR+AI+Developer"
)

feed = feedparser.parse(RSS_URL)

articles = []

for entry in feed.entries[:20]:
    articles.append({
        "category": "chatgpt",
        "label": "AI News",
        "time": "Latest",
        "title": entry.title,
        "summary": getattr(entry, "summary", "")[:250],
        "linkText": "Read article →",
        "url": entry.link,
        "difficulty": "News"
    })

with open("articles.json", "w") as f:
    json.dump(articles, f, indent=2)

print(f"Updated {len(articles)} articles")

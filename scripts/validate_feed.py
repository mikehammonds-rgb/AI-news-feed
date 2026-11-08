"""Automatic pass/fail checks for the news feed. No human needed.

Usage: python scripts/validate_feed.py [articles.json] [feed-info.json]
Exit code 0 = all checks pass, 1 = at least one failure.
"""
import json
import re
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

REQUIRED_FIELDS = {
    "category", "label", "time", "publishedAt", "source",
    "title", "summary", "linkText", "url", "difficulty",
}
VALID_CATEGORIES = {"chatgpt", "claude", "gemini", "codex"}
MIN_ARTICLES = 10      # a healthy run produces ~32
MAX_AGE_HOURS = 24 * 14  # newest article should be recent


def normalize(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def validate_articles(articles):
    """Return a list of human-readable failure strings (empty list = pass)."""
    failures = []

    if not isinstance(articles, list):
        return ["articles.json is not a list"]
    if len(articles) < MIN_ARTICLES:
        failures.append(f"only {len(articles)} articles (minimum {MIN_ARTICLES})")

    seen_titles, seen_urls = set(), set()
    newest = None

    for i, a in enumerate(articles):
        where = f"article[{i}]"
        missing = REQUIRED_FIELDS - set(a)
        if missing:
            failures.append(f"{where} missing fields: {sorted(missing)}")
            continue

        if a["category"] not in VALID_CATEGORIES:
            failures.append(f"{where} bad category {a['category']!r}")

        parsed = urlparse(a["url"])
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            failures.append(f"{where} invalid url {a['url']!r}")

        if not a["title"].strip():
            failures.append(f"{where} empty title")

        source = a["source"]
        if re.match(r"^https?://", source):
            failures.append(f"{where} source is a raw URL: {source!r}")

        nt = normalize(a["title"])
        if nt in seen_titles:
            failures.append(f"{where} duplicate title: {a['title']!r}")
        seen_titles.add(nt)
        if a["url"] in seen_urls:
            failures.append(f"{where} duplicate url")
        seen_urls.add(a["url"])

        if a["publishedAt"]:
            try:
                ts = datetime.fromisoformat(a["publishedAt"])
                if newest is None or ts > newest:
                    newest = ts
            except ValueError:
                failures.append(f"{where} unparseable publishedAt {a['publishedAt']!r}")

    if newest is not None:
        age_h = (datetime.now(timezone.utc) - newest).total_seconds() / 3600
        if age_h > MAX_AGE_HOURS:
            failures.append(f"newest article is {age_h:.0f}h old (feed looks stale)")

    return failures


def validate_info(info):
    failures = []
    for key in ("lastUpdated", "lastUpdatedUtc"):
        if key not in info:
            failures.append(f"feed-info.json missing {key}")
    return failures


def main():
    articles_path = sys.argv[1] if len(sys.argv) > 1 else "articles.json"
    info_path = sys.argv[2] if len(sys.argv) > 2 else "feed-info.json"
    try:
        with open(articles_path, encoding="utf-8") as f:
            articles = json.load(f)
        with open(info_path, encoding="utf-8") as f:
            info = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: cannot load files: {exc}")
        return 1

    failures = validate_articles(articles) + validate_info(info)
    if failures:
        print(f"FAIL: {len(failures)} problem(s)")
        for line in failures:
            print(f"  - {line}")
        return 1
    print(f"PASS: {len(articles)} articles, all checks OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())

# AI Developer News Feed

A GitHub Pages dashboard for tracking AI developer news across ChatGPT/OpenAI,
Claude/Anthropic, Gemini/Google AI, and coding-agent tools like Codex, Copilot,
and Cursor.

The feed is refreshed by a scheduled GitHub Action every 30 minutes. The updater
pulls Google News RSS results, cleans low-signal titles, deduplicates articles,
and writes the latest data to `articles.json` and `feed-info.json`.

## Features

- Search and category filters
- Local saved-article list
- Source labels and article timestamps
- Static GitHub Pages deployment
- Scheduled feed updates through GitHub Actions

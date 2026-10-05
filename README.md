# AI OS News Data

This repository supplies the expandable AI news widget in [AI OS](https://morning-ai-os.the-unlimite-3666.chatgpt.site/). AI OS is the dashboard; the former standalone GitHub Pages dashboard is retired.

The existing GitHub Action continues collecting news every 30 minutes. It pulls Google News RSS results, cleans low-signal titles, deduplicates articles, and writes `articles.json` and `feed-info.json`.

AI OS reads these JSON files directly from the repository's main branch. GitHub Pages is not required for the news widget. Keep the updater, workflow, article data, metadata and repository available.

The old Pages entry point redirects to AI OS for existing bookmarks. AI OS retains its private access settings.

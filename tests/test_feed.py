"""Offline tests: these are the pass/fail judge for any change to the updater.

Run: python -m unittest discover -s tests -v   (from the repo root)
"""
import os
import sys
import time
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import update_news  # noqa: E402
from validate_feed import validate_articles  # noqa: E402


def fake_entry(i, source="Example News", title=None, link=None):
    published = time.gmtime(time.time() - i * 3600)
    return {
        "title": title or f"Story number {i} about OpenAI - {source}",
        "link": link or f"https://news.example.com/{i}",
        "summary": "",
        "source": {"title": source},
        "published_parsed": published,
    }


def fake_parse_factory(entries):
    """Each search call gets its own slice, like four distinct real queries."""
    calls = {"n": 0}

    def parse(_url):
        n = calls["n"]
        calls["n"] += 1
        return SimpleNamespace(entries=entries[n * 8:(n + 1) * 8])
    return parse


class CleanSource(unittest.TestCase):
    def test_url_becomes_domain(self):
        self.assertEqual(update_news.clean_source("https://tech-insider.org/"), "tech-insider.org")
        self.assertEqual(update_news.clean_source("https://www.foo.com/x"), "foo.com")

    def test_plain_name_untouched(self):
        self.assertEqual(update_news.clean_source("Pulse 2.0"), "Pulse 2.0")

    def test_empty_falls_back(self):
        self.assertEqual(update_news.clean_source(""), "Unknown source")


class BuildArticles(unittest.TestCase):
    def test_empty_feed_yields_no_articles(self):
        self.assertEqual(update_news.build_articles(fake_parse_factory([])), [])

    def test_dedupes_by_title_and_url(self):
        entries = [fake_entry(1), fake_entry(1)]
        articles = update_news.build_articles(fake_parse_factory(entries))
        self.assertEqual(len(articles), 1)

    def test_url_source_is_cleaned_end_to_end(self):
        entries = [fake_entry(i, source="https://tech-insider.org/") for i in range(24)]
        articles = update_news.build_articles(fake_parse_factory(entries))
        self.assertTrue(articles)
        self.assertTrue(all(not a["source"].startswith("http") for a in articles))

    def test_output_passes_validator(self):
        entries = [fake_entry(i) for i in range(24)]
        articles = update_news.build_articles(fake_parse_factory(entries))
        self.assertEqual(validate_articles(articles), [])


class Guard(unittest.TestCase):
    def test_main_refuses_to_overwrite_on_thin_fetch(self):
        original = update_news.build_articles
        update_news.build_articles = lambda *a, **k: []
        cwd = os.getcwd()
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            os.chdir(tmp)
            try:
                with open("articles.json", "w") as f:
                    f.write('["keep me"]')
                code = update_news.main()
                with open("articles.json") as f:
                    kept = f.read()
            finally:
                os.chdir(cwd)
                update_news.build_articles = original
        self.assertEqual(code, 1)
        self.assertEqual(kept, '["keep me"]')


class Validator(unittest.TestCase):
    def test_flags_url_source(self):
        a = update_news.build_articles(fake_parse_factory([fake_entry(i) for i in range(24)]))
        a[0]["source"] = "https://bad.example/"
        self.assertTrue(any("raw URL" in f for f in validate_articles(a)))

    def test_flags_too_few(self):
        self.assertTrue(any("only 0" in f for f in validate_articles([])))


if __name__ == "__main__":
    unittest.main()

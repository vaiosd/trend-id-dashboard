"""Offline tests for the parsers and script generator."""

from __future__ import annotations

from app.google_trends import parse_rss
from app.script_generator import generate_script
from app.twitter_trends import TwitterTrend, parse_trends

SAMPLE_TRENDS24 = """
<html><body>
<ol class="trend-card__list">
<li>
  <a href="https://twitter.com/search?q=Foo">Foo</a>
  <span class="tweet-count">10K Tweets</span>
</li>
<li><a href="https://twitter.com/search?q=%23Bar">#Bar</a></li>
<li><a href="https://twitter.com/search?q=Baz">Baz</a></li>
</ol>
<ol class="trend-card__list">
<li><a href="https://twitter.com/search?q=Old">Old</a></li>
</ol>
</body></html>
"""

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:ht="https://trends.google.com/trending/rss" version="2.0">
<channel>
<title>Daily Search Trends</title>
<item>
<title>topik satu</title>
<ht:approx_traffic>500+</ht:approx_traffic>
<pubDate>Mon, 27 Apr 2026 06:30:00 -0700</pubDate>
<ht:picture>https://example.com/p.jpg</ht:picture>
<ht:news_item>
<ht:news_item_title>Berita pertama tentang topik satu</ht:news_item_title>
<ht:news_item_url>https://news.example.com/a</ht:news_item_url>
<ht:news_item_source>Example News</ht:news_item_source>
</ht:news_item>
</item>
<item>
<title>topik dua</title>
<ht:approx_traffic>200+</ht:approx_traffic>
</item>
</channel></rss>
"""


def test_parse_trends_picks_first_snapshot():
    trends = parse_trends(SAMPLE_TRENDS24)
    names = [t.name for t in trends]
    assert names == ["Foo", "#Bar", "Baz"]
    assert trends[0].rank == 1
    assert trends[0].tweet_volume == "10K Tweets"
    assert trends[0].url and trends[0].url.startswith("https://twitter.com/search?q=")


def test_parse_rss_extracts_news():
    trends = parse_rss(SAMPLE_RSS)
    assert len(trends) == 2
    assert trends[0].title == "topik satu"
    assert trends[0].traffic == "500+"
    assert len(trends[0].news) == 1
    assert trends[0].news[0].source == "Example News"
    assert trends[1].title == "topik dua"
    assert trends[1].news == []


def test_generate_script_word_count_in_range():
    twitter = [
        TwitterTrend(rank=1, name="Foo"),
        TwitterTrend(rank=2, name="Bar"),
        TwitterTrend(rank=3, name="Baz"),
    ]
    google = parse_rss(SAMPLE_RSS)
    script = generate_script(twitter, google)
    assert script.duration_seconds == 50
    assert 90 <= script.word_count <= 200
    assert len(script.sections) == 5
    assert "Foo" in script.full_text
    assert "topik satu" in script.full_text


def test_generate_script_handles_empty_inputs():
    script = generate_script([], [])
    assert script.duration_seconds == 50
    assert script.word_count > 0
    assert len(script.sections) == 5

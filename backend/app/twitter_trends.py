"""Scrape latest X (Twitter) trending topics for Indonesia from trends24.in.

trends24.in publishes a public page of trending topics per country every ~50 minutes.
The page contains a series of `<ol>` elements, one per snapshot. The first `<ol>` is
the most recent snapshot. Each list item is a trending term, optionally including a
tweet-volume tooltip.
"""

from __future__ import annotations

import html as html_lib
import re
from dataclasses import dataclass

import httpx

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)

URL = "https://trends24.in/indonesia/"

OL_RE = re.compile(r"<ol[^>]*>(.*?)</ol>", re.DOTALL | re.IGNORECASE)
LI_RE = re.compile(r"<li[^>]*>(.*?)</li>", re.DOTALL | re.IGNORECASE)
A_TEXT_RE = re.compile(r"<a[^>]*>([^<]+)</a>", re.IGNORECASE)
VOLUME_RE = re.compile(r'class="tweet-count"[^>]*>([^<]+)<', re.IGNORECASE)


@dataclass
class TwitterTrend:
    rank: int
    name: str
    tweet_volume: str | None = None
    url: str | None = None

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "name": self.name,
            "tweet_volume": self.tweet_volume,
            "url": self.url,
        }


def _twitter_search_url(name: str) -> str:
    from urllib.parse import quote_plus

    return f"https://twitter.com/search?q={quote_plus(name)}"


def parse_trends(html: str) -> list[TwitterTrend]:
    """Parse the most recent snapshot of trends from trends24 HTML."""
    ols = OL_RE.findall(html)
    if not ols:
        return []
    first = ols[0]
    trends: list[TwitterTrend] = []
    seen: set[str] = set()
    items = LI_RE.findall(first)
    for raw_item in items:
        a = A_TEXT_RE.search(raw_item)
        if not a:
            continue
        name = html_lib.unescape(a.group(1)).strip()
        if not name or name in seen:
            continue
        seen.add(name)
        vol_match = VOLUME_RE.search(raw_item)
        volume = (
            html_lib.unescape(vol_match.group(1)).strip() if vol_match else None
        )
        trends.append(
            TwitterTrend(
                rank=len(trends) + 1,
                name=name,
                tweet_volume=volume,
                url=_twitter_search_url(name),
            )
        )
    return trends


async def fetch_twitter_trends(timeout: float = 15.0) -> list[TwitterTrend]:
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "id-ID,id;q=0.9,en;q=0.8"}
    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        resp = await client.get(URL)
        resp.raise_for_status()
        return parse_trends(resp.text)

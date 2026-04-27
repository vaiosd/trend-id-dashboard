"""Fetch Google Daily Search Trends for Indonesia via the public RSS feed.

Google publishes a daily search trends RSS feed at
``https://trends.google.com/trending/rss?geo=ID``. Each ``<item>`` is one trending
search query with an approximate traffic estimate and zero or more associated news
articles.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

import httpx

URL = "https://trends.google.com/trending/rss?geo=ID"
NS = {"ht": "https://trends.google.com/trending/rss"}

USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


@dataclass
class NewsItem:
    title: str
    url: str
    source: str | None = None

    def to_dict(self) -> dict:
        return {"title": self.title, "url": self.url, "source": self.source}


@dataclass
class GoogleTrend:
    rank: int
    title: str
    traffic: str | None = None
    pub_date: str | None = None
    picture: str | None = None
    news: list[NewsItem] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "title": self.title,
            "traffic": self.traffic,
            "pub_date": self.pub_date,
            "picture": self.picture,
            "news": [n.to_dict() for n in self.news],
        }


def parse_rss(xml_text: str) -> list[GoogleTrend]:
    root = ET.fromstring(xml_text)
    channel = root.find("channel")
    if channel is None:
        return []
    out: list[GoogleTrend] = []
    for idx, item in enumerate(channel.findall("item"), start=1):
        title_el = item.find("title")
        title = (title_el.text or "").strip() if title_el is not None else ""
        if not title:
            continue
        traffic_el = item.find("ht:approx_traffic", NS)
        traffic = traffic_el.text.strip() if traffic_el is not None and traffic_el.text else None
        pub_el = item.find("pubDate")
        pub_date = pub_el.text.strip() if pub_el is not None and pub_el.text else None
        pic_el = item.find("ht:picture", NS)
        picture = pic_el.text.strip() if pic_el is not None and pic_el.text else None

        news: list[NewsItem] = []
        for ni in item.findall("ht:news_item", NS):
            n_title_el = ni.find("ht:news_item_title", NS)
            n_url_el = ni.find("ht:news_item_url", NS)
            n_src_el = ni.find("ht:news_item_source", NS)
            n_title = n_title_el.text.strip() if n_title_el is not None and n_title_el.text else ""
            n_url = n_url_el.text.strip() if n_url_el is not None and n_url_el.text else ""
            n_src = n_src_el.text.strip() if n_src_el is not None and n_src_el.text else None
            if n_title and n_url:
                news.append(NewsItem(title=n_title, url=n_url, source=n_src))

        out.append(
            GoogleTrend(
                rank=idx,
                title=title,
                traffic=traffic,
                pub_date=pub_date,
                picture=picture,
                news=news,
            )
        )
    return out


async def fetch_google_trends(timeout: float = 15.0) -> list[GoogleTrend]:
    headers = {"User-Agent": USER_AGENT, "Accept-Language": "id-ID,id;q=0.9,en;q=0.8"}
    async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
        resp = await client.get(URL)
        resp.raise_for_status()
        return parse_rss(resp.text)

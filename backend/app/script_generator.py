"""Generate a 50-second YouTube Shorts script from today's trending topics.

A 50-second voiceover at conversational Indonesian pace lands at roughly
130–150 words. The generator uses a deterministic, rule-based template so it
works without any external LLM API key, but the structure is intentionally
LLM-friendly: the same data shape can be passed to an LLM later.

Sections produced (mirroring viral Shorts pacing):
  - Hook (0-5s)        : eye-catching opener referencing top trend
  - Beat 1 (5-20s)     : top X trends with one-line context
  - Beat 2 (20-35s)    : top Google Trends with news angle
  - Beat 3 (35-45s)    : "kenapa ini viral?" synthesis
  - CTA (45-50s)       : like + follow prompt
"""

from __future__ import annotations

from dataclasses import dataclass

from .google_trends import GoogleTrend
from .twitter_trends import TwitterTrend


@dataclass
class ScriptSection:
    label: str
    timecode: str
    text: str

    def to_dict(self) -> dict:
        return {"label": self.label, "timecode": self.timecode, "text": self.text}


@dataclass
class ShortsScript:
    title: str
    sections: list[ScriptSection]
    duration_seconds: int
    word_count: int
    full_text: str
    sources: dict[str, list[str]]

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "sections": [s.to_dict() for s in self.sections],
            "duration_seconds": self.duration_seconds,
            "word_count": self.word_count,
            "full_text": self.full_text,
            "sources": self.sources,
        }


def _join_id(items: list[str]) -> str:
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    return ", ".join(items[:-1]) + ", dan " + items[-1]


def _trim_news_headline(headline: str, limit: int = 90) -> str:
    headline = headline.strip()
    if len(headline) <= limit:
        return headline
    return headline[: limit - 1].rsplit(" ", 1)[0] + "…"


def generate_script(
    twitter: list[TwitterTrend],
    google: list[GoogleTrend],
    top_n: int = 3,
) -> ShortsScript:
    top_x = twitter[:top_n]
    top_g = google[:top_n]

    if top_x:
        hook_topic = top_x[0].name
    elif top_g:
        hook_topic = top_g[0].title
    else:
        hook_topic = "tren hari ini"

    hook = (
        f"Stop scroll dulu! Hari ini netizen Indonesia rame banget ngomongin "
        f"\"{hook_topic}\". Aku rangkum semuanya dalam 50 detik."
    )

    if top_x:
        x_names = [t.name for t in top_x]
        beat1 = (
            f"Di X alias Twitter, tiga topik paling rame adalah {_join_id(x_names)}. "
            f"Dari obrolan netizen, \"{x_names[0]}\" jadi yang paling kenceng "
            f"karena lagi banyak banget tweet yang ngebahas ini barengan."
        )
    else:
        beat1 = "Di X hari ini lagi sepi tren menonjol dari Indonesia."

    if top_g:
        g_titles = [t.title for t in top_g]
        first_news = top_g[0].news[0] if top_g[0].news else None
        if first_news:
            angle = _trim_news_headline(first_news.title)
            source = first_news.source or "media nasional"
            beat2 = (
                f"Di Google Trends Indonesia, yang paling banyak dicari justru "
                f"{_join_id(g_titles)}. Salah satu pemicunya: {source} baru saja merilis "
                f"berita \"{angle}\"."
            )
        else:
            beat2 = (
                f"Di Google Trends Indonesia, pencarian terbanyak hari ini adalah "
                f"{_join_id(g_titles)}."
            )
    else:
        beat2 = "Google Trends Indonesia hari ini relatif kalem, belum ada lonjakan signifikan."

    beat3 = (
        "Kenapa topik-topik ini bisa meledak barengan? Karena pola viralnya sama: "
        "ada momentum berita, ditambah komunitas fandom yang aktif, lalu algoritma "
        "ngedorong ke timeline lebih banyak orang. Sekali masuk trending, efek bola "
        "saljunya susah dihentikan."
    )

    cta = (
        "Kalau kamu mau update tren Indonesia tiap hari kayak gini, "
        "jangan lupa like dan follow ya! Sampai ketemu di Shorts berikutnya."
    )

    sections = [
        ScriptSection(label="Hook", timecode="0:00–0:05", text=hook),
        ScriptSection(label="Beat 1 — X Trends", timecode="0:05–0:20", text=beat1),
        ScriptSection(label="Beat 2 — Google Trends", timecode="0:20–0:35", text=beat2),
        ScriptSection(label="Beat 3 — Insight", timecode="0:35–0:45", text=beat3),
        ScriptSection(label="CTA", timecode="0:45–0:50", text=cta),
    ]

    full_text = "\n\n".join(f"[{s.label} | {s.timecode}]\n{s.text}" for s in sections)
    word_count = sum(len(s.text.split()) for s in sections)

    title_topic = top_x[0].name if top_x else (top_g[0].title if top_g else "Tren Hari Ini")
    title = f"Tren Indonesia hari ini: {title_topic} & lainnya (50 detik)"

    return ShortsScript(
        title=title,
        sections=sections,
        duration_seconds=50,
        word_count=word_count,
        full_text=full_text,
        sources={
            "twitter": [t.name for t in top_x],
            "google": [t.title for t in top_g],
        },
    )

"""FastAPI app exposing the trends dashboard backend."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .cache import TTLCache
from .google_trends import fetch_google_trends
from .script_generator import generate_script
from .twitter_trends import fetch_twitter_trends

log = logging.getLogger("trend-id")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(title="Trend ID Dashboard", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

cache = TTLCache(ttl_seconds=600)  # 10 minutes


class ScriptRequest(BaseModel):
    top_n: int = Field(default=3, ge=1, le=10)


@app.get("/")
async def root() -> dict:
    return {
        "service": "trend-id-dashboard",
        "version": "0.1.0",
        "endpoints": ["/api/health", "/api/trends/twitter", "/api/trends/google", "/api/script"],
    }


@app.get("/api/health")
async def health() -> dict:
    return {"ok": True, "time": datetime.now(UTC).isoformat()}


async def _get_twitter_cached() -> list[dict]:
    cached = cache.get("twitter")
    if cached is not None:
        return cached
    try:
        trends = await fetch_twitter_trends()
    except Exception as exc:  # noqa: BLE001
        log.exception("Failed to fetch Twitter trends: %s", exc)
        raise HTTPException(status_code=502, detail=f"Twitter trends fetch failed: {exc}") from exc
    data = [t.to_dict() for t in trends]
    cache.set("twitter", data)
    return data


async def _get_google_cached() -> list[dict]:
    cached = cache.get("google")
    if cached is not None:
        return cached
    try:
        trends = await fetch_google_trends()
    except Exception as exc:  # noqa: BLE001
        log.exception("Failed to fetch Google trends: %s", exc)
        raise HTTPException(status_code=502, detail=f"Google trends fetch failed: {exc}") from exc
    data = [t.to_dict() for t in trends]
    cache.set("google", data)
    return data


@app.get("/api/trends/twitter")
async def twitter_endpoint() -> dict:
    data = await _get_twitter_cached()
    return {
        "source": "trends24.in/indonesia",
        "country": "ID",
        "fetched_at": datetime.now(UTC).isoformat(),
        "count": len(data),
        "trends": data,
    }


@app.get("/api/trends/google")
async def google_endpoint() -> dict:
    data = await _get_google_cached()
    return {
        "source": "trends.google.com/trending/rss?geo=ID",
        "country": "ID",
        "fetched_at": datetime.now(UTC).isoformat(),
        "count": len(data),
        "trends": data,
    }


@app.post("/api/script")
async def script_endpoint(req: ScriptRequest | None = None) -> dict:
    req = req or ScriptRequest()
    twitter_data = await _get_twitter_cached()
    google_data = await _get_google_cached()

    # Reconstruct dataclasses for the generator.
    from .google_trends import GoogleTrend, NewsItem
    from .twitter_trends import TwitterTrend

    twitter = [TwitterTrend(**t) for t in twitter_data]
    google = [
        GoogleTrend(
            rank=g["rank"],
            title=g["title"],
            traffic=g.get("traffic"),
            pub_date=g.get("pub_date"),
            picture=g.get("picture"),
            news=[NewsItem(**n) for n in g.get("news", [])],
        )
        for g in google_data
    ]
    script = generate_script(twitter, google, top_n=req.top_n)
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "script": script.to_dict(),
    }


@app.post("/api/refresh")
async def refresh() -> dict:
    """Force-clear the cache so the next call refetches from upstream."""
    cache.clear()
    return {"cleared": True, "time": datetime.now(UTC).isoformat()}

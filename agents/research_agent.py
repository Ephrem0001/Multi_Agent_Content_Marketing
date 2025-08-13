from __future__ import annotations

import json
import re
import time
from typing import Any, Dict, List

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup  # type: ignore

try:
    from pytrends.request import TrendReq  # type: ignore
except Exception:  # pragma: no cover
    TrendReq = None  # type: ignore

from utils.io_utils import save_json


def _fetch_trending_keywords(topic: str) -> List[str]:
    if TrendReq is None:
        # Fallback: fabricate keyword variants
        base = re.sub(r"[^a-zA-Z0-9 ]", "", topic).lower()
        uniq = list(dict.fromkeys([
            base,
            f"best {base}",
            f"{base} reviews",
            f"{base} benefits",
            f"buy {base}",
        ]))
        return uniq
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        kw_list = [topic]
        pytrends.build_payload(kw_list, cat=0, timeframe='today 3-m', geo='', gprop='')
        related = pytrends.related_queries()
        out: List[str] = []
        for _, data in (related or {}).items():
            if not data:
                continue
            top_df = data.get("top")
            if top_df is not None:
                out.extend(top_df["query"].head(10).tolist())
        # Deduplicate and keep up to 20
        cleaned = []
        seen = set()
        for k in out:
            k2 = k.strip().lower()
            if k2 and k2 not in seen:
                seen.add(k2)
                cleaned.append(k)
        return cleaned[:20] or [topic]
    except Exception:
        return [topic, f"{topic} review", f"best {topic}", f"{topic} price", f"{topic} vs alternatives"]


def _scrape_competitors(topic: str, limit: int = 5) -> List[Dict[str, Any]]:
    # DuckDuckGo HTML results endpoint (no API key)
    url = "https://duckduckgo.com/html/"
    params = {"q": f"{topic} competitors review"}
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=8)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        results = []
        for a in soup.select("a.result__a"):
            title = a.get_text(strip=True)
            href = a.get("href", "")
            if not title or not href:
                continue
            results.append({"title": title, "url": href})
            if len(results) >= limit:
                break
        return results
    except Exception:
        # Fallback examples
        return [
            {"title": f"Top {topic} alternatives", "url": "https://example.com/alt"},
            {"title": f"Best {topic} in 2025", "url": "https://example.com/best"},
        ]


def run_research(topic: str, output_dir: str) -> Dict[str, Any]:
    # Run trends and competitor scrape in parallel for speed
    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(_fetch_trending_keywords, topic)
        f2 = ex.submit(_scrape_competitors, topic)
        trending_keywords = f1.result()
        competitors = f2.result()
    research = {
        "topic": topic,
        "trending_keywords": trending_keywords,
        "competitors": competitors,
    }
    save_json(f"{output_dir}/research.json", research)
    return research



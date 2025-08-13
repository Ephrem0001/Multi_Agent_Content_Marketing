from __future__ import annotations

import os
from typing import Any, Dict

import requests

from utils.io_utils import save_base64_image


def _summarize_for_prompt(blog_md: str) -> str:
    # Heuristic summary for image prompt
    lines = [l.strip() for l in blog_md.splitlines() if l.strip()]
    title = lines[0] if lines else "Hero Image"
    keywords = []
    for l in lines[:50]:
        if len(keywords) > 20:
            break
        if len(l.split()) >= 2:
            keywords.extend(l.split()[:2])
    primary = " ".join(keywords[:12])
    return f"{title}, {primary}, clean composition, modern, high contrast, photorealistic, 35mm, 4k"


def generate_image(blog_md: str, output_dir: str) -> Dict[str, Any]:
    sd_url = os.getenv("SD_WEBUI_URL", "http://127.0.0.1:7860").rstrip("/")
    endpoint = f"{sd_url}/sdapi/v1/txt2img"

    prompt = _summarize_for_prompt(blog_md)
    payload = {
        "prompt": prompt,
        "width": 768,
        "height": 512,
        "steps": 25,
        "cfg_scale": 7.0,
        "sampler_name": "Euler a",
    }

    try:
        resp = requests.post(endpoint, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        images = data.get("images", [])
        if not images:
            return {"status": "no_images"}
        # Save first image
        hero_path = f"{output_dir}/hero.png"
        save_base64_image(hero_path, images[0])
        return {"status": "ok", "hero_image": hero_path}
    except Exception:
        return {"status": "skipped"}



from __future__ import annotations

from typing import Any, Dict, List

from utils.io_utils import save_json
from utils.llm import LocalLLM


def _build_social_prompt(topic: str, blog_md: str) -> str:
    return (
        "SYSTEM: Social media strategist.\n"
        "TASK: Create 3 tweets, 2 LinkedIn posts, and 3 Instagram captions based on the blog content.\n"
        "STYLE: Punchy, value-driven, with clear hooks and hashtags.\n\n"
        f"TOPIC: {topic}\n\n"
        "BLOG_SNIPPET:\n" + blog_md[:2000] + "\n\n"
        "OUTPUT:\n"
        "SOCIAL_SNIPPETS\n"
    )


def _fallback_social(topic: str) -> Dict[str, List[str]]:
    base = topic.strip().capitalize()
    tweets = [
        f"{base}: what to know in 60s ⏱️ #HowTo",
        f"Why {base} matters in 2025 — practical tips inside. #Growth",
        f"{base} checklist you can actually use. Save this! #Productivity",
    ]
    linkedin = [
        f"We just published a practical guide to {base}. It covers benefits, how-to, and a quick comparison. Read the highlights and contribute your insights.",
        f"Looking to adopt {base}? Start with the fundamentals, align your goals, and ship a small pilot. Our guide breaks it down step-by-step.",
    ]
    instagram = [
        f"{base} made simple. Swipe for the essentials. #LearnByDoing",
        f"3 tips to get started with {base} today. #QuickWins",
        f"From zero to confident with {base}. Save for later! #Guide",
    ]
    return {"tweets": tweets, "linkedin_posts": linkedin, "instagram_captions": instagram}


def generate_social(topic: str, blog_md: str, output_dir: str) -> Dict[str, Any]:
    llm = LocalLLM()
    if llm.is_available():
        prompt = _build_social_prompt(topic, blog_md)
        raw = llm.generate(prompt, max_tokens=384)
        # Very light parsing for the structured list outputs
        tweets, linkedin, instagram = [], [], []
        bucket = None
        for line in raw.splitlines():
            l = line.strip()
            if not l:
                continue
            lower = l.lower()
            if lower.startswith("tweets"):
                bucket = "tweets"; continue
            if lower.startswith("linkedin"):
                bucket = "linkedin"; continue
            if lower.startswith("instagram"):
                bucket = "instagram"; continue
            if l.startswith("-"):
                item = l[1:].strip()
            else:
                item = l
            if bucket == "tweets":
                tweets.append(item)
            elif bucket == "linkedin":
                linkedin.append(item)
            elif bucket == "instagram":
                instagram.append(item)
        # Minimum viable count fallback
        if len(tweets) < 3 or len(linkedin) < 2 or len(instagram) < 3:
            data = _fallback_social(topic)
        else:
            data = {
                "tweets": tweets[:3],
                "linkedin_posts": linkedin[:2],
                "instagram_captions": instagram[:3],
            }
    else:
        data = _fallback_social(topic)

    save_json(f"{output_dir}/social.json", data)
    return data



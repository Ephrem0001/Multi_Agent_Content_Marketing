from __future__ import annotations

from typing import Any, Dict, List

from utils.io_utils import save_json, save_text
from utils.llm import LocalLLM


def _build_blog_prompt(topic: str, keywords: List[str], competitors: List[Dict[str, str]]) -> str:
    comp_lines = "\n".join(f"- {c.get('title','')} ({c.get('url','')})" for c in competitors[:5])
    kw_line = ", ".join(keywords[:12])
    return (
        "SYSTEM: You are an expert marketing writer.\n"  # guidance
        "TASK: Write a comprehensive blog post in Markdown. Include headings, bullet points, and a clear CTA.\n"
        "STYLE: Helpful, concise, SEO-friendly.\n\n"
        f"TOPIC: {topic}\n"
        f"KEYWORDS: {kw_line}\n"
        f"COMPETITORS:\n{comp_lines}\n\n"
        "OUTPUT_FORMAT: Start with a strong H1. Provide sections (Intro, Benefits, How-To, Comparison, FAQs, Conclusion).\n"
        "INCLUDE: A brief meta title and meta description at the end as \n"
        "'SEO TITLE: ...' and 'SEO DESCRIPTION: ...'.\n\n"
        "BLOG_POST:"
    )


def generate_blog(topic: str, research: Dict[str, Any], output_dir: str) -> Dict[str, Any]:
    llm = LocalLLM()
    keywords = research.get("trending_keywords", [])
    competitors = research.get("competitors", [])
    prompt = _build_blog_prompt(topic, keywords, competitors)
    blog_md = llm.generate(prompt, max_tokens=min(600, llm.max_tokens_default))

    # Extract SEO tags if present in output
    seo_title = None
    seo_description = None
    for line in blog_md.splitlines()[-10:]:
        line_low = line.strip().lower()
        if line_low.startswith("seo title:"):
            seo_title = line.split(":", 1)[1].strip()
        if line_low.startswith("seo description:"):
            seo_description = line.split(":", 1)[1].strip()

    if not seo_title:
        seo_title = f"{topic} — A Practical Guide"
    if not seo_description:
        seo_description = (
            f"Explore {topic}: key benefits, how to choose, and answers to common questions."
        )

    seo = {
        "title": seo_title,
        "meta_description": seo_description,
        "keywords": keywords[:15],
    }

    save_text(f"{output_dir}/blog.md", blog_md)
    save_json(f"{output_dir}/seo.json", seo)
    return {"blog_md": blog_md, "seo": seo}



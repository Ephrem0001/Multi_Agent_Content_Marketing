from __future__ import annotations

from typing import Any, Dict

from langgraph.graph import StateGraph, END  # type: ignore

from agents.research_agent import run_research
from agents.content_writer import generate_blog
from agents.social_media_agent import generate_social
from agents.image_agent import generate_image


def build_graph(include_image: bool = True):
    # State is a simple dictionary carried across nodes
    def research_node(state: Dict[str, Any]) -> Dict[str, Any]:
        topic = state["topic"]
        out_dir = state["output_dir"]
        research = run_research(topic, out_dir)
        # Propagate essential keys forward so downstream nodes always have them
        return {"topic": topic, "output_dir": out_dir, "research": research}

    def content_node(state: Dict[str, Any]) -> Dict[str, Any]:
        topic = state["topic"]
        out_dir = state["output_dir"]
        research = state["research"]
        content = generate_blog(topic, research, out_dir)
        return {"topic": topic, "output_dir": out_dir, "content": content}

    def social_node(state: Dict[str, Any]) -> Dict[str, Any]:
        topic = state["topic"]
        out_dir = state["output_dir"]
        blog_md = state["content"]["blog_md"]
        social = generate_social(topic, blog_md, out_dir)
        return {"topic": topic, "output_dir": out_dir, "social": social}

    def image_node(state: Dict[str, Any]) -> Dict[str, Any]:
        topic = state["topic"]
        out_dir = state["output_dir"]
        blog_md = state["content"]["blog_md"]
        image = generate_image(blog_md, out_dir)
        return {"topic": topic, "output_dir": out_dir, "images": image}

    graph = StateGraph(dict)
    graph.add_node("research", research_node)
    graph.add_node("content", content_node)
    graph.add_node("social", social_node)
    if include_image:
        graph.add_node("image", image_node)

    graph.set_entry_point("research")
    graph.add_edge("research", "content")
    # After content, run social and image in parallel
    graph.add_edge("content", "social")
    if include_image:
        graph.add_edge("content", "image")

    # Both branches end the graph
    graph.add_edge("social", END)
    if include_image:
        graph.add_edge("image", END)

    return graph.compile()



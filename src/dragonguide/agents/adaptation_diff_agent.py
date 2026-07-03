"""AdaptationDiffAgent — compares book canon vs. show; flags divergences."""
from __future__ import annotations

from google.adk.agents import LlmAgent

from ..config import GEMINI_MODEL


def build_adaptation_diff_agent() -> LlmAgent:
    return LlmAgent(
        name="AdaptationDiffAgent",
        model=GEMINI_MODEL,
        description="Identifies invented / changed / omitted beats vs. the book.",
        instruction=(
            "Compare the show events transcripts against the canonical lore notes.\n"
            "Transcripts:\n{transcripts}\n\n"
            "Lore Notes:\n{lore_notes}\n\n"
            "Produce a list of BookVsShowItem objects, each tagged type=invented|changed|omitted, "
            "with a short detail and a source URL from the lore notes. "
            "Be precise and only assert divergences you can support from the provided material. "
            "Your output will be saved as the state['book_vs_show'] list of BookVsShowItem objects."
        ),
        output_key="book_vs_show",
    )

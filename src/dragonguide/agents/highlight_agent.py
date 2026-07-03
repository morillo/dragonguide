"""HighlightAgent — produces the summary + timestamped 'watch-for-this' items.

The timestamped, source-linked callouts are DragonGuide's killer feature:
"At ~14:30, watch for X — it matters because of Y."
"""
from __future__ import annotations

from google.adk.agents import LlmAgent

from ..config import GEMINI_MODEL
from ..schemas import EpisodeGuide


def build_highlight_agent() -> LlmAgent:
    return LlmAgent(
        name="HighlightAgent",
        model=GEMINI_MODEL,
        description="Writes the episode summary and timestamped watch-for callouts.",
        instruction=(
            "You are working on House of the Dragon Season 3, Episode {current_episode}.\n"
            "Synthesize a concise, spoiler-free-by-construction summary for this episode, "
            "plus a list of WatchForItem callouts.\n\n"
            "Here is the context gathered so far:\n"
            "- Transcripts:\n{transcripts}\n\n"
            "- Lore Notes:\n{lore_notes}\n\n"
            "- Book vs. Show Differences:\n{book_vs_show}\n\n"
            "For each WatchForItem callout, include:\n"
            "1. timestamp (MM:SS formatting)\n"
            "2. what happens that the viewer should notice\n"
            "3. why it matters to the larger story\n"
            "4. importance (high|medium|low)\n"
            "5. payoff_episode (the Season 3 episode number where this foreshadowing/glance/action resolves or pays off)\n"
            "6. source URL (prefer a YouTube URL from the transcripts)\n\n"
            "Assemble everything into a single, fully structured EpisodeGuide schema. "
            "Set the episode field to {current_episode}. "
            "Make sure to copy the book_vs_show differences list into the book_vs_show field. "
            "Gather all unique source URLs into the sources list field. "
            "Do NOT self-censor future events here — the SpoilerGuard handles that next; "
            "your job is completeness and accurate payoff_episode tagging for each callout. "
            "Your output will be saved as the state['draft_guide'] EpisodeGuide object."
        ),
        # output_schema enforces the structured contract on this agent's output.
        output_schema=EpisodeGuide,
        output_key="draft_guide",
    )

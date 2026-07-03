"""Structured output contract for DragonGuide.

Everything in the pipeline conforms to these models. Keeping a single,
typed contract is what lets the agents stay decoupled: each agent fills in
its slice, and the SpoilerGuard can reason over a predictable shape.
"""
from __future__ import annotations

from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class Importance(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class WatchForItem(BaseModel):
    """A single 'pay attention to this' callout for the viewer."""
    timestamp: str = Field(..., description="MM:SS within the episode / clip")
    what: str = Field(..., description="What happens that the viewer should notice")
    why: str = Field(..., description="Why it matters to the larger story")
    importance: Importance = Importance.MEDIUM
    # The episode where this beat pays off. The SpoilerGuard uses this to
    # decide whether the item is safe to show given the user's current episode.
    payoff_episode: int = Field(..., description="Episode where this foreshadowing resolves")
    source: str = Field(..., description="Source URL (e.g. YouTube deep-link with ?t=)")


class BookVsShowItem(BaseModel):
    """One book-vs-show divergence."""
    type: Literal["invented", "changed", "omitted"]
    detail: str
    source: str = Field(..., description="Wiki / Fire & Blood reference URL")


class EpisodeGuide(BaseModel):
    """The full, spoiler-safe response returned to the UI."""
    episode: int
    summary: str = ""
    watch_for: List[WatchForItem] = Field(default_factory=list)
    book_vs_show: List[BookVsShowItem] = Field(default_factory=list)
    sources: List[str] = Field(default_factory=list)
    redacted_count: int = 0  # how many items the SpoilerGuard removed (shown in UI)

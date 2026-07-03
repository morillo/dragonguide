"""Security layer: spoiler guardrails + input-safety helpers.

This module backs the project's "Security features" concept. It does two things:

1. Filters any EpisodeGuide so nothing references events past the user's
   current episode (or unaired book material). Used by SpoilerGuardAgent AND as
   an in-flight ADK callback (defense in depth).
2. Treats fetched external text as untrusted (prompt-injection mitigation).
"""
from __future__ import annotations

import re
from typing import Any, Optional

from .schemas import EpisodeGuide


# Phrases in fetched text that indicate an attempt to hijack the agent.
_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous\s+)?instructions",
    r"system prompt",
    r"you are now",
    r"disregard",
]


def sanitize_external_text(text: str) -> str:
    """Neutralize obvious prompt-injection in fetched transcripts/wiki text.

    We don't delete content (that would harm summaries); we defang it by
    annotating, so the model treats it as quoted data, not commands.
    """
    cleaned = text
    for pat in _INJECTION_PATTERNS:
        cleaned = re.sub(pat, "[redacted-instruction]", cleaned, flags=re.IGNORECASE)
    return cleaned


def enforce_spoiler_boundary(guide: EpisodeGuide, current_episode: int) -> EpisodeGuide:
    """Remove anything that pays off after the user's current episode or reveals future/unaired events.

    This is the core safety invariant of the product and is covered by
    tests/test_spoiler_guard.py with adversarial cases.
    """
    redacted = 0

    # Patterns indicating future spoilers or unaired book material
    future_indicators = [
        r"later in the (book|story|season)",
        r"eventually",
        r"unaired",
        r"end of the (book|war|season)",
        r"book spoiler",
        r"next[- ]episode",
        r"trailer for",
        r"preview of",
        r"promo for",
        r"foreshadows?.*?\bdeath\b",
        r"will die",
        r"dies later",
    ]

    def is_spoiler(text: str) -> bool:
        # Check explicit episode number mentions
        match = re.search(r"episode\s*(\d+)", text, re.IGNORECASE)
        if match:
            ep = int(match.group(1))
            if ep > current_episode:
                return True
        # Check future indicator keywords
        for pattern in future_indicators:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    safe_watch = []
    for item in guide.watch_for:
        # Check payoff episode threshold
        if item.payoff_episode > current_episode:
            redacted += 1
            continue
        # Scan text for future indicators
        if is_spoiler(item.what) or is_spoiler(item.why):
            redacted += 1
            continue
        safe_watch.append(item)
    guide.watch_for = safe_watch

    # Book-vs-show items must not reveal unaired adaptations.
    safe_diff = []
    for d in guide.book_vs_show:
        if is_spoiler(d.detail):
            redacted += 1
            continue
        safe_diff.append(d)
    guide.book_vs_show = safe_diff

    guide.redacted_count = redacted
    return guide


def spoiler_after_tool_callback(
    tool: Any, args: dict, tool_context: Any, tool_response: Any
) -> Optional[Any]:
    """ADK after_tool_callback hook.

    Runs after each tool call. If a tool returns structured guide data, we
    re-apply the spoiler boundary in-flight so nothing leaks between stages.
    Return None to keep the original response, or a modified response to swap it.
    The exact signature follows your installed ADK version — adjust if needed.
    """
    current_episode = getattr(tool_context, "state", {}).get("current_episode")
    if current_episode is None:
        return None
    if isinstance(tool_response, EpisodeGuide):
        return enforce_spoiler_boundary(tool_response, current_episode)
    return None

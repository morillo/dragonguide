"""SpoilerGuardAgent — the final security gate.

Takes the draft EpisodeGuide and the user's current_episode and removes anything
that pays off later, then reports how many items were redacted. This is the
product's core safety invariant and is exercised by tests/test_spoiler_guard.py.

Implemented as a BaseAgent so we run deterministic Python (the spoiler rule must
be provable, not left to model discretion).
"""
from __future__ import annotations

from typing import AsyncGenerator

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event, EventActions

from ..guardrails import enforce_spoiler_boundary
from ..schemas import EpisodeGuide


class SpoilerGuardAgent(BaseAgent):
    """Deterministic final gate over the draft guide."""

    async def _run_async_impl(
        self, ctx: InvocationContext
    ) -> AsyncGenerator[Event, None]:
        state = ctx.session.state
        current_episode = int(state.get("current_episode", 1))

        draft = state.get("draft_guide")
        guide = draft if isinstance(draft, EpisodeGuide) else EpisodeGuide(**draft)

        # The single source of truth for the spoiler rule lives in guardrails.py.
        safe = enforce_spoiler_boundary(guide, current_episode)

        # Emit a final event containing the state delta to persist final_guide.
        yield Event(
            author=self.name,
            actions=EventActions(state_delta={"final_guide": safe.model_dump()})
        )


def build_spoiler_guard_agent() -> SpoilerGuardAgent:
    return SpoilerGuardAgent(name="SpoilerGuardAgent")

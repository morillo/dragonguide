"""Command line entry point for DragonGuide.

Exposes a CLI companion that runs the multi-agent pipeline and outputs the
structured guide as JSON.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from google.adk.runners import InMemoryRunner
from google.genai import types

from dragonguide.schemas import EpisodeGuide
from dragonguide.config import AIRED_EPISODES


async def run_pipeline(episode: int, message: str) -> EpisodeGuide:
    from dragonguide.coordinator import build_root_agent
    root_agent = build_root_agent()
    runner = InMemoryRunner(agent=root_agent, app_name="dragonguide")
    session = await runner.session_service.create_session(
        app_name="dragonguide",
        user_id="cli_user",
        state={"current_episode": episode}
    )
    content = types.Content(role="user", parts=[types.Part(text=message)])
    async for _ in runner.run_async(
        user_id="cli_user", session_id=session.id, new_message=content
    ):
        pass
    final = (await runner.session_service.get_session(
        app_name="dragonguide", user_id="cli_user", session_id=session.id
    )).state.get("final_guide", {})
    return EpisodeGuide(**final) if final else EpisodeGuide(episode=episode)


def main() -> None:
    parser = argparse.ArgumentParser(description="DragonGuide CLI companion.")
    parser.add_argument("--episode", type=int, required=True, help="Current episode number")
    parser.add_argument("--message", type=str, default="What should I watch for?", help="User query message")
    args = parser.parse_args()

    episode = args.episode
    if episode > AIRED_EPISODES:
        print(f"hasn't aired; showing Episode {AIRED_EPISODES}")
        episode = AIRED_EPISODES

    from dragonguide import config
    if config.OFFLINE:
        from dragonguide.offline import build_offline_guide
        guide = build_offline_guide(episode)
    else:
        guide = asyncio.run(run_pipeline(episode, args.message))
    print(json.dumps(guide.model_dump(), indent=2))


if __name__ == "__main__":
    main()

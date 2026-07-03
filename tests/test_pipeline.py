"""End-to-end offline smoke test against fixtures.

Runs the full pipeline in DRAGONGUIDE_OFFLINE=1 mode and asserts that a
well-formed, spoiler-safe EpisodeGuide is produced.
"""
from __future__ import annotations

import os
import pytest

os.environ.setdefault("DRAGONGUIDE_OFFLINE", "1")


def test_full_pipeline_offline(monkeypatch):
    import app
    import asyncio
    from dragonguide import config

    # 1. Force OFFLINE mode
    monkeypatch.setattr(config, "OFFLINE", True)

    # 2. Call the real app._run (which routes to build_offline_guide under the hood)
    guide = asyncio.run(app._run(current_episode=1, user_msg="What should I watch for?"))

    # 3. Assertions
    assert guide.episode == 1
    assert guide.summary
    assert len(guide.watch_for) > 0
    assert all(w.payoff_episode <= 1 for w in guide.watch_for)


def test_search_official_hotd_videos_catalog(tmp_path, monkeypatch):
    import json
    import mcp_server.server as server

    # Mock catalog
    mock_catalog = {
        "_official_channels": ["hbo"],
        "_comment": "test comment",
        "s3e1": [
            {"type": "sneak_peek", "url": "https://www.youtube.com/watch?v=1"},
            {"type": "inside_the_episode", "url": ""}
        ],
        "s3e2": [
            {"type": "sneak_peek", "url": ""},
            {"type": "inside_the_episode", "url": ""}
        ]
    }

    # Setup monkeypatch
    monkeypatch.setattr(server, "DATA", tmp_path)
    monkeypatch.setattr(server, "FIXTURES", tmp_path / "fixtures")
    (tmp_path / "fixtures").mkdir(parents=True, exist_ok=True)
    (tmp_path / "official_videos.json").write_text(json.dumps(mock_catalog))

    # Disable network lookups in test
    monkeypatch.setattr(server, "OFFLINE", True)

    # 1. Episode 1 has a mix of empty and real URLs -> should return only the real ones (usable is non-empty)
    res_ep1 = server.search_official_hotd_videos(episode_number=1, season=3)
    assert len(res_ep1) == 1
    assert res_ep1[0]["url"] == "https://www.youtube.com/watch?v=1"

    # 2. Episode 2 has only empty URLs -> should return empty list (does not return the placeholder/empty objects)
    res_ep2 = server.search_official_hotd_videos(episode_number=2, season=3)
    assert res_ep2 == []


def test_offline_empty_urls_serve_fixtures_not_fake_links(tmp_path, monkeypatch):
    import json
    import mcp_server.server as server

    # 1. Setup DATA and FIXTURES paths
    monkeypatch.setattr(server, "DATA", tmp_path)
    monkeypatch.setattr(server, "FIXTURES", tmp_path / "fixtures")
    (tmp_path / "fixtures").mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(server, "OFFLINE", True)

    # 2. Write official_videos.json with _about key and s3e2 empty urls
    mock_catalog = {
        "_about": "Official Curated Catalog",
        "s3e2": [
            {"type": "sneak_peek", "url": ""},
            {"type": "inside_the_episode", "url": ""}
        ]
    }
    (tmp_path / "official_videos.json").write_text(json.dumps(mock_catalog))

    # 3. Write fixtures/transcripts.json
    mock_transcripts = {
        "EXAMPLEID04": {
            "video": "EXAMPLEID04",
            "title": "House of the Dragon S3E2 | Inside the Episode",
            "text": "Beat 1",
            "source": "https://source"
        },
        "EXAMPLEID05": {
            "video": "EXAMPLEID05",
            "title": "House of the Dragon S3E2 | Sneak Peek",
            "text": "Beat 2",
            "source": "https://source"
        }
    }
    (tmp_path / "fixtures" / "transcripts.json").write_text(json.dumps(mock_transcripts))

    # 4. Call tool
    res = server.search_official_hotd_videos(episode_number=2, season=3)
    assert len(res) == 2
    for entry in res:
        assert "watch?v=" not in entry["url"]
        assert entry["source"] == "fixture://transcripts"
        assert entry["url"] in ["EXAMPLEID04", "EXAMPLEID05"]


def test_respond_clamps_unaired_episodes(monkeypatch):
    import app
    from dragonguide.config import AIRED_EPISODES
    from dragonguide.schemas import EpisodeGuide

    # Mock _run so it doesn't execute live LLM calls
    async def mock_run(current_episode, user_msg):
        return EpisodeGuide(episode=current_episode, summary="Clamped summary")

    monkeypatch.setattr(app, "_run", mock_run)

    # Call respond for an unaired episode (e.g. Episode 5)
    # This should run the pipeline for AIRED_EPISODES instead of Episode 5
    guide_html, banner_html = app.respond(f"Season 3, Episode {AIRED_EPISODES + 3}", "What should I watch for?")

    # Assert that the clamping notice is present in the rendered HTML
    assert f"Season 3, Episode {AIRED_EPISODES + 3}" in guide_html
    assert "hasn't aired yet" in guide_html
    assert f"Episode {AIRED_EPISODES}" in guide_html


def test_spoiler_guard_agent_runner():
    """Verify that SpoilerGuardAgent filters future details and reports redacted count correctly.

    Runs end-to-end using InMemoryRunner to drive the safety state logic.
    """
    import asyncio
    from google.genai import types
    from dragonguide.agents.spoiler_guard_agent import build_spoiler_guard_agent
    from dragonguide.schemas import EpisodeGuide, WatchForItem, Importance, BookVsShowItem
    from google.adk.runners import InMemoryRunner

    async def _run_test():
        agent = build_spoiler_guard_agent()
        runner = InMemoryRunner(agent=agent, app_name="test_app")

        draft = EpisodeGuide(
            episode=1,
            summary="Draft Summary",
            watch_for=[
                WatchForItem(timestamp="10:00", what="Safe Highlight", why="safe", importance=Importance.HIGH, payoff_episode=1, source="https://s"),
                WatchForItem(timestamp="20:00", what="Spoiler Highlight", why="spoiler", importance=Importance.HIGH, payoff_episode=3, source="https://s")
            ],
            book_vs_show=[
                BookVsShowItem(type="invented", detail="Safe book deviation", source="https://w"),
                BookVsShowItem(type="changed", detail="Spoiler book deviation in Episode 4", source="https://w")
            ]
        )

        session = await runner.session_service.create_session(
            app_name="test_app",
            user_id="test_user",
            state={"current_episode": 1, "draft_guide": draft.model_dump()}
        )

        # Drive execution of the SpoilerGuardAgent
        content = types.Content(role="user", parts=[types.Part(text="Filter please")])
        async for _ in runner.run_async(user_id="test_user", session_id=session.id, new_message=content):
            pass

        final_session = await runner.session_service.get_session(
            app_name="test_app", user_id="test_user", session_id=session.id
        )
        final_guide_dict = final_session.state.get("final_guide")
        assert final_guide_dict is not None
        assert final_guide_dict["redacted_count"] == 2
        assert len(final_guide_dict["watch_for"]) == 1
        assert len(final_guide_dict["book_vs_show"]) == 1
        assert final_guide_dict["watch_for"][0]["what"] == "Safe Highlight"
        assert final_guide_dict["book_vs_show"][0]["detail"] == "Safe book deviation"

    asyncio.run(_run_test())

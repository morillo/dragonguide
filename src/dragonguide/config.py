"""Central configuration, all sourced from environment (never hard-coded secrets)."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # reads .env if present; in prod, env vars are set by the platform

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
FIXTURES_DIR = DATA_DIR / "fixtures"
CACHE_DIR = DATA_DIR / "cache"
OFFICIAL_VIDEOS = DATA_DIR / "official_videos.json"

# Model selection: default to a cheap/fast Gemini model; allow override.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # absent => offline/fixture mode
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Offline mode forces fixture-backed tools when specified or when no credentials are found.
OFFLINE = os.getenv("DRAGONGUIDE_OFFLINE", "0") == "1" or (
    not GEMINI_API_KEY and os.getenv("GOOGLE_GENAI_USE_VERTEXAI") != "True"
)

# Dynamic episode configuration:
# AIRED_EPISODES is bumped by 1 each week as new episodes air.
AIRED_EPISODES = int(os.getenv("DRAGONGUIDE_AIRED_EPISODES", "2"))
# SEASON_EPISODES is a projected upper bound only for the user interface selector.
SEASON_EPISODES = int(os.getenv("DRAGONGUIDE_SEASON_EPISODES", "8"))

# Path to the MCP server we launch over stdio.
MCP_SERVER_PATH = str(ROOT / "mcp_server" / "server.py")

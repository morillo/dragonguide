"""TranscriptionAgent — fetches official HBO YouTube caption text via MCP.

Demonstrates ADK <-> MCP integration: the agent gets its tools from our MCP
server through McpToolset, never touching the network itself. Caption TEXT only
is fetched; we never download or re-host copyrighted audio/video.
"""
from __future__ import annotations

import sys
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

from ..config import GEMINI_MODEL, MCP_SERVER_PATH


def _mcp_tools() -> McpToolset:
    """Connect to our local MCP server over stdio and expose its tools to ADK."""
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(command=sys.executable, args=[MCP_SERVER_PATH]),
        ),
        # Only expose the YouTube-related tools to this agent (least privilege).
        tool_filter=["search_official_hotd_videos", "fetch_youtube_transcript"],
    )


def build_transcription_agent() -> LlmAgent:
    return LlmAgent(
        name="TranscriptionAgent",
        model=GEMINI_MODEL,
        description="Gathers official HBO YouTube caption text for the episode.",
        instruction=(
            "You are a strict data-gathering agent for House of the Dragon Season 3, Episode {current_episode}.\n"
            "Your ONLY task is to call search_official_hotd_videos(episode_number={current_episode}) to find the official video URLs.\n"
            "Once you get the list of URLs, you must call fetch_youtube_transcript for each video URL.\n"
            "Do NOT write any conversational text, introductions, or explanations. "
            "You MUST call the tools. Do not output anything until you have fetched the transcripts. "
            "Once you have the transcripts, output the concatenated transcript texts paired with their source URLs."
        ),
        tools=[_mcp_tools()],
        output_key="transcripts",
    )

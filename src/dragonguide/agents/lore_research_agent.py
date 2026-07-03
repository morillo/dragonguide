"""LoreResearchAgent — looks up canonical Fire & Blood lore via MCP.

Summarizes and LINKS to A Wiki of Ice and Fire; never bulk-copies passages.
"""
from __future__ import annotations

import sys
from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset, StdioConnectionParams
from mcp import StdioServerParameters

from ..config import GEMINI_MODEL, MCP_SERVER_PATH


def _mcp_tools() -> McpToolset:
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(command=sys.executable, args=[MCP_SERVER_PATH]),
        ),
        tool_filter=["lookup_lore"],  # least privilege: only the wiki tool
    )


def build_lore_research_agent() -> LlmAgent:
    return LlmAgent(
        name="LoreResearchAgent",
        model=GEMINI_MODEL,
        description="Finds canonical Fire & Blood events behind the episode.",
        instruction=(
            "You are a lore research agent for House of the Dragon Season 3, Episode {current_episode}.\n"
            "Here are the transcripts for this episode:\n{transcripts}\n\n"
            "Using these transcripts, identify the key names, events, and lore topics mentioned. "
            "For each topic, call lookup_lore(query=topic) to get the canonical Fire & Blood lore from the wiki.\n"
            "Do NOT write conversational filler or say what you are going to do. "
            "You MUST call lookup_lore. Do not output anything until you have retrieved the lore.\n"
            "Once you have the lore details, output a summarized list of lore notes with their wiki source URLs."
        ),
        tools=[_mcp_tools()],
        output_key="lore_notes",
    )

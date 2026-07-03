# DragonGuide MCP Server

Exposes three tools over stdio for the ADK agents:

| Tool | Purpose |
|---|---|
| `search_official_hotd_videos(episode_number, season=3)` | Curated official HBO YouTube URLs per episode |
| `fetch_youtube_transcript(video_url_or_id)` | Caption **text** only (never re-hosts media); caches to `data/cache/` |
| `lookup_lore(query)` | Summarized + linked Fire & Blood / A Wiki of Ice and Fire lore |

## Run standalone
```bash
python mcp_server/server.py   # stdio transport
```

## Offline mode
With no `YOUTUBE_API_KEY` (or `DRAGONGUIDE_OFFLINE=1`), all tools read from
`data/fixtures/`, so the full demo runs reproducibly without any keys.

## Inspect with the MCP Inspector (optional)
```bash
npx @modelcontextprotocol/inspector python mcp_server/server.py
```

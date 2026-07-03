# DragonGuide — Architecture

## System diagram (Mermaid)

> Source also in `docs/architecture.mmd`. Renders automatically on GitHub.

```mermaid
flowchart TD
    U([Viewer: \"I'm on Episode N\"]):::user

    subgraph UI[Gradio Chat UI]
      U --> APP[app.py]
    end

    APP --> RC

    subgraph ADK[Google ADK Multi-Agent System]
      RC[RootCoordinator<br/>LlmAgent<br/>owns spoiler boundary]:::coord
      RC --> PIPE

      subgraph PIPE[EpisodePipeline — SequentialAgent]
        direction TB
        T[TranscriptionAgent<br/>LlmAgent]:::agent
        L[LoreResearchAgent<br/>LlmAgent]:::agent
        D[AdaptationDiffAgent<br/>LlmAgent]:::agent
        H[HighlightAgent<br/>LlmAgent]:::agent
        S[SpoilerGuardAgent<br/>security gate]:::guard
        T --> L --> D --> H --> S
      end
    end

    subgraph MCP[MCP Server — mcp_server/server.py]
      Y[[fetch_youtube_transcript]]:::tool
      V[[search_official_hotd_videos]]:::tool
      W[[lookup_lore]]:::tool
    end

    T -. McpToolset .-> Y
    T -. McpToolset .-> V
    L -. McpToolset .-> W

    Y --> YT[(Official HBO YouTube<br/>captions — text only)]:::ext
    V --> CFG[(data/official_videos.json)]:::ext
    W --> WIKI[(A Wiki of Ice and Fire /<br/>Fire & Blood — summarized + linked)]:::ext

    S --> OUT[/Structured, spoiler-safe output<br/>summary · watch_for[] · book_vs_show[] · sources[]/]:::out
    OUT --> APP

    GR{{guardrails.py<br/>spoiler callback +<br/>input-safety}}:::guard
    GR -.enforces.- PIPE

    classDef user fill:#1f2937,stroke:#9ca3af,color:#fff;
    classDef coord fill:#7c2d12,stroke:#fb923c,color:#fff;
    classDef agent fill:#312e81,stroke:#818cf8,color:#fff;
    classDef guard fill:#7f1d1d,stroke:#f87171,color:#fff;
    classDef tool fill:#064e3b,stroke:#34d399,color:#fff;
    classDef ext fill:#1e293b,stroke:#64748b,color:#cbd5e1;
    classDef out fill:#374151,stroke:#9ca3af,color:#fff;
```

## Data modes: live vs. fixture

Each MCP tool in the server (`mcp_server/server.py`) is designed to degrade gracefully to high-fidelity, local static fixtures on disk:
- `search_official_hotd_videos` uses `data/official_videos.json` (filtering out placeholders).
- `fetch_youtube_transcript` falls back to `data/fixtures/transcripts.json`.
- `lookup_lore` falls back to `data/fixtures/lore.json`.

This decoupling is a key design choice: the ADK agents themselves never contact external APIs, execute network requests, or handle live transcripts directly. They strictly invoke the tools via the MCP toolset connections. Because of this boundary, shifting the entire app between live data fetching and simulated fixture execution is a zero-agent-change operation.

## Data flow

1. **Viewer sets `current_episode`** in the Gradio UI. This becomes the *spoiler boundary* and is written to ADK session state.
2. **RootCoordinator** validates input (episode in range; rejects injection) and invokes **EpisodePipeline**.
3. **TranscriptionAgent** calls the MCP tools `search_official_hotd_videos` → `fetch_youtube_transcript` to assemble cleaned caption text + source URLs for that episode's official videos.
4. **LoreResearchAgent** calls MCP `lookup_lore` for the canonical *Fire & Blood* events behind the episode; returns sourced lore notes.
5. **AdaptationDiffAgent** compares transcript-derived show events vs. lore notes → structured `book_vs_show[]` (invented / changed / omitted).
6. **HighlightAgent** synthesizes the summary and the timestamped `watch_for[]` callouts (`{timestamp, what, why, importance, payoff_episode}`).
7. **SpoilerGuardAgent** (security gate) removes any item whose `payoff_episode` or source references content after `current_episode`, or unaired book material, and records `redacted_count`.
8. **guardrails.py** additionally runs as an ADK callback inspecting tool outputs in-flight, so nothing leaks even mid-pipeline.
9. The structured, spoiler-safe result returns to the UI, which renders clickable YouTube timestamp deep-links and a "🛡️ N items redacted" banner.

## Why a multi-agent design (not one big prompt)

- **Separation of concerns:** transcription, lore, diffing, highlighting, and safety are distinct reasoning tasks with different tools and failure modes. Splitting them makes each independently testable and the whole pipeline auditable.
- **Tool decoupling:** agents never touch the network directly — all I/O is through the MCP layer, so data sources can be swapped or mocked (fixtures) without touching agent logic.
- **Safety as a discrete stage:** making the spoiler guard its own agent *and* a callback means the safety guarantee is centralized, testable, and visible in the demo.

## Output contract (`schemas.py`)

```jsonc
{
  "episode": 1,
  "summary": "…",
  "watch_for": [
    { "timestamp": "14:30", "what": "…", "why": "…",
      "importance": "high", "payoff_episode": 1, "source": "https://youtu.be/…?t=870" }
  ],
  "book_vs_show": [
    { "type": "invented|changed|omitted", "detail": "…", "source": "https://…" }
  ],
  "sources": ["https://…", "https://…"],
  "redacted_count": 0
}
```

## Security model

- **Spoiler guarantee:** Enforced at two layers (final agent + callback); covered by 11 comprehensive tests: 8 adversarial cases in `tests/test_spoiler_guard.py` (which verify redacting future events, unaired book material, trailer leaks, and character death foreshadowing, plus prompt injection defanging) and 3 end-to-end integration and clamping tests in `tests/test_pipeline.py`.
- **Dynamic Episode Boundary Clamping:** The UI lists projected episodes up to `SEASON_EPISODES` (default 8). If a user requests a future episode > `AIRED_EPISODES` (currently 2), the system dynamically clamps execution to `AIRED_EPISODES` as the effective spoiler boundary, shielding all subsequent plot details.
- **Secret hygiene:** keys only via `.env`; `.env` + `data/cache/` git-ignored; `.env.example` documents required vars.
- **Untrusted input:** fetched transcript/wiki text is treated strictly as data, never as model instructions.

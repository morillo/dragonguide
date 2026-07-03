# DragonGuide — Kaggle Writeup Outline + 5-Minute Video Script

This file gives you (1) a section-by-section Writeup outline with word budgets that total **≤2,500 words**, mapped to the rubric, and (2) a timed video script for the **≤5-minute** YouTube submission.

---

## PART 1 — Kaggle Writeup outline (target ~2,350 words, hard cap 2,500)

> Rubric reminder: Writeup is worth 10 pts (clarity of problem/solution/architecture/journey). Technical Implementation (50) and Documentation (20) are also judged largely from what you describe + link here. Lead with value, prove the concepts, link the repo and video.

**Title:** `DragonGuide: A Spoiler-Aware Multi-Agent Companion for House of the Dragon`
**Subtitle:** `Just-in-time, source-linked context for the episode you're on — and nothing you shouldn't see yet.`
**Track:** Freestyle (fallback: Agents for Good — supporting art & literature)

### 1. The Problem (≈250 words)
- HOTD's dense, multi-timeline plot + heavy divergence from *Fire & Blood* leaves casual viewers lost.
- Existing recaps are spoiler minefields; book lore is even worse for the unspoiled.
- The unmet need: **spoiler-safe, just-in-time context** bound to the viewer's current episode, with pointers to *what to watch for* and *what the show changed*.
- One-line stakes: viewers either get spoiled, stay confused, or disengage.

### 2. The Solution & Why Agents (≈300 words)
- DragonGuide: a Google ADK multi-agent system producing a per-episode summary, **timestamped "watch-for-this" callouts**, and a **book-vs-show "what changed"** brief — all gated by a spoiler guardrail.
- **Why agents specifically (not one prompt):** the task decomposes into distinct, tool-using sub-problems (fetch official captions, look up canon, diff them, synthesize highlights, enforce safety). Each is a separate reasoning task with its own tools, failure modes, and tests. A multi-agent pipeline makes the system auditable and the safety guarantee centralizable.
- Name the killer feature: clickable timestamps ("At ~14:30, watch for X — it matters because of Y").

### 3. Architecture (≈450 words) — embed the diagram here
- RootCoordinator (LlmAgent) → EpisodePipeline (SequentialAgent) of 5 specialists:
  TranscriptionAgent → LoreResearchAgent → AdaptationDiffAgent → HighlightAgent → SpoilerGuardAgent.
- **MCP tool layer:** 3 tools (`search_official_hotd_videos`, `fetch_youtube_transcript`, `lookup_lore`) exposed by a local MCP server, consumed via `McpToolset` with least-privilege `tool_filter` per agent.
- **Structured contract** (`EpisodeGuide`) threading through ADK session state.
- **Two-layer safety:** SpoilerGuardAgent (deterministic final gate) + an ADK `after_tool_callback` (in-flight). Explain *defense in depth*.
- Insert the Mermaid diagram (from `docs/architecture.mmd`).

### 4. Course Concepts Demonstrated (≈250 words) — make this table explicit
| Concept | Evidence | File |
|---|---|---|
| Multi-agent (ADK) | Coordinator + 5 sub-agents | `coordinator.py`, `agents/*` |
| MCP Server | 3 tools over stdio via `McpToolset` | `mcp_server/server.py` |
| Security | Spoiler guardrail + secret hygiene + injection defense; 13 passing tests | `guardrails.py`, `tests/test_spoiler_guard.py`, `tests/test_pipeline.py` |
| Deployability | Dockerfile + reproducible local run | `Dockerfile`, `README.md` |
- State plainly: **4 of the required 3 concepts**, verifiable in the linked repo.

### 5. How It Works — A Walkthrough (≈350 words)
- Trace one request for Episode 1: input validation → official-video lookup → caption fetch → lore lookup → diff → highlights → spoiler gate → rendered output with redaction banner.
- Show the example structured output JSON.
- Note offline/fixture mode: full pipeline runs with **no API keys**, which is how a judge can reproduce it.

### 6. Engineering Decisions & Trade-offs (≈300 words)
- Why ADK SequentialAgent (determinism, testability) over a free-form agent loop.
- Why MCP (clean tool decoupling, swap live↔fixtures with no agent changes).
- Why deterministic Python for the spoiler rule (must be provable, not model discretion).
- Data ethics: captions text only, never re-host media; summarize + link lore, no bulk copying.
- Scope discipline: one episode deep, config-driven extension to more.

### 7. The Build Journey (≈250 words)
- Built with Antigravity + ADK + Gemini on macOS.
- What was hard: matching ADK's evolving import surface; designing the spoiler invariant to be testable; keeping the demo reproducible offline.
- A concrete bug story (e.g., the injection-defense regex that initially missed "ignore all previous instructions" — caught by a unit test). This shows engineering rigor and reads well.

### 8. Results, Limitations, Future Work (≈200 words)
- Results: working spoiler-safe pipeline on S3E1–E2; 13 green safety tests; one-command demo.
- Limitations: fixture-backed lore depth; timestamp precision depends on caption quality.
- Future: character relationship graph per episode, auto "previously + watch-for" cards, season-long divergence tracker.

### 9. Links (≈50 words)
- GitHub repo (with README + setup), YouTube demo video, live demo (if hosted).

---

## PART 2 — 5-Minute Video Script (≤5:00, published to YouTube)

> Rubric: video is 10 pts — clarity, problem statement, why agents, architecture, demo, how built/tools. Practice once; aim for ~4:40 to leave margin. Record the screen demo live if possible.

**[0:00–0:30] Hook + problem**
> "If you watch House of the Dragon, you know the feeling: half the cast shares a name, the timelines jump, and the show quietly rewrites the book. Look anything up online and you get spoiled. I built DragonGuide — an AI agent that tells you exactly what to watch for in the episode you're on, and nothing you shouldn't see yet."
- On screen: title card + the confusion/spoiler problem in one sentence.

**[0:30–1:15] What it does (value first)**
> "Pick the episode you're on. DragonGuide gives you a spoiler-safe summary, timestamped 'watch for this' callouts — like 'at 14:30, notice this glance, it pays off this episode' — and a 'book vs. show: what changed' brief from George R.R. Martin's Fire & Blood. A guardrail guarantees it never reveals anything past your episode."
- On screen: the Gradio UI; click a timestamp; show the "🛡️ items redacted" banner.

**[1:15–2:00] Why agents / why ADK**
> "This isn't one big prompt. It's a Google ADK multi-agent system, because the job splits into distinct tool-using tasks: fetch official HBO captions, look up canon, diff book vs. show, write highlights, and enforce safety. Each is its own agent — independently testable, and the safety guarantee lives in one place."
- On screen: the architecture diagram, highlight the 5 agents.

**[2:00–3:00] Architecture + MCP + security (the concepts)**
> "A RootCoordinator delegates to a Sequential pipeline of five agents. External data comes through an MCP server exposing three tools — official-video lookup, YouTube caption fetch, and lore lookup — connected via McpToolset with least-privilege filtering. Safety is two layers: a deterministic SpoilerGuard plus an in-flight callback. And no secrets in code — keys live in a .env."
- On screen: scroll `mcp_server/server.py`, then `guardrails.py`, then the concept-mapping table.

**[3:00–4:15] Live demo**
> "Let's run it. I'm on Episode 1. I ask 'what should I watch for?' The pipeline fetches the official Inside the Episode and Sneak Peek, pulls the matching Fire & Blood lore, diffs them, and returns timestamped callouts — each with a clickable source. Now watch the guardrail: a moment that pays off in Episode 3 is automatically redacted, and it tells me so."
- On screen: real run end-to-end; click a timestamp deep-link; show redaction count change when you switch episodes.

**[4:15–4:45] How it's built**
> "Built on macOS with Antigravity, Google's Agent Development Kit, Gemini, and MCP. It runs fully offline on cached fixtures, so anyone can reproduce the demo with no API keys, and the safety invariant is covered by passing unit tests."
- On screen: terminal `pytest -q` → 13 passed; repo structure.

**[4:45–5:00] Close**
> "DragonGuide: spoiler-safe context, exactly when you need it. Repo and setup are linked below. Thanks for watching."
- On screen: repo URL + "Built for the Kaggle × Google AI Agents Capstone."

---

### Recording tips
- Record the demo segment **live** (judges value a real demo); pre-load fixtures so it's fast.
- Keep cuts tight; show code on screen while you narrate the concepts so all three concept-checks are visually evident.
- Your **cover image**: a clean screenshot of the Gradio UI showing timestamped callouts + the 🛡️ redaction banner.

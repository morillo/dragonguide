"""Gradio chat UI for DragonGuide (interactive demo + cover-image surface).

Lets the viewer pick their current episode and ask for guidance. Renders the
structured EpisodeGuide with clickable YouTube timestamp deep-links and a
"items redacted to avoid spoilers" banner — making the safety feature visible
in the demo video.
"""
from __future__ import annotations

import asyncio
import os
import gradio as gr
from google.adk.runners import InMemoryRunner
from google.genai import types
from dragonguide.schemas import EpisodeGuide
from dragonguide.config import AIRED_EPISODES, SEASON_EPISODES
from dragonguide import config

_lazy_runner = None


def get_runner():
    global _lazy_runner
    if _lazy_runner is None:
        from dragonguide.coordinator import build_root_agent
        agent = build_root_agent()
        _lazy_runner = InMemoryRunner(agent=agent, app_name="dragonguide")
    return _lazy_runner


async def _run(current_episode: int, user_msg: str) -> EpisodeGuide:
    if config.OFFLINE:
        from dragonguide.offline import build_offline_guide
        return build_offline_guide(int(current_episode))

    runner = get_runner()
    session = await runner.session_service.create_session(
        app_name="dragonguide", user_id="viewer",
        state={"current_episode": int(current_episode)},
    )
    content = types.Content(role="user", parts=[types.Part(text=user_msg)])
    async for _ in runner.run_async(
        user_id="viewer", session_id=session.id, new_message=content
    ):
        pass  # drive the pipeline to completion
    final = (await runner.session_service.get_session(
        app_name="dragonguide", user_id="viewer", session_id=session.id
    )).state.get("final_guide", {})
    return EpisodeGuide(**final) if final else EpisodeGuide(episode=int(current_episode))


def _render(guide: EpisodeGuide) -> str:
    # Summary Card
    summary_html = f"""
    <div style="background: rgba(18, 21, 29, 0.6); border: 1px solid #252b38; padding: 20px; border-radius: 12px; margin-bottom: 24px; line-height: 1.6; color: #e8eaf0; font-size: 1.1em; font-family: 'Outfit', sans-serif;">
      <strong style="color: #d9a441;">Episode Summary:</strong> {guide.summary}
    </div>
    """

    # Side-by-Side Columns Grid
    cols_html = """
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; font-family: 'Outfit', 'Inter', sans-serif;">
      <!-- Left Column: 👀 Watch for this -->
      <div>
        <h3 style="color: #f2c76b; font-size: 1.4em; margin-top: 0; margin-bottom: 16px; border-bottom: 1px solid #252b38; padding-bottom: 8px; font-weight: 700; display: flex; align-items: center; gap: 8px;">
          <span>👀</span> Watch for this
        </h3>
    """

    if not guide.watch_for:
        cols_html += """
        <p style="color: #9aa3b2; font-style: italic; background: rgba(18, 21, 29, 0.4); padding: 14px; border-radius: 8px; border: 1px dashed #252b38; margin-bottom: 24px;">
          No watch-for items are safe to show for this episode due to spoiler boundaries.
        </p>
        """
    else:
        cols_html += '<div style="display: flex; flex-direction: column; gap: 14px;">'
        for w in guide.watch_for:
            clean_time = w.timestamp.strip()
            # Priority color coding
            if w.importance.value == "high":
                badge_style = "background: rgba(226, 81, 58, 0.15); color: #e2513a; border: 1px solid rgba(226, 81, 58, 0.3);"
            else:
                badge_style = "background: rgba(217, 164, 65, 0.15); color: #d9a441; border: 1px solid rgba(217, 164, 65, 0.3);"

            cols_html += f"""
            <div style="background: rgba(18, 21, 29, 0.5); border: 1px solid #252b38; border-left: 4px solid #d9a441; border-radius: 8px; padding: 16px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; gap: 10px;">
                <a href="{w.source}" target="_blank" style="background: #d9a441; color: #0b0d12; padding: 4px 10px; border-radius: 6px; font-weight: 700; text-decoration: none; font-size: 0.85em; display: inline-flex; align-items: center; gap: 4px;">
                  ⏱️ {clean_time}
                </a>
                <span style="padding: 2px 8px; border-radius: 12px; font-size: 0.75em; text-transform: uppercase; font-weight: 600; {badge_style}">
                  {w.importance.value} priority
                </span>
              </div>
              <div style="color: #e8eaf0; font-weight: 600; font-size: 1.05em; margin-bottom: 6px;">{w.what}</div>
              <div style="color: #9aa3b2; font-size: 0.95em; line-height: 1.4;"><span style="color: #f2c76b; font-weight: 500;">Why it matters:</span> {w.why}</div>
            </div>
            """
        cols_html += "</div>"

    cols_html += """
      </div>
      <!-- Right Column: 📖 Book vs. Show -->
      <div>
        <h3 style="color: #f2c76b; font-size: 1.4em; margin-top: 0; margin-bottom: 16px; border-bottom: 1px solid #252b38; padding-bottom: 8px; font-weight: 700; display: flex; align-items: center; gap: 8px;">
          <span>📖</span> Book vs. Show
        </h3>
    """

    if not guide.book_vs_show:
        cols_html += """
        <p style="color: #9aa3b2; font-style: italic; background: rgba(18, 21, 29, 0.4); padding: 14px; border-radius: 8px; border: 1px dashed #252b38; margin-bottom: 24px;">
          No divergences documented for this episode.
        </p>
        """
    else:
        cols_html += '<div style="display: flex; flex-direction: column; gap: 14px;">'
        for d in guide.book_vs_show:
            if d.type == "invented":
                border_color = "#a855f7"
                badge_bg = "rgba(168, 85, 247, 0.15)"
                badge_color = "#d8b4fe"
            elif d.type == "changed":
                border_color = "#3b82f6"
                badge_bg = "rgba(59, 130, 246, 0.15)"
                badge_color = "#93c5fd"
            else: # omitted
                border_color = "#e2513a"
                badge_bg = "rgba(226, 81, 58, 0.15)"
                badge_color = "#fca5a5"

            cols_html += f"""
            <div style="background: rgba(18, 21, 29, 0.5); border: 1px solid #252b38; border-left: 4px solid {border_color}; border-radius: 8px; padding: 16px;">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="background: {badge_bg}; color: {badge_color}; padding: 2px 8px; border-radius: 4px; font-size: 0.75em; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; border: 1px solid rgba(255,255,255,0.05);">
                  {d.type}
                </span>
                <a href="{d.source}" target="_blank" style="color: #f2c76b; text-decoration: none; font-size: 0.85em; font-weight: 500; display: inline-flex; align-items: center; gap: 4px;">
                  🔗 Source
                </a>
              </div>
              <div style="color: #cbd5e1; font-size: 0.95em; line-height: 1.5;">{d.detail}</div>
            </div>
            """
        cols_html += "</div>"

    cols_html += """
      </div>
    </div>
    """

    return f"""
    <div class="guide-container">
      {summary_html}
      {cols_html}
    </div>
    """


def respond(episode_str, user_msg):
    # Extract episode integer from "Season 3, Episode N"
    episode = int(episode_str.split("Episode ")[1])
    
    notice_html = ""
    effective_episode = episode
    if episode > AIRED_EPISODES:
        effective_episode = AIRED_EPISODES
        notice_html = f"""
        <div style="background: rgba(217, 164, 65, 0.08); border: 1px solid rgba(217, 164, 65, 0.2); border-left: 4px solid #d9a441; color: #f2c76b; padding: 14px 18px; border-radius: 10px; margin-bottom: 20px; font-family: 'Outfit', sans-serif; line-height: 1.4; display: flex; align-items: center; gap: 10px; font-size: 1em;">
          <span style="font-size: 1.4em;">📺</span>
          <div>
            <strong>Season 3, Episode {episode}</strong> hasn't aired yet. Showing the spoiler-safe guide through the latest aired episode (Episode {AIRED_EPISODES}).
          </div>
        </div>
        """
    
    # Run the pipeline for the effective (clamped) episode
    guide = asyncio.run(_run(effective_episode, user_msg or "What should I watch for?"))
    
    # Render guide HTML and prepend notice if applicable
    guide_html = notice_html + _render(guide)
    
    # Render spoiler banner HTML (green translucent card for left panel) using effective_episode
    banner_html = ""
    if guide.redacted_count > 0:
        banner_html = f"""
        <div style="background: rgba(62, 207, 142, 0.08); border: 1px solid rgba(62, 207, 142, 0.2); border-left: 4px solid #3ecf8e; color: #3ecf8e; padding: 12px 16px; border-radius: 10px; margin-top: 20px; display: flex; align-items: center; gap: 10px; font-family: 'Outfit', sans-serif;">
          <span style="font-size: 1.4em;">🛡️</span>
          <div style="font-size: 0.9em; font-weight: 500; line-height: 1.4;">
            <strong>Spoiler Guard:</strong> {guide.redacted_count} item(s) redacted to avoid spoilers beyond Episode {effective_episode}.
          </div>
        </div>
        """
    
    return guide_html, banner_html


# Custom CSS Theme
CSS = """
body, .gradio-container {
    background-color: #0b0d12 !important;
    background-image: radial-gradient(circle at top right, rgba(217, 164, 65, 0.12), transparent 55%) !important;
    font-family: 'Outfit', 'Inter', system-ui, -apple-system, sans-serif !important;
    color: #e8eaf0 !important;
    border: none !important;
}

/* Styled Left control panel */
.left-panel {
    background: linear-gradient(180deg, #12151d, #171b25) !important;
    border: 1px solid #252b38 !important;
    border-radius: 18px !important;
    padding: 24px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4) !important;
}

/* Gold Gradient Guide me Button */
.gold-button {
    background: linear-gradient(135deg, #d9a441, #f2c76b) !important;
    color: #0b0d12 !important;
    font-weight: 700 !important;
    font-size: 1.05em !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px 24px !important;
    cursor: pointer !important;
    transition: all 0.2s ease-in-out !important;
}
.gold-button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(217, 164, 65, 0.35) !important;
}

/* Custom styled textbox and dropdown */
.gradio-container input, .gradio-container select, .gradio-container textarea {
    background-color: #12151d !important;
    border: 1px solid #252b38 !important;
    color: #e8eaf0 !important;
}

.guide-container {
    animation: fadeIn 0.4s ease-out;
}
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}
"""

with gr.Blocks(title="DragonGuide 🐉", css=CSS) as demo:
    # Header Bar
    with gr.Row():
        gr.HTML("""
            <div class="top-bar" style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #252b38; padding: 16px 24px; margin-bottom: 24px; font-family: 'Outfit', sans-serif; width: 100%;">
              <div style="display: flex; align-items: center; gap: 12px;">
                <span style="font-size: 2em; line-height: 1;">🐉</span>
                <div>
                  <span style="font-size: 1.8em; font-weight: 900; background: linear-gradient(to right, #d9a441, #f2c76b); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">DragonGuide</span>
                  <span style="color: #9aa3b2; font-size: 0.9em; margin-left: 12px; font-weight: 300;">Spoiler-safe companion for House of the Dragon</span>
                </div>
              </div>
              <div style="background: rgba(217, 164, 65, 0.1); border: 1px solid rgba(217, 164, 65, 0.2); color: #f2c76b; padding: 6px 16px; border-radius: 99px; font-size: 0.85em; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase;">
                Google ADK · MCP · Gemini
              </div>
            </div>
        """)
        
    with gr.Row():
        with gr.Column(scale=1, elem_classes="left-panel"):
            gr.Markdown("### ⚙️ Control Panel")
            ep = gr.Dropdown(
                choices=[f"Season 3, Episode {i}" for i in range(1, SEASON_EPISODES + 1)],
                value="Season 3, Episode 1",
                label="Select Your Current Episode",
                info="Future episodes are listed; unaired selections fall back to the latest aired episode."
            )
            msg = gr.Textbox(
                value="What should I watch for?",
                label="Ask DragonGuide",
                placeholder="What details should I pay attention to?",
                lines=2
            )
            btn = gr.Button("Guide me", variant="primary", elem_classes="gold-button")
            spoiler_banner_out = gr.HTML(value="", show_label=False)
            
        with gr.Column(scale=2):
            gr.Markdown("### 🔍 Safe Companion Guide")
            out = gr.HTML(
                value="<div style='color: #9aa3b2; font-style: italic; text-align: center; padding: 40px;'>Select your episode and click 'Guide me' to begin.</div>",
                label="Output Content"
            )
            
    btn.click(respond, [ep, msg], [out, spoiler_banner_out])

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)

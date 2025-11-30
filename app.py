"""Monte Carlo Oracle — Gradio 6 UI

Run: python app.py
"""

import asyncio

import gradio as gr
from claude_agent_sdk import (
    AssistantMessage,
    TextBlock,
    ToolUseBlock,
    ResultMessage,
    query,
    ClaudeAgentOptions,
)

from src.agents import get_agent

MODELS = ["claude", "gpt", "gemini"]


async def generate_research_prompt(user_query: str) -> str:
    """Generate a detailed Monte Carlo research prompt."""
    system = """You are a Monte Carlo simulation architect. Given a user's "what if" question,
generate a detailed research and simulation prompt for AI agents.
Output ONLY the prompt text, no explanations."""

    meta_prompt = f"""User's question: "{user_query}"

Generate a comprehensive Monte Carlo simulation prompt with:

# Deep Analysis: [Title]

## Phase 1: Research (use web search)
List 8-10 specific data points to research relevant to this question.

## Phase 2: Multi-Factor Simulation
List 5-7 quantitative factors with appropriate distributions.
Request 10,000 iterations.

## Phase 3: Output
- Success/failure probability with 95% CI
- Expected value
- Sensitivity analysis
- Risk factors

End with: "Show your work. Print intermediate data."
"""

    prompt_text = []
    options = ClaudeAgentOptions(system_prompt=system)
    async for msg in query(prompt=meta_prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    prompt_text.append(block.text)
    return "\n".join(prompt_text)


async def generate_collation_prompt(user_query: str, results: list[dict]) -> str:
    """Generate a collation prompt for synthesizing results."""
    system = """You are a prompt engineer. Generate a collation prompt for synthesizing
Monte Carlo results from 3 AI models. Output ONLY the prompt text."""

    meta_prompt = f"""User's question: "{user_query}"

Generate a prompt that asks Claude to:
1. Compare predictions from 3 models
2. Calculate weighted ensemble
3. Identify consensus vs divergence
4. Produce final verdict with confidence level
5. Clear recommendation

Format the final output professionally with emojis and clear sections.
"""

    prompt_text = []
    options = ClaudeAgentOptions(system_prompt=system)
    async for msg in query(prompt=meta_prompt, options=options):
        if isinstance(msg, AssistantMessage):
            for block in msg.content:
                if isinstance(block, TextBlock):
                    prompt_text.append(block.text)

    base_prompt = "\n".join(prompt_text)
    return f"""{base_prompt}

---
## Claude's Analysis:
{results[0]["result"]}

## GPT's Analysis:
{results[1]["result"]}

## Gemini's Analysis:
{results[2]["result"]}
"""


async def run_single_model(model: str, prompt: str) -> dict:
    """Run a single model and return results."""
    result_text = []
    tool_calls = []
    stats = {"turns": 0, "duration_ms": 0, "cost": 0.0}

    async with get_agent(model, session_id=f"oracle-{model}") as client:
        await client.query(prompt)
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        result_text.append(block.text)
                    elif isinstance(block, ToolUseBlock):
                        tool_calls.append(block.name)
            elif isinstance(msg, ResultMessage):
                stats["turns"] = msg.num_turns
                stats["duration_ms"] = msg.duration_ms
                stats["cost"] = msg.total_cost_usd or 0.0

    return {
        "model": model,
        "result": "\n".join(result_text),
        "tool_calls": len(tool_calls),
        "stats": stats,
    }


async def run_collator(prompt: str) -> str:
    """Run the collator to synthesize results."""
    final_result = []
    async with get_agent("claude", session_id="oracle-collator") as client:
        await client.query(prompt)
        async for msg in client.receive_response():
            if isinstance(msg, AssistantMessage):
                for block in msg.content:
                    if isinstance(block, TextBlock):
                        final_result.append(block.text)
    return "\n".join(final_result)


async def run_oracle(user_query: str, progress=gr.Progress()):
    """Main orchestration function."""

    # Step 1: Generate research prompt
    progress(0.05, desc="📝 Generating research prompt...")
    research_prompt = await generate_research_prompt(user_query)

    # Step 2: Run models in parallel
    progress(0.15, desc="🚀 Launching Claude, GPT, Gemini...")

    tasks = [run_single_model(model, research_prompt) for model in MODELS]
    results = await asyncio.gather(*tasks)

    progress(0.80, desc="🧠 Synthesizing results...")

    # Step 3: Generate collation prompt and run collator
    collation_prompt = await generate_collation_prompt(user_query, results)
    ensemble = await run_collator(collation_prompt)

    progress(1.0, desc="✅ Complete!")

    # Format outputs
    claude_result = results[0]["result"]
    gpt_result = results[1]["result"]
    gemini_result = results[2]["result"]

    # Stats summary
    total_cost = sum(r["stats"]["cost"] for r in results)
    stats_md = f"""| Model | Turns | Time | Cost |
|-------|-------|------|------|
| Claude | {results[0]["stats"]["turns"]} | {results[0]["stats"]["duration_ms"]}ms | ${results[0]["stats"]["cost"]:.4f} |
| GPT | {results[1]["stats"]["turns"]} | {results[1]["stats"]["duration_ms"]}ms | ${results[1]["stats"]["cost"]:.4f} |
| Gemini | {results[2]["stats"]["turns"]} | {results[2]["stats"]["duration_ms"]}ms | ${results[2]["stats"]["cost"]:.4f} |
| **Total** | — | — | **${total_cost:.4f}** |"""

    return claude_result, gpt_result, gemini_result, ensemble, stats_md


def run_sync(user_query: str, progress=gr.Progress()):
    """Sync wrapper for async function."""
    return asyncio.run(run_oracle(user_query, progress))


# --- Gradio 6 UI ---

EXAMPLES = [
    "Should I open a coffee shop in Seattle with $50K investment?",
    "Will the Lakers win the NBA championship this season?",
    "Should I invest $10K in NVIDIA stock right now?",
    "Is it a good time to buy a house in Austin, Texas?",
    "Will CSK win next season?",
]

with gr.Blocks() as demo:
    gr.Markdown(
        """
# 🎲 Monte Carlo Oracle

**Ask any "what if" question. Get probability-backed answers from 3 AI models running simulations.**

Claude, GPT, and Gemini independently research your question, build Monte Carlo simulations,
and produce probability distributions — then we ensemble their predictions.
"""
    )

    with gr.Row():
        query_input = gr.Textbox(
            label="Your Question",
            placeholder="Should I open a coffee shop in Seattle with $50K?",
            lines=2,
            scale=4,
        )
        submit_btn = gr.Button("🔮 Predict", variant="primary", scale=1)

    gr.Examples(examples=EXAMPLES, inputs=query_input)

    # Ensemble result at top
    with gr.Accordion("🎯 Ensemble Prediction", open=True):
        ensemble_output = gr.Markdown(label="Final Prediction")

    # Individual model results in tabs
    with gr.Accordion("📊 Individual Model Analyses", open=False):
        with gr.Tabs():
            with gr.TabItem("Claude"):
                claude_output = gr.Markdown()
            with gr.TabItem("GPT"):
                gpt_output = gr.Markdown()
            with gr.TabItem("Gemini"):
                gemini_output = gr.Markdown()

    # Stats
    with gr.Accordion("⚡ Performance Stats", open=False):
        stats_output = gr.Markdown()

    # Event handler
    submit_btn.click(
        fn=lambda: "⏳ **Running simulations across Claude, GPT, and Gemini...**\n\nThis takes 5-10 minutes. Please wait.",
        outputs=ensemble_output,
    ).then(
        fn=run_sync,
        inputs=query_input,
        outputs=[claude_output, gpt_output, gemini_output, ensemble_output, stats_output],
    )

    query_input.submit(
        fn=lambda: "⏳ **Running simulations across Claude, GPT, and Gemini...**\n\nThis takes 5-10 minutes. Please wait.",
        outputs=ensemble_output,
    ).then(
        fn=run_sync,
        inputs=query_input,
        outputs=[claude_output, gpt_output, gemini_output, ensemble_output, stats_output],
    )

if __name__ == "__main__":
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        theme=gr.themes.Soft(),
        footer_links=["gradio"],
    )

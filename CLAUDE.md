# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

yoyo-bench is an automated benchmark and optimization loop for the yoyo coding agent. It runs Terminal-Bench 2 daily via Harbor, tracks scores over time, and auto-optimizes yoyo's prompts and skills based on failure analysis.

## Repository Structure

- `agents/yoyo_agent.py` — Harbor agent adapter. Implements `BaseInstalledAgent` to install and run yoyo inside benchmark containers.
- `prompts/system_prompt.md` — The system prompt template injected into yoyo during bench runs. This is the primary optimization target.
- `skills/` — Bench-specific skills loaded via `--skills`. Focused on terminal task patterns.
- `analysis/results.jsonl` — Append-only score history. Each line is one bench run with date, score, model, and prompt hash.
- `analysis/failures/` — Per-run failure logs for analysis.
- `.github/workflows/bench.yml` — Daily benchmark run.
- `.github/workflows/analyze.yml` — Post-run analysis and auto-optimization.

## Key Concepts

**The optimization loop:** bench run -> score -> compare to baseline -> analyze failures -> adjust prompts/skills -> next run. If a score drops, the last optimization is reverted automatically.

**Prompt hash tracking:** Each run records a hash of the system prompt, so we can correlate prompt changes with score changes.

**Score guard:** The analyze workflow checks if the score improved. If it dropped, it reverts the last commit to `prompts/` or `skills/` and tags the revert. This prevents cascading regressions.

**Harbor agent adapter:** `yoyo_agent.py` follows the `BaseInstalledAgent` pattern from Harbor. Key methods: `install()` puts the yoyo binary in the container, `run()` executes yoyo with the bench task, `populate_context_post_run()` parses output for scoring.

## No Build System

This repo is Python (the agent adapter) + markdown (prompts/skills) + YAML (workflows). No build step. Harbor handles execution.

## Testing locally

```bash
harbor run -d terminal-bench/terminal-bench-2 -m anthropic/claude-sonnet-4-6 --agent-import-path agents.yoyo_agent:Yoyo --env daytona -n 4
```

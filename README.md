# yoyo-bench

Automated benchmark loop for [yoyo](https://github.com/yologdev/yoyo). Runs [Terminal-Bench 2](https://tbench.ai) daily via [Harbor](https://github.com/laude-institute/harbor), tracks scores, and auto-optimizes prompts and skills based on failures.

## How it works

```
Daily cron
  ├── Run terminal-bench via Harbor
  ├── Score results, append to analysis/results.jsonl
  ├── Compare to previous best
  │
  ├── If score improved → commit as new baseline
  ├── If score dropped → revert last optimization, re-run
  │
  └── Analyze failure patterns
      ├── Identify recurring failure modes
      ├── Adjust prompts/skills to address them
      └── Commit changes for next day's run
```

## What gets optimized

| Layer | File | How |
|-------|------|-----|
| System prompt | `prompts/system_prompt.md` | Tuned based on failure patterns |
| Skills | `skills/` | Bench-specific skills for tool use, error recovery |
| Agent harness | `agents/yoyo_agent.py` | CLI flags, timeout, retry logic |

## Setup

### Prerequisites

- [Harbor](https://www.harborframework.com/docs) installed
- [Daytona](https://www.daytona.io/) API key (or other Harbor-supported environment)
- Anthropic API key

### Repository secrets

| Secret | Description |
|--------|-------------|
| `ANTHROPIC_API_KEY` | LLM provider key for yoyo |
| `DAYTONA_API_KEY` | Environment provider key |

### Run manually

```bash
# Verify setup
harbor run -d terminal-bench/terminal-bench-2 -a oracle

# Run yoyo
harbor run \
  -d terminal-bench/terminal-bench-2 \
  -m anthropic/claude-sonnet-4-6 \
  --agent-import-path agents.yoyo_agent:Yoyo \
  --env daytona \
  -n 4
```

## Scores

Results are tracked in `analysis/results.jsonl`. Each line:

```json
{"date": "2026-04-05", "score": 0.42, "total": 100, "passed": 42, "prompt_hash": "abc123", "model": "claude-sonnet-4-6"}
```

View the leaderboard: [tbench.ai/leaderboard](https://tbench.ai/leaderboard)

## Feeding back to yoyo

When optimizations here prove stable (3+ consecutive score improvements), they can be PR'd back to the main [yoyo repo](https://github.com/yologdev/yoyo) as skill or prompt improvements.

## License

MIT

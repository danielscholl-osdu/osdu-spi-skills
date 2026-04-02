---
title: Commands
description: Slash commands and their platform mappings
---

Commands are shortcuts that route to skills. They map differently per platform:

| Command | Claude Code | Copilot | What it does |
|---------|-------------|---------|-------------|
| `/clone` | `.claude/commands/clone.md` | `.github/prompts/clone.prompt.md` | Route to clone skill |
| `/prime` | `.claude/commands/prime.md` | `.github/prompts/prime.prompt.md` | Discover workspace, scan repos, load context |
| `/qa` | `.claude/commands/qa.md` | `.github/prompts/qa.prompt.md` | Route to osdu-qa skill |
| `/ship` | `.claude/commands/ship.md` | `.github/prompts/ship.prompt.md` | Route to send skill |

## Usage

In Claude Code, type the command directly:

```
/clone partition
/qa test smoke
/ship
```

In Copilot, use the prompt file or just describe what you want — the routing table in `AGENTS.md` handles dispatch.

## How Commands Work with APM

APM automatically maps `commands/*.md` files to the appropriate platform format:

- **Claude Code / OpenCode:** Deployed as `commands/*.md`
- **Copilot:** Deployed as `prompts/*.prompt.md`
- **Cursor:** Not applicable (no command/prompt concept)

This mapping happens during `apm install` — no manual configuration needed.

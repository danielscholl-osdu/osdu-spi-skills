---
title: GitHub Copilot
description: Using OSDU SPI Skills with GitHub Copilot CLI
---

## Installation

### Via APM

```bash
apm install danielscholl-osdu/osdu-spi-skills --target copilot
```

### Via Copilot CLI

```bash
copilot plugin install https://github.com/danielscholl-osdu/osdu-spi-skills.git
```

## What Gets Deployed

| Directory | Contents |
|-----------|----------|
| `.github/agents/` | 8 agent files (`*.agent.md`) |
| `.github/skills/` | 28 skill directories |
| `.github/prompts/` | 4 prompt files (`*.prompt.md`) |

The `AGENTS.md` routing table at the repo root provides the delegation model and skill ownership mappings.

## Agent Delegation

Copilot CLI uses the `task` tool to spawn sub-agents:

```
task(
  agent_type: "general-purpose",
  description: "build-runner: compile partition",
  prompt: "Read agents/build-runner.md for your charter..."
)
```

The @osdu agent automatically detects whether `task` (CLI) or `runSubagent` (VS Code) is available and adapts.

## Prompts

Commands are deployed as Copilot prompts:

- `clone.prompt.md` — Clone an OSDU repo
- `prime.prompt.md` — Prime workspace context
- `qa.prompt.md` — Run QA tests
- `ship.prompt.md` — Ship changes

## CI/CD (Copilot Coding Agent)

To use OSDU skills with the Copilot coding agent in GitHub Actions:

1. Copy `examples/apm.yml` to your repo root
2. Copy `examples/copilot-setup-steps.yml` to `.github/workflows/copilot-setup-steps.yml`
3. Commit and push

The setup workflow runs `apm install` before the coding agent starts, making all skills available. See [`examples/README.md`](https://github.com/danielscholl-osdu/osdu-spi-skills/tree/main/examples) for details and alternative approaches.

## Key Differences from Claude

| Feature | Copilot | Claude |
|---------|---------|--------|
| Agent filenames | `*.agent.md` | `*.md` |
| Commands | `prompts/*.prompt.md` | `commands/*.md` |
| Tool restrictions | Not supported | `allowed-tools` frontmatter |
| Sub-agent spawn | `task` tool | `Agent` tool with `subagent_type` |
| MCP config | `.vscode/mcp.json` | Plugin-level `.mcp.json` |
| Discovery | `AGENTS.md` + `CLAUDE.md` | `CLAUDE.md` (references `AGENTS.md`) |

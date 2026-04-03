# OSDU SPI Skills

[![AI: Enabled](https://img.shields.io/badge/AI-Enabled-blueviolet)](#)
[![Docs](https://img.shields.io/badge/docs-starlight-blue)](https://danielscholl-osdu.github.io/osdu-spi-skills)
[![Status: Experimental](https://img.shields.io/badge/status-experimental-orange)](#)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

Unified AI agent skills for the OSDU / SPI ecosystem. One package, every AI tool.

## Install

```bash
# Install APM (if you haven't already)
curl -sSL https://aka.ms/apm-unix | sh

# Add to any project
apm install danielscholl-osdu/osdu-spi-skills
```

Your AI coding assistant is now OSDU-aware — across Copilot, Claude Code, Cursor, OpenCode, and Codex.

## Try It

| What you say | What happens |
|---|---|
| "good morning" | Daily briefing from knowledge vault |
| "clone partition" | Clone OSDU repo with worktree layout |
| "build storage" | Maven build with structured output |
| "check deps for legal" | Dependency scan with CVE overlay |
| "run smoke tests" | OSDU API test execution |
| "review MR 320" | Code analysis + pipeline diagnostics |
| "ship it" | Review, commit, push, create MR |
| "environment health" | Cluster + PaaS + OSDU health report |
| "sync upstream for partition" | SPI fork management |

## What's Inside

| Component | Count |
|-----------|-------|
| Agents | 8 — osdu, cimpl, spi, build-runner, qa-runner, qa-analyzer, qa-comparator, qa-reporter |
| Skills | 28 — brain, glab, maven, osdu-qa, iac, forks, send, health, and 20 more |
| Commands | 4 — /clone, /prime, /qa, /ship |
| MCP Server | 1 — osdu-mcp-server (live platform data) |

## Architecture

```
You ──→ Default Context (observe, plan, ship)
            ├──→ @osdu   (platform: builds, tests, dependencies)
            ├──→ @cimpl  (CIMPL: Terraform, Helm, AKS)
            └──→ @spi    (SPI: Azure PaaS, fork management)
```

The default context handles planning, briefings, and shipping. Specialist agents handle complex operations in their domain. Skills are shared procedures that both contexts can use.

## Platforms

Deploys from a single `plugin.json` via [APM](https://github.com/microsoft/apm):

| Platform | Agents | Skills | Commands | MCP |
|----------|--------|--------|----------|-----|
| GitHub Copilot | `.github/agents/*.agent.md` | `.github/skills/` | `.github/prompts/*.prompt.md` | `.vscode/mcp.json` |
| Claude Code | `.claude/agents/*.md` | `.claude/skills/` | `.claude/commands/` | auto-configured |
| Cursor | `.cursor/agents/*.md` | `.cursor/skills/` | — | `.cursor/mcp.json` |
| OpenCode | `.opencode/agents/*.md` | `.opencode/skills/` | `.opencode/commands/` | `opencode.json` |
| Codex | `.codex/agents/` | `.agents/skills/` | — | — |

## CI/CD

Use OSDU skills with the GitHub Copilot coding agent or other CI/CD AI agents. See [`examples/`](examples/) for ready-to-copy setup files.

```bash
# In your consumer repo: add apm.yml, then
apm install
```

## Testing

Six-layer test framework:

```bash
make test                          # L0-L2: fast structural checks (no AI)
make test-triggers CLI=copilot     # L3: live trigger accuracy
make test-sessions CLI=claude      # L4: multi-turn workflows
make test-all                      # Full matrix across both CLIs
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, testing guide, and how to add new skills.

## License

[Apache 2.0](LICENSE)

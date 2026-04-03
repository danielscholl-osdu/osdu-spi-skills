# OSDU SPI Skills

[![AI: Enabled](https://img.shields.io/badge/AI-Enabled-blueviolet)](#)
[![Docs](https://img.shields.io/badge/docs-starlight-blue)](https://danielscholl-osdu.github.io/osdu-spi-skills)
[![Status: Experimental](https://img.shields.io/badge/status-experimental-orange)](#)
[![License: Apache 2.0](https://img.shields.io/badge/license-Apache%202.0-green)](LICENSE)

### An agentic skill system for OSDU — one package, every AI tool

A plugin marketplace package that bundles specialized agents, skills, and live platform access for infrastructure automation, platform analytics, QA testing, and knowledge management across OSDU environments on Azure.

Built for OSDU maintainers, platform engineers, QA contributors, and community operators.

## Install

Pick your platform:

```bash
# Claude Code
claude plugin add danielscholl-osdu/osdu-spi-skills

# GitHub Copilot
gh copilot plugin install danielscholl-osdu/osdu-spi-skills

# Any platform via APM
curl -sSL https://aka.ms/apm-unix | sh
apm install danielscholl-osdu/osdu-spi-skills

# CI/CD (Copilot coding agent)
# Copy examples/apm.yml + examples/copilot-setup-steps.yml to your repo
# See examples/README.md for details
```

## Use

```
> good morning                          → daily briefing from knowledge vault
> clone partition                       → clone OSDU repo with worktree layout
> build storage                         → Maven build with structured output
> check deps for legal                  → dependency scan with CVE overlay
> run smoke tests                       → OSDU API test execution
> review MR 320                         → code analysis + pipeline diagnostics
> ship it                               → review, commit, push, create MR
> environment health                    → cluster + PaaS + OSDU health report
> sync upstream for partition           → SPI fork management
```

## What's Inside

| Category | Skills |
|----------|--------|
| Knowledge | brain, briefing, learn, consolidate |
| Analytics | osdu-activity, osdu-engagement, osdu-quality |
| Build & Deps | maven, dependencies, dependency-scan, build-runner, remediate |
| QA Testing | osdu-qa, acceptance-test |
| Git Workflow | send, mr-review, contribute, glab, fossa, maintainer, clone |
| Infrastructure | iac, health, forks, status, setup |
| Automation | loop |

**Agents:** osdu (orchestrator), cimpl (infrastructure), spi (fork management), build-runner, qa-runner, qa-analyzer, qa-comparator, qa-reporter

**Commands:** /clone, /prime, /qa, /ship

**MCP Server:** [osdu-mcp-server](https://pypi.org/project/osdu-mcp-server/) — live platform access (search, storage, schema, entitlements, legal, partition)

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
| GitHub Copilot | `.github/agents/` | `.github/skills/` | `.github/prompts/` | `.vscode/mcp.json` |
| Claude Code | `.claude/agents/` | `.claude/skills/` | `.claude/commands/` | auto-configured |
| Cursor | `.cursor/agents/` | `.cursor/skills/` | — | `.cursor/mcp.json` |
| OpenCode | `.opencode/agents/` | `.opencode/skills/` | `.opencode/commands/` | `opencode.json` |
| Codex | `.codex/agents/` | `.agents/skills/` | — | — |
| CI/CD | via `apm install` | via `apm install` | — | — |

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

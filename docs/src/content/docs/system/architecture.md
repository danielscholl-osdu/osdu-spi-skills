---
title: Architecture
description: How the AI system is organized — delegation model, layers, and routing
---

## Mental Model

You talk to **one assistant**. It observes, plans, and ships. When you need to operate on infrastructure or services, it invokes a **specialist agent**.

The default context knows *why* — goals, priorities, decisions. Specialists know *how* — deep domain execution.

## Discovery Model

Two files control how AI platforms discover skills:

- **`AGENTS.md`** — Universal skill catalog with paths, routing, and rules. Read by Copilot, Codex, and any platform that supports AGENTS.md.
- **`CLAUDE.md`** — Claude-specific overlay (delegation model, conventions). References AGENTS.md for the shared catalog.

Copilot reads both files. Claude reads only CLAUDE.md. Codex reads AGENTS.md. The skill content itself (`skills/*/SKILL.md`) is platform-agnostic.

## Delegation Model

```
Default Context (observe / plan / ship)
    │
    ├── @osdu   (platform operations)
    │   ├── build-runner
    │   ├── qa-runner
    │   ├── qa-analyzer
    │   ├── qa-comparator
    │   └── qa-reporter
    │
    ├── @cimpl  (CIMPL infrastructure)
    │
    └── @spi    (SPI infrastructure)
```

**One-way delegation** — the default context delegates to specialists. Specialists do not invoke the default context or each other.

## Routing

The boundary is **intent, not topic**.

| Intent | Route | Example |
|--------|-------|---------|
| Understand state | Default | "what's failing in CI?" |
| Plan an approach | Default | "should I fix this in storage or indexer?" |
| Ship changes | Default (send skill) | "send it" |
| Build a service | @osdu | "build partition" |
| Run tests | @osdu (qa-runner) | "run smoke tests" |
| Modify Terraform | @cimpl or @spi | "add a readiness probe" |
| Manage forks | @spi | "sync upstream for partition" |
| Quick factual question | Answer directly | "what branch am I on?" |

**Simple queries** (MR lists, pipeline status, contribution stats) are handled directly by the default context using CLI tools — no need to spawn an agent.

## Layers

| Layer | What lives here |
|-------|----------------|
| **Workflows** | End-to-end patterns (briefing, ship, review) |
| **Agents** | Specialist execution contexts (@osdu, @cimpl, @spi) |
| **Skills** | Domain procedures with guardrails |
| **Commands** | Shortcuts that route to skills |
| **Knowledge** | Brain vault, reference docs, environment config |
| **Infrastructure** | MCP servers, CLI tools |

## Developer Personas

**Service Developers** use the Default context + @osdu agent. They clone repos, scan dependencies, build, test, review MRs, and ship changes.

**Platform Engineers** use the Default context + @cimpl and/or @spi agents. They provision environments, modify Terraform, debug deployments, manage forks, and verify infrastructure.

Both personas share skills like `brain`, `glab`, `send`, `mr-review`, and `setup`.

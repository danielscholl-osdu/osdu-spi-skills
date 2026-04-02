---
title: Introduction
description: What OSDU SPI Skills is and why it exists
---

## The Problem

AI coding assistants are powerful, but they don't know your platform. They don't know that OSDU services live on GitLab at `community.opengroup.org`, that `partition` is short for `osdu/platform/system/partition`, or that your Terraform modules use Azure Verified Modules. Every developer configures their AI tools differently — skills in one tool, instructions in another, nothing portable, nothing versioned.

## The Solution

**OSDU SPI Skills** is a unified package of agents, skills, and tools that gives any AI coding assistant deep knowledge of the OSDU / SPI ecosystem. It deploys to multiple platforms from a single source:

| Platform | How it deploys |
|----------|---------------|
| GitHub Copilot | `.github/agents/`, `.github/skills/`, `.github/prompts/` |
| Claude Code | `.claude/agents/`, `.claude/skills/`, `.claude/commands/` |
| Cursor | `.cursor/agents/`, `.cursor/skills/` |
| OpenCode | `.opencode/agents/`, `.opencode/skills/`, `.opencode/commands/` |
| Codex | `.codex/agents/` |

One `apm install`, all platforms configured.

## Architecture

The system follows a **delegation model** — you talk to one assistant that observes, plans, and ships. When you need to operate on infrastructure or services, it invokes a specialist agent.

```
You ──→ Default Context (observe, plan, ship)
            ├──→ @osdu   (platform operations: builds, tests, dependencies)
            ├──→ @cimpl  (CIMPL infrastructure: Terraform, Helm, AKS)
            └──→ @spi    (SPI infrastructure: Azure PaaS, fork management)
```

**Skills** are domain procedures that agents (or the default context) execute. They contain step-by-step instructions, scripts, reference docs, and guardrails.

**Commands** are shortcuts — `/qa`, `/clone`, `/ship` — that route to the appropriate skill.

## CIMPL + SPI: Side by Side

The OSDU ecosystem has two infrastructure patterns:

| | CIMPL | SPI |
|---|---|---|
| **Repository** | `cimpl-azure-provisioning` | `osdu-spi-infra` |
| **Middleware** | In-cluster (RabbitMQ, MinIO, Keycloak) | Azure PaaS (CosmosDB, Service Bus, Storage) |
| **Platform** | GitLab | GitHub |
| **Goal** | Community reference implementation | Azure-native production SPI |

Both run on AKS, use `azd` for provisioning, and share Terraform/Helm patterns. The agent system works with both — the `iac` and `health` skills auto-detect which context you're in and adapt.

## What's Inside

| Component | Count | Examples |
|-----------|-------|---------|
| Agents | 8 | @osdu, @cimpl, @spi, qa-runner, qa-analyzer, build-runner |
| Skills | 28 | brain, glab, maven, osdu-qa, iac, forks, send, health |
| Commands | 4 | /clone, /prime, /qa, /ship |
| MCP Server | 1 | osdu-mcp-server (live platform data access) |
| Trigger Evals | 28 | Per-skill routing accuracy tests |
| Scenario Evals | 20 | Multi-turn workflow tests |

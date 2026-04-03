# OSDU SPI Skills

Unified AI agent skills for the OSDU / SPI ecosystem. This document is the universal skill catalog — read by Copilot, Codex, and referenced by Claude via CLAUDE.md.

## Skill Catalog

### Shared Skills

Available to the default context and all specialist agents.

| Skill | Path | Domain | Triggers |
|-------|------|--------|----------|
| brain | `skills/brain/SKILL.md` | Obsidian vault reads/writes | vault, knowledge, decisions, daily notes |
| briefing | `skills/briefing/SKILL.md` | Daily briefing generation | "gm", "good morning", "briefing" |
| clone | `skills/clone/SKILL.md` | Clone OSDU repos to workspace | "clone partition", "setup workspace" |
| consolidate | `skills/consolidate/SKILL.md` | Vault hygiene and cleanup | "consolidate", "clean up the vault" |
| contribute | `skills/contribute/SKILL.md` | Push changes into someone else's MR | "contribute to MR", "sub-MR" |
| glab | `skills/glab/SKILL.md` | GitLab CLI operations | MRs, pipelines, GitLab issues |
| health | `skills/health/SKILL.md` | Environment health reporting | "cluster health", "environment status" |
| learn | `skills/learn/SKILL.md` | Knowledge acquisition from external sources | "learn about", "study the wiki" |
| mr-review | `skills/mr-review/SKILL.md` | MR code analysis + pipeline diagnostics | "review MR", "assess this MR", MR URL |
| osdu-activity | `skills/osdu-activity/SKILL.md` | Open MRs, pipeline status | "what's failing in CI?" |
| osdu-data-load | `skills/osdu-data-load/SKILL.md` | Load datasets into OSDU instances | "load reference data", "bootstrap instance" |
| osdu-engagement | `skills/osdu-engagement/SKILL.md` | Contribution and review stats | "who's contributing most?" |
| osdu-quality | `skills/osdu-quality/SKILL.md` | Test reliability analysis | "how reliable are partition tests?" |
| send | `skills/send/SKILL.md` | Ship changes (review, commit, push, MR) | "send it", "ship it" |
| setup | `skills/setup/SKILL.md` | Environment validation and tool install | "setup", "check my environment" |

### Specialist Skills

Loaded by owning agent only.

| Skill | Path | Owner | Domain |
|-------|------|-------|--------|
| acceptance-test | `skills/acceptance-test/SKILL.md` | @osdu | Java acceptance/integration tests against live environments |
| build-runner | `skills/build-runner/SKILL.md` | @osdu | Build execution with structured output |
| dependencies | `skills/dependencies/SKILL.md` | @osdu | Dependency analysis and risk scoring |
| forks | `skills/forks/SKILL.md` | @spi | Three-branch fork lifecycle, upstream sync |
| iac | `skills/iac/SKILL.md` | @cimpl, @spi | Terraform, AVM, Helm, AKS safeguards |
| maven | `skills/maven/SKILL.md` | @osdu | Java builds and dependency management |
| osdu-qa | `skills/osdu-qa/SKILL.md` | @osdu | QA test execution, environments, and reporting |
| status | `skills/status/SKILL.md` | @spi | Cross-repo dashboard |

### Default-Only Skills

| Skill | Path | Domain |
|-------|------|--------|
| dependency-scan | `skills/dependency-scan/SKILL.md` | Full dependency analysis with risk scoring |
| fossa | `skills/fossa/SKILL.md` | Fix FOSSA NOTICE file from failed pipeline |
| loop | `skills/loop/SKILL.md` | In-session recurring tasks |
| maintainer | `skills/maintainer/SKILL.md` | MR review/allow via trusted branch sync |
| remediate | `skills/remediate/SKILL.md` | Apply dependency updates from scan report |

## Agents

| Agent | Path | Domain |
|-------|------|--------|
| osdu | `agents/osdu.md` | Platform operations: builds, tests, dependencies, live platform data |
| cimpl | `agents/cimpl.md` | CIMPL infrastructure: Terraform, Helm, AKS, Kustomize |
| spi | `agents/spi.md` | SPI infrastructure: Azure PaaS, fork management |
| build-runner | `agents/build-runner.md` | Sub-agent: structured build execution |
| qa-runner | `agents/qa-runner.md` | Sub-agent: parallel test execution |
| qa-analyzer | `agents/qa-analyzer.md` | Sub-agent: test failure root cause analysis |
| qa-comparator | `agents/qa-comparator.md` | Sub-agent: cross-environment result comparison |
| qa-reporter | `agents/qa-reporter.md` | Sub-agent: QA report and dashboard generation |

## Commands

| Command | Path | Description |
|---------|------|-------------|
| /clone | `commands/clone.md` | Clone an OSDU repository |
| /prime | `commands/prime.md` | Prime workspace context |
| /qa | `commands/qa.md` | Run QA tests |
| /ship | `commands/ship.md` | Ship changes (review, commit, push, MR) |

## Routing

The default context **observes, plans, and ships**. Specialist agents **operate** in their domain.

| Signal | Route | Examples |
|--------|-------|----------|
| Briefing, daily standup | Default (briefing) | "gm", "good morning" |
| Goal tracking, priorities | Default (brain) | "what should I focus on?" |
| Ship / commit / push / MR | Default (send) | "send it", "ship it" |
| Review an MR | Default (mr-review) | "review MR 845" |
| Contribute to someone's MR | Default (contribute) | "push this into their MR" |
| Environment health | Default (health) | "cluster health" |
| Pipeline status, open MRs | Default (osdu-activity) | "what's failing?" |
| Test reliability stats | Default (osdu-quality) | "how reliable are partition tests?" |
| Contribution stats | Default (osdu-engagement) | "who's contributing?" |
| Load test data | Default (osdu-data-load) | "load reference data" |
| Clone repos | Default (clone) | "clone partition" |
| Learn from external source | Default (learn) | "learn about OSDU" |
| Build a service | @osdu (build-runner) | "build partition" |
| Run tests, analyze failures | @osdu (osdu-qa) | "run smoke tests" |
| Acceptance tests | @osdu (acceptance-test) | "run acceptance tests for storage" |
| Dependency analysis, CVEs | @osdu (dependencies) | "check deps for partition" |
| FOSSA / NOTICE fixes | Default (fossa) | "fix FOSSA failure" |
| Terraform / IaC changes | @cimpl or @spi (iac) | "add a readiness probe" |
| Fork management | @spi (forks) | "sync upstream for partition" |
| Quick factual question | Answer directly | "what branch am I on?" |

Delegation is **one-way** — the default context delegates to specialists. Specialists do not invoke the default context or each other.

## Rules

1. **Quick facts — answer directly.** Don't route to an agent for "what branch am I on?"
2. **Observe vs operate** is the key boundary. Understanding state, planning, shipping → default context. Changing infrastructure or platform services → specialist agent.
3. **When two specialists could handle it**, pick the one whose domain is the primary concern.
4. **Ambiguous?** State the inferred route in one line before proceeding.
5. **Skills are always available.** Any context can use shared skills in `skills/`.
6. **Missing tools — delegate to setup.** If a pre-flight check fails with "command not found", stop and switch to the `setup` skill. Do NOT install tools inline.
7. **Graceful degradation without brain vault.** If `$OSDU_BRAIN` does not exist, skills still work — just without persistence. Reports save to the current working directory. Never create the vault directory implicitly.

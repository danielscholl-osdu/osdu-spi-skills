---
title: Skills
description: Complete skill reference organized by function
---

Skills are domain procedures that agents execute. Each skill is a directory containing a `SKILL.md` file with instructions, guardrails, and optionally scripts, reference docs, and templates.

## Observe and Plan

| Skill | Description |
|-------|-------------|
| **brain** | Read/write the Obsidian vault — decisions, reports, meeting notes, knowledge base |
| **briefing** | Generate daily briefing from GitLab MRs, SPI fork health, vault goals |
| **learn** | Study external sources (GitLab wikis, docs, URLs) and produce knowledge notes |
| **consolidate** | Scan vault for stale notes and contradictory decisions |
| **osdu-activity** | Query open MRs, pipelines, issues across OSDU services |
| **osdu-engagement** | Engineering contribution analysis — commits, reviews, ADR engagement |
| **osdu-quality** | CI/CD test reliability — flaky tests, pass rates, cloud provider metrics |
| **glab** | GitLab CLI guardrails — correct syntax, self-hosted instances, common errors |
| **health** | Environment health — cluster, Azure PaaS, workloads, OSDU services |
| **status** | Cross-repo dashboard — open issues/PRs, blocked cascades, workflow health (SPI) |

## Ship and Automate

| Skill | Description |
|-------|-------------|
| **send** | Ship changes: review → quality checks → commit → push → MR/PR |
| **mr-review** | Review a merge request: code analysis + pipeline diagnostics + verdict |
| **contribute** | Push changes into someone else's MR via sub-MR |
| **clone** | Clone OSDU repos with bare clone + worktree layout |
| **maintainer** | Sync trusted branches so child pipelines can run |
| **fossa** | Fix FOSSA NOTICE file from failed CI pipeline |
| **loop** | Run a prompt on a recurring interval |

## Operate — Platform

| Skill | Description |
|-------|-------------|
| **maven** | Maven dependency checking, security scanning, build profiles |
| **dependencies** | Dependency analysis and risk scoring |
| **dependency-scan** | Full dependency scan with CVE overlay and remediation report |
| **build-runner** | Execute builds and compress output to structured summaries |
| **acceptance-test** | Java acceptance/integration tests against live environments |
| **osdu-qa** | OSDU QA testing — environments, API tests, failure analysis, reports |
| **remediate** | Apply dependency updates from scan reports with build verification |
| **osdu-data-load** | Load datasets (reference data, TNO, Volve, NOPIMS) into OSDU instances |

## Operate — Infrastructure

| Skill | Description |
|-------|-------------|
| **iac** | Terraform, Helm, AKS Safeguards, Azure PaaS — both CIMPL and SPI |
| **forks** | Three-branch fork lifecycle — upstream sync, cascade, conflict resolution (SPI) |
| **setup** | Check and install CLI tool dependencies |

## Skill Structure

Each skill follows this layout:

```
skills/brain/
├── SKILL.md              # Primary instructions (required)
├── references/           # Supporting documentation
│   ├── templates.md
│   └── session-digest.md
├── scripts/              # Executable code
│   └── consolidate.py
└── scaffold/             # Template files
    └── templates/
        ├── daily-note.md
        └── decision-record.md
```

The `SKILL.md` frontmatter declares:

```yaml
---
name: brain
allowed-tools: Bash, Read, Write, Glob, Grep
description: >-
  Use when reading from, writing to, or organizing the OSDU brain vault...
---
```

- `name` — lowercase kebab-case, must match directory name
- `allowed-tools` — Claude Code tool restrictions (Copilot ignores this)
- `description` — trigger description used by all platforms for routing

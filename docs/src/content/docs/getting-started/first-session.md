---
title: First Session
description: Try out OSDU SPI Skills in your first conversation
---

After installation, open your AI coding assistant and try these prompts.

## Morning Briefing

> good morning

The assistant generates a daily briefing by aggregating open MRs, pipeline failures, and goal progress from the Obsidian brain vault.

## Clone a Service

> clone partition

Downloads the `partition` service repo from GitLab using bare clone + worktree layout.

## Scan Dependencies

> check dependencies for storage

Runs a full dependency analysis with CVE overlay, producing a risk-scored remediation report.

## Run QA Tests

> run smoke tests on azure/ship

Executes OSDU API test collections against a live environment and generates a report.

## Review a Merge Request

> review MR 845 on partition

Fetches the MR diff, categorizes changes by risk area, checks pipeline status, classifies failures, and drafts a review comment.

## Ship Changes

> send it

Reviews your changes, runs quality checks, commits with a conventional message, pushes, and creates a merge request.

## Infrastructure Health

> report on my environments

Enumerates AZD environments, connects to clusters, checks node health, workload status, Azure PaaS resources (SPI), and OSDU platform services.

## Common Task Routing

| What you say | What happens |
|---|---|
| "gm" / "briefing" | Daily briefing from brain vault |
| "clone partition" | Clone OSDU repo with worktree layout |
| "build storage" | Maven build with structured output |
| "run acceptance tests" | Java integration tests against live env |
| "check deps for legal" | Dependency scan with CVE overlay |
| "fix the FOSSA failure" | Download updated NOTICE file |
| "review MR 320" | Code analysis + pipeline diagnostics |
| "contribute to MR 845" | Push changes into someone else's MR |
| "ship it" | Review → commit → push → MR |
| "environment health" | Cluster + PaaS + OSDU service health |
| "add a Helm chart" | IaC skill for infrastructure changes |
| "sync upstream for partition" | Fork management (SPI three-branch) |

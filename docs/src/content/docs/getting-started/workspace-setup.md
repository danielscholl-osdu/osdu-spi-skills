---
title: Workspace Setup
description: Setting up a complete OSDU workspace with AI agent skills
---

This guide walks through setting up a complete OSDU development workspace where your AI coding assistant knows how to work with all your repositories, infrastructure, and platform services.

## Overview

The OSDU workspace is a directory containing multiple cloned repositories (services, infrastructure, tools) plus the AI agent skills that know how to operate across them. After setup:

- Your AI assistant can clone, build, test, scan, and ship across 30+ OSDU services
- Infrastructure operations (Terraform, Helm, AKS) are handled by specialist agents
- Fork management, upstream sync, and cascade workflows are automated
- A persistent knowledge vault tracks decisions, reports, and architecture notes

## Step 1: Install APM

```bash
# macOS / Linux
curl -sSL https://aka.ms/apm-unix | sh

# Or via pip
pip install apm-cli

# Verify
apm --version
```

## Step 2: Create Your Workspace

```bash
mkdir -p ~/source/osdu-workspace
cd ~/source/osdu-workspace
git init
```

## Step 3: Add OSDU SPI Skills

Create an `apm.yml` that declares the skills package:

```yaml
# apm.yml
name: osdu-workspace
version: 0.1.0
description: OSDU development workspace

dependencies:
  apm:
    - danielscholl-osdu/osdu-spi-skills#v1.0.0
```

Install:

```bash
apm install
```

This deploys agents, skills, commands, and MCP configuration for your AI tool (Copilot, Claude, Cursor — auto-detected).

## Step 4: Install CLI Tools

Open your AI assistant and ask:

> check my environment

Or run the setup skill directly:

> /setup

The assistant checks for required tools (`glab`, `az`, `terraform`, `helm`, `kubectl`, `java`, `mvn`, `newman`, etc.) and provides install commands for anything missing.

## Step 5: Clone OSDU Services

Ask your assistant to clone the services you need:

> clone partition storage legal entitlements

This clones each service from GitLab using bare clone + worktree layout:

```
osdu-workspace/
├── partition/
│   ├── .bare/           # Bare git repo
│   └── master/          # Read-only reference
├── storage/
│   ├── .bare/
│   └── master/
├── .github/             # Copilot agents/skills (from APM)
├── .claude/             # Claude agents/skills (from APM)
├── apm.yml              # Skills dependency
└── apm.lock.yaml        # Pinned version
```

## Step 6: Configure MCP Server (Optional)

For live platform data access (searching records, listing schemas, checking entitlements), configure the OSDU MCP server:

```bash
export OSDU_MCP_SERVER_URL="https://your-osdu-instance.energy.azure.com"
export OSDU_MCP_SERVER_DATA_PARTITION="opendes"
```

The MCP server is auto-configured by APM. Just set the environment variables and restart your AI tool.

## Step 7: Initialize Brain Vault (Optional)

For persistent knowledge management:

> initialize brain vault

This creates an Obsidian vault at `~/.osdu-brain` with templates for decisions, daily notes, reports, and architecture notes.

## Updating Skills

When a new version of the skills package is released:

```bash
# Update to latest
apm deps update

# Or pin to a specific version
# Edit apm.yml: danielscholl-osdu/osdu-spi-skills#v1.1.0
apm install
```

## Workspace Layout After Setup

```
osdu-workspace/
├── apm.yml                    # Skills dependency declaration
├── apm.lock.yaml              # Pinned commit SHA
├── apm_modules/               # Downloaded packages (gitignored)
│
├── .github/                   # Copilot: agents, skills, prompts
│   ├── agents/
│   ├── skills/
│   └── prompts/
├── .claude/                   # Claude: agents, skills, commands
│   ├── agents/
│   ├── skills/
│   └── commands/
├── .cursor/                   # Cursor: agents, skills
│
├── partition/                 # OSDU service repos
│   ├── .bare/
│   └── master/
├── storage/
├── legal/
├── cimpl-azure-provisioning/  # Infrastructure repos
├── osdu-spi-infra/
└── ...
```

## Team Onboarding

New team members get the full setup with three commands:

```bash
git clone <your-workspace-repo>
cd osdu-workspace
apm install
```

The `apm.yml` and `apm.lock.yaml` ensure everyone has identical AI tool configuration. The lock file pins the exact commit SHA, so there are no surprises.

## Multiple Workspaces

You can have separate workspaces for different purposes:

```bash
# OSDU platform development
cd ~/source/osdu-workspace && apm install

# SPI infrastructure only
cd ~/source/spi-workspace && apm install
```

Each workspace gets its own `apm.yml` and can pin different versions of the skills package.

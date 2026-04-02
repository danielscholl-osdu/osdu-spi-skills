---
title: Installation
description: How to install OSDU SPI Skills via APM or directly
---

## Via APM (Recommended)

[APM](https://github.com/microsoft/apm) (Agent Package Manager) is the simplest way to install. It auto-detects your AI tools and deploys the right files.

### 1. Install APM

```bash
# macOS / Linux
curl -sSL https://aka.ms/apm-unix | sh

# Windows PowerShell
irm https://aka.ms/apm-windows | iex

# Or via pip
pip install apm-cli
```

### 2. Add to Your Project

```bash
cd your-project
apm install danielscholl-osdu/osdu-spi-skills
```

APM will:
- Download the package to `apm_modules/`
- Deploy agents, skills, commands to `.github/`, `.claude/`, `.cursor/` (auto-detected)
- Configure the `osdu-mcp-server` MCP server for live platform data access
- Generate `apm.lock.yaml` for reproducible installs

### 3. Pin a Version

```bash
# Pin to a tag
apm install danielscholl-osdu/osdu-spi-skills#v1.0.0

# Pin to a branch
apm install danielscholl-osdu/osdu-spi-skills#main
```

### 4. Update

```bash
apm deps update
```

## Via apm.yml

For team projects, declare the dependency in `apm.yml` so everyone gets the same setup:

```yaml
# apm.yml
name: my-osdu-project
version: 0.1.0
dependencies:
  apm:
    - danielscholl-osdu/osdu-spi-skills#v1.0.0
```

Then:

```bash
git clone <your-project> && cd <your-project>
apm install
# Done — all AI tools configured
```

Commit `apm.yml` and `apm.lock.yaml` to version control.

## Target a Specific Platform

```bash
# Only Claude Code
apm install danielscholl-osdu/osdu-spi-skills --target claude

# Only Copilot
apm install danielscholl-osdu/osdu-spi-skills --target copilot

# All platforms
apm install danielscholl-osdu/osdu-spi-skills --target all
```

## Manual Installation

If you prefer not to use APM:

### For Claude Code

Clone the repo and symlink:

```bash
git clone https://github.com/danielscholl-osdu/osdu-spi-skills.git
cd your-project
ln -s ../osdu-spi-skills/agents .claude/agents
ln -s ../osdu-spi-skills/skills .claude/skills
ln -s ../osdu-spi-skills/commands .claude/commands
```

### For GitHub Copilot

```bash
copilot plugin install https://github.com/danielscholl-osdu/osdu-spi-skills.git
```

## Verify Installation

After installation, verify by asking your AI assistant:

> "What skills do you have for OSDU?"

It should reference skills like `brain`, `glab`, `maven`, `osdu-qa`, etc.

## Prerequisites

The skills themselves require various CLI tools depending on which skills you use:

| Tool | Required by | Install |
|------|-------------|---------|
| `glab` | glab, send, fossa, maintainer | `brew install glab` |
| `gh` | forks, status | `brew install gh` |
| `terraform` | iac | `brew install terraform` |
| `helm` | iac, health | `brew install helm` |
| `kubectl` | iac, health | `brew install kubectl` |
| `az` | health | `brew install azure-cli` |
| `azd` | iac, health | `brew install azure/azd/azd` |
| `java`, `mvn` | maven, build-runner | `brew install openjdk@17 maven` |
| `newman` | osdu-qa | `npm install -g newman` |

Run the **setup** skill to check what's installed: ask your AI assistant "check my environment" or "run setup".

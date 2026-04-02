---
title: Cursor & Others
description: Using OSDU SPI Skills with Cursor, OpenCode, and Codex
---

## Cursor

### Installation

```bash
apm install danielscholl-osdu/osdu-spi-skills --target cursor
```

### What Gets Deployed

| Directory | Contents |
|-----------|----------|
| `.cursor/agents/` | 8 agent files |
| `.cursor/skills/` | 28 skill directories |
| `.cursor/mcp.json` | MCP server configuration |

Cursor does not support commands/prompts. Skills and agents work through Cursor's agent and rules system.

## OpenCode

### Installation

```bash
apm install danielscholl-osdu/osdu-spi-skills --target opencode
```

### What Gets Deployed

| Directory | Contents |
|-----------|----------|
| `.opencode/agents/` | 8 agent files |
| `.opencode/skills/` | 28 skill directories |
| `.opencode/commands/` | 4 command files |
| `opencode.json` | MCP server configuration |

## Codex

### Installation

```bash
apm install danielscholl-osdu/osdu-spi-skills --target codex
```

Codex receives agent definitions in `.codex/agents/` as TOML files. Skills are deployed to `.agents/skills/`.

## All Platforms at Once

```bash
apm install danielscholl-osdu/osdu-spi-skills --target all
```

This creates output directories for all supported platforms simultaneously.

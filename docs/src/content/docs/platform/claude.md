---
title: Claude Code
description: Using OSDU SPI Skills with Claude Code
---

## Installation

### Via APM

```bash
apm install danielscholl-osdu/osdu-spi-skills --target claude
```

## What Gets Deployed

| Directory | Contents |
|-----------|----------|
| `.claude/agents/` | 8 agent files (`*.md`) |
| `.claude/skills/` | 28 skill directories |
| `.claude/commands/` | 4 command files |

The `CLAUDE.md` at the repo root provides the delegation model, skill ownership, and core principles.

## Agent Delegation

Claude Code uses the `Agent` tool with `subagent_type`:

```
Agent(
  subagent_type: "osdu:osdu",
  description: "Build partition service",
  prompt: "..."
)
```

## Commands

Claude Code commands are invoked with `/`:

```
/clone partition
/qa test smoke
/ship
```

## Allowed Tools

Skills declare which tools they need via `allowed-tools` frontmatter:

```yaml
---
name: brain
allowed-tools: Bash, Read, Write, Glob, Grep
---
```

Claude Code enforces this — the skill can only use the declared tools. Other platforms ignore this field.

## MCP Server

The `osdu-mcp-server` provides live platform data. When installed via APM, the MCP server is configured automatically. You can also configure it manually:

```json
{
  "mcpServers": {
    "osdu-mcp-server": {
      "command": "uvx",
      "args": ["osdu-mcp-server"],
      "env": {
        "OSDU_MCP_SERVER_URL": "https://your-osdu-instance.com",
        "OSDU_MCP_SERVER_DATA_PARTITION": "opendes"
      }
    }
  }
}
```

## Sub-Plugin Migration Note

This package replaces the previous `claude-osdu` multi-plugin marketplace package, which had three separate sub-plugins (`osdu`, `cimpl`, `spi`). In this unified package:

- All skills live in a flat `skills/` directory
- Agent scoping is declared in agent definitions, not directory isolation
- The `cimpl:health` and `spi:health` distinction is replaced by a single `health` skill that auto-detects environment type

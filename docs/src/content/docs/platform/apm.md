---
title: APM Integration
description: How this package works with the Agent Package Manager
---

[APM](https://github.com/microsoft/apm) (Agent Package Manager) is an open-source dependency manager for AI agent configuration. Think `package.json` for AI tools.

## How It Works

This package uses `plugin.json` as its manifest. When a consumer runs `apm install`, APM:

1. **Downloads** the package to `apm_modules/`
2. **Detects** which AI tools are present (`.github/`, `.claude/`, `.cursor/`)
3. **Deploys** agents, skills, commands, and MCP config to each target
4. **Locks** the exact commit SHA in `apm.lock.yaml`

## What Gets Deployed

| Component | Copilot (.github/) | Claude (.claude/) | Cursor (.cursor/) |
|-----------|--------------------|--------------------|---------------------|
| Agents | `*.agent.md` | `*.md` | `*.md` |
| Skills | `skills/*/` | `skills/*/` | `skills/*/` |
| Commands | `prompts/*.prompt.md` | `commands/*.md` | — |
| MCP | `.vscode/mcp.json` | — | `mcp.json` |

APM handles filename adaptation automatically — `osdu.md` becomes `osdu.agent.md` for Copilot and `osdu.toml` for Codex.

## Package Structure

```
osdu-spi-skills/
├── plugin.json        # Manifest: name, agents, skills, commands, mcpServers
├── agents/            # 8 agent definitions
├── skills/            # 28 skill directories
├── commands/          # 4 command files
├── AGENTS.md          # Copilot routing table
└── CLAUDE.md          # Claude routing table
```

The `plugin.json` declares everything APM needs:

```json
{
  "name": "osdu-spi-skills",
  "agents": "agents/",
  "skills": "skills/",
  "commands": "commands/",
  "mcpServers": {
    "osdu-mcp-server": {
      "command": "uvx",
      "args": ["osdu-mcp-server"]
    }
  }
}
```

## Version Pinning

Pin to a specific version for reproducible builds:

```yaml
# apm.yml
dependencies:
  apm:
    - danielscholl-osdu/osdu-spi-skills#v1.0.0
```

## MCP Server

The `osdu-mcp-server` provides live OSDU platform data access — searching records, listing schemas, checking entitlements. APM auto-configures it for each runtime:

| Runtime | Config file | Format |
|---------|-------------|--------|
| VS Code | `.vscode/mcp.json` | `{ "servers": { ... } }` |
| Cursor | `.cursor/mcp.json` | `{ "mcpServers": { ... } }` |
| OpenCode | `opencode.json` | `{ "mcp": { ... } }` |

## Updating

```bash
apm deps update                           # Update all dependencies
apm deps update danielscholl-osdu/osdu-spi-skills  # Update this package only
```

## Uninstalling

```bash
apm uninstall danielscholl-osdu/osdu-spi-skills
```

APM cleanly removes all deployed files tracked in `apm.lock.yaml`.

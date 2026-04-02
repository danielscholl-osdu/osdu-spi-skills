# Contributing

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- `tmux` — `brew install tmux` (for L3/L4 session tests)
- GitHub Copilot CLI and/or Claude Code (for live tests)
- [APM](https://github.com/microsoft/apm) — `pip install apm-cli` (for L0 verification)

## Quick Start

```bash
git clone https://github.com/danielscholl-osdu/osdu-spi-skills.git
cd osdu-spi-skills
make test          # Should pass — L0 + L1 + L2 + pytest
```

## Development Workflow

```bash
# After every change (fast, no AI)
make test

# Before pushing (requires Copilot or Claude CLI)
make test-triggers CLI=copilot

# For multi-turn workflow changes
make test-sessions CLI=claude S=brain

# Full matrix
make test-all
```

## Running Tests

### L0 — APM Verification (~5s, no AI)

Validates `plugin.json`, agent files, skill directories, and commands.

```bash
make test-apm
```

### L1 — Structure Validation (~3s, no AI)

Checks frontmatter, cross-references, naming conventions.

```bash
make lint
```

### L2 — Trigger Eval Dry-Run (~10s, no AI)

Validates trigger eval JSON files are well-formed and balanced (8+ positive, 5+ negative).

```bash
make unit              # All skills
make unit S=brain      # One skill
```

### L3 — Live Trigger Accuracy (~2m, requires AI)

Sends prompts to a live AI assistant and checks correct skill activation.

```bash
make test-triggers CLI=copilot
make test-triggers CLI=claude
make test-triggers CLI=copilot S=glab   # One skill
```

### L4 — Session Tests (~5m, requires AI + tmux)

Multi-turn conversation tests with output assertions.

```bash
make test-sessions CLI=copilot
make test-sessions CLI=claude S=brain
make test-sessions CLI=copilot DEBUG=1  # Show tmux output
```

### L5 — Value Benchmark (variable, requires AI)

Compares skill performance with vs without the skill enabled.

```bash
make test-benchmark S=brain
```

### Pytest Unit Tests

```bash
make pytest
```

## Testing Philosophy

AI plugins are **probabilistic**. Quality degrades silently — a description change can steal triggers, a routing edit can break conversations. The six-layer framework catches issues at every level:

| Layer | Catches |
|-------|---------|
| L0 | Missing files, broken manifests |
| L1 | Invalid frontmatter, orphaned files, naming violations |
| L2 | Unbalanced trigger evals (too few positive or negative cases) |
| L3 | Wrong skill activation on real prompts |
| L4 | Broken multi-turn workflows, context loss |
| L5 | Skill regressions (did the skill get worse?) |

## Adding a New Skill

1. Create `skills/<name>/SKILL.md` with frontmatter (`name`, `description`, `allowed-tools`)
2. Create `tests/evals/triggers/<name>.json` with 8+ positive and 5+ negative evals
3. Optionally create `tests/evals/scenarios/<name>-workflow.json` for multi-turn tests
4. Update `AGENTS.md` and `CLAUDE.md` routing tables
5. Run `make test` — all green
6. Run `make test-triggers CLI=copilot S=<name>` — verify accuracy
7. Submit PR with conventional commit: `feat(skills): add <name>`

## Adding a New Agent

1. Create `agents/<name>.md` with frontmatter (`name`, `description`)
2. Declare skill scope in the agent definition
3. Create trigger evals
4. Update routing files
5. Run `make test`

## Commit Conventions

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(skills): add dependency-scan skill
fix(agents): correct osdu agent routing for acceptance tests
docs: update installation guide
test: add trigger evals for health skill
chore: update deps.json with kubelogin
```

## Key Conventions

### Do

- Keep skill descriptions under 500 characters
- Include "Not for:" exclusions in every description
- Test on both Copilot and Claude before merging
- Use `$OSDU_WORKSPACE` and `$OSDU_BRAIN` for paths
- Reference the `setup` skill when tools are missing

### Don't

- Don't overlap skill triggers — check negative evals
- Don't hard-code paths or environment-specific values
- Don't add AI attribution to commits
- Don't skip L1+L2 tests before pushing

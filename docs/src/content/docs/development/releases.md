---
title: Releases
description: Versioning strategy, release process, and APM distribution
---

## Versioning

This package uses [semantic versioning](https://semver.org/) in `plugin.json`:

```json
{ "version": "1.2.3" }
```

| Bump | When | Example |
|------|------|---------|
| **Patch** (1.2.**3**) | Bug fixes, eval improvements, docs | Fix glab trigger description |
| **Minor** (1.**2**.0) | New skills, new agents, new features | Add `status` skill |
| **Major** (**2**.0.0) | Breaking changes to routing or structure | Rename agent, remove skill |

## Release Process

### 1. Bump Version in PR

When your PR changes skills, agents, or commands, bump the version in `plugin.json`:

```bash
# Example: adding a new skill (minor bump)
# Edit plugin.json: "version": "1.1.0" → "1.2.0"
```

CI will warn if skill changes are detected without a version bump.

### 2. Merge to Main

After PR approval and CI passes, merge to `main`.

### 3. Tag the Release

```bash
git tag v1.2.0
git push origin v1.2.0
```

### 4. Automated Release

The tag triggers the release workflow which:

1. **Validates** — runs tests, verifies tag matches `plugin.json` version
2. **Creates GitHub Release** — with auto-generated notes from conventional commits and an install summary
3. **Deploys docs** — ensures the docs site matches the released version

### 5. Consumers Update

```bash
# Pin to the new version
# apm.yml: danielscholl-osdu/osdu-spi-skills#v1.2.0
apm install
```

## APM Distribution

APM resolves packages directly from git — no registry or build step needed. When a consumer runs:

```bash
apm install danielscholl-osdu/osdu-spi-skills#v1.2.0
```

APM:
1. Clones the repo at the tag's commit SHA
2. Reads `plugin.json` for agent/skill/command/MCP declarations
3. Deploys to platform directories (`.github/`, `.claude/`, `.cursor/`)
4. Records the commit SHA in `apm.lock.yaml`

**No build artifacts to publish.** The git repo IS the package.

## What Gets Shipped

| File | Purpose | Consumed by |
|------|---------|-------------|
| `plugin.json` | Package manifest | APM |
| `agents/*.md` | Agent definitions | All platforms |
| `skills/*/SKILL.md` | Skill instructions | All platforms |
| `commands/*.md` | Slash commands | Claude, OpenCode |
| `AGENTS.md` | Routing table | Copilot |
| `CLAUDE.md` | Routing table | Claude |
| `reference/` | Shared docs | Agents/skills |

Tests, docs, workflows, and Makefile are NOT deployed to consumers — they stay in the source repo.

## CI/CD Pipeline

| Event | What runs |
|-------|-----------|
| **Pull request** | L0-L2 + pytest, docs build (if changed), version check (if skills changed) |
| **Merge to main** | L0-L2 + pytest, deploy docs (if changed) |
| **Tag push** | Full validation, create release, deploy docs |
| **Manual dispatch** | Docs deployment |

### Change Detection

CI uses path filters to skip unnecessary work:

| Change | Jobs triggered |
|--------|---------------|
| `skills/**`, `agents/**`, `commands/**`, `plugin.json` | validate + version-check |
| `docs/**` | docs-build (PR) or deploy (main) |
| `tests/**`, `Makefile` | validate |
| `.github/workflows/**` | all |

## Conventional Commits

Use conventional commits for auto-generated release notes:

```
feat(skills): add dependency-scan skill
fix(agents): correct osdu routing for acceptance tests
docs: update workspace setup guide
test: improve glab trigger evals
chore: update deps.json with kubelogin
```

GitHub auto-groups these in release notes by category.

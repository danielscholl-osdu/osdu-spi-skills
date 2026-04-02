---
title: Adding Skills
description: Step-by-step guide for adding a new skill or agent
---

## Adding a New Skill

### 1. Create the Skill Directory

```bash
mkdir -p skills/my-skill
```

### 2. Write SKILL.md

```yaml
---
name: my-skill
allowed-tools: Bash, Read, Glob
description: >-
  One-paragraph description of what this skill does, when to trigger it,
  and what it is NOT for. Keep under 500 characters. Include trigger
  phrases and negative boundaries.
---

# My Skill

## Quick Start

Check prerequisites:
\`\`\`bash
some-tool --version
\`\`\`
If not found, **stop and use the `setup` skill**.

## Procedure

Step-by-step instructions...
```

### 3. Create Trigger Evals

```bash
cat > tests/evals/triggers/my-skill.json << 'EOF'
{
  "skill_name": "my-skill",
  "evals": [
    { "query": "do the thing my skill does", "should_trigger": true },
    { "query": "another way to ask for it", "should_trigger": true },
    { "query": "something another skill handles", "should_trigger": false, "note": "→ other-skill" }
  ]
}
EOF
```

**Required:** At least 8 positive and 5 negative evals. Negative evals should reference which skill *should* handle the query.

### 4. Create Scenario Eval (Optional)

For multi-step skills, add a scenario:

```bash
cat > tests/evals/scenarios/my-skill-workflow.json << 'EOF'
{
  "name": "my-skill-workflow",
  "description": "Test my-skill end-to-end",
  "ready_pattern": "❯|\\$|>|claude",
  "steps": [
    {
      "name": "basic-usage",
      "prompt": "use my skill to do something",
      "timeout": 120,
      "assertions": [
        { "pattern": "expected output pattern", "type": "regex", "description": "Skill produces expected result" }
      ]
    }
  ]
}
EOF
```

### 5. Update Routing Files

Add the skill to the routing tables:

- **AGENTS.md** — add to the appropriate skills section and routing table
- **CLAUDE.md** — add to the shared or specialist skills list

### 6. Update plugin.json (if needed)

The `"skills": "skills/"` declaration in `plugin.json` auto-discovers all skill directories. No change needed unless you're modifying agent paths.

### 7. Run Tests

```bash
make test                          # L0 + L1 + L2 + pytest
make test-triggers CLI=copilot S=my-skill  # L3
```

### 8. Verify APM Deployment

```bash
apm install --dry-run . --target all
```

### 9. Submit

Create a PR with conventional commit message: `feat(skills): add my-skill for X`

## Adding a New Agent

### 1. Create Agent File

```bash
cat > agents/my-agent.md << 'EOF'
---
name: my-agent
description: "Brief description of what this agent does"
---

You are the **my-agent** agent. [Charter and instructions...]
EOF
```

### 2. Update Routing Files

- **AGENTS.md** — add routing rules
- **CLAUDE.md** — add delegation model entry

### 3. Update plugin.json

If using a non-standard agents path, update `plugin.json`. The default `"agents": "agents/"` auto-discovers all files.

### 4. Create Trigger Evals

Same process as skills — create `tests/evals/triggers/my-agent.json`.

### 5. Run Tests

```bash
make test
```

## Checklist

- [ ] `SKILL.md` has name, description, and allowed-tools frontmatter
- [ ] Name is lowercase kebab-case matching directory name
- [ ] Description includes trigger phrases and "Not for:" exclusions
- [ ] Trigger evals: 8+ positive, 5+ negative
- [ ] AGENTS.md updated with routing
- [ ] CLAUDE.md updated with skill ownership
- [ ] `make test` passes
- [ ] Tested against both Copilot and Claude

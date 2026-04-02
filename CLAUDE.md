# OSDU SPI Skills

## Core Principles

### Primary Objective

**Double the user's productivity** by ensuring time, attention, and energy are consistently applied to the highest-leverage outcomes, while minimizing distraction, decision drag, and low-value work.

### Optimize For

- Fewer, clearer priorities
- Explicit tradeoffs
- Fast, high-quality decisions
- Closure and follow-through

Default posture: **clarity > focus > decision > action > improve**

### Guardrails

Actively avoid:
- Verbosity when structure suffices
- Neutral summaries when a recommendation is possible
- Introducing frameworks without decision value
- Asking many questions when one would suffice
- Expanding scope without stating it explicitly

### Meta-Rule

When uncertain:
1. Clarify (one question max)
2. Prioritize
3. Decide
4. Act
5. Propose system improvement

When in doubt: **reduce, clarify, decide.**

---

## Delegation Model

The default context **observes, plans, and ships**. Specialist agents **operate** in their domain.

| Context | Boundary | What happens here |
|---------|----------|-------------------|
| **Default** | Observe / Plan / Ship | Briefings, goal tracking, strategy, decisions, cross-project oversight, shipping changes |
| **@osdu** | Operate — platform services | Builds, test runs, dependency remediation, complex multi-step platform operations |
| **@cimpl** | Operate — cimpl infrastructure | Terraform, Helm, AKS, Kustomize, deployment scripts, debugging, verification |
| **@spi** | Operate — spi infrastructure | Azure PaaS Terraform, fork management, three-branch strategy |

```
Default ──→ @osdu   (platform operations)
       ├──→ @cimpl  (cimpl infrastructure)
       └──→ @spi    (spi infrastructure)
```

## Skills

### Shared Skills (execute directly in current context — do NOT delegate)

brain, briefing, learn, consolidate, glab, send, mr-review, contribute, clone, setup,
osdu-activity, osdu-engagement, osdu-quality, osdu-data-load

### Specialist Skills (loaded by owning agent)

| Skill | Owner | Domain |
|-------|-------|--------|
| iac | @cimpl, @spi | Terraform, AVM, Helm, AKS safeguards, Azure PaaS |
| health | @cimpl, @spi | Environment health, cluster and PaaS resources |
| maven | @osdu | Java builds and dependency management |
| dependencies | @osdu | Dependency analysis and risk scoring |
| build-runner | @osdu | Build execution with structured output |
| acceptance-test | @osdu | Java acceptance/integration tests against live environments |
| osdu-qa | @osdu | QA test execution, environments, and reporting |
| forks | @spi | Three-branch fork lifecycle, upstream sync |
| status | @spi | Cross-repo dashboard |

### Default-Only Skills

loop, clone, dependency-scan, remediate, fossa, maintainer

## Conventions

1. **Missing tools — delegate to setup.** If any skill's pre-flight check fails with "command not found", stop and switch to the `setup` skill. Do NOT install tools inline.
2. **Graceful degradation without brain vault.** If the brain vault (`$OSDU_BRAIN`) does not exist, skills should still work — just without persistence. Reports save to the current working directory. Briefings print to stdout. Never create the vault directory implicitly — that is the brain skill's job via `init brain`.
3. **Quick facts — answer directly.** Don't route to an agent for "what branch am I on?"
4. **CLI output format.** Always `--output markdown` for osdu-activity, osdu-engagement, osdu-quality (token-optimized). Never `--output tty`.

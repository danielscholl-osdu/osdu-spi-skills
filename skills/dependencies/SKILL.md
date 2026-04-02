---
name: dependencies
description: |
  Multi-ecosystem dependency analysis tools. Provides structured data for vulnerability scanning
  and version checking. The AI applies intelligence to create rich reports - scripts are data providers only.
  Supports Maven projects (pom.xml), with Python and Node.js support planned.
---

# Dependencies Skill

Tools for dependency analysis data collection. **Scripts provide data, AI provides intelligence.**

## Philosophy

The rich reports users value come from AI intelligence, not script logic:
- Scripts run Trivy, query Maven Central, parse POMs
- AI understands context, identifies legacy packages, assesses breaking changes
- AI writes contextual recommendations, not template fill-ins

## Available Tools

### Trivy Vulnerability Scanning
Via maven skill's scan.py:
```bash
# Full output (can be large - 160KB+ for complex projects)
uv run {workspace}/skills/maven/scripts/scan.py scan \
  --path {project-path} \
  --json

# Compact output (recommended - deduplicates CVEs, ~90% smaller)
uv run {workspace}/skills/maven/scripts/scan.py scan \
  --path {project-path} \
  --compact \
  --json
```

**Compact mode:**
- Deduplicates CVEs by (CVE_ID, package_name)
- Shows full details only for CRITICAL/HIGH severity
- Includes `versions_found[]` and `occurrence_count` to preserve version spread info
- Reduces output from ~160KB to ~16KB for typical projects

### POM Analysis
Via maven skill's scan.py:
```bash
uv run {workspace}/skills/maven/scripts/scan.py analyze \
  --path {pom.xml-path} \
  --check-versions \
  --json
```

### Version Checking
Via maven skill's check.py:
```bash
uv run {workspace}/skills/maven/scripts/check.py check \
  -d {groupId:artifactId} \
  -v {version} \
  --json
```

### Data Aggregation (JSON only)
Via report.py - aggregates data for CI/automation:
```bash
uv run {workspace}/skills/dependencies/scripts/report.py \
  {project-path} \
  --json
```

**Note:** report.py provides JSON data aggregation. For rich markdown reports, use the `/osduskill.dependencies` command which applies AI intelligence.

## Usage

### For Rich Reports (Recommended)
Use the `/osduskill.dependencies` command:
```
/osduskill.dependencies partition
/osduskill.dependencies /path/to/project
```

The command orchestrates tools and applies AI intelligence for:
- Context-aware analysis
- Legacy package identification
- Breaking change assessment
- Downstream impact evaluation
- Risk-prioritized recommendations

### For Raw Data (CI/Automation)
Use scripts directly for structured JSON:
```bash
# Vulnerability data (compact mode recommended)
uv run skills/maven/scripts/scan.py scan --path ./project --compact --json

# Full vulnerability data (large output)
uv run skills/maven/scripts/scan.py scan --path ./project --json

# Version data
uv run skills/maven/scripts/check.py check -d "org.springframework:spring-core" -v "6.1.0" --json
```

## Risk Framework

Risk is calculated by combining multiple factors, not just version bump type.

**Risk Score = Category + Jump + CVE + Location**

| Factor | Modifier | Examples |
|--------|----------|----------|
| **Category** | | |
| Framework | +2 | Spring Boot, Spring Security, Quarkus |
| Serialization/Network/DB/Security/Cloud | +1 | Jackson, Netty, Protobuf, Azure SDK |
| Utility/Testing | 0 | Commons-*, Guava, JUnit |
| **Version Jump** | | |
| Patch | 0 | x.y.Z changes |
| Minor | +1 | x.Y.z changes |
| Major | +3 | X.y.z changes |
| **CVE Context** | | |
| CRITICAL CVE | -1 | Urgency justifies faster action |
| HIGH/MEDIUM/LOW CVE | 0 | Standard priority |
| No CVE (proactive) | +1 | No urgency, more caution |
| **Fix Location** | | |
| Direct/proper fix | 0 | Update in this service |
| Temporary override | +1 | Upstream library should fix |

**Risk Levels:**
- **LOW (0-1)**: Batch apply, standard validation
- **MEDIUM (2-3)**: Individual commits, standard validation
- **HIGH (4+)**: Research first, extended validation

See `reference/risk-framework.md` for complete details.

## Report Structure

**CRITICAL**: Organize reports by **update risk level**, NOT by CVE severity.

### Input → Output Transformation

| Input (from Trivy) | Output (in report) |
|-------------------|-------------------|
| CVE Severity (CRITICAL/HIGH/MEDIUM/LOW) | Update Risk (LOW/MEDIUM/HIGH) |
| "How dangerous is this vulnerability?" | "How safe is this fix to apply?" |

### Required Output Sections

```
## Updates by Risk Level

### LOW Risk (Score 0-1)
[Batch apply - list updates with score breakdown]

### MEDIUM Risk (Score 2-3)
[Individual commits - list updates with score breakdown]

### HIGH Risk (Score 4+)
[Research first - list updates with score breakdown]

## For /osduskill.remediate Command
[Machine-readable tables grouped by risk level]
```

### Examples

- CRITICAL CVE + patch fix = **LOW** risk update (urgent AND safe)
- No CVE + major framework bump = **HIGH** risk update (not urgent, potentially breaking)

**Anti-pattern**: Do NOT organize sections by CVE severity (Critical Vulnerabilities, High Vulnerabilities, etc.). Users need to know what's safe to fix first, not what's most dangerous.

## Workflow

```
┌─────────────────┐         ┌─────────────────┐
│  /osduskill.dependencies  │────────▶│   /osduskill.remediate    │
│                 │         │                 │
│  AI-driven      │         │  Apply updates  │
│  analysis       │         │  with validation│
└─────────────────┘         └─────────────────┘
        │                           │
        ▼                           ▼
   {workspace}/reports/       git commits +
   dependencies-{project}-    code changes
     {date}.md
```

# CI/CD Examples

Two approaches for making OSDU SPI Skills available to AI coding agents in CI/CD.

## Option 1: Runtime Install (Recommended)

Install skills at runtime before the coding agent starts. Always gets the latest version.

1. Copy `apm.yml` to your repo root
2. Copy `copilot-setup-steps.yml` to `.github/workflows/copilot-setup-steps.yml`
3. Commit and push

The Copilot coding agent will run the setup workflow before each session, installing skills into the correct platform directories.

## Option 2: Committed Output

Install skills locally and commit the output. Simpler but requires manual updates.

```bash
# In your project repo
apm install danielscholl-osdu/osdu-spi-skills
git add .github/ .claude/
git commit -m "chore: add OSDU SPI skills"
```

To update later, re-run `apm install` and commit the changes.

## Which to Choose?

| | Runtime Install | Committed Output |
|---|---|---|
| Always up-to-date | Yes | No — manual updates |
| Works offline | No | Yes |
| Repo size impact | None | Adds ~200 files |
| Setup complexity | One-time workflow | One-time install |

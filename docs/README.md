# OSDU SPI Skills — Documentation

[![Built with Starlight](https://astro.badg.es/v2/built-with-starlight/tiny.svg)](https://starlight.astro.build)

Documentation site for OSDU SPI Skills, built with [Astro Starlight](https://starlight.astro.build).

**Live site:** https://danielscholl-osdu.github.io/osdu-spi-skills

## Development

```bash
cd docs
npm install      # Install dependencies (first time only)
npm run dev      # Start dev server at localhost:4321
```

The dev server hot-reloads on changes — edit any `.md` file in `src/content/docs/` and see changes instantly.

## Building

```bash
npm run build    # Build to ./dist/
npm run preview  # Preview the build locally
```

## Adding Pages

Create `.md` or `.mdx` files in `src/content/docs/`. Each file becomes a route based on its path:

```
src/content/docs/
├── index.mdx                        → /
├── getting-started/
│   ├── introduction.md              → /getting-started/introduction/
│   ├── installation.md              → /getting-started/installation/
│   └── first-session.md             → /getting-started/first-session/
├── system/
│   ├── architecture.md              → /system/architecture/
│   ├── agents.md                    → /system/agents/
│   ├── skills.md                    → /system/skills/
│   └── commands.md                  → /system/commands/
├── platform/
│   ├── apm.md                       → /platform/apm/
│   ├── copilot.md                   → /platform/copilot/
│   ├── claude.md                    → /platform/claude/
│   └── cursor.md                    → /platform/cursor/
└── development/
    ├── contributing.md              → /development/contributing/
    ├── testing.md                   → /development/testing/
    └── adding-skills.md             → /development/adding-skills/
```

## Sidebar Configuration

The sidebar is defined in `astro.config.mjs`. To add a new page:

1. Create the `.md` file in the appropriate directory
2. Add it to the `sidebar` array in `astro.config.mjs`

## Frontmatter

Every page needs frontmatter at the top:

```yaml
---
title: Page Title
description: Brief description for search and SEO
---
```

## Deployment

The docs deploy automatically to GitHub Pages when changes are pushed to `main` (via `.github/workflows/docs.yml`). The workflow:

1. Installs Node 20
2. Runs `npm ci` and `npm run build`
3. Uploads `dist/` as a Pages artifact
4. Deploys to GitHub Pages

## Commands Reference

| Command | Action |
|---------|--------|
| `npm install` | Install dependencies |
| `npm run dev` | Start dev server at `localhost:4321` |
| `npm run build` | Build production site to `./dist/` |
| `npm run preview` | Preview build locally |
| `npm run astro check` | Check for errors |

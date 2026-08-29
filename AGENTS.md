# AGENTS.md

## Purpose
hardonia.store — product catalog and artifact storefront for the Hardonia AI lab. This repository manages product manifests, backup artifacts, and copy references for the storefront system.

## Project Overview
- **Name**: hardonia.store
- **Primary branch**: mainsa
- **Purpose**: Product catalog, backup artifacts, and copy references for the AI lab storefront

## Connective Tissue
This repo is part of the larger Hardonia/AIAS sovereign AI-lab stack. It connects with:
- **Settler** — monorepo managing core infrastructure, agents, and API services
- **Reach** — protocol and protocol-adapter layer
- **WarrantyWeasel** — warranty and agent guidance framework
- **MissionLedger** — mission and documentation tracking
- **Nautilus** — gateway and CLI command center

## Standards & Conventions
- **Node version**: 24.16.0 (via `.nvmrc`)
- **Package manager**: `pnpm` (via `packageManager` in `package.json`)
- **Code style**: Biome formatting, ESLint linting
- **CI/CD**: `verify:fast` profile gate required for all PRs; `verify-release` opt-in for release profiles
- **Security**: gitleaks v3 scanning enabled via `.github/workflows/security.yml`
- **Dependencies**: Dependabot auto-merge enabled for Tier 1 PRs; Tier 2 conflicting PRs require manual review

## Repository Structure
- `.github/workflows/` — Caddy deployment, CI/CD pipelines
- `docs/` — Architecture decision records and operational guidance
- `src/` — Source code and product manifests
- `package.json` — Project metadata and scripts
- `.env.local` — Environment configuration (do not commit secrets)
- 151 untracked product/backup/copy artifacts preserved as-is per directive

## Development Workflow
1. Create a topic branch from `mainsa` (never work directly on `mainsa`)
2. Make changes following project conventions
3. Run `pnpm run verify:fast` locally — must pass
4. Commit with clear, descriptive messages
5. Push to `origin/mainsa` and open a Pull Request
6. Dependabot auto-merge applies to Tier 1 (dependency/doc PRs); Tier 2 requires manual review

## Adding New Product Artifacts
- Place new product manifests under `src/` or appropriate directories
- Ensure `.gitignore` preserves 151 existing untracked artifacts as-is
- Update `.nvmrc` if Node version changes
- Run `pnpm run verify:fast` to validate

## Rolling Back Changes
- Use `git stash` for uncommitted work
- Use `git reset --hard origin/mainsa` to restore clean state (after `git fetch origin`)
- Preserve untracked artifact directory structure under `.gitignore`
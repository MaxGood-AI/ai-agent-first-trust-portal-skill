# CLAUDE.md — Trust Portal Compliance Skill

## Overview

This is a Claude Code agent skill that wraps the AI Agent-First Trust Portal API. It provides a CLI interface for managing SOC 2 compliance data: controls, tests, policies, evidence, audit logs, portal settings, and automated evidence collectors (AWS, Git/CodeCommit, Platform, Policy, Vendor).

## File Structure

- **SKILL.md** — Skill definition with OpenClaw frontmatter. Claude Code reads this to understand the skill's capabilities and trigger phrases.
- **scripts/trust_portal_api.py** — Single-file Python CLI. Stdlib only (no third-party dependencies). All output is JSON.
- **references/api-reference.md** — API endpoint documentation for the trust portal.
- **CLAUDE.md / AGENTS.md** — Developer guidelines (this file). Must be kept identical.

## Adding New Commands

1. Add a `cmd_<name>(args)` handler function in `trust_portal_api.py`.
2. Add a subparser in `main()` with the command name and arguments.
3. Add the command to the `commands` dict in `main()`.
4. Update the Command Reference table in `SKILL.md`.
5. Update `references/api-reference.md` if wrapping a new API endpoint.

## Code Style

- **PEP 8**, 4-space indentation
- **Stdlib only** — no `pip install`, no `requirements.txt`
- **All output** must be valid JSON via `json.dump()`
- **Errors** exit with code 1 and output `{"error": true, "message": "..."}`
- **Write operations** use `--data-file` (read JSON from a file) to avoid shell quoting issues
- **Sensitive credentials** (API keys, access keys, bearer tokens, role ARNs with external IDs) MUST come from `--data-file` only — never accept them as CLI arguments, since argv leaks into shell history, process lists, decision-log transcripts, and any hook that captures command lines. See `configure-collector` for the canonical example.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TRUST_PORTAL_API_URL` | Yes | Trust portal base URL (e.g., `http://localhost:5100`) |
| `TRUST_PORTAL_API_KEY` | Yes | API key for the authenticated team member |

Auto-loaded from `.env` file in the current directory or parent directories.

## Testing

Tests use `unittest` (stdlib only). Run from the skill directory:

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Tests mock HTTP responses — no running trust portal instance required.

## Commit Style

- **Subject line**: short imperative verb phrase under ~72 chars
- **Body** (for non-trivial changes): `## Problem`, `## Solution`, `## Verified` sections
- **Co-authorship**: `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>`

**CRITICAL INSTRUCTION:** If there is a discrepancy between CLAUDE.md and AGENTS.md, it must be identified immediately and the user asked for repair instructions.

## Synchronization Rule

If both `AGENTS.md` and `CLAUDE.md` exist in this directory, they must be identical in content and updated together in the same commit. Do not allow them to drift.

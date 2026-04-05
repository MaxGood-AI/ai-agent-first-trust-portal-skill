---
name: trust-portal
description: Interact with the AI Agent-First Trust Portal via the compliance API. Use when the user wants to manage compliance controls, view or submit evidence, check compliance scores, review policies/systems/vendors/risks, query the audit log, upload decision logs, or manage portal settings. Supports listing and CRUD for controls, tests, policies, systems, vendors, evidence, risks, and pentest findings. Even if the user just says "check compliance", "what evidence is missing", "show the audit log", or mentions SOC 2 controls, tests, or evidence, use this skill.
license: MIT
compatibility: Requires python3 and environment variables TRUST_PORTAL_API_URL and TRUST_PORTAL_API_KEY
metadata:
  version: "1.0.0"
  openclaw:
    requires:
      env:
        - TRUST_PORTAL_API_URL
        - TRUST_PORTAL_API_KEY
      bins:
        - python3
    primaryEnv: TRUST_PORTAL_API_KEY
    homepage: https://github.com/MaxGood-AI/ai-agent-first-trust-portal
---

# Trust Portal

Manage SOC 2 compliance data through the AI Agent-First Trust Portal API.

## Environment Setup

The CLI script reads two environment variables: `TRUST_PORTAL_API_URL` and `TRUST_PORTAL_API_KEY`.

The script **automatically loads** these from a `.env` file if they are not already in the environment. It searches for `.env` in the current working directory and in the skill's parent directory. No shell export or command substitution is needed — just run the Python command directly.

**Get your API key:** Log in to the trust portal admin at `/admin/team` and create a team member (human or agent role). The API key is shown on creation.

## Quick Start

```bash
# Check connectivity
python3 scripts/trust_portal_api.py health

# View compliance status
python3 scripts/trust_portal_api.py compliance-score

# List controls
python3 scripts/trust_portal_api.py controls

# Find tests needing evidence
python3 scripts/trust_portal_api.py evidence-gaps

# Submit evidence
python3 scripts/trust_portal_api.py submit-evidence \
  --test-record-id abc123 --evidence-type link \
  --url "https://..." --description "Monthly scan results"

# Query audit log
python3 scripts/trust_portal_api.py audit-log --table controls --limit 10

# Upload decision log transcript
python3 scripts/trust_portal_api.py upload-decision-log --file /path/to/transcript.jsonl
```

## Core Workflows

### View Compliance Status
1. Run `compliance-score` to see overall and per-category scores.
2. Run `evidence-gaps` to find tests needing evidence.

### Manage Controls
1. `controls` — list all controls
2. `control --id X` — get details for a specific control
3. `create-control --name "..." --category security` — create a new control
4. `update-control --id X --data-file /tmp/update.json` — update fields
5. `delete-control --id X` — remove a control

### Submit Evidence
1. `evidence-gaps` — find what needs evidence
2. `submit-evidence --test-record-id X --evidence-type link --url "..." --description "..."`

### Decision Logs
1. `upload-decision-log --file /path/to/transcript.jsonl` — upload a session transcript
2. `decision-log-sessions` — list all uploaded sessions
3. `decision-log-session --id X` — view session entries

### Audit Log
1. `audit-log` — recent changes across all tables
2. `audit-log --table controls` — changes to controls only
3. `audit-log --action DELETE --limit 5` — recent deletions

### Portal Settings
1. `settings` — view current portal settings
2. `update-settings --data-file /tmp/settings.json` — update settings (admin only)

## Description Updates (IMPORTANT)

**Always use `--data-file` instead of inline JSON for create or update operations.** This avoids multi-line quoting issues in shell commands.

Workflow:
1. Write the data to a temp file (e.g., `/tmp/update.json`) using the Write tool.
2. Run the command with `--data-file /tmp/update.json`.

## Command Reference

| Command | Description |
|---------|-------------|
| `health` | Health check |
| `compliance-score` | Overall and per-category compliance scores |
| `evidence-gaps` | Tests with missing or outdated evidence |
| `settings` | Get portal settings |
| `update-settings` | Update portal settings (admin) |
| `controls` | List all controls |
| `control` | Get a single control |
| `create-control` | Create a control |
| `update-control` | Update a control |
| `delete-control` | Delete a control |
| `tests` | List all test records |
| `test` | Get a single test record |
| `create-test` | Create a test record |
| `update-test` | Update a test record |
| `policies` | List all policies |
| `policy` | Get a single policy |
| `systems` | List all systems |
| `system` | Get a single system |
| `vendors` | List all vendors |
| `vendor` | Get a single vendor |
| `risks` | List risk register entries |
| `evidence` | List all evidence |
| `submit-evidence` | Submit evidence for a test |
| `pentest-findings` | List pentest findings |
| `audit-log` | Query the audit log |
| `upload-decision-log` | Upload a JSONL decision log |
| `decision-log-sessions` | List decision log sessions |
| `decision-log-session` | Get a decision log session |

## API Reference

See [references/api-reference.md](./references/api-reference.md) for complete endpoint documentation.

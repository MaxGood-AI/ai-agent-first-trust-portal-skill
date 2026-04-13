---
name: trust-portal
description: Let AI agents drive SOC 2 Type 2 compliance end-to-end. Use when the user wants to get SOC 2 compliant, start a compliance program, manage controls, view or submit evidence, check compliance scores, generate policies, review systems/vendors/risks, query the audit log, upload decision logs, manage portal settings, or configure and run automated evidence collectors (AWS, Git/CodeCommit, Platform, Policy, Vendor). TRIGGER on any of these phrases — "get me SOC 2 compliant", "set up compliance", "start our compliance program", "check compliance", "what evidence is missing", "show the audit log", "set up evidence collection", "configure collectors", "run the collectors", or any mention of SOC 2 controls, tests, evidence, policies, or evidence collectors. For end-to-end SOC 2 journey guidance, read references/soc2-playbook.md which contains the complete 8-phase workflow with exact API calls, decision trees, and conversational scripts.
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

## SOC 2 Journey — End-to-End Orchestration

For the complete 8-phase SOC 2 journey (bootstrap → discovery → policies → controls → evidence → gap analysis → audit prep → ongoing), read the **[SOC 2 Agent Playbook](./references/soc2-playbook.md)**. It contains exact API call sequences, decision trees, and conversational scripts for driving the entire compliance program.

**Quick start:**
1. `compliance-journey` — Check current phase and what to do next
2. Read `references/soc2-playbook.md` for the complete workflow
3. Use `references/discovery-questions.json` for structured discovery interviews

**Resuming after interruption:** Always call `compliance-journey` first. It returns the current phase, what's completed, and the next 1-3 actions to take.

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

### Record Test Execution
1. `record-execution --test-id X --outcome success --finding "All checks passed"`
2. `record-execution --test-id X --outcome failure --finding "MFA not enforced" --comment "2 users affected"`
3. `record-execution --test-id X --outcome success --finding "Verified" --evidence-file /tmp/evidence.json` — include evidence
4. `execution-history --test-id X` — view past executions for a test
5. `execution-history --test-id X --limit 5` — limit results

The `--evidence-file` flag accepts a JSON file containing an array of evidence items:
```json
[
  {"evidence_type": "screenshot", "description": "Password manager showing AWS creds", "url": "https://..."},
  {"evidence_type": "link", "description": "Audit log export", "url": "https://..."},
  {"evidence_type": "file", "description": "Exported audit CSV", "file": "/path/to/audit.csv"}
]
```
Items with a `file` field are read from disk and uploaded directly to the database. Items with a `url` field are stored as link references. Evidence items are linked to the test record and its evidence status is set to "submitted".

### Batch Operations
1. `batch-record-execution --data-file /tmp/executions.json` — record results for multiple tests
2. `batch-submit-evidence --data-file /tmp/evidence.json` — submit evidence to multiple tests

Batch execution file format:
```json
{"executions": [
  {"test_id": "abc", "outcome": "success", "finding": "All good"},
  {"test_id": "def", "outcome": "failure", "finding": "MFA not enforced", "evidence": [
    {"evidence_type": "screenshot", "description": "MFA settings page", "file": "/path/to/screenshot.png"}
  ]}
]}
```

Batch evidence file format:
```json
{"evidence": [
  {"test_record_id": "abc", "evidence_type": "link", "description": "Scan report", "url": "https://..."},
  {"test_record_id": "def", "evidence_type": "file", "description": "Export", "file": "/path/to/export.csv"}
]}
```

Both return per-item results with succeeded/failed counts. Items with `file` paths are auto-encoded.

### Submit Evidence
1. `evidence-gaps` — find what needs evidence
2. `submit-evidence --test-record-id X --evidence-type link --url "..." --description "..."` — link evidence
3. `submit-evidence --test-record-id X --evidence-type file --file /path/to/export.pdf --description "..."` — upload a file directly

### Decision Logs
1. `upload-decision-log --file /path/to/transcript.jsonl` — upload a session transcript
2. `decision-log-sessions` — list all uploaded sessions
3. `decision-log-session --id X` — view session entries

### Audit Log
1. `verify-audit-log` — verify the hash chain integrity (tamper detection)
2. `audit-log` — recent changes across all tables
2. `audit-log --table controls` — changes to controls only
3. `audit-log --action DELETE --limit 5` — recent deletions

### Portal Settings
1. `settings` — view current portal settings
2. `update-settings --data-file /tmp/settings.json` — update settings (admin only)

### Evidence Collectors

Evidence collectors are the core of SOC 2 Phase 5 (Evidence Collection). They
gather compliance evidence from infrastructure on a schedule. The portal
ships five: `aws`, `git`, `platform`, `policy`, `vendor`.

```bash
# Discover which AWS account/region the portal is running in
python3 scripts/trust_portal_api.py collector-environment

# Inventory / status
python3 scripts/trust_portal_api.py collectors
python3 scripts/trust_portal_api.py collector --name aws

# Configure a collector — credentials MUST come from a JSON file, never CLI args
cat > /tmp/aws-config.json <<'EOF'
{
  "credential_mode": "task_role_assume",
  "credentials": {
    "role_arn": "arn:aws:iam::123456789012:role/trust-portal-collector-role"
  },
  "config": {"region": "ca-central-1"},
  "schedule_cron": "0 6 * * 1",
  "enabled": true
}
EOF
python3 scripts/trust_portal_api.py configure-collector --name aws --data-file /tmp/aws-config.json

# Verify the credentials work (STS identity + optional permission probe)
python3 scripts/trust_portal_api.py test-collector-connection --name aws
python3 scripts/trust_portal_api.py probe-collector --name aws

# Fetch the IAM policy JSON the collector needs (copy this into Terraform)
python3 scripts/trust_portal_api.py collector-required-policy --name aws

# Enable / disable
python3 scripts/trust_portal_api.py enable-collector --name aws --enabled true

# Trigger a manual run
python3 scripts/trust_portal_api.py run-collector --name aws

# Run history and per-check detail
python3 scripts/trust_portal_api.py collector-runs --name aws
python3 scripts/trust_portal_api.py collector-run --run-id <uuid>
```

**Credential safety.** The `configure-collector` command requires
`--data-file` because credentials (AWS access keys, bearer tokens, collector
role ARNs with external IDs) must never appear as CLI arguments — they would
leak into shell history, process listings, decision-log transcripts, and any
hook that captures command lines. Write the JSON body to a temp file and
pass the file path; the contents of the file never touch the command line.

**Simpler collectors.** `policy` and `vendor` don't need credentials at all
(they read the portal's own database). `platform` only needs credentials if
your services require bearer or basic auth. For these, `credential_mode`
can be set to `"none"`.

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
| `compliance-journey` | Full SOC 2 journey state — current phase, completion checks, next actions |
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
| `record-execution` | Record an externally-performed test execution result |
| `execution-history` | Get execution history for a test record |
| `batch-record-execution` | Record execution results for multiple tests at once |
| `batch-submit-evidence` | Submit evidence for multiple tests at once |
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
| `verify-audit-log` | Verify audit log hash chain integrity |
| `audit-log` | Query the audit log |
| `upload-decision-log` | Upload a JSONL decision log |
| `decision-log-sessions` | List decision log sessions |
| `decision-log-session` | Get a decision log session |
| `collector-environment` | Detect running environment (AWS account/region/identity) |
| `collectors` | List all configured evidence collectors |
| `collector` | Get one collector config (credentials never returned) |
| `configure-collector` | Save collector config + credentials (requires `--data-file`) |
| `test-collector-connection` | Lightweight connection test for a collector |
| `probe-collector` | Run the full permission probe for a collector |
| `enable-collector` | Enable or disable a collector |
| `run-collector` | Trigger a manual collector run synchronously |
| `collector-runs` | Recent run history for a collector |
| `collector-run` | Run detail with per-check results |
| `collector-required-policy` | Return the IAM policy JSON a collector needs |

## API Reference

See [references/api-reference.md](./references/api-reference.md) for complete endpoint documentation.

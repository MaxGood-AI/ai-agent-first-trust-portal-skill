# Trust Portal API Reference

Base URL: configured via `TRUST_PORTAL_API_URL` environment variable.

Authentication: `X-API-Key` header with team member API key.

## System

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/health` | No | Health check (returns status, service name, database state) |
| GET | `/api/openapi.json` | No | Raw OpenAPI 3.0 specification |

## Compliance

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/compliance-score` | Yes | Overall score + per-category scores |
| GET | `/api/gaps` | Yes | Tests with missing/outdated/due_soon evidence |

## CRUD Endpoints

All CRUD endpoints require API key authentication. Each entity type supports:
- `GET /api/{entity}` — List all
- `GET /api/{entity}/{id}` — Get by ID
- `POST /api/{entity}` — Create (JSON body)
- `PUT /api/{entity}/{id}` — Update (JSON body)
- `DELETE /api/{entity}/{id}` — Delete

| Entity | Path | Required Fields (POST) |
|--------|------|----------------------|
| Controls | `/api/controls` | `name`, `category` |
| Tests | `/api/tests` | `name`, `control_id` |
| Policies | `/api/policies` | `title`, `category` |
| Systems | `/api/systems` | `name` |
| Vendors | `/api/vendors` | `name` |
| Evidence | `/api/evidence` | `test_record_id`, `evidence_type` |
| Risks | `/api/risks` | `name` |
| Pentest Findings | `/api/pentest-findings` | `layer` |

## Audit Log

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/audit-log` | Yes | Query change history |

Query parameters:
- `table` — Filter by table name (e.g., `controls`, `policies`)
- `record_id` — Filter by record UUID
- `action` — Filter by action (`INSERT`, `UPDATE`, `DELETE`)
- `changed_by` — Filter by team member UUID
- `since` — ISO 8601 timestamp, only entries after this time
- `limit` — Max entries (default 50, max 200)

## Decision Log

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/decision-log/upload` | Yes | Upload JSONL transcript (Content-Type: application/jsonl) |
| POST | `/api/decision-log/ingest` | Yes | Ingest pending transcripts from decision-logs/ directory |
| GET | `/api/decision-log/sessions` | Yes | List all sessions with metadata |
| GET | `/api/decision-log/session/{id}` | Yes | Get session entries |

Upload query parameters:
- `session_id` — Optional (generated if omitted)
- `exit_reason` — Optional session exit reason

## Settings

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/settings` | Yes | Get portal settings |
| PUT | `/api/settings` | Admin | Update portal settings (JSON body) |

Settings fields: `company_legal_name`, `company_brand_name`, `contact_email`, `physical_address`, `website_url`, `soc2_current_stage`, `soc2_stage_dates`, `legal_content_md`, `legal_external_url`, `ai_transparency_md`.

## Evidence Collectors

All collector endpoints require admin authentication. Credentials are
never returned from any endpoint — the response indicates only whether
credentials are stored (`has_stored_credentials`).

Five collectors are registered in the portal: `aws`, `git`, `platform`,
`policy`, `vendor`. Each has its own required IAM permissions (AWS-backed
collectors) or config schema (e.g., `platform.services`).

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/api/collectors/environment` | Admin | Detect current AWS account, region, identity, and whether the portal is running on ECS |
| GET | `/api/collectors` | Admin | List all collector configs (no credentials) |
| GET | `/api/collectors/{name}` | Admin | Get a single collector config (no credentials) |
| POST | `/api/collectors/{name}/configure` | Admin | Create or update a collector config. Body: `{credential_mode, credentials?, config?, schedule_cron?, enabled?}` |
| POST | `/api/collectors/{name}/test-connection` | Admin | Resolve credentials and run a minimal identity check (STS GetCallerIdentity for AWS-backed collectors) |
| POST | `/api/collectors/{name}/probe` | Admin | Run the full permission probe for the collector. Result cached on the config. Optional body: `{required_actions: [...]}` to override the collector's default list |
| POST | `/api/collectors/{name}/enable` | Admin | Toggle enabled/disabled. Body: `{enabled: bool}` |
| POST | `/api/collectors/{name}/run` | Admin | Trigger a manual run synchronously. Creates a `CollectorRun` row and returns its final state |
| GET | `/api/collectors/{name}/runs` | Admin | Recent run history (up to 100 runs) |
| GET | `/api/collectors/runs/{run_id}` | Admin | Single run detail with per-check results |
| GET | `/api/collectors/{name}/required-policy` | Admin | Return the IAM policy JSON the collector needs, either from `iam/trust-portal-collector-policy.json` in the portal repo or synthesized from the collector's declared `required_permissions` |

### `configure-collector` body schema

```json
{
  "credential_mode": "task_role | task_role_assume | access_keys | none",
  "credentials": {
    "role_arn": "arn:aws:iam::...:role/...",
    "external_id": "...",
    "session_name": "...",
    "access_key_id": "...",
    "secret_access_key": "...",
    "bearer_token": "...",
    "basic_user": "...",
    "basic_password": "..."
  },
  "config": {
    "region": "ca-central-1",
    "services": [
      {"name": "api", "url": "https://api.example.com", "health_path": "/health", "auth": "none"}
    ],
    "repositories": ["repo-one", "repo-two"],
    "lookback_days": 30,
    "review_warning_days": 30,
    "probe_urls": false,
    "http_timeout_seconds": 10
  },
  "schedule_cron": "0 6 * * 1",
  "enabled": true
}
```

Only the fields relevant to the chosen collector are read; unknown fields
are ignored. `credentials` must be omitted (or empty) for `credential_mode`
values of `none` or `task_role`.

### Permission probe result shape

```json
{
  "ok": true,
  "probe": {
    "session_identity": "arn:aws:sts::123456789012:assumed-role/...",
    "account_id": "123456789012",
    "region": "ca-central-1",
    "checked_at": "2026-04-13T10:15:00Z",
    "all_passed": false,
    "results": [
      {"action": "iam:ListUsers", "status": "pass", "message": null},
      {"action": "s3:GetBucketEncryption", "status": "fail", "message": "AccessDenied"}
    ],
    "missing_actions": ["s3:GetBucketEncryption"]
  }
}
```

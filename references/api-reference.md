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

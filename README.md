# AI Agent-First Trust Portal — Claude Code Skill

A Claude Code agent skill for managing SOC 2 compliance data through the [AI Agent-First Trust Portal](https://github.com/MaxGood-AI/ai-agent-first-trust-portal) API.

## Features

- **Compliance status**: Overall and per-category scores, evidence gaps
- **Full CRUD**: Controls, tests, policies, systems, vendors, evidence, risks
- **Audit log**: Query change history with filters
- **Decision logs**: Upload session transcripts for compliance audit trail
- **Portal settings**: View and update portal configuration
- **Pentest findings**: View security assessment results
- **Evidence collectors**: Configure, test, run, and inspect the portal's five evidence collectors (AWS, Git/CodeCommit, Platform, Policy, Vendor)

## Installation

1. Clone this repo into your development directory:
   ```bash
   git clone https://github.com/MaxGood-AI/ai-agent-first-trust-portal-skill.git
   ```

2. Create a symlink in your Claude Code skills directory:
   ```bash
   ln -sf /path/to/ai-agent-first-trust-portal-skill ~/.claude/skills/trust-portal
   ```

3. Add your trust portal credentials to `.env` in your workspace:
   ```
   TRUST_PORTAL_API_URL=http://localhost:5100
   TRUST_PORTAL_API_KEY=your-api-key-here
   ```

## Usage

```bash
# Check compliance
python3 scripts/trust_portal_api.py compliance-score

# Find evidence gaps
python3 scripts/trust_portal_api.py evidence-gaps

# List controls
python3 scripts/trust_portal_api.py controls

# Query audit log
python3 scripts/trust_portal_api.py audit-log --table controls --limit 5

# Configure and run an evidence collector (credentials via data file only)
cat > /tmp/policy-config.json <<'EOF'
{"credential_mode": "none", "schedule_cron": "0 6 * * 1", "enabled": true}
EOF
python3 scripts/trust_portal_api.py configure-collector --name policy --data-file /tmp/policy-config.json
python3 scripts/trust_portal_api.py run-collector --name policy
```

See [SKILL.md](SKILL.md) for the complete command reference.

## Requirements

- Python 3.8+ (stdlib only — no pip install needed)
- A running AI Agent-First Trust Portal instance
- API key from the trust portal admin (`/admin/team`)

## License

MIT — see [LICENSE.txt](LICENSE.txt)

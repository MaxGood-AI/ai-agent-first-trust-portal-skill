# SOC 2 Agent Playbook

## Purpose

This playbook is the operational guide for AI agents driving a complete SOC 2 compliance program using the AI Agent-First Trust Portal. It covers every phase from initial deployment through audit readiness and ongoing compliance maintenance. The target audience is an AI agent (Claude Code or equivalent) that has been asked by a user to "get me SOC 2 compliant" or similar. The agent should follow this playbook sequentially, skipping phases that are already complete.

The core philosophy is **"Document what you ACTUALLY do, not aspirations."** SOC 2 auditors verify that an organization follows its own stated policies. A simple, honest policy that matches reality will pass an audit. An impressive-sounding policy that does not match reality will fail. Every policy, control, and test generated through this playbook must reflect the organization's real practices. If a practice is not strong enough, help the user improve the practice first, then document it.

## How to Use This Playbook

- Call `python3 scripts/trust_portal_api.py compliance-journey` first to determine the current phase and what has already been completed.
- Skip completed phases entirely. Resume from the earliest incomplete phase.
- Steps marked **[ASK USER]** require human input before proceeding. Do not guess or assume answers.
- Steps marked **[AUTOMATED]** can execute without user confirmation. Proceed directly.
- Steps marked **[ASK USER for each]** require user input once per item in a set.
- All CLI commands use the trust-portal skill script at `scripts/trust_portal_api.py`. The script auto-loads `TRUST_PORTAL_API_URL` and `TRUST_PORTAL_API_KEY` from the nearest `.env` file.
- When writing JSON data for API calls, always write to a temp file first (e.g., `/tmp/control.json`) and pass it via `--data-file`. Never use inline JSON in shell commands.
- The five SOC 2 Trust Service Categories (TSC) are: `security`, `availability`, `confidentiality`, `privacy`, `processing_integrity`. All five must have policies, controls, and tests.

## Prerequisites

- Claude Code or equivalent AI agent with filesystem and shell access
- Python 3 installed on the host
- Docker and Docker Compose installed
- Admin access to the organization's cloud provider (AWS, GCP, Azure)
- Trust portal deployed and accessible (or readiness to deploy it in Phase 1)
- A `.env` file in the working directory with `TRUST_PORTAL_API_URL` and `TRUST_PORTAL_API_KEY`

---

## Phase 1: Bootstrap & Deploy

**Goal:** Get the trust portal running, configured, and connected to the development environment.

### 1.1 Clone Repositories [AUTOMATED]

Clone the trust portal and the skill repo if they are not already present:

```bash
git clone https://github.com/MaxGood-AI/ai-agent-first-trust-portal.git
git clone https://github.com/MaxGood-AI/ai-agent-first-trust-portal-skill.git
```

Verify both directories exist and contain expected files (`docker-compose.yml`, `scripts/trust_portal_api.py`).

### 1.2 Environment Configuration [ASK USER]

Ask the user the following questions:

1. "What is your company's legal name?" (e.g., "Acme Corp Inc.")
2. "What is your company's brand name?" (e.g., "Acme")
3. "What is the compliance contact email?" (e.g., "security@acme.com")
4. "What is your company's physical address?"
5. "What is your company's website URL?"
6. "What port should the trust portal run on?" (default: 5100)

Generate a `.env` file for the trust portal with:

```
PORTAL_COMPANY_NAME=<legal name>
PORTAL_BRAND_NAME=<brand name>
PORTAL_CONTACT_EMAIL=<email>
POSTGRES_PASSWORD=<generate a secure random string>
SECRET_KEY=<generate a secure random string>
```

### 1.3 Deploy Trust Portal [AUTOMATED]

```bash
cd ai-agent-first-trust-portal
docker compose -f docker-compose.dev.yml up --build -d
```

Wait for the container to be healthy, then verify:

```bash
python3 scripts/trust_portal_api.py health
```

Expected output: `{"status": "healthy", ...}`. If the health check fails, inspect container logs with `docker logs trust-portal-dev` and resolve before proceeding.

### 1.4 Create Admin API Key [ASK USER]

Tell the user:

> "Open the trust portal admin interface at `http://localhost:5100/admin/team` in your browser. Create a team member with your name, email, and the role 'human'. Check the 'Compliance Admin' checkbox. Copy the API key that is displayed on creation."

Once the user provides the API key, store it in the working directory's `.env` file:

```
TRUST_PORTAL_API_URL=http://localhost:5100
TRUST_PORTAL_API_KEY=<the key the user provided>
```

Verify the key works:

```bash
python3 scripts/trust_portal_api.py compliance-score
```

If this returns a JSON response (even with all zeros), the key is valid.

### 1.5 Initialize Portal Settings [AUTOMATED]

Write the settings JSON to a temp file and apply:

```bash
# Write settings to /tmp/settings.json using the Write tool with:
# {
#   "company_legal_name": "<from 1.2>",
#   "company_brand_name": "<from 1.2>",
#   "contact_email": "<from 1.2>",
#   "physical_address": "<from 1.2>",
#   "website_url": "<from 1.2>",
#   "soc2_current_stage": "not_started"
# }
python3 scripts/trust_portal_api.py update-settings --data-file /tmp/settings.json
```

Verify:

```bash
python3 scripts/trust_portal_api.py settings
```

Confirm the company name and other fields are populated.

### 1.6 Install Governance Templates [ASK USER]

Ask the user: "Where is your main development directory?" (e.g., `~/Development`)

If CLAUDE.md and AGENTS.md do not already exist in that directory:

1. Copy the governance templates from the trust portal's `docs/` directory or generate them based on the standard format.
2. Walk the user through customizing the placeholder values (company name, repos, architecture).
3. Commit the governance files to the user's governance repository.

If governance files already exist, skip this step.

### 1.7 Set Up SessionEnd Hook [AUTOMATED]

Check if `~/.claude/settings.json` exists and contains a `SessionEnd` hook pointing to the trust portal's `scripts/session-end-hook.sh`.

If not configured, guide the user through adding the hook:

```json
{
  "hooks": {
    "SessionEnd": [
      {
        "command": "/path/to/ai-agent-first-trust-portal/scripts/session-end-hook.sh",
        "timeout": 30000
      }
    ]
  }
}
```

Test by checking that the `decision-logs/` directory is configured to receive transcripts:

```bash
ls -la /path/to/ai-agent-first-trust-portal/decision-logs/
```

### 1.8 Connect Planning Tool [ASK USER]

Ask: "What project management tool do you use for tracking work? (e.g., KanbanZone, Jira, GitHub Issues, Linear, Trello, or none)"

Decision tree:

- **KanbanZone**: Ask for `KANBANZONE_API_KEY` and `KANBANZONE_BOARD_ID`. Add to `.env`. The kanban-zone skill will provide automated change management evidence (card plans, review approvals).
- **GitHub Issues / GitHub Projects**: Evidence will come from the GitHub collector (configured in Phase 2). No additional setup needed.
- **Jira / Linear / Trello / Other**: Note in the portal settings that manual evidence export will be needed for change management controls. Inform the user: "For SOC 2, you'll need to periodically export your task board activity as evidence. I'll remind you during evidence collection."
- **None**: Recommend adopting a lightweight tool. SOC 2 requires evidence of change management. At minimum, GitHub Issues or a kanban board.

### 1.9 Connect Security Scanning [ASK USER]

Ask: "Do you have automated security scanning set up? (e.g., MGSecurityAssessment, Snyk, SonarQube, Dependabot, or none)"

Decision tree:

- **MGSecurityAssessment**: Verify the pre-push hook is active. Security scan results will be ingested as pentest findings evidence.
- **Snyk / SonarQube / Dependabot**: Note the tool. During evidence collection, the user will need to export scan results. Configure a reminder.
- **None**: Recommend setting up at least dependency vulnerability scanning. SOC 2 requires evidence of vulnerability management. For Python projects, `pip-audit` or `safety` inside Docker is minimal. For Node.js, `npm audit`.

### 1.10 Verify Bootstrap [AUTOMATED]

```bash
python3 scripts/trust_portal_api.py compliance-journey
```

Check the response: `phases.1_bootstrap.status` should be `"completed"`. If not, review the `checks` object to identify what is missing and address it before proceeding.

---

## Phase 2: Discovery

**Goal:** Build a complete picture of the organization's technology, vendors, team, and current security practices. This information drives policy generation, control creation, and evidence collection strategy.

### 2.1 Pre-Discovery State Check [AUTOMATED]

Check if systems or vendors already exist:

```bash
python3 scripts/trust_portal_api.py systems
python3 scripts/trust_portal_api.py vendors
```

If data exists, summarize it for the user: "I see you already have X systems and Y vendors registered. I'll ask about anything that's missing."

### 2.2 Organization Profile [ASK USER]

Ask these questions in a natural conversation (not a rigid form):

1. "How many employees does your company have? Include full-time, part-time, and contractors."
2. "What industry are you in, and what do you build or provide?"
3. "Are you targeting SOC 2 Type 1 (point-in-time) or Type 2 (observation period)? Type 1 is faster but Type 2 is what most enterprise customers require."
4. "What's your target timeline for being audit-ready?"
5. "Do you have any existing compliance frameworks (ISO 27001, HIPAA, PCI-DSS, etc.)?"
6. "Which of the five SOC 2 Trust Service Categories are in scope? Most companies start with Security only, or Security + Availability. The categories are: Security, Availability, Confidentiality, Privacy, Processing Integrity."

Record answers for use in policy generation. Update portal settings if needed (e.g., `soc2_current_stage`).

### 2.3 Technology Infrastructure [ASK USER]

Ask about each layer of the technology stack:

1. "What cloud provider(s) do you use? (AWS, GCP, Azure, on-premises, other)"
2. "What are your production services? (e.g., ECS, EC2, Lambda, Kubernetes, Heroku, Vercel)"
3. "What databases do you run? (e.g., PostgreSQL on RDS, MongoDB Atlas, DynamoDB)"
4. "What is your network architecture? (VPC, subnets, load balancers, CDN)"
5. "Do you use containers? If so, where are images stored and scanned?"
6. "What monitoring and logging tools do you use? (CloudWatch, Datadog, Sentry, etc.)"

For each system identified, create a System record:

```bash
# Write to /tmp/system.json:
# {"name": "AWS RDS PostgreSQL", "description": "Primary production database", "type": "database"}
python3 scripts/trust_portal_api.py create-system --data-file /tmp/system.json
```

### 2.4 Vendor Inventory [ASK USER]

Ask: "What third-party SaaS tools and services does your company use? Think about categories: email, communication, code hosting, CI/CD, monitoring, payment processing, analytics, HR, identity."

Prompt for specific categories if the user gives a short list:

- Code hosting (GitHub, GitLab, Bitbucket, CodeCommit)
- CI/CD (CodeBuild, GitHub Actions, CircleCI, Jenkins)
- Communication (Slack, Teams, Discord)
- Email (Google Workspace, Microsoft 365)
- Monitoring (Datadog, CloudWatch, Sentry, PagerDuty)
- Payment processing (Stripe, Braintree)
- Identity/Auth (Auth0, Cognito, Okta)
- HR/People (Gusto, Rippling, BambooHR)
- Any sub-processors that handle customer data

For each vendor, create a Vendor record:

```bash
# Write to /tmp/vendor.json:
# {"name": "GitHub", "description": "Source code hosting and CI/CD", "risk_level": "high"}
python3 scripts/trust_portal_api.py create-vendor --data-file /tmp/vendor.json
```

Risk level guidance: `high` if vendor handles customer data or has production access; `medium` if vendor handles internal data; `low` if vendor has no data access.

### 2.5 Team & Roles [ASK USER]

Ask: "Who are the key people responsible for compliance-relevant activities?"

Specifically ask about:

- **Compliance owner**: Who is accountable for the SOC 2 program?
- **Infrastructure/DevOps**: Who manages cloud resources, deployments, and monitoring?
- **Engineering lead**: Who approves code changes and architecture decisions?
- **HR contact**: Who handles onboarding, offboarding, and background checks?
- **Vendor management**: Who evaluates and approves new vendors?
- **Incident response**: Who gets called when something breaks at 2 AM?

Create team members in the portal for key individuals who will interact with the system.

### 2.6 Security Practices [ASK USER]

Ask about current security practices. Be explicit that honest answers are better than aspirational ones:

1. "How do employees authenticate? Password-only, SSO, MFA? Is MFA enforced or optional?"
2. "How do you manage access to production systems? Who has access, and how is it granted/revoked?"
3. "Do you do access reviews? How often, and who does them?"
4. "Is data encrypted at rest? In transit? Which systems?"
5. "Do you have security monitoring or alerting? What triggers alerts?"
6. "Do you have an incident response process? What happens when a security incident is detected?"
7. "Do you run vulnerability scans or penetration tests? How often?"
8. "Do you have a security awareness training program for employees?"

Record all answers. These directly feed into the Information Security Policy and Access Control Policy in Phase 3.

### 2.7 Change Management [ASK USER]

Ask about the software development lifecycle:

1. "Where is your source code hosted?" (GitHub, GitLab, CodeCommit, etc.)
2. "Do you use pull requests / merge requests for code changes?"
3. "Is code review required before merging? By how many reviewers?"
4. "Do you have CI/CD pipelines? What do they run?" (tests, linting, security scans)
5. "How do you deploy to production?" (automated, manual, approval gates)
6. "Do you have separate development, staging, and production environments?"
7. "How do you track what changes are being made and why?" (tickets, cards, issues)

If the user uses GitHub, configure the GitHub evidence collector:

```bash
# Add to the trust portal .env:
# GITHUB_TOKEN=<personal access token with repo scope>
# GITHUB_ORG=<organization name>
# GITHUB_REPOS=<comma-separated repo names>
```

### 2.8 Availability & Business Continuity [ASK USER]

Ask:

1. "Do you have an uptime SLA or target? What is it?" (e.g., 99.9%)
2. "How are backups configured? What's backed up, how often, and where are backups stored?"
3. "Have you tested restoring from a backup? When was the last test?"
4. "Do you have a disaster recovery plan? What does it cover?"
5. "Do you use high availability or auto-scaling? For which services?"
6. "What is your Recovery Time Objective (RTO) and Recovery Point Objective (RPO)?"

### 2.9 Data & Privacy Practices [ASK USER]

Ask:

1. "What types of data does your system store?" (PII, financial, health, credentials, user-generated content)
2. "Do you have a data classification scheme?" (public, internal, confidential, restricted)
3. "Do you handle personal data of EU residents?" (GDPR relevance)
4. "Do you have a privacy policy published on your website?"
5. "How do users request data deletion or export?"
6. "Do you have data retention policies? How long is data kept?"
7. "Do any third parties (sub-processors) process personal data on your behalf?"

### 2.10 Configure Evidence Collectors [AUTOMATED]

Based on discovery answers, configure the relevant automated collectors:

**AWS Collector** (if AWS is used):

```bash
# Verify AWS credentials are available:
# AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION
# Or IAM role if running on EC2/ECS
```

The AWS collector checks: IAM password policy, MFA on root, CloudTrail status, S3 bucket encryption, RDS encryption, VPC flow logs, security group rules, EBS encryption, and more.

**GitHub Collector** (if GitHub is used):

Verify the `GITHUB_TOKEN`, `GITHUB_ORG`, and `GITHUB_REPOS` environment variables are set. The GitHub collector checks: branch protection rules, required PR reviews, CI status checks, and repository security settings.

Test each configured collector:

```bash
docker exec trust-portal-dev python -m collectors.aws_collector
docker exec trust-portal-dev python -m collectors.github_collector
```

### 2.11 Discovery Summary [AUTOMATED]

Present a summary to the user:

```bash
python3 scripts/trust_portal_api.py systems
python3 scripts/trust_portal_api.py vendors
```

Format: "Based on our conversation, I've registered X systems and Y vendors. Here's the summary: [list]. Does this look complete, or is anything missing?"

Wait for user confirmation before proceeding to Phase 3.

---

## Phase 3: Policy Generation

**Goal:** Generate SOC 2 policies that accurately describe the organization's real practices. Each policy must be reviewed and approved by the user.

### 3.1 Strategy [AUTOMATED]

Explain to the user:

> "I'll now generate your SOC 2 policies. These are formal documents that describe what your organization actually does for security, availability, confidentiality, privacy, and processing integrity. Each policy is based on the answers you gave during discovery. I'll present each one for your review. Remember: these must describe what you ACTUALLY do. If something sounds too strong, tell me and I'll tone it down to match reality. A simple honest policy beats an impressive one you don't follow."

### 3.2 Generate Policies [ASK USER for each]

Generate policies in this order. For each policy:

1. Load the corresponding template from `policy-templates/` in the trust portal repo (if one exists).
2. Fill in all CUSTOMIZE sections using the discovery answers from Phase 2.
3. Present the completed policy to the user for review.
4. Iterate on feedback until the user approves.
5. On approval, create the policy via API and set status to `approved`.

**Policy order and TSC mapping:**

| # | Policy | TSC Category | Template File |
|---|--------|-------------|---------------|
| 1 | Information Security Policy | security | `information-security-policy.md` |
| 2 | Access Control Policy | security | `access-control-policy.md` |
| 3 | Change Management Policy | security | (generate from template pattern) |
| 4 | Incident Response Policy | security | (generate from template pattern) |
| 5 | Risk Management Policy | security | (generate from template pattern) |
| 6 | Data Classification & Handling Policy | confidentiality | `data-classification-and-handling-policy.md` |
| 7 | Business Continuity & DR Policy | availability | `business-continuity-and-disaster-recovery-policy.md` |
| 8 | Vendor Management Policy | security | (generate from template pattern) |
| 9 | Privacy Policy | privacy | (generate from template pattern) |
| 10 | Acceptable Use Policy | security | (generate from template pattern) |

For policies without existing templates, follow the same structure as the existing templates: clear CUSTOMIZE markers, SOC 2 reference codes, and a practical tone.

To create each approved policy:

```bash
# Write to /tmp/policy.json:
# {
#   "title": "Information Security Policy",
#   "category": "security",
#   "status": "approved",
#   "content": "<full markdown content>",
#   "version": "1.0"
# }
python3 scripts/trust_portal_api.py create-policy --data-file /tmp/policy.json
```

### 3.3 Policy-Control Mapping [AUTOMATED]

After all policies are created and approved, the mapping between policies and controls will be established in Phase 4 when controls are created. Each control will reference the relevant policy.

Verify all policies are approved:

```bash
python3 scripts/trust_portal_api.py policies
```

Check that every policy has `"status": "approved"`. If any are in draft, return to the user for approval.

---

## Phase 4: Controls & Tests

**Goal:** Create the SOC 2 control framework with testable controls and test records. Controls are the specific measures the organization takes. Tests verify those measures work.

### 4.1 Generate Controls [AUTOMATED]

For each TSC category, create controls based on the discovery answers and approved policy content. Controls should be specific and testable, not vague aspirations.

Good control: "Production database access is restricted to the operations team via IAM roles with MFA required."
Bad control: "Access to sensitive systems is appropriately restricted."

Create each control:

```bash
# Write to /tmp/control.json:
# {
#   "name": "Database access restricted to operations team",
#   "category": "security",
#   "description": "Production RDS instances are accessible only via IAM roles assigned to the operations team. MFA is required for all IAM users. Direct database credentials are stored in AWS Secrets Manager.",
#   "implementation_status": "implemented"
# }
python3 scripts/trust_portal_api.py create-control --data-file /tmp/control.json
```

See **Appendix B** for the standard controls to create per category. Adapt each control to match the organization's actual practices as discovered in Phase 2.

### 4.2 Generate Test Records [AUTOMATED]

For each control, create 1-3 test records with clear pass/fail criteria. Tests should be things that can be verified with evidence.

Good test: "Verify that the IAM password policy requires minimum 14 characters, MFA, and 90-day rotation."
Bad test: "Check that passwords are secure."

```bash
# Write to /tmp/test.json:
# {
#   "name": "IAM password policy meets requirements",
#   "control_id": "<control UUID from 4.1>",
#   "description": "Verify IAM password policy: min 14 chars, require uppercase, lowercase, numbers, symbols, MFA enforced, max age 90 days.",
#   "frequency": "quarterly",
#   "test_type": "automated"
# }
python3 scripts/trust_portal_api.py create-test --data-file /tmp/test.json
```

Set `test_type` to `automated` if the AWS or GitHub collector can verify it, or `manual` if it requires human action (screenshots, exports, etc.). Set `frequency` to `quarterly` for most tests, `monthly` for high-risk items, or `annually` for low-risk items like policy reviews.

### 4.3 Review Framework [ASK USER]

Present the complete framework to the user:

```bash
python3 scripts/trust_portal_api.py controls
python3 scripts/trust_portal_api.py tests
```

Summarize: "I've created X controls and Y tests across the five TSC categories. Here's the breakdown per category: [list]. Does this coverage look right? Are there any controls or tests you'd add or remove?"

Wait for user approval before proceeding to evidence collection.

---

## Phase 5: Evidence Collection

**Goal:** Collect evidence for every test record. Evidence proves that controls are operating as described. A mix of automated collection and manual evidence gathering.

### 5.1 Run Automated Collectors [AUTOMATED]

Run all configured collectors and record results:

```bash
# AWS collector (if configured) - checks 20+ AWS security settings
docker exec trust-portal-dev python -m collectors.aws_collector

# GitHub collector (if configured) - checks branch protection, PR reviews
docker exec trust-portal-dev python -m collectors.github_collector
```

After collectors run, batch-record the results:

```bash
# Write collector results to /tmp/executions.json in batch format:
# {"executions": [
#   {"test_id": "<id>", "outcome": "success", "finding": "IAM password policy meets all requirements"},
#   {"test_id": "<id>", "outcome": "failure", "finding": "Root account MFA is not enabled"}
# ]}
python3 scripts/trust_portal_api.py batch-record-execution --data-file /tmp/executions.json
```

### 5.2 Pull Planning Tool Evidence [AUTOMATED]

If KanbanZone is configured:

- Use the kanban-zone skill to pull cards that have approved plans and review notes.
- These serve as change management evidence (design review, approval before implementation).
- Submit as evidence for change management controls.

If another tool is used:

- Inform the user: "I need you to export your recent task board activity (last 90 days) showing work items with plans, reviews, and approvals. Export as PDF or screenshots."

### 5.3 Pull Security Scan Evidence [AUTOMATED]

If MGSecurityAssessment or another scanner is configured:

- Pull the latest scan results from `MGDataAndEvidence/` or the scanner's output directory.
- Map findings to pentest-findings in the portal.
- Submit as evidence for vulnerability management controls.

```bash
python3 scripts/trust_portal_api.py submit-evidence \
  --test-record-id <vuln-mgmt-test-id> \
  --evidence-type file \
  --file /path/to/scan-results.json \
  --description "Automated security scan results from MGSecurityAssessment"
```

### 5.4 Ingest Decision Logs [AUTOMATED]

Upload any staged session transcripts from the decision-logs directory:

```bash
# Upload each .jsonl file in decision-logs/
python3 scripts/trust_portal_api.py upload-decision-log --file /path/to/transcript.jsonl
```

Decision logs serve as evidence for:
- Change management (audit trail of what was decided and implemented)
- Operational controls (proof that procedures are followed)
- Access management (proof of review and approval processes)

### 5.5 Manual Evidence Collection [ASK USER]

Check which tests still need evidence:

```bash
python3 scripts/trust_portal_api.py evidence-gaps
```

For each test with `evidence_status: "missing"`, guide the user through collecting the evidence. Use plain language and specific instructions:

- **MFA enforcement**: "Open your AWS IAM console, go to Account Settings, and take a screenshot showing the password policy. Also screenshot the IAM users list showing the MFA column."
- **Backup configuration**: "Open your RDS console, click on your production database, go to the Maintenance & Backups tab, and screenshot the backup settings."
- **Access review**: "Export your IAM users list from the AWS console as a CSV. Review it and note any users who should be removed."
- **Encryption at rest**: "Open your RDS instance details and screenshot the Storage section showing encryption status."
- **Incident response test**: "When was the last time you had an incident or ran a tabletop exercise? Provide any notes or post-mortem documents."

For each piece of evidence collected:

```bash
python3 scripts/trust_portal_api.py submit-evidence \
  --test-record-id <test-id> \
  --evidence-type screenshot \
  --file /path/to/screenshot.png \
  --description "AWS IAM password policy settings showing 14-char minimum and MFA required"
```

Evidence types: `screenshot`, `file`, `link`, `document`, `log`.

### 5.6 Record Test Results [AUTOMATED]

For each test that now has evidence, evaluate whether the evidence demonstrates pass or fail:

```bash
python3 scripts/trust_portal_api.py record-execution \
  --test-id <test-id> \
  --outcome success \
  --finding "IAM password policy verified: 14-char minimum, MFA enforced, 90-day rotation"
```

Or for failures:

```bash
python3 scripts/trust_portal_api.py record-execution \
  --test-id <test-id> \
  --outcome failure \
  --finding "Root account MFA is not enabled. 2 IAM users lack MFA." \
  --comment "Remediation required before audit"
```

---

## Phase 6: Gap Analysis & Remediation

**Goal:** Identify all gaps in compliance coverage, fix them, and reach a compliance score of 80% or higher with zero evidence gaps.

### 6.1 Run Analysis [AUTOMATED]

```bash
python3 scripts/trust_portal_api.py compliance-score
python3 scripts/trust_portal_api.py evidence-gaps
```

Present results to the user:

- Overall compliance score (target: >= 80%)
- Per-category scores
- Number of tests with missing evidence
- Number of failed tests
- List of specific gaps

### 6.2 Remediation [ASK USER per gap]

For each gap or failed test, explain the issue and provide specific remediation steps:

**Example — MFA not enforced:**
> "Your IAM password policy does not require MFA. To fix this:
> 1. Go to AWS IAM > Account Settings > Password Policy
> 2. Check 'Require MFA for all IAM users'
> 3. For each existing user without MFA, enable a virtual MFA device
> 4. Once done, I'll re-collect the evidence and update the test."

**Example — No branch protection:**
> "Your main branch on GitHub does not have branch protection rules. To fix this:
> 1. Go to your repo > Settings > Branches > Branch protection rules
> 2. Add a rule for 'main'
> 3. Check: Require pull request reviews (at least 1 reviewer)
> 4. Check: Require status checks to pass
> 5. Check: Do not allow bypassing
> Once done, I'll re-run the GitHub collector."

After the user completes each remediation:
1. Re-collect evidence (automated or manual)
2. Re-record the test execution
3. Verify the test now passes

### 6.3 Iterate [AUTOMATED]

Loop until target is met:

```bash
python3 scripts/trust_portal_api.py compliance-score
python3 scripts/trust_portal_api.py evidence-gaps
```

Continue the analysis-remediation-retest cycle until:
- Compliance score >= 80%
- Evidence gaps count = 0
- No critical (security category) tests are failing

If the score is stuck below 80%, identify the weakest category and focus remediation there.

---

## Phase 7: Audit Preparation

**Goal:** Verify all compliance artifacts are complete, consistent, and ready for auditor review. Engage an auditor.

### 7.1 Verify Audit Log [AUTOMATED]

```bash
python3 scripts/trust_portal_api.py verify-audit-log
```

The response must show `"status": "valid"` and `"chain_valid": true`. The audit log uses hash chaining for tamper detection. If the hash chain is broken, investigate and resolve before proceeding. A broken chain will raise auditor concerns.

### 7.2 Verify Policies [AUTOMATED]

```bash
python3 scripts/trust_portal_api.py policies
```

Check that:
- All policies have `"status": "approved"`
- No policy has a `next_review_at` date in the past
- All five TSC categories have at least one policy
- Policy content accurately reflects current practices (if practices changed during remediation, update the policies)

If any policy is due for review or out of date, present it to the user for re-approval.

### 7.3 Verify Evidence [AUTOMATED]

```bash
python3 scripts/trust_portal_api.py evidence-gaps
```

This must return an empty list (no tests with missing, outdated, or due_soon evidence). If any gaps remain, return to Phase 5 or 6 to address them.

Also verify evidence freshness:
- For quarterly tests: evidence must be less than 90 days old
- For monthly tests: evidence must be less than 30 days old
- For annual tests: evidence must be less than 365 days old

### 7.4 Generate Audit-Ready Report [AUTOMATED]

Compile a comprehensive report covering:

1. **Organization profile**: company name, industry, scope of SOC 2 engagement
2. **Trust Service Categories in scope**: which categories, rationale
3. **Control framework**: total controls by category, implementation status
4. **Test results**: total tests, pass rate, per-category breakdown
5. **Evidence inventory**: total evidence items by type, automated vs. manual ratio
6. **Audit log status**: hash chain valid, total entries, date range covered
7. **Compliance score**: overall and per-category
8. **Policy inventory**: all policies with approval dates and next review dates
9. **System inventory**: all registered systems
10. **Vendor inventory**: all registered vendors with risk levels

Present this report to the user as a summary. The trust portal's public-facing pages (`/controls`, `/policies`, `/status`) serve as the live report for auditors.

### 7.5 Auditor Readiness [ASK USER]

Ask the user:

1. "Have you selected a SOC 2 auditor? (CPA firm)" If not, provide guidance: the auditor must be an AICPA-accredited CPA firm. Common options for startups: Johanson Group, Prescient Assurance, Barr Advisory, Schellman.
2. "For Type 2, what observation period are you targeting?" Typical: 3, 6, or 12 months. First-time audits often use a 3-month period.
3. "Would you like to give the auditor read-only access to the trust portal?"

If auditor access is needed, guide the user to create a team member with a client/read-only role at `/admin/team`.

Update the SOC 2 stage:

```bash
# Write to /tmp/stage.json:
# {"soc2_current_stage": "auditor_engaged"}
python3 scripts/trust_portal_api.py update-settings --data-file /tmp/stage.json
```

---

## Phase 8: Ongoing Compliance

**Goal:** Maintain compliance continuously. SOC 2 Type 2 requires evidence of ongoing operation, not just point-in-time compliance. This phase runs indefinitely.

### 8.1 Periodic Evidence Collection [AUTOMATED]

On a regular schedule (monthly or quarterly, depending on test frequency):

1. Re-run automated collectors:
```bash
docker exec trust-portal-dev python -m collectors.aws_collector
docker exec trust-portal-dev python -m collectors.github_collector
```

2. Record new test executions with fresh evidence.

3. Check for approaching due dates:
```bash
python3 scripts/trust_portal_api.py evidence-gaps
```

Flag any tests with `evidence_status: "due_soon"` and collect fresh evidence before they become `"outdated"`.

### 8.2 Policy Reviews [AUTOMATED]

Check policy review dates:

```bash
python3 scripts/trust_portal_api.py policies
```

For each policy where `next_review_at` is within 30 days or past due:
- Present the policy to the user
- Ask: "Has anything changed about this practice since the last review?"
- If yes: update the policy content and set a new review date
- If no: update `next_review_at` to the next review cycle (typically +12 months)

### 8.3 Resume After Interruption [AUTOMATED]

If an agent session starts and the user asks to continue SOC 2 work:

```bash
python3 scripts/trust_portal_api.py compliance-journey
```

The response contains:
- `current_phase`: the earliest incomplete phase number
- `phases`: status and checks for each phase
- `next_actions`: specific actions to take next (up to 3)
- `compliance_score`: current overall score

Pick up from the `next_actions` list and continue the playbook from the corresponding phase.

### 8.4 Quarterly Review [ASK USER]

Every quarter (or as the user's compliance calendar dictates), conduct a review:

1. "Are your policies still accurate? Has anything changed about how you operate?"
2. "Have you added any new systems, tools, or vendors since the last review?"
3. "Have there been any security incidents, near-misses, or suspicious activity?"
4. "Are there any new risks to add to the risk register?"
5. "Have any team members joined or left? Do access reviews need to be updated?"
6. "Have there been any changes to compliance requirements from customers or regulators?"

For each change identified:
- Update the relevant records (systems, vendors, risks, policies)
- Collect new evidence if controls are affected
- Re-run gap analysis to verify the score is maintained

---

## Appendix A: The "Document What You Do" Principle

This principle is the single most important concept in SOC 2 compliance. Violating it is the primary reason organizations fail audits.

**The rule:** Every policy, procedure, and control description must describe what the organization actually does today. Not what it plans to do. Not what it did last year. Not what the industry best practice says to do. What it actually does right now.

**Why this matters:** During a SOC 2 audit, the auditor will:
1. Read your policy (e.g., "All code changes require two reviewers before merging")
2. Sample evidence (e.g., pull 25 random pull requests from the last 6 months)
3. Check if the evidence matches the policy (did all 25 PRs have two reviewers?)
4. If even a few PRs were merged with zero or one reviewer, the control FAILS

**Examples of correct vs. incorrect policy language:**

| Correct (matches reality) | Incorrect (aspirational) |
|---------------------------|--------------------------|
| "We use GitHub pull requests with at least one reviewer before merging to main." | "All code changes undergo rigorous multi-stage review by senior engineers." |
| "Backups run daily via automated RDS snapshots retained for 7 days." | "Comprehensive backup procedures ensure business continuity." |
| "The CTO reviews access permissions quarterly using an IAM user export." | "Regular access reviews are conducted by authorized personnel." |
| "We use Dependabot for automated vulnerability scanning on every PR." | "Industry-leading vulnerability management practices protect our systems." |
| "Employees complete a 30-minute security training video during onboarding." | "Robust security awareness programs ensure all staff understand their obligations." |

**When the user's practice is not strong enough:**

If the user tells you they do not have MFA enforced, do not write a policy saying they enforce MFA. Instead:

1. Explain the gap: "SOC 2 auditors will ask for evidence that MFA is enforced on all accounts with access to production systems."
2. Help them fix it: "Here's how to enforce MFA in AWS IAM / Google Workspace / Okta."
3. After they fix it, then write the policy describing the new practice.
4. Collect evidence of the new practice.

This order is critical: fix the practice, then document it. Never document a practice that does not exist.

**Handling partial compliance:**

If a practice is partially implemented, describe it honestly with its current scope and limitations:

- "MFA is enforced for AWS console access and GitHub. MFA is not yet enforced for Slack. Migration to enforced MFA for Slack is planned for Q2."
- "Code reviews are required for the backend repository. Frontend repository changes are currently merged without review. A code review requirement for frontend is being implemented."

This honesty builds auditor trust and demonstrates a mature compliance program.

---

## Appendix B: Standard Controls by TSC Category

This is a reference list of typical SOC 2 controls. During Phase 4, create controls from this list, adapting each to match the organization's actual practices. Not every control applies to every organization. Skip controls that are irrelevant to the organization's scope.

### Security (CC) Controls

| Control Area | Description | Typical Tests |
|-------------|-------------|---------------|
| Access Management | User provisioning, deprovisioning, role-based access | Verify terminated users are removed within 24 hours; verify RBAC is enforced |
| Authentication | Password policy, MFA enforcement | Check IAM password policy; verify MFA on all privileged accounts |
| Network Security | Firewall rules, VPC configuration, security groups | Review security group rules for overly permissive access; verify VPC flow logs enabled |
| Encryption in Transit | TLS/SSL on all external endpoints | Verify all public endpoints use TLS 1.2+; check certificate validity |
| Encryption at Rest | Database encryption, storage encryption | Verify RDS encryption enabled; verify S3 default encryption; verify EBS encryption |
| Logging & Monitoring | Centralized logging, alerting on anomalies | Verify CloudTrail enabled; verify log retention >= 90 days; verify alerts configured |
| Vulnerability Management | Scanning, patching, remediation tracking | Verify automated scanning runs on every PR; verify critical CVEs patched within SLA |
| Change Management | Code reviews, CI/CD, deployment process | Verify branch protection on main; verify PRs require review; verify CI passes before merge |
| Incident Response | Detection, response, communication procedures | Verify incident response plan exists; verify last tabletop exercise date |
| Risk Assessment | Risk identification, evaluation, treatment | Verify risk register exists and is reviewed quarterly |
| Security Awareness | Training program for employees | Verify onboarding includes security training; verify annual refresher |
| Endpoint Security | Device management, anti-malware | Verify device encryption; verify screen lock policies |

### Availability (A) Controls

| Control Area | Description | Typical Tests |
|-------------|-------------|---------------|
| Uptime Monitoring | System availability tracking | Verify monitoring is configured; verify uptime meets SLA |
| Backup & Recovery | Automated backups, restore testing | Verify backup schedule; verify last successful restore test |
| Disaster Recovery | DR plan, failover capability | Verify DR plan exists; verify RTO/RPO documented |
| Capacity Planning | Resource monitoring, scaling policies | Verify auto-scaling configured; verify capacity alerts set |
| Redundancy | High availability, multi-AZ deployment | Verify multi-AZ RDS; verify load balancer health checks |

### Confidentiality (C) Controls

| Control Area | Description | Typical Tests |
|-------------|-------------|---------------|
| Data Classification | Classification scheme, labeling | Verify classification policy exists; verify data inventory |
| Data Access Controls | Need-to-know access, segregation | Verify database access restricted to authorized roles |
| Data Retention | Retention schedules, secure deletion | Verify retention policy; verify deletion procedures |
| Confidentiality Agreements | NDAs, employment agreements | Verify NDA process for employees and contractors |

### Privacy (P) Controls

| Control Area | Description | Typical Tests |
|-------------|-------------|---------------|
| Privacy Notice | Published privacy policy, consent | Verify privacy policy is current and accessible |
| Data Subject Rights | Access, deletion, portability requests | Verify process exists for data subject requests |
| Consent Management | Collection, storage, withdrawal of consent | Verify consent is obtained before data collection |
| Sub-processor Management | Vendor data processing agreements | Verify DPAs with all sub-processors |
| Data Breach Notification | Notification procedures, timelines | Verify breach notification procedure exists |

### Processing Integrity (PI) Controls

| Control Area | Description | Typical Tests |
|-------------|-------------|---------------|
| Input Validation | Data validation at ingestion | Verify input validation on API endpoints |
| Processing Accuracy | Output verification, error handling | Verify error handling and logging on critical processes |
| Output Completeness | Delivery confirmation, reconciliation | Verify data processing produces expected outputs |
| Error Handling | Error detection, correction, reporting | Verify error monitoring and alerting |

---

## Appendix C: Evidence Collection Cheat Sheet

Quick reference for common evidence types and how to collect them.

| Evidence Needed | Type | How to Collect |
|----------------|------|---------------|
| IAM password policy | screenshot | AWS Console > IAM > Account Settings |
| MFA status for users | screenshot | AWS Console > IAM > Users (MFA column) |
| CloudTrail enabled | automated | AWS collector checks this |
| S3 bucket encryption | automated | AWS collector checks this |
| RDS encryption | automated | AWS collector checks this |
| Branch protection | automated | GitHub collector checks this |
| PR review requirements | automated | GitHub collector checks this |
| Backup configuration | screenshot | AWS Console > RDS > Instance > Backups tab |
| Security group rules | screenshot | AWS Console > VPC > Security Groups |
| Incident response plan | document | Upload the IR plan document |
| Security training records | file | Export from LMS or HR system |
| Access review evidence | file | Export IAM user list, annotate with review notes |
| Vendor agreements | document | Upload signed DPA/NDA/MSA |
| Risk register | link | Link to the living risk register document |
| Penetration test results | file | Upload scan results from security tool |
| Disaster recovery plan | document | Upload DR plan document |
| Uptime reports | link | Link to monitoring dashboard or export |
| Privacy policy | link | URL of published privacy policy page |
| Change management records | automated | Decision logs + KanbanZone cards via skills |
| Code review evidence | automated | GitHub collector pulls PR review data |

---

## Appendix D: SOC 2 Stage Progression

The trust portal tracks the organization's SOC 2 stage. Update this as milestones are reached.

| Stage Key | Meaning | When to Set |
|-----------|---------|-------------|
| `not_started` | No SOC 2 work has begun | Initial state |
| `policies_established` | All policies written and approved | After Phase 3 completes |
| `collecting_point_in_time` | Controls and tests in place, evidence being collected for Type 1 | After Phase 4 completes |
| `auditor_engaged` | Auditor selected, observation period defined | After Phase 7.5 |
| `type_1_completed` | Type 1 audit report received | After Type 1 audit |
| `collecting_continuous` | Ongoing evidence collection for Type 2 observation period | During Type 2 observation |
| `type_2_completed` | Type 2 audit report received | After Type 2 audit |

Update via:

```bash
# Write to /tmp/stage.json:
# {"soc2_current_stage": "<stage_key>"}
python3 scripts/trust_portal_api.py update-settings --data-file /tmp/stage.json
```

---

## Appendix E: Troubleshooting

### Trust portal health check fails
```bash
docker logs trust-portal-dev
```
Common causes: database not ready (wait and retry), port conflict (change port in `.env`), missing environment variables.

### API key rejected (401)
- Verify the key in `.env` matches the key in the portal's `/admin/team` page.
- Verify `TRUST_PORTAL_API_URL` does not have a trailing slash.
- Verify the team member is active (not deactivated).

### Collector fails with credentials error
- AWS collector: verify `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_DEFAULT_REGION` are set in the trust portal's Docker environment.
- GitHub collector: verify `GITHUB_TOKEN` has `repo` scope and is not expired.

### Compliance journey shows wrong phase
The journey endpoint determines the current phase based on the earliest incomplete phase. If Phase 2 shows incomplete but you believe it is done, check the `checks` object: `systems_registered` and `vendors_registered` must both be true (at least one system and one vendor exist).

### Hash chain verification fails
```bash
python3 scripts/trust_portal_api.py verify-audit-log
```
If the chain is invalid, this indicates either a bug or data tampering. Check the `first_broken_link` field for the specific audit log entry where the chain breaks. This is a critical issue that must be investigated before an audit.

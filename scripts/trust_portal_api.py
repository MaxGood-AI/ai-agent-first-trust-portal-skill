#!/usr/bin/env python3
"""Trust Portal API CLI client.

Self-contained client using only Python standard library.
All output is JSON.

Environment variables (auto-loaded from .env if not in environment):
    TRUST_PORTAL_API_URL — Trust portal base URL (e.g., http://localhost:5100)
    TRUST_PORTAL_API_KEY — API key for the authenticated team member
"""

import argparse
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.parse
import urllib.request


_env_loaded = False


def _load_env_file():
    """Load TRUST_PORTAL_* variables from .env if not already in the environment."""
    global _env_loaded
    if _env_loaded:
        return
    _env_loaded = True

    if os.environ.get("TRUST_PORTAL_API_KEY"):
        return

    candidates = []
    seen = set()

    search_roots = [
        Path.cwd(),
        Path(__file__).resolve().parents[1],
    ]
    for root in search_roots:
        current = root
        while True:
            candidate = current / ".env"
            candidate_str = str(candidate)
            if candidate_str not in seen:
                candidates.append(candidate_str)
                seen.add(candidate_str)
            if current.parent == current:
                break
            current = current.parent

    for path in candidates:
        if os.path.isfile(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" not in line:
                        continue
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip().strip("'\"")
                    if key.startswith("TRUST_PORTAL_"):
                        os.environ.setdefault(key, value)
            break


def _get_config():
    """Return (base_url, api_key) or exit with error."""
    _load_env_file()
    base_url = os.environ.get("TRUST_PORTAL_API_URL", "").rstrip("/")
    api_key = os.environ.get("TRUST_PORTAL_API_KEY", "")
    if not base_url or not api_key:
        _error_exit("TRUST_PORTAL_API_URL and TRUST_PORTAL_API_KEY must be set")
    return base_url, api_key


def _error_exit(message):
    json.dump({"error": True, "message": message}, sys.stdout, indent=2)
    print()
    sys.exit(1)


def _api_request(method, path, params=None, body=None):
    """Make an authenticated request to the trust portal API."""
    base_url, api_key = _get_config()
    url = f"{base_url}{path}"

    if params:
        filtered = {k: v for k, v in params.items() if v is not None}
        if filtered:
            url += "?" + urllib.parse.urlencode(filtered)

    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("X-API-Key", api_key)
    req.add_header("Content-Type", "application/json")
    req.add_header("Accept", "application/json")

    try:
        with urllib.request.urlopen(req) as resp:
            raw = resp.read().decode("utf-8")
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                return {"error": True, "message": raw.strip() or "Empty response"}
    except urllib.error.HTTPError as e:
        body_text = ""
        try:
            body_text = e.read().decode("utf-8")
        except Exception:
            pass
        return {"error": True, "status": e.code, "message": e.reason, "body": body_text}
    except urllib.error.URLError as e:
        return {"error": True, "message": str(e.reason)}


def _output(data):
    json.dump(data, sys.stdout, indent=2, default=str)
    print()


def _read_data_file(path):
    """Read JSON from a file path."""
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError) as e:
        _error_exit(f"Could not read data file: {e}")


# --- Command handlers ---


def cmd_health(args):
    _output(_api_request("GET", "/api/health"))


def cmd_compliance_score(args):
    _output(_api_request("GET", "/api/compliance-score"))


def cmd_evidence_gaps(args):
    _output(_api_request("GET", "/api/gaps"))


def cmd_settings(args):
    _output(_api_request("GET", "/api/settings"))


def cmd_update_settings(args):
    data = _read_data_file(args.data_file)
    _output(_api_request("PUT", "/api/settings", body=data))


# --- CRUD: Controls ---

def cmd_controls(args):
    _output(_api_request("GET", "/api/controls"))


def cmd_control(args):
    _output(_api_request("GET", f"/api/controls/{args.id}"))


def cmd_create_control(args):
    body = {"name": args.name, "category": args.category}
    if args.data_file:
        body = _read_data_file(args.data_file)
    _output(_api_request("POST", "/api/controls", body=body))


def cmd_update_control(args):
    data = _read_data_file(args.data_file)
    _output(_api_request("PUT", f"/api/controls/{args.id}", body=data))


def cmd_delete_control(args):
    _output(_api_request("DELETE", f"/api/controls/{args.id}"))


# --- CRUD: Tests ---

def cmd_tests(args):
    _output(_api_request("GET", "/api/tests"))


def cmd_test(args):
    _output(_api_request("GET", f"/api/tests/{args.id}"))


def cmd_create_test(args):
    body = {"name": args.name, "control_id": args.control_id}
    if args.data_file:
        body = _read_data_file(args.data_file)
    _output(_api_request("POST", "/api/tests", body=body))


def cmd_update_test(args):
    data = _read_data_file(args.data_file)
    _output(_api_request("PUT", f"/api/tests/{args.id}", body=data))


# --- CRUD: Policies ---

def cmd_policies(args):
    _output(_api_request("GET", "/api/policies"))


def cmd_policy(args):
    _output(_api_request("GET", f"/api/policies/{args.id}"))


# --- CRUD: Systems, Vendors, Risks ---

def cmd_systems(args):
    _output(_api_request("GET", "/api/systems"))


def cmd_system(args):
    _output(_api_request("GET", f"/api/systems/{args.id}"))


def cmd_vendors(args):
    _output(_api_request("GET", "/api/vendors"))


def cmd_vendor(args):
    _output(_api_request("GET", f"/api/vendors/{args.id}"))


def cmd_risks(args):
    _output(_api_request("GET", "/api/risks"))


# --- Evidence ---

def cmd_evidence(args):
    _output(_api_request("GET", "/api/evidence"))


def cmd_submit_evidence(args):
    body = {
        "test_record_id": args.test_record_id,
        "evidence_type": args.evidence_type,
        "description": args.description,
    }
    if args.url:
        body["url"] = args.url
    _output(_api_request("POST", "/api/evidence", body=body))


# --- Pentest Findings ---

def cmd_pentest_findings(args):
    _output(_api_request("GET", "/api/pentest-findings"))


# --- Audit Log ---

def cmd_audit_log(args):
    params = {
        "table": args.table,
        "record_id": args.record_id,
        "action": args.action,
        "changed_by": args.changed_by,
        "since": args.since,
        "limit": args.limit,
    }
    _output(_api_request("GET", "/api/audit-log", params=params))


# --- Decision Log ---

def cmd_upload_decision_log(args):
    base_url, api_key = _get_config()
    with open(args.file, "rb") as f:
        content = f.read()

    params = {}
    if args.session_id:
        params["session_id"] = args.session_id

    url = f"{base_url}/api/decision-log/upload"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url, data=content, method="POST")
    req.add_header("X-API-Key", api_key)
    req.add_header("Content-Type", "application/jsonl")

    try:
        with urllib.request.urlopen(req) as resp:
            _output(json.loads(resp.read().decode("utf-8")))
    except urllib.error.HTTPError as e:
        body_text = e.read().decode("utf-8") if e.fp else ""
        _output({"error": True, "status": e.code, "message": e.reason, "body": body_text})


def cmd_decision_log_sessions(args):
    _output(_api_request("GET", "/api/decision-log/sessions"))


def cmd_decision_log_session(args):
    _output(_api_request("GET", f"/api/decision-log/session/{args.id}"))


# --- Argument parser ---


def main():
    parser = argparse.ArgumentParser(
        description="Trust Portal API client for Claude Code agent skills"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # Health
    sub.add_parser("health", help="Health check")

    # Compliance
    sub.add_parser("compliance-score", help="Overall and per-category compliance scores")
    sub.add_parser("evidence-gaps", help="Tests with missing or outdated evidence")

    # Settings
    sub.add_parser("settings", help="Get portal settings")
    p = sub.add_parser("update-settings", help="Update portal settings (admin)")
    p.add_argument("--data-file", required=True, help="JSON file with settings data")

    # Controls
    sub.add_parser("controls", help="List all controls")
    p = sub.add_parser("control", help="Get a single control")
    p.add_argument("--id", required=True, help="Control ID")
    p = sub.add_parser("create-control", help="Create a control")
    p.add_argument("--name", help="Control name")
    p.add_argument("--category", help="TSC category")
    p.add_argument("--data-file", help="JSON file with full control data")
    p = sub.add_parser("update-control", help="Update a control")
    p.add_argument("--id", required=True, help="Control ID")
    p.add_argument("--data-file", required=True, help="JSON file with update data")
    p = sub.add_parser("delete-control", help="Delete a control")
    p.add_argument("--id", required=True, help="Control ID")

    # Tests
    sub.add_parser("tests", help="List all test records")
    p = sub.add_parser("test", help="Get a single test record")
    p.add_argument("--id", required=True, help="Test record ID")
    p = sub.add_parser("create-test", help="Create a test record")
    p.add_argument("--name", help="Test name")
    p.add_argument("--control-id", help="Parent control ID")
    p.add_argument("--data-file", help="JSON file with full test data")
    p = sub.add_parser("update-test", help="Update a test record")
    p.add_argument("--id", required=True, help="Test record ID")
    p.add_argument("--data-file", required=True, help="JSON file with update data")

    # Policies
    sub.add_parser("policies", help="List all policies")
    p = sub.add_parser("policy", help="Get a single policy")
    p.add_argument("--id", required=True, help="Policy ID")

    # Systems
    sub.add_parser("systems", help="List all systems")
    p = sub.add_parser("system", help="Get a single system")
    p.add_argument("--id", required=True, help="System ID")

    # Vendors
    sub.add_parser("vendors", help="List all vendors")
    p = sub.add_parser("vendor", help="Get a single vendor")
    p.add_argument("--id", required=True, help="Vendor ID")

    # Risks
    sub.add_parser("risks", help="List risk register entries")

    # Evidence
    sub.add_parser("evidence", help="List all evidence")
    p = sub.add_parser("submit-evidence", help="Submit evidence for a test")
    p.add_argument("--test-record-id", required=True, help="Test record ID")
    p.add_argument("--evidence-type", required=True, help="Evidence type: link, file, screenshot, automated")
    p.add_argument("--description", required=True, help="Evidence description")
    p.add_argument("--url", help="URL for link-type evidence")

    # Pentest Findings
    sub.add_parser("pentest-findings", help="List pentest findings")

    # Audit Log
    p = sub.add_parser("audit-log", help="Query the audit log")
    p.add_argument("--table", help="Filter by table name")
    p.add_argument("--record-id", help="Filter by record ID")
    p.add_argument("--action", help="Filter by action (INSERT, UPDATE, DELETE)")
    p.add_argument("--changed-by", help="Filter by team member ID")
    p.add_argument("--since", help="Only entries after this ISO timestamp")
    p.add_argument("--limit", type=int, help="Max entries to return (default 50)")

    # Decision Log
    p = sub.add_parser("upload-decision-log", help="Upload a JSONL decision log transcript")
    p.add_argument("--file", required=True, help="Path to JSONL file")
    p.add_argument("--session-id", help="Optional session ID (generated if omitted)")
    sub.add_parser("decision-log-sessions", help="List decision log sessions")
    p = sub.add_parser("decision-log-session", help="Get a decision log session")
    p.add_argument("--id", required=True, help="Session ID")

    args = parser.parse_args()

    commands = {
        "health": cmd_health,
        "compliance-score": cmd_compliance_score,
        "evidence-gaps": cmd_evidence_gaps,
        "settings": cmd_settings,
        "update-settings": cmd_update_settings,
        "controls": cmd_controls,
        "control": cmd_control,
        "create-control": cmd_create_control,
        "update-control": cmd_update_control,
        "delete-control": cmd_delete_control,
        "tests": cmd_tests,
        "test": cmd_test,
        "create-test": cmd_create_test,
        "update-test": cmd_update_test,
        "policies": cmd_policies,
        "policy": cmd_policy,
        "systems": cmd_systems,
        "system": cmd_system,
        "vendors": cmd_vendors,
        "vendor": cmd_vendor,
        "risks": cmd_risks,
        "evidence": cmd_evidence,
        "submit-evidence": cmd_submit_evidence,
        "pentest-findings": cmd_pentest_findings,
        "audit-log": cmd_audit_log,
        "upload-decision-log": cmd_upload_decision_log,
        "decision-log-sessions": cmd_decision_log_sessions,
        "decision-log-session": cmd_decision_log_session,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

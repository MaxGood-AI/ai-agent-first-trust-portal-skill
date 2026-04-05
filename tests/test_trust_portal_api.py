"""Tests for trust_portal_api.py — stdlib unittest with mocked HTTP."""

import http.client
import io
import json
import os
import sys
import tempfile
import unittest
from unittest import mock

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import trust_portal_api  # noqa: E402


class TestLoadEnv(unittest.TestCase):
    def setUp(self):
        trust_portal_api._env_loaded = False
        self._orig_env = os.environ.copy()

    def tearDown(self):
        os.environ.clear()
        os.environ.update(self._orig_env)
        trust_portal_api._env_loaded = False

    def test_load_env_from_cwd(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = os.path.join(tmpdir, ".env")
            with open(env_path, "w") as f:
                f.write("TRUST_PORTAL_API_URL=http://test:5100\n")
                f.write("TRUST_PORTAL_API_KEY=test-key-123\n")

            os.environ.pop("TRUST_PORTAL_API_KEY", None)
            os.environ.pop("TRUST_PORTAL_API_URL", None)

            from pathlib import Path
            with mock.patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
                trust_portal_api._load_env_file()

            self.assertEqual(os.environ.get("TRUST_PORTAL_API_URL"), "http://test:5100")
            self.assertEqual(os.environ.get("TRUST_PORTAL_API_KEY"), "test-key-123")

    def test_skip_if_already_set(self):
        os.environ["TRUST_PORTAL_API_KEY"] = "already-set"
        trust_portal_api._load_env_file()
        self.assertTrue(trust_portal_api._env_loaded)

    def test_ignores_non_trust_portal_vars(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            env_path = os.path.join(tmpdir, ".env")
            with open(env_path, "w") as f:
                f.write("TRUST_PORTAL_API_KEY=key1\n")
                f.write("OTHER_VAR=should-not-be-set\n")

            os.environ.pop("TRUST_PORTAL_API_KEY", None)
            os.environ.pop("OTHER_VAR", None)

            from pathlib import Path
            with mock.patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
                trust_portal_api._load_env_file()

            self.assertEqual(os.environ.get("TRUST_PORTAL_API_KEY"), "key1")
            self.assertNotIn("OTHER_VAR", os.environ)


class TestApiRequest(unittest.TestCase):
    def setUp(self):
        trust_portal_api._env_loaded = False
        os.environ["TRUST_PORTAL_API_URL"] = "http://test-portal:5100"
        os.environ["TRUST_PORTAL_API_KEY"] = "test-api-key"

    def tearDown(self):
        os.environ.pop("TRUST_PORTAL_API_URL", None)
        os.environ.pop("TRUST_PORTAL_API_KEY", None)
        trust_portal_api._env_loaded = False

    @mock.patch("urllib.request.urlopen")
    def test_sends_auth_header(self, mock_urlopen):
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = b'{"status": "ok"}'
        mock_resp.__enter__ = mock.Mock(return_value=mock_resp)
        mock_resp.__exit__ = mock.Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        trust_portal_api._api_request("GET", "/api/health")

        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_header("X-api-key"), "test-api-key")

    @mock.patch("urllib.request.urlopen")
    def test_sends_json_content_type(self, mock_urlopen):
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = b'{"status": "ok"}'
        mock_resp.__enter__ = mock.Mock(return_value=mock_resp)
        mock_resp.__exit__ = mock.Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        trust_portal_api._api_request("POST", "/api/controls", body={"name": "Test"})

        req = mock_urlopen.call_args[0][0]
        self.assertEqual(req.get_header("Content-type"), "application/json")
        self.assertIsNotNone(req.data)

    @mock.patch("urllib.request.urlopen")
    def test_handles_http_error(self, mock_urlopen):
        error = trust_portal_api.urllib.error.HTTPError(
            url="http://test:5100/api/controls/bad",
            code=404,
            msg="Not Found",
            hdrs={},
            fp=io.BytesIO(b'{"detail": "not found"}'),
        )
        mock_urlopen.side_effect = error

        result = trust_portal_api._api_request("GET", "/api/controls/bad")
        self.assertTrue(result.get("error"))
        self.assertEqual(result["status"], 404)

    @mock.patch("urllib.request.urlopen")
    def test_handles_connection_error(self, mock_urlopen):
        mock_urlopen.side_effect = trust_portal_api.urllib.error.URLError("Connection refused")

        result = trust_portal_api._api_request("GET", "/api/health")
        self.assertTrue(result.get("error"))
        self.assertIn("Connection refused", result["message"])

    @mock.patch("urllib.request.urlopen")
    def test_passes_query_params(self, mock_urlopen):
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = b'[]'
        mock_resp.__enter__ = mock.Mock(return_value=mock_resp)
        mock_resp.__exit__ = mock.Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        trust_portal_api._api_request("GET", "/api/audit-log", params={"table": "controls", "limit": 5})

        req = mock_urlopen.call_args[0][0]
        self.assertIn("table=controls", req.full_url)
        self.assertIn("limit=5", req.full_url)

    @mock.patch("urllib.request.urlopen")
    def test_skips_none_params(self, mock_urlopen):
        mock_resp = mock.MagicMock()
        mock_resp.read.return_value = b'[]'
        mock_resp.__enter__ = mock.Mock(return_value=mock_resp)
        mock_resp.__exit__ = mock.Mock(return_value=False)
        mock_urlopen.return_value = mock_resp

        trust_portal_api._api_request("GET", "/api/audit-log", params={"table": "controls", "action": None})

        req = mock_urlopen.call_args[0][0]
        self.assertIn("table=controls", req.full_url)
        self.assertNotIn("action", req.full_url)


class TestMissingConfig(unittest.TestCase):
    def setUp(self):
        trust_portal_api._env_loaded = False
        os.environ.pop("TRUST_PORTAL_API_URL", None)
        os.environ.pop("TRUST_PORTAL_API_KEY", None)

    def tearDown(self):
        trust_portal_api._env_loaded = False

    def test_missing_env_vars_exits(self):
        with self.assertRaises(SystemExit) as ctx:
            trust_portal_api._get_config()
        self.assertEqual(ctx.exception.code, 1)


class TestDataFile(unittest.TestCase):
    def test_read_valid_json_file(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump({"name": "Test"}, f)
            f.flush()
            result = trust_portal_api._read_data_file(f.name)
        os.unlink(f.name)
        self.assertEqual(result["name"], "Test")

    def test_read_missing_file_exits(self):
        with self.assertRaises(SystemExit):
            trust_portal_api._read_data_file("/nonexistent/file.json")

    def test_read_invalid_json_exits(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("not json")
            f.flush()
        with self.assertRaises(SystemExit):
            trust_portal_api._read_data_file(f.name)
        os.unlink(f.name)


class TestCommandHandlers(unittest.TestCase):
    def setUp(self):
        trust_portal_api._env_loaded = False
        os.environ["TRUST_PORTAL_API_URL"] = "http://test:5100"
        os.environ["TRUST_PORTAL_API_KEY"] = "test-key"

    def tearDown(self):
        os.environ.pop("TRUST_PORTAL_API_URL", None)
        os.environ.pop("TRUST_PORTAL_API_KEY", None)
        trust_portal_api._env_loaded = False

    @mock.patch("trust_portal_api._api_request")
    @mock.patch("trust_portal_api._output")
    def test_health_command(self, mock_output, mock_req):
        mock_req.return_value = {"status": "ok"}
        args = mock.MagicMock()
        trust_portal_api.cmd_health(args)
        mock_req.assert_called_once_with("GET", "/api/health")
        mock_output.assert_called_once_with({"status": "ok"})

    @mock.patch("trust_portal_api._api_request")
    @mock.patch("trust_portal_api._output")
    def test_controls_command(self, mock_output, mock_req):
        mock_req.return_value = [{"id": "1", "name": "Test"}]
        args = mock.MagicMock()
        trust_portal_api.cmd_controls(args)
        mock_req.assert_called_once_with("GET", "/api/controls")

    @mock.patch("trust_portal_api._api_request")
    @mock.patch("trust_portal_api._output")
    def test_submit_evidence_command(self, mock_output, mock_req):
        mock_req.return_value = {"id": "ev-1"}
        args = mock.MagicMock()
        args.test_record_id = "tr-1"
        args.evidence_type = "link"
        args.description = "Scan results"
        args.url = "https://example.com/scan"
        trust_portal_api.cmd_submit_evidence(args)
        call_body = mock_req.call_args[1]["body"]
        self.assertEqual(call_body["test_record_id"], "tr-1")
        self.assertEqual(call_body["evidence_type"], "link")
        self.assertEqual(call_body["url"], "https://example.com/scan")

    @mock.patch("trust_portal_api._api_request")
    @mock.patch("trust_portal_api._output")
    def test_audit_log_passes_filters(self, mock_output, mock_req):
        mock_req.return_value = []
        args = mock.MagicMock()
        args.table = "controls"
        args.record_id = None
        args.action = "INSERT"
        args.changed_by = None
        args.since = None
        args.limit = 10
        trust_portal_api.cmd_audit_log(args)
        call_params = mock_req.call_args[1]["params"]
        self.assertEqual(call_params["table"], "controls")
        self.assertEqual(call_params["action"], "INSERT")
        self.assertEqual(call_params["limit"], 10)
        self.assertIsNone(call_params["record_id"])


if __name__ == "__main__":
    unittest.main()

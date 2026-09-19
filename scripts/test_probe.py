#!/usr/bin/env python3
"""Unit tests for status classification and HTML honesty."""

from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

import probe

FIXED = datetime(2026, 9, 19, 20, 45, tzinfo=timezone.utc)

WEBSITE = {
    "id": "website",
    "name": "Website",
    "url": "https://dominionprotectivesolutions.com/",
    "expect": [200],
    "note": "Public marketing site",
}
CRM = {
    "id": "crm",
    "name": "Nexus CRM",
    "url": "https://crm.dominionprotectivesolutions.com/",
    "expect": [200, 401],
    "auth_challenge_is_up": True,
    "note": "Staff CRM",
}
SIGN = {
    "id": "sign",
    "name": "OpenSign",
    "url": "https://sign.dominionprotectivesolutions.com/",
    "expect": [200, 302, 308],
    "note": "Document signing",
}


class ClassifyTests(unittest.TestCase):
    def test_website_200_is_up(self) -> None:
        row = probe.classify(WEBSITE, {"status_code": 200, "headers": {}, "error": None})
        self.assertEqual(row["state"], "operational")
        self.assertEqual(row["detail"], "HTTP 200")

    def test_website_500_is_down(self) -> None:
        row = probe.classify(WEBSITE, {"status_code": 500, "headers": {}, "error": None})
        self.assertEqual(row["state"], "down")
        self.assertEqual(row["detail"], "HTTP 500")

    def test_sign_404_is_down(self) -> None:
        row = probe.classify(SIGN, {"status_code": 404, "headers": {}, "error": None})
        self.assertEqual(row["state"], "down")
        self.assertNotEqual(row["state"], "operational")

    def test_crm_401_with_authenticate_is_up(self) -> None:
        row = probe.classify(
            CRM,
            {
                "status_code": 401,
                "headers": {"www-authenticate": 'Basic realm="Nexus CRM"'},
                "error": None,
            },
        )
        self.assertEqual(row["state"], "operational")
        self.assertIn("401", row["detail"])

    def test_timeout_is_check_failed_not_operational(self) -> None:
        row = probe.classify(
            WEBSITE,
            {"status_code": None, "headers": {}, "error": "TimeoutError: timed out"},
        )
        self.assertEqual(row["state"], "error")
        self.assertIn("TimeoutError", row["detail"])


class HeadlineTests(unittest.TestCase):
    def test_mixed_is_partial_outage_not_all_green(self) -> None:
        rows = [
            probe.classify(WEBSITE, {"status_code": 200, "headers": {}, "error": None}),
            probe.classify(CRM, {"status_code": 401, "headers": {"www-authenticate": "Basic"}, "error": None}),
            probe.classify(SIGN, {"status_code": 404, "headers": {}, "error": None}),
        ]
        color, headline, banner = probe.headline_for(rows)
        self.assertEqual(headline, "Partial outage")
        self.assertIn("OpenSign", banner)
        self.assertNotIn("All systems operational", headline)
        html = probe.render_html(
            {"brand": "Dominion Protective Solutions", "license": "CA PPO #122483"},
            rows,
            FIXED,
        )
        self.assertIn("Partial outage", html)
        self.assertIn("● Down", html)
        self.assertIn("Last published: 2026-09-19 20:45 UTC", html)
        self.assertNotIn("All systems operational", html)
        self.assertNotIn("Checks are not publishing", html)
        self.assertIn("CA PPO #122483", html)
        self.assertIn("Company license only", html)

    def test_all_up_does_not_claim_unverified(self) -> None:
        rows = [
            probe.classify(WEBSITE, {"status_code": 200, "headers": {}, "error": None}),
            probe.classify(SIGN, {"status_code": 302, "headers": {}, "error": None}),
        ]
        _, headline, banner = probe.headline_for(rows)
        self.assertEqual(headline, "Checked systems operational")
        self.assertEqual(banner, "")

    def test_html_escapes_injected_text(self) -> None:
        row = {
            "id": "x",
            "name": "<script>alert(1)</script>",
            "url": "https://example.test/",
            "state": "down",
            "http_status": 404,
            "detail": "HTTP 404",
            "note": "ok",
        }
        html = probe.render_html({"brand": "DPS", "license": "CA PPO #122483"}, [row], FIXED)
        self.assertNotIn("<script>alert(1)</script>", html)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", html)


class LoadChecksTests(unittest.TestCase):
    def test_repo_checks_json_has_marketing_site_only_in_service_hosts(self) -> None:
        config = probe.load_checks(probe.DEFAULT_CHECKS)
        urls = [check["url"] for check in config["checks"]]
        self.assertIn("https://dominionprotectivesolutions.com/", urls)
        joined = " ".join(urls)
        self.assertNotIn("docs.dominionprotectivesolutions.com", joined)
        self.assertNotIn("portal.dominionprotectivesolutions.com", joined)
        self.assertNotIn("dl.dominionprotectivesolutions.com", joined)
        self.assertNotIn("ironclad", joined.lower())
        self.assertNotIn("pitetti", joined.lower())
        self.assertEqual(config["license"], "CA PPO #122483")

    def test_empty_checks_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "checks.json"
            path.write_text(json.dumps({"checks": []}), encoding="utf-8")
            with self.assertRaises(ValueError):
                probe.load_checks(path)


if __name__ == "__main__":
    unittest.main()

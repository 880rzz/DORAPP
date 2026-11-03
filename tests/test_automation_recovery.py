#!/usr/bin/env python3
"""Automation recovery tests: schedule gaps, JSON smoke classification, workflow gates."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import production_json_probe  # noqa: E402
import steward_schedule  # noqa: E402


class StewardScheduleTests(unittest.TestCase):
    def test_daily_due_when_press_not_run_today(self):
        now = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)
        decision = steward_schedule.decide(
            now,
            {"lastRunAt": "2026-11-02T09:00:00+00:00"},
            {"lastRunAt": "2026-11-02T09:54:23+00:00"},
        )
        self.assertTrue(decision["daily_due"])
        self.assertTrue(decision["hourly_late"])
        self.assertGreater(decision["gap_hours"], 2)

    def test_daily_not_due_same_utc_day(self):
        now = datetime(2026, 11, 3, 12, 0, tzinfo=timezone.utc)
        decision = steward_schedule.decide(
            now,
            {"lastRunAt": "2026-11-03T01:00:00+00:00"},
            {"lastRunAt": "2026-11-03T11:30:00+00:00"},
        )
        self.assertFalse(decision["daily_due"])
        self.assertFalse(decision["hourly_late"])


class ProductionJsonProbeTests(unittest.TestCase):
    def test_valid_json_ok(self):
        category, message = production_json_probe.classify_dataset_response(
            iso="es",
            route="/data/countries/es/organizations.json",
            status="200",
            body='{"organizations":[]}',
            required_keys=("organizations",),
            optional=True,
        )
        self.assertEqual(category, "ok")
        self.assertIsNone(message)

    def test_html_body_not_generic_invalid_json(self):
        category, message = production_json_probe.classify_dataset_response(
            iso="es",
            route="/data/countries/es/organizations.json",
            status="200",
            body="<!DOCTYPE html><html><body>deploying</body></html>",
            required_keys=("organizations",),
            optional=True,
        )
        self.assertEqual(category, "html_body")
        self.assertIn("HTML body instead of JSON", message)

    def test_optional_404_is_coverage_gap(self):
        category, message = production_json_probe.classify_dataset_response(
            iso="fi",
            route="/data/countries/fi/organizations.json",
            status="404",
            body="Not Found",
            required_keys=("organizations",),
            optional=True,
        )
        self.assertEqual(category, "absent_optional")
        self.assertIsNone(message)

    def test_syntax_error_keeps_prefix(self):
        category, message = production_json_probe.classify_dataset_response(
            iso="es",
            route="/data/countries/es/organizations.json",
            status="200",
            body="{not-json",
            required_keys=("organizations",),
            optional=True,
        )
        self.assertEqual(category, "invalid_json")
        self.assertIn("body_prefix=", message)


class WorkflowGateTests(unittest.TestCase):
    def test_steward_restores_hourly_and_stops_direct_main_push(self):
        text = (ROOT / ".github/workflows/global-daily-steward.yml").read_text()
        # PyYAML 1.1 maps the GitHub Actions key `on` to boolean True.
        doc = yaml.safe_load(text)
        schedule = doc[True]["schedule"]
        crons = [item["cron"] for item in schedule]
        self.assertIn("37 0-1,3-23 * * *", crons)
        self.assertIn("37 2 * * *", crons)
        self.assertNotIn("git push origin HEAD:main", text)
        self.assertIn("peter-evans/create-pull-request@v7", text)
        self.assertIn("scripts/steward_schedule.py", text)

    def test_static_build_uses_pull_request_gate(self):
        text = (ROOT / ".github/workflows/deploy-pages.yml").read_text()
        self.assertNotIn("git push origin HEAD:main", text)
        self.assertIn("peter-evans/create-pull-request@v7", text)
        self.assertIn("node --check world.js", text)

    def test_smoke_workflow_uses_classifier(self):
        text = (ROOT / ".github/workflows/production-smoke.yml").read_text()
        self.assertIn("production_json_probe", text)
        self.assertIn("actions/checkout@v5", text)

    def test_no_workflow_pushes_directly_to_main(self):
        for path in (ROOT / ".github/workflows").glob("*.yml"):
            text = path.read_text()
            self.assertNotIn(
                "git push origin HEAD:main",
                text,
                f"{path.name} still pushes directly to main",
            )


if __name__ == "__main__":
    unittest.main()

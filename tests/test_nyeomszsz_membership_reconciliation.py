#!/usr/bin/env python3
"""Tests for NYEOMSZSZ membership reconciliation and BGA adapter safety."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import bga_source_adapter  # noqa: E402
import nyeomszsz_membership_audit  # noqa: E402


class MembershipReconciliationTests(unittest.TestCase):
    def test_audit_script_passes_on_committed_artifacts(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "nyeomszsz_membership_audit.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_homepage_directory_conflict_is_explicit(self):
        recon = json.loads((ROOT / "data/nyeomszsz/membership-source-reconciliation.json").read_text())
        self.assertEqual(recon["sourceConflictSummary"]["homepageMemberCountryCount"], 17)
        self.assertEqual(recon["sourceConflictSummary"]["directoryNamedOrganizationCount"], 20)
        self.assertEqual(
            set(recon["sourceConflictSummary"]["directoryOnlyRelativeToHomepageCountryList"]),
            {"BA", "IE", "MK"},
        )

    def test_england_and_ireland_jurisdiction_guards(self):
        recon = json.loads((ROOT / "data/nyeomszsz/membership-source-reconciliation.json").read_text())
        by_id = {row["seedId"]: row for row in recon["directoryEntries"]}
        self.assertIn("England", by_id["nyeomszsz-dir-gb-maosz"]["jurisdictionNotes"])
        self.assertIn("Northern Ireland", by_id["nyeomszsz-dir-ie-island"]["jurisdictionNotes"])
        self.assertEqual(by_id["nyeomszsz-dir-gb-maosz"]["memberStatusEvidence"], "disputed")
        self.assertEqual(by_id["nyeomszsz-dir-ie-island"]["memberStatusEvidence"], "disputed")

    def test_seeds_are_not_publishable(self):
        seeds = json.loads((ROOT / "data/nyeomszsz/discovery-seeds.json").read_text())
        for seed in seeds["seeds"]:
            self.assertEqual(seed["lifecycle"], "DISCOVERED")


class BgaAdapterTests(unittest.TestCase):
    def test_default_mode_is_blocked_without_live_fetch(self):
        with tempfile.TemporaryDirectory() as tmp:
            status_path = Path(tmp) / "status.json"
            code = bga_source_adapter.main(["--mode", "BLOCKED_LICENSE_OR_EXPORT", "--status-out", str(status_path)])
            self.assertEqual(code, 0)
            status = json.loads(status_path.read_text())
            self.assertFalse(status["ingestAllowed"])
            self.assertEqual(status["blockerId"], "BLOCKED_LICENSE_OR_EXPORT")
            self.assertEqual(status["counts"]["applicants"], 0)

    def test_approved_file_separates_award_from_unsuccessful_and_redacts_tax(self):
        fixture = ROOT / "tests/fixtures/bga/approved-sample.json"
        with tempfile.TemporaryDirectory() as tmp:
            status_path = Path(tmp) / "status.json"
            out_path = Path(tmp) / "normalized.json"
            code = bga_source_adapter.main(
                [
                    "--mode",
                    "approved_file_import",
                    "--input",
                    str(fixture),
                    "--status-out",
                    str(status_path),
                    "--normalized-out",
                    str(out_path),
                ]
            )
            self.assertEqual(code, 0)
            status = json.loads(status_path.read_text())
            self.assertEqual(status["counts"]["awards"], 1)
            self.assertEqual(status["counts"]["unsuccessful"], 1)
            normalized = json.loads(out_path.read_text())
            blob = json.dumps(normalized)
            self.assertNotIn("12345678-1-42", blob)
            self.assertNotIn("87654321-2-41", blob)
            award_row = next(r for r in normalized["records"] if r["award"])
            fail_row = next(r for r in normalized["records"] if r["unsuccessfulApplication"])
            self.assertIn("not proof of NYEOMSZSZ membership", award_row["organizationCandidate"]["notes"])
            self.assertIsNone(fail_row["award"])

    def test_name_collision_does_not_become_membership(self):
        row = bga_source_adapter.normalize_record(
            {
                "applicantId": "x1",
                "legalName": "Spanyolországi Magyarok Egyesülete",
                "applicationId": "a1",
                "outcome": "awarded",
            }
        )
        self.assertEqual(row["organizationCandidate"]["matchConfidence"], "name-only-unverified")
        self.assertNotEqual(row["decision"]["outcome"], "nyeomszsz-member")


if __name__ == "__main__":
    unittest.main()

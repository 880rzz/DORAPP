#!/usr/bin/env python3
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CountryCoveragePilotTests(unittest.TestCase):
    def test_validator_passes(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "nyeomszsz_country_coverage.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_pilot_batch_has_four_countries_none_complete(self):
        files = sorted((ROOT / "data/nyeomszsz/coverage").glob("??.json"))
        self.assertEqual({p.stem for p in files}, {"at", "es", "nl", "fi"})
        for path in files:
            doc = json.loads(path.read_text())
            self.assertFalse(doc["countryComplete"])
            self.assertEqual(doc["umbrellaSeed"]["lifecycle"], "DISCOVERED")

    def test_es_does_not_invent_madach_canonical_id(self):
        doc = json.loads((ROOT / "data/nyeomszsz/coverage/es.json").read_text())
        self.assertIsNone(doc["umbrellaSeed"]["canonicalEntityId"])

    def test_fi_has_no_organizations_file_yet(self):
        self.assertFalse((ROOT / "data/countries/fi/organizations.json").exists())
        doc = json.loads((ROOT / "data/nyeomszsz/coverage/fi.json").read_text())
        self.assertFalse(doc["countsSnapshot"]["organizationsFilePresent"])


if __name__ == "__main__":
    unittest.main()

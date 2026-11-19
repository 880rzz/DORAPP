"""Contract tests: Ökoszisztéma owns all 29 members' event sources."""
import copy
import json
import unittest
from pathlib import Path

from scripts import sync_member_sources as sync


ROOT = Path(__file__).resolve().parents[1]


class FederationSourcesTests(unittest.TestCase):
    def setUp(self):
        self.registry = json.loads((ROOT / "data/member-event-sources-ecosystem.json").read_text(encoding="utf-8"))

    def test_all_members_have_a_source(self):
        document = sync.validate(self.registry)
        self.assertEqual(document["organizationCount"], 29)
        self.assertEqual(document["sourceCount"], 45)
        self.assertEqual(len(document["members"]), 29)
        self.assertEqual(sum(s["ingestEvents"] for m in document["members"] for s in m["calendarSources"]), 5)

    def test_original_automatic_source_flags_preserved(self):
        organizations = {
            row["id"]: row
            for row in json.loads((ROOT / "data/organizations.json").read_text(encoding="utf-8"))["organizations"]
        }
        for entry in self.registry["members"]:
            org = organizations[entry["organizerId"]]
            self.assertEqual(org.get("calendarSources") or [], entry["calendarSources"])
            self.assertEqual(org.get("eventSources") or [], entry["eventSources"])

    def test_unapproved_http_auto_source_rejected(self):
        bad = copy.deepcopy(self.registry)
        source = bad["members"][0]["calendarSources"][0]
        source["url"] = "http://example.org/events"
        source["ingestEvents"] = True
        with self.assertRaises(ValueError):
            sync.validate(bad)

    def test_duplicate_source_url_rejected(self):
        bad = copy.deepcopy(self.registry)
        sources = bad["members"][0]["calendarSources"]
        sources[1]["url"] = sources[0]["url"]
        with self.assertRaises(ValueError):
            sync.validate(bad)

    def test_wrong_authority_rejected(self):
        bad = copy.deepcopy(self.registry)
        bad["sourceRepository"] = "untrusted/other"
        with self.assertRaises(ValueError):
            sync.validate(bad)


if __name__ == "__main__":
    unittest.main()

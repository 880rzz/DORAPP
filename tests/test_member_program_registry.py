"""Regression tests for the federation-program source-of-truth boundary."""
import copy
import json
import unittest
from pathlib import Path

from scripts import sync_member_programs as sync


class MemberProgramSourceTests(unittest.TestCase):
    def setUp(self):
        self.payload = json.loads(
            (Path(__file__).resolve().parents[1] / "data/member-programs-ecosystem.json").read_text(encoding="utf-8")
        )

    def test_undated_social_leads_are_not_events(self):
        self.assertEqual(len(sync.validate_registry(self.payload)["programCandidates"]), 4)
        self.assertEqual(sync.event_records(self.payload, {}), [])
        self.assertTrue(all(p["status"] == "date-unverified" for p in self.payload["programCandidates"]))

    def test_candidate_with_invented_date_is_rejected(self):
        invalid = copy.deepcopy(self.payload)
        invalid["programCandidates"][0]["startDate"] = "2026-12-06"
        with self.assertRaises(ValueError):
            sync.validate_registry(invalid)

    def test_only_membership_verified_event_can_publish(self):
        verified = copy.deepcopy(self.payload)
        event = {
            "id": "salzung-test-2027-03-01", "memberId": "salzung",
            "organizerId": "salzung", "name": "Teszt rendezvény",
            "verificationStatus": "verified", "startDate": "2027-03-01T18:00:00+01:00",
            "verifiedAt": "2026-11-19T10:00:00+01:00",
            "sourceUrl": "https://example.org/verified-event"
        }
        verified["verifiedEvents"] = [event]
        sync.validate_registry(verified)
        allowed = {"salzung": {"name": "SalzUNG", "state": "salzburg",
                               "city": "Salzburg", "memberships": [{"umbrellaId": "kozponti-szovetseg"}]}}
        out = sync.event_records(verified, allowed)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["sourceType"], "ecosystem-member-programs")
        with self.assertRaises(ValueError):
            sync.event_records(verified, {})


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Fixture-backed evidence lifecycle and entity resolution tests."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import entity_resolution  # noqa: E402
import evidence_lifecycle  # noqa: E402


class EvidenceLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {
            row["id"]: row
            for row in json.loads((ROOT / "tests/fixtures/evidence/lifecycle-cases.json").read_text())["cases"]
        }

    def test_illegal_skip_to_published(self):
        with self.assertRaises(ValueError):
            evidence_lifecycle.transition("DISCOVERED", "PUBLISHED", reason="auto")

    def test_legal_path_to_publishable(self):
        state = "DISCOVERED"
        for nxt in ("QUALIFIED", "FIRST_PARTY_CHECKED", "HUMAN_REVIEWED", "PUBLISHABLE"):
            evidence_lifecycle.transition(state, nxt, reason="gated")
            state = nxt
        self.assertTrue(evidence_lifecycle.is_publishable(state))

    def test_press_only_blocked(self):
        case = self.cases["press-only-candidate"]
        self.assertTrue(evidence_lifecycle.secondary_mention_alone_blocks_verification(case["evidenceSources"]))

    def test_grant_relationships_are_not_membership(self):
        case = self.cases["bga-award-vs-unsuccessful"]
        self.assertTrue(evidence_lifecycle.grant_is_not_membership(case["awardRelationship"]))
        self.assertTrue(evidence_lifecycle.grant_is_not_membership(case["unsuccessfulRelationship"]))
        edge = evidence_lifecycle.RelationshipEdge(
            relationshipType="funding_award",
            fromEntityId="org-1",
            toLabel="BGA programme",
            confidence="medium",
        )
        payload = evidence_lifecycle.serialize_relationship(edge)
        self.assertEqual(payload["relationshipType"], "funding_award")

    def test_dead_website_goes_stale_not_rejected_automatically(self):
        case = self.cases["dead-website-no-auto-dissolution"]
        event = evidence_lifecycle.transition(case["from"], case["to"], reason=case["reason"])
        self.assertEqual(event["to"], "STALE")

    def test_church_self_id_not_auto_publishable(self):
        case = self.cases["church-self-identified"]
        self.assertFalse(evidence_lifecycle.is_publishable(case["entity"]["lifecycle"]))
        self.assertEqual(case["entity"]["religiousTradition"], "Roman Catholic")


class EntityResolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cases = {
            row["id"]: row
            for row in json.loads((ROOT / "tests/fixtures/evidence/lifecycle-cases.json").read_text())["cases"]
        }

    def test_false_positive_cross_country_blocked(self):
        case = self.cases["false-positive-name-collision"]
        match = entity_resolution.find_duplicate(case["candidate"], case["existing"])
        self.assertIsNone(match)

    def test_ie_gb_cross_border_not_merged(self):
        case = self.cases["ie-gb-cross-border"]
        match = entity_resolution.find_duplicate(case["candidate"], case["existing"])
        self.assertIsNone(match)

    def test_double_import_detects_duplicate(self):
        case = self.cases["double-import-zero-dup"]
        match = entity_resolution.find_duplicate(case["candidate"], case["existing"])
        self.assertIsNotNone(match)
        self.assertEqual(match["id"], "finnorszagi-magyarok-egyesulete")

    def test_stable_id_allocation_preserves_existing(self):
        used = {"finnorszagi-magyarok-egyesulete"}
        new_id = entity_resolution.allocate_stable_id("Finnországi Magyarok Egyesülete", used)
        self.assertEqual(new_id, "finnorszagi-magyarok-egyesulete-2")


if __name__ == "__main__":
    unittest.main()

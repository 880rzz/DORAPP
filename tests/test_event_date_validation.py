#!/usr/bin/env python3
"""Regression tests for event date retention and validation."""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from update_events import futureish, source_event_allowed


class EventDateTests(unittest.TestCase):
    def test_source_exclusion_matches_event_urls_and_locations(self):
        cfg = {"excludeRegex": [r"Kastl|csapattabor"]}
        self.assertFalse(source_event_allowed(
            {"name": "CSAPATTÁBOR", "sourceUrl": "https://example.test/events/csapattabor/"},
            cfg,
        ))
        self.assertFalse(source_event_allowed(
            {"name": "Konferencia", "address": "92280 Kastl-Mennersberg"},
            cfg,
        ))
        self.assertTrue(source_event_allowed(
            {"name": "Cserkészfoglalkozás", "address": "4600 Wels"},
            cfg,
        ))

    def test_source_inclusion_still_applies_after_exclusion(self):
        cfg = {"includeRegex": [r"magyar"], "excludeRegex": [r"Németország"]}
        self.assertTrue(source_event_allowed({"name": "Magyar program"}, cfg))
        self.assertFalse(source_event_allowed({"name": "Más program"}, cfg))
        self.assertFalse(source_event_allowed(
            {"name": "Magyar program", "description": "Németország"},
            cfg,
        ))

    def test_invalid_dates_are_not_upcoming(self):
        for value in (None, "", "not-a-date", "2026-99-99", {}):
            with self.subTest(value=value):
                self.assertFalse(futureish(value))

    def test_expired_event_is_not_upcoming(self):
        self.assertFalse(futureish((datetime.now(timezone.utc) - timedelta(days=2)).isoformat()))

    def test_future_event_is_upcoming(self):
        self.assertTrue(futureish((datetime.now(timezone.utc) + timedelta(days=2)).isoformat()))

    def test_date_only_event_is_visible_during_its_day(self):
        self.assertTrue(futureish(datetime.now(timezone.utc).date().isoformat()))

    def test_end_date_takes_precedence(self):
        now = datetime.now(timezone.utc)
        self.assertTrue(futureish((now - timedelta(hours=1)).isoformat(), (now + timedelta(hours=1)).isoformat()))


if __name__ == "__main__":
    unittest.main()

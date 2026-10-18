#!/usr/bin/env python3
"""Regression tests for event date retention and validation."""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from update_events import futureish


class EventDateTests(unittest.TestCase):
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

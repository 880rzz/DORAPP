#!/usr/bin/env python3
"""Regression coverage for generated country event cards."""
import importlib.util
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location("generate_country_pages",ROOT/"scripts/generate_country_pages.py")
GEN=importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


class CountryEventCardTests(unittest.TestCase):
    def setUp(self):
        self.event={
            "id":"test-event", "name":"Teszt esemény", "startDate":"2026-12-01T18:00:00+01:00",
            "state":"madrid", "city":"Madrid", "venue":"Kultúrház", "organizer":"MADACH",
            "programCategories":["kultura"], "description":"Tényszerű rövid ismertető.",
            "sourceUrl":"https://example.org/event",
        }

    def test_card_contains_metadata_detail_link_and_separate_source(self):
        html=GEN.event_cards([self.event],{})
        for value in ("Teszt esemény","datetime=", "Kultúrház", "Madrid", "MADACH",
                      "Tényszerű rövid ismertető.", 'href="events/test-event.html"',
                      'href="https://example.org/event"', 'class="event-card-main"'):
            self.assertIn(value,html)
        self.assertEqual(html.count("<a "),2)

    def test_missing_optional_values_are_not_invented(self):
        event={"id":"sparse","name":"Ismeretlen adatú program","state":"madrid"}
        html=GEN.event_cards([event],{})
        self.assertIn("Magyar közösségi program",html)
        self.assertNotIn("<time",html)
        self.assertNotIn("Eredeti forrás",html)
        self.assertNotIn("ismeretlen helyszín",html.casefold())

    def test_description_is_html_escaped(self):
        self.event["description"]="<script>alert(1)</script>"
        html=GEN.event_cards([self.event],{})
        self.assertNotIn("<script>",html)
        self.assertIn("&lt;script&gt;",html)


if __name__=="__main__":
    unittest.main()

#!/usr/bin/env python3
"""Regression tests for evidence-bound global diaspora promotions."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent

def load_script(filename, name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class GlobalResearchIntegrityTests(unittest.TestCase):
    def test_news_publisher_schema_is_not_first_party_organization_evidence(self):
        verifier = load_script("verify_first_party_sites.py", "verify_first_party_sites_test")
        original_fetch = verifier.fetch
        def fake_fetch(url):
            if url.endswith("news"):
                name = "Example News Publisher"
            else:
                name = "Sydney Hungarian House"
            document = (
                "<html><head><script type=\"application/ld+json\">"
                + json.dumps({"@type":"Organization","name":name,"address":{
                    "addressLocality":"Sydney","addressCountry":"AU"}})
                + "</script></head><body>Sydney Hungarian House "
                  "Hungarian cultural association in Australia</body></html>"
            )
            return url, document, "text/html"
        verifier.fetch = fake_fetch
        try:
            country = {"iso2":"au","name":{"en":"Australia"}}
            unrelated = {"country":"au","title":"Sydney Hungarian House",
                         "firstPartyCandidates":["https://example.com/news"]}
            self.assertIsNone(verifier.verify_item(unrelated,country,"2026-10-15T00:00:00+00:00"))
            self.assertEqual(unrelated["firstPartyStatus"],"no-strong-first-party-proof")
            confirmed = {"country":"au","title":"Sydney Hungarian House",
                         "firstPartyCandidates":["https://example.com/official"]}
            result = verifier.verify_item(confirmed,country,"2026-10-15T00:00:00+00:00")
            self.assertIsNotNone(result)
            self.assertGreaterEqual(result["verificationScore"],7)
            self.assertEqual(result["city"],"Sydney")
        finally:
            verifier.fetch = original_fetch

    def test_promotion_rejects_unverified_and_reopens_negative_country(self):
        promoter = load_script("promote_verified_entities.py", "promote_verified_entities_test")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root/"global.json").write_text(json.dumps({"countries":[
                {"iso2":"zz","researchStatus":"verified-zero"}]}),encoding="utf-8")
            def candidate(name,path,score,method):
                return {
                    "country":"zz","name":name,"website":"https://example.org/"+path,
                    "city":"Test City","addressCountry":"ZZ","entityType":"Organization",
                    "verificationScore":score,"verificationMethod":method,
                    "verifiedAt":"2026-10-15T00:00:00+00:00"
                }
            inputs = [
                candidate("Unverified Candidate","bad",2,"Wikipedia alone"),
                candidate("Verified Hungarian House","house",7,"first-party HTML + JSON-LD organization + country match"),
                candidate("Verified Hungarian School","school",7,"first-party HTML + JSON-LD organization + country match")
            ]
            (root/"promotion-ready.json").write_text(json.dumps({"items":inputs}),encoding="utf-8")
            old_data,old_ready=promoter.DATA,promoter.READY
            promoter.DATA,promoter.READY=root,root/"promotion-ready.json"
            try:
                promoter.main()
            finally:
                promoter.DATA,promoter.READY=old_data,old_ready
            orgs=json.loads((root/"countries"/"zz"/"organizations.json").read_text(encoding="utf-8"))["organizations"]
            self.assertEqual(len(orgs),2)
            self.assertNotIn("Unverified Candidate",[org["name"] for org in orgs])
            self.assertEqual({org["website"] for org in orgs},{"https://example.org/house","https://example.org/school"})
            country=json.loads((root/"global.json").read_text(encoding="utf-8"))["countries"][0]
            self.assertEqual(country["researchStatus"],"researching")
            self.assertTrue(country["verifiedZeroInvalidatedByEntity"])
            self.assertTrue(country["verifiedZeroInvalidatedAt"])

if __name__=="__main__":
    unittest.main()

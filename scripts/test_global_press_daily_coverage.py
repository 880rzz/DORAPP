#!/usr/bin/env python3
"""Offline regression for full daily press discovery and review-only publication."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "discover_global_press.py"

def load_press():
    spec = importlib.util.spec_from_file_location("global_press_discovery_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

class GlobalPressCoverageTests(unittest.TestCase):
    def test_all_verified_organizations_attempted_and_candidates_never_published(self):
        press = load_press()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            orgdir = root / "countries" / "zz"
            orgdir.mkdir(parents=True)
            organizations = [
                {"id":f"org-{i}","name":f"Test Hungarian House {i}","website":f"https://test-{i}.org/","profileVerifiedAt":"2026-10-15"}
                for i in range(30)
            ]
            organizations.append({"id":"unverified","name":"Unverified House","website":"https://unverified.test/","status":"candidate","profileVerifiedAt":"2026-10-15"})
            orgdir.joinpath("organizations.json").write_text(json.dumps({"organizations":organizations}),encoding="utf-8")
            output = root / "press-queue.json"
            original=(press.DATA,press.OUT,press.discover_one)
            queried=[]
            def fake_discover(organization):
                queried.append(organization[1])
                if organization[1] == "org-7":
                    return organization, [], "TimeoutError"
                return organization, [{
                    "country":organization[0], "organizationId":organization[1],
                    "organizationName":organization[2], "title":"Possible press article",
                    "url":f"https://news.google.com/{organization[1]}",
                    "status":"candidate-needs-identity-and-source-verification",
                    "discoverySource":"Google News RSS"
                }], None
            press.DATA,press.OUT,press.discover_one=root,output,fake_discover
            try:
                press.main()
            finally:
                press.DATA,press.OUT,press.discover_one=original
            result=json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(result["organizationsAttempted"],30)
            self.assertEqual(result["organizationsChecked"],29)
            self.assertEqual(result["organizationsFailed"],1)
            self.assertEqual(len(result["candidates"]),29)
            self.assertNotIn("unverified",queried)
            self.assertEqual(len(set(queried)),30)
            self.assertTrue(all(c["status"].startswith("candidate-") for c in result["candidates"]))
            self.assertEqual(result["errors"][0]["organizationId"],"org-7")

if __name__=="__main__":
    unittest.main()

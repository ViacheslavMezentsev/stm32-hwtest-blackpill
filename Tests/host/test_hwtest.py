import json
import os
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
from unittest.mock import patch

from hwtest.collect import collect, trace
from hwtest.processes import probe_lock
from hwtest.openocd import load_stand
from hwtest.reports import write_reports
from hwtest.runner import ROOT, run


class HostTests(unittest.TestCase):
    def setUp(self):
        directory = ROOT / "build/host-tests"
        directory.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=directory)
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)

    def test_collection_does_not_execute_code(self):
        (self.directory / "test_one.py").write_text(
            'raise RuntimeError("must not import")\n@case("HW_ONE", labels=("gpio",))\ndef one(t): pass\n')
        cases = collect(self.directory)
        self.assertEqual(cases[0]["id"], "HW_ONE")

    def test_duplicate_and_dynamic_metadata_rejected(self):
        p = self.directory / "test_bad.py"
        for source in ('@case(make_id())\ndef one(t): pass\n',
                       '@case("HW_ONE")\ndef one(t): pass\n@case("HW_ONE")\ndef two(t): pass\n'):
            p.write_text(source)
            with self.assertRaises(ValueError):
                collect(self.directory)

    def test_trace_rejects_missing_and_duplicate_requirements(self):
        p = self.directory / "requirements.md"
        for content in ("## HW_OTHER\n", "## HW_ONE\n## HW_ONE\n"):
            p.write_text(content)
            with self.assertRaises(ValueError):
                trace([{"id": "HW_ONE"}], p)

    def test_stand_rejects_misspelled_flash_policy(self):
        path = self.directory / "stand.toml"
        path.write_text('[probe]\nbackend="openocd"\nserial="TEST"\nflash_policy="verify-only"\n')
        with self.assertRaisesRegex(ValueError, "Unknown probe setting"):
            load_stand(path)

    def test_reports_distinguish_assertion_and_infrastructure(self):
        for status, tag in (("PASS", None), ("FAIL", "failure"), ("ERROR", "error")):
            report = dict(id="HW_ONE", status=status, duration_s=1.25, error='expected <x> & "y"')
            write_reports(self.directory, report)
            root = ET.parse(self.directory / "junit.xml").getroot()
            case = root.find("testcase")
            self.assertEqual(root.attrib["failures"], str(int(status == "FAIL")))
            self.assertEqual(root.attrib["errors"], str(int(status == "ERROR")))
            if tag:
                self.assertIn(report["error"], case.find(tag).text)
            self.assertEqual(json.loads((self.directory / "result.json").read_text()), report)

    def test_missing_stand_is_error_with_reports(self):
        session = dict(out=str(self.directory), stand=str(self.directory / "absent.toml"))
        with patch.dict(os.environ, {"HWTEST_STAND": ""}):
            code = run(session, {"id": "HW_ONE", "timeout_s": 1})
        self.assertEqual(code, 2)
        report = json.loads(next(self.directory.glob("*/result.json")).read_text())
        self.assertEqual(report["status"], "ERROR")
        self.assertTrue(next(self.directory.glob("*/junit.xml")).exists())

    @unittest.skipUnless(os.name == "nt", "Windows lock")
    def test_probe_lock_rejects_concurrent_owner_and_releases(self):
        with probe_lock(self.directory, "TESTSERIAL"):
            with self.assertRaises(RuntimeError):
                with probe_lock(self.directory, "TESTSERIAL"):
                    self.fail("Concurrent ownership")
        with probe_lock(self.directory, "TESTSERIAL"):
            pass


if __name__ == "__main__":
    unittest.main()

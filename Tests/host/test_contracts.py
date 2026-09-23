import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from hwtest.collect import collect
from hwtest.contracts import select_contracts
from hwtest.runner import ROOT, execute


class ContractTests(unittest.TestCase):
    def setUp(self):
        base = ROOT / "build/host-tests"
        base.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=base)
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.registry = ROOT / "profiles/f103/Tests/contracts.json"

    def test_literal_selection_does_not_import_tests(self):
        p = self.directory / "test_one.py"
        p.write_text('raise RuntimeError("no import")\n@case("HW_ONE", contracts=("rcc_error",))\ndef one(t): pass\n')
        self.assertEqual(collect(self.directory)[0]["contracts"], ["rcc_error"])
        for expression in ('("unknown", "unknown")', 'get_contracts()', '"rcc_error"'):
            p.write_text('@case("HW_ONE", contracts=' + expression + ')\ndef one(t): pass\n')
            with self.assertRaises(ValueError):
                collect(self.directory)

    def test_missing_and_unreviewed_source_fail_closed(self):
        review = json.loads(self.registry.read_text())["contracts"]["rcc_osc_null"]["source_reviews"][0]
        for manifest in (None, {"inputs": []}, {"inputs": [{"file": review["file"], "sha256": "changed"}]}):
            with self.assertRaisesRegex(ValueError, "Reviewed source mismatch"):
                select_contracts(self.registry, ["rcc_osc_null"], manifest)
        selected = select_contracts(self.registry, ["rcc_osc_null"], {"inputs": [review]})
        self.assertEqual(list(selected["contracts"]), ["rcc_osc_null"])
        with self.assertRaises(KeyError):
            select_contracts(self.registry, ["typo"], None)

    def test_unrequested_contracts_do_not_require_registry(self):
        self.assertEqual(select_contracts(self.directory / "absent", [], None)["contracts"], {})

    def test_bad_preflight_stops_before_debug_server(self):
        elf = self.directory / "firmware.elf"
        elf.write_bytes(b"fixture")
        out = self.directory / "run"
        out.mkdir()
        session = dict(elf=str(elf), profile=str(ROOT / "profiles/f103/target.toml"), gdb="unused.exe")
        report = {}
        def fail_preflight(*args, **kwargs):
            (out / "contract-result.json").write_text(json.dumps(dict(status="ERROR", errors=["wrong signature"])))
            return type("Process", (), {"returncode": 2})()
        with patch("hwtest.runner.subprocess.run", side_effect=fail_preflight) as run, patch("hwtest.runner.subprocess.Popen") as popen:
            execute(session, {"contracts": ["rcc_error"]}, {}, out, report, 10, {})
        self.assertEqual(run.call_count, 1)
        popen.assert_not_called()
        self.assertEqual(report["status"], "ERROR")
        self.assertEqual(report["contracts"]["status"], "ERROR")
        self.assertFalse((out / "server.log").exists())

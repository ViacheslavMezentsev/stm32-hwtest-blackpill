"""Explicit F401 firmware experiment on the marked-F401 board reporting DEV_ID 0x431.

This does not validate a standard F401. Firmware, manifest and test expectations
remain unchanged; only the runtime identity expectation is replaced, and recorded.
"""
import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from hwtest.backends import load_stand
from hwtest.collect import collect
from hwtest.compatibility import runtime_manifest
from hwtest.processes import probe_lock
from hwtest.profile import load_profile
from hwtest.reports import CODES, write_reports
from hwtest.runner import execute, local_directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stand', type=Path, required=True)
    parser.add_argument('--test', action='append', required=True,
                        help='Case ID; repeat, or use ALL for all F401 cases')
    args = parser.parse_args()
    session = json.loads((ROOT / 'build/f401cc-debug-hwtest/hwtest/session.json').read_text())
    original = load_profile(session['profile'])
    if (Path(session['profile']).resolve() != ROOT / 'profiles/f401cc/target.toml'
            or original['mcu'] != 'STM32F401CCU6'
            or original['identity']['value'] != 0x423
            or original['flash_size'] != 262144):
        raise ValueError('Experiment requires the original F401CC profile')
    stand = load_stand(args.stand)
    if stand['backend'] != 'openocd':
        raise ValueError('This experiment is limited to the confirmed OpenOCD stand')
    cases = {case['id']: case for case in collect(session['tests'])}
    selected = list(cases) if args.test == ['ALL'] else args.test
    if any(name not in cases for name in selected):
        raise ValueError('Unknown case ID')
    runtime = deepcopy(original)
    runtime['identity']['value'] = 0x431
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    base = local_directory(ROOT / 'build/f401-marking-experiment' / stamp)
    results = []
    for name in selected:
        case = cases[name]
        out = local_directory(base / name)
        started = time.monotonic()
        report = dict(id=name, status='ERROR', checks=[], started_utc=stamp,
                      backend=stand['backend'], profile=runtime,
                      experiment=dict(name='f401-marking-on-id431',
                          marked_mcu='STM32F401CCU6', standard_profile_validation=False,
                          original_profile=original, identity_override='0x423 -> 0x431',
                          flash_kib_observed_before_experiment=256,
                          limitation='Only this specimen; silicon identity unresolved'))
        try:
            with probe_lock(ROOT, stand['serial']):
                execute(session, case, stand, out, report, case['timeout_s'], runtime)
        except BaseException:
            report.update(status='ERROR', error=traceback.format_exc())
        log = out / 'server.log'
        report['compatibility'] = runtime_manifest(report, log.read_text(errors='replace') if log.exists() else '')
        report['duration_s'] = round(time.monotonic() - started, 3)
        write_reports(out, report)
        results.append(dict(id=name, status=report['status'], report=str(out / 'result.json')))
        print(f"EXPERIMENT {name}: {report['status']} ({out})", flush=True)
        # Stop for infrastructure/fault errors; assertion failures remain evidence.
        if report['status'] == 'ERROR':
            break
    (base / 'summary.json').write_text(json.dumps(results, indent=2) + '\n')
    return max(CODES[item['status']] for item in results)


if __name__ == '__main__':
    raise SystemExit(main())

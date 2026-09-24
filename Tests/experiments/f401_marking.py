"""Legacy entry point: delegates to the standard runner without identity overrides.

Prefer cmake --build --preset f401cc-check-hw. Historical experiment results
and the former implementation remain in Git history.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from hwtest.collect import collect
from hwtest.runner import run


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stand', type=Path, required=True)
    parser.add_argument('--test', action='append', required=True)
    args = parser.parse_args()
    session = json.loads((ROOT / 'build/f401cc-debug-hwtest/hwtest/session.json').read_text())
    cases = {case['id']: case for case in collect(session['tests'])}
    selected = list(cases) if args.test == ['ALL'] else args.test
    if any(name not in cases for name in selected):
        raise ValueError('Unknown case ID')
    print('Legacy entry point: standard runner, no identity override')
    code = 0
    for name in selected:
        result = run(session, cases[name], args.stand)
        code = max(code, result)
        if result == 2:
            break
    return code


if __name__ == '__main__':
    raise SystemExit(main())

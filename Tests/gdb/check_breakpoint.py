"""Run with gdb-py -nx -batch -ex 'source Tests/gdb/check_breakpoint.py'. No board needed."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
import gdb
from stm32_gdbtest.target import Target
gdb.execute("set breakpoint pending off")
t = Target({"checks": []}, {"breakpoint_limit": 6})
try:
    try:
        t.breakpoint("__hwtest_missing_symbol__")
    except RuntimeError as exc:
        assert "absent from ELF" in str(exc), str(exc)
        assert not any(bp.is_valid() for bp in t.owned)
        print("PASS: missing symbol rejected and pending breakpoint deleted")
    else:
        raise AssertionError("Missing symbol accepted")
finally:
    t.close()

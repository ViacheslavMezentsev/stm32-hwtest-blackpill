"""Project entry point using the pinned Git submodule."""
from pathlib import Path
import sys

sys.dont_write_bytecode = True
module = Path(__file__).resolve().parents[1] / "modules/stm32-gdbtest"
if not (module / "stm32_gdbtest/cli.py").is_file():
    raise SystemExit("Initialize dependency: git submodule update --init --recursive")
sys.path.insert(0, str(module))
from stm32_gdbtest.cli import main

try:
    raise SystemExit(main())
except (ValueError, KeyError, OSError) as exc:
    print(f"ERROR: {exc}", file=sys.stderr)
    raise SystemExit(2)

"""Run dependency host tests in an isolated project build copy, never in modules/."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
module = ROOT / "modules/stm32-gdbtest"
files = subprocess.check_output(["git", "-c", "safe.directory=" + module.as_posix(),
    "-C", str(module), "ls-files", "stm32_gdbtest", "Tests/host", "Tests/fixtures",
    "examples/minimal-consumer"], text=True, timeout=15).splitlines()
if not files:
    raise SystemExit("Initialize dependency: git submodule update --init --recursive")
copy = ROOT / "build/module-host" / uuid.uuid4().hex
copy.mkdir(parents=True)
for name in files:
    source = module / name
    destination = copy / name
    if not source.resolve().is_relative_to(module.resolve()) or not destination.resolve().is_relative_to(copy):
        raise ValueError("Invalid dependency path")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)
temp = copy / "build/tmp"
temp.mkdir(parents=True)
env = os.environ.copy()
env.update(TEMP=str(temp), TMP=str(temp), PYTHONDONTWRITEBYTECODE="1")
env.pop("PYTHONPATH", None)
with (copy / "build/host.log").open("wb") as log:
    result = subprocess.run([sys.executable, "-B", "-m", "unittest", "discover", "-s",
        "Tests/host", "-v"], cwd=copy, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=30)
print((copy / "build/host.log").read_text(encoding="utf-8", errors="replace"))
print("Host evidence: " + str(copy / "build/host.log"))
raise SystemExit(result.returncode)

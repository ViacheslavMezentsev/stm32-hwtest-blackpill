"""Consumer-side ELF/manifest/contracts check. Never starts a debug server."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules/stm32-gdbtest"
sys.path.insert(0, str(MODULE))
from stm32_gdbtest.build_manifest import load_verified
from stm32_gdbtest.collect import collect, trace
from stm32_gdbtest.contracts import select_contracts
from stm32_gdbtest.profile import load_profile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", type=Path, required=True)
    args = parser.parse_args()
    session_path = args.session.resolve()
    if not session_path.is_relative_to(ROOT / "build"):
        raise ValueError("Session must be inside this project's build directory")
    session = json.loads(session_path.read_text(encoding="utf-8"))
    profile_path = Path(session["profile"]).resolve()
    profile = load_profile(profile_path)
    tests = collect(session["tests"])
    trace(tests, profile_path.parent / "Tests/requirements.md")
    out = session_path.parent / "offline"
    out.mkdir(exist_ok=True)
    snapshot = out / "firmware.elf"
    snapshot.write_bytes(Path(session["elf"]).read_bytes())
    digest = hashlib.sha256(snapshot.read_bytes()).hexdigest()
    manifest = load_verified(session["build_manifest"], digest, profile_path)
    names = sorted({name for test in tests for name in test.get("contracts", [])})
    if not names:
        raise ValueError("No contracts requested; no ELF compatibility claim is possible")
    selected = select_contracts(profile_path.parent / "Tests/contracts.json", names, manifest)
    request, result = out / "request.json", out / "result.json"
    result.unlink(missing_ok=True)
    request.write_text(json.dumps(dict(elf=str(snapshot), result=str(result), selected=selected)),
                       encoding="utf-8")
    env = os.environ.copy()
    env.update(STM32_GDBTEST_CONTRACT_REQUEST=str(request), PYTHONDONTWRITEBYTECODE="1",
               TEMP=str(out), TMP=str(out))
    command = [session["gdb"], "-nx", "-batch", "-q", "-iex", "set auto-load off",
               str(snapshot), "-x", str(MODULE / "stm32_gdbtest/contract_preflight.py")]
    with (out / "gdb.log").open("wb") as log:
        process = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, env=env,
                                 timeout=30, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    report = json.loads(result.read_text(encoding="utf-8"))
    if (process.returncode or report.get("status") != "PASS"
            or report.get("elf_sha256") != digest or report.get("connection_attempted") is not False):
        raise RuntimeError(f"Offline contract check failed: {result}")
    print(f"PASS {profile['name']}: {len(tests)} collected tests, {len(names)} contracts; "
          f"ELF {digest}; no connection attempted")


if __name__ == "__main__":
    main()

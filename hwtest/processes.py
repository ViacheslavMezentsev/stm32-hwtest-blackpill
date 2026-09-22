"""Bounded process lifetime and repository-local locking on Windows."""

from contextlib import contextmanager
import hashlib
import os
from pathlib import Path
import subprocess


FLAGS = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


def stop_tree(process):
    if process is None or process.poll() is not None:
        return
    result = subprocess.run(["taskkill", "/PID", str(process.pid), "/T", "/F"],
                            capture_output=True, timeout=10, creationflags=FLAGS)
    if result.returncode and process.poll() is None:
        process.kill()
    process.wait(timeout=5)


@contextmanager
def probe_lock(root, serial):
    import msvcrt
    directory = Path(root) / "build/probe-locks"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / (hashlib.sha256(serial.encode()).hexdigest() + ".lock")
    with path.open("a+b") as lock:
        try:
            if os.fstat(lock.fileno()).st_size == 0:
                lock.write(b"0")
                lock.flush()
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        except OSError as exc:
            raise RuntimeError("Probe already owned by another runner in this checkout") from exc
        try:
            yield
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)

"""Server dialects: shared test scenarios never contain vendor monitor commands."""

from pathlib import Path
import re
import shutil
import tomllib

from hwtest import openocd


def load_stand(path):
    data = tomllib.loads(Path(path).read_text(encoding="utf-8"))["probe"]
    if data.get("backend") == "openocd":
        return openocd.load_stand(path)
    if data.get("backend") != "stlink":
        raise ValueError("Supported backends: openocd, stlink")
    if set(data) - {"backend", "serial", "executable", "programmer_dir", "speed_khz", "flash"}:
        raise ValueError("Unknown probe setting; check the stand TOML")
    if not re.fullmatch(r"[A-Za-z0-9]+", data.get("serial", "")):
        raise ValueError("Set an alphanumeric ST-Link serial in the local stand file")
    speed = data.get("speed_khz", 1000)
    if type(speed) is not int or not 1 <= speed <= 4000:
        raise ValueError("speed_khz must be an integer between 1 and 4000")
    policy = data.get("flash", "if-different")
    if policy not in ("if-different", "verify-only"):
        raise ValueError("flash must be if-different or verify-only")
    executable = shutil.which(data.get("executable", "ST-LINK_gdbserver.exe"))
    if not executable:
        raise FileNotFoundError("ST-LINK GDB Server executable not found")
    programmer = Path(data.get("programmer_dir", ""))
    if not programmer.is_absolute() or not (programmer / "STM32_Programmer_CLI.exe").is_file():
        raise ValueError("programmer_dir must contain STM32_Programmer_CLI.exe")
    return dict(data, executable=executable, programmer_dir=str(programmer),
                speed_khz=speed, flash=policy)


def server_spec(stand, port, profile, out):
    if stand["backend"] == "openocd":
        return dict(command=openocd.server_command(stand, port, profile),
                    ready=f"Listening on port {port} for gdb connections",
                    reset_halt=profile["reset_halt"],
                    finish=[profile["reset_run"], "disconnect"])
    if stand["backend"] != "stlink":
        raise ValueError("Unsupported backend")
    return dict(
        command=[stand["executable"], "-d", "-e", "-g", "-p", str(port),
                 "-i", stand["serial"], "--frequency", str(stand["speed_khz"]),
                 "-cp", stand["programmer_dir"], "--temp-path", str(out),
                 "-f", str(out / "stlink.log"), "-l", "31", "-s"],
        ready="Waiting for debugger connection",
        reset_halt="monitor reset",
        finish=["monitor reset", "detach"],
    )

"""Android Debug Bridge helpers for Laytix."""

import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path


class AdbError(RuntimeError):
    """Raised when an ADB command cannot be completed."""


def find_adb() -> Path | None:
    """Return the adb executable path if it is available."""

    adb_path = shutil.which("adb")
    return Path(adb_path) if adb_path else None


def list_devices() -> list[str]:
    """Return connected Android device ids reported by ADB."""

    adb_path = find_adb()
    if adb_path is None:
        raise AdbError("ADB was not found. Install Android Platform Tools and make sure adb is available in PATH.")

    completed = subprocess.run(
        [str(adb_path), "devices"],
        check=False,
        capture_output=True,
        text=True,
    )

    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip()
        raise AdbError(f"ADB devices command failed. {message}")

    devices = []
    for line in completed.stdout.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])

    return devices


def capture_screenshot(output: Path | str) -> Path:
    """Capture a PNG screenshot from the active Android device."""

    adb_path = find_adb()
    if adb_path is None:
        raise AdbError("ADB was not found. Install Android Platform Tools and make sure adb is available in PATH.")

    devices = list_devices()
    if not devices:
        raise AdbError("No Android devices found. Start an emulator or connect a device with USB debugging enabled.")

    output_path = _resolve_output_path(Path(output))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    completed = subprocess.run(
        [str(adb_path), "exec-out", "screencap", "-p"],
        check=False,
        capture_output=True,
    )

    if completed.returncode != 0:
        message = completed.stderr.decode(errors="replace").strip()
        raise AdbError(f"ADB screenshot capture failed. {message}")

    if not completed.stdout.startswith(b"\x89PNG"):
        raise AdbError("ADB screenshot capture did not return a PNG image.")

    output_path.write_bytes(completed.stdout)
    return output_path


def _resolve_output_path(output: Path) -> Path:
    if output.suffix.lower() == ".png":
        return output

    timestamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    return output / f"screenshot-{timestamp}.png"

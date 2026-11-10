"""Find or build the native helper (``pcmtap-helper``) that does the real-time capture.

The helper is a small Swift program shipped as source (``pcmtap/helper/``) and
compiled with ``swiftc`` on first use into :func:`helper_dir`, under a name that
carries the source's hash, so a new pcmtap version rebuilds it and an unchanged one
never does. macOS keys the *System Audio Recording* permission to the binary, so a
rebuild means granting it once more; keeping the build stable is the point.

Set ``$PCMTAP_HELPER`` to use a helper binary built elsewhere.
"""

from __future__ import annotations

import hashlib
import os
import platform
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

HELPER_SOURCE_DIR = Path(__file__).parent / "helper"
HELPER_SOURCE = HELPER_SOURCE_DIR / "pcmtap_helper.swift"
HELPER_PLIST = HELPER_SOURCE_DIR / "Info.plist"
HELPER_SIGNING_ID = "com.thorwhalen.pcmtap-helper"
#: Process taps arrived in macOS 14.2.
MIN_MACOS = (14, 2)


class HelperUnavailable(RuntimeError):
    """The native helper cannot be found or built on this machine."""


def helper_dir() -> Path:
    """Where built helpers live: ``$PCMTAP_DATA_DIR/bin`` or ``~/.local/share/pcmtap/bin``."""
    root = os.environ.get("PCMTAP_DATA_DIR") or "~/.local/share/pcmtap"
    return Path(root).expanduser() / "bin"


def _source_hash() -> str:
    h = hashlib.sha256()
    for path in (HELPER_SOURCE, HELPER_PLIST):
        h.update(path.read_bytes())
    return h.hexdigest()[:12]


def macos_version() -> tuple[int, ...] | None:
    """This Mac's version as a tuple, or ``None`` when not on macOS."""
    if platform.system() != "Darwin":
        return None
    return tuple(int(p) for p in platform.mac_ver()[0].split(".") if p.isdigit())


def _require_platform() -> None:
    version = macos_version()
    if version is None:
        raise HelperUnavailable(
            f"pcmtap uses Core Audio process taps, which exist only on macOS (this is "
            f"{platform.system()})."
        )
    if version < MIN_MACOS:
        raise HelperUnavailable(
            f"pcmtap needs macOS {'.'.join(map(str, MIN_MACOS))} or later for process "
            f"taps; this Mac runs {'.'.join(map(str, version))}."
        )


def build_helper(target: Path) -> Path:
    """Compile the helper into ``target`` with ``swiftc`` and sign it (ad hoc)."""
    swiftc = shutil.which("swiftc")
    if swiftc is None:
        raise HelperUnavailable(
            "Building pcmtap's helper needs the Swift compiler. Install the Xcode "
            "command line tools: xcode-select --install"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    tmp = target.with_suffix(".building")
    cmd = [
        swiftc, "-O", str(HELPER_SOURCE), "-o", str(tmp),
        "-Xlinker", "-sectcreate", "-Xlinker", "__TEXT",
        "-Xlinker", "__info_plist", "-Xlinker", str(HELPER_PLIST),
    ]  # fmt: skip
    run = subprocess.run(cmd, capture_output=True, text=True)
    if run.returncode != 0:
        raise HelperUnavailable(f"swiftc failed to build the helper:\n{run.stderr}")
    subprocess.run(
        ["codesign", "-f", "-s", "-", "-i", HELPER_SIGNING_ID, str(tmp)],
        capture_output=True,
        check=False,
    )
    tmp.replace(target)
    return target


@lru_cache(maxsize=1)
def helper_path(*, rebuild: bool = False) -> Path:
    """The helper binary, building it first if this version has not been built yet."""
    if env := os.environ.get("PCMTAP_HELPER"):
        path = Path(env).expanduser()
        if not path.is_file():
            raise HelperUnavailable(f"$PCMTAP_HELPER points at nothing: {path}")
        return path
    _require_platform()
    target = helper_dir() / f"pcmtap-helper-{_source_hash()}"
    if rebuild or not target.is_file():
        build_helper(target)
    return target

"""``check_requirements``: what this machine still needs for pcmtap, and how to get it."""

from __future__ import annotations

import shutil

from pcmtap.helper_build import MIN_MACOS, HelperUnavailable, helper_path, macos_version


def check_requirements(*, request: bool = False) -> list[str]:
    """Problems (each with its remedy) that stop pcmtap from recording; empty means ready.

    With ``request=True``, a missing permission is asked for (a dialog on the Mac).
    """
    from pcmtap.tap import permission_status, request_permission

    problems = []
    version = macos_version()
    if version is None:
        return ["pcmtap works only on macOS (Core Audio process taps)."]
    if version < MIN_MACOS:
        return [f"macOS {'.'.join(map(str, MIN_MACOS))}+ is needed for process taps."]
    try:
        helper_path()
    except HelperUnavailable as exc:
        return [str(exc)]
    status = permission_status()
    if status != "granted" and request:
        status = "granted" if request_permission() else permission_status()
    if status != "granted":
        problems.append(
            f"System Audio Recording permission is {status}: run `pcmtap permission "
            "--request` (a dialog appears on the Mac) or allow 'pcmtap-helper' in System "
            "Settings > Privacy & Security > Screen & System Audio Recording."
        )
    if shutil.which("ffmpeg") is None:
        problems.append(
            "Optional: ffmpeg (brew install ffmpeg) to write formats other than .wav."
        )
    return problems

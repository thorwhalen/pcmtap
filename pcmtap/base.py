"""``record``: what an app (or the whole Mac) plays, into an audio file, in one call."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Sequence

from pcmtap.stream import (
    DEFAULT_SILENCE_THRESHOLD,
    peak,
    skip_silence,
    take_seconds,
    take_until,
)
from pcmtap.tap import PermissionMissing, Tap, permission_status
from pcmtap.write import write_audio

#: Seconds of exact digital silence after which a missing permission is suspected.
SILENCE_CHECK_S = 3.0


def _guard_permission(chunks, fmt, *, check_s: float = SILENCE_CHECK_S):
    """Pass chunks through; if the first ``check_s`` seconds are exactly zero and the
    permission is not granted, raise :class:`PermissionMissing` (a tap without the
    permission delivers zeros, not an error)."""
    needed = fmt.frames_to_bytes(fmt.seconds_to_frames(check_s))
    seen, held = 0, []
    for chunk in chunks:
        if seen is None:
            yield chunk
            continue
        held.append(chunk)
        seen += len(chunk)
        if peak(chunk) > 0.0:
            yield from held
            held, seen = [], None
        elif seen >= needed:
            if permission_status() != "granted":
                raise PermissionMissing(
                    "The tap returns only silence and macOS has not granted System Audio "
                    "Recording to pcmtap's helper. Run `pcmtap permission --request` "
                    "and allow it, or enable it in System Settings > Privacy & Security "
                    "> Screen & System Audio Recording."
                )
            yield from held
            held, seen = [], None
    yield from held


def record(
    path: str | Path,
    seconds: float | None = None,
    *,
    app: str | Sequence[str] | None = None,
    pid: int | Sequence[int] | None = None,
    exclude: bool = False,
    mute: bool = False,
    skip_leading_silence: bool = False,
    silence_threshold: float = DEFAULT_SILENCE_THRESHOLD,
    silence_timeout_s: float | None = 30.0,
    until: Callable[[], bool] | None = None,
    bitrate: str | None = None,
) -> Path:
    """Record what ``app`` (default: every process) plays into ``path``; returns the path.

    >>> record("out.wav", 10, app="Spotify")  # doctest: +SKIP

    Args:
        path: Output file; ``.wav`` needs nothing, other formats need ffmpeg.
        seconds: How long to record (of sound, if ``skip_leading_silence``). With
            neither ``seconds`` nor ``until``, records until interrupted (Ctrl-C).
        app, pid, exclude, mute: Which processes to record; see :class:`pcmtap.tap.Tap`.
        skip_leading_silence: Start the file at the first sound, waiting up to
            ``silence_timeout_s`` for it.
        until: Stop as soon as this returns true (checked about every 10 ms).
        bitrate: For lossy formats, e.g. ``"320k"``.
    """
    with Tap(app, pid=pid, exclude=exclude, mute=mute) as tap:
        fmt = tap.format
        chunks = _guard_permission(iter(tap), fmt)
        if skip_leading_silence:
            chunks = skip_silence(
                chunks, fmt, threshold=silence_threshold, timeout_s=silence_timeout_s
            )
        if seconds is not None:
            chunks = take_seconds(chunks, fmt, seconds)
        if until is not None:
            chunks = take_until(chunks, until)
        try:
            return write_audio(path, chunks, fmt, bitrate=bitrate)
        except KeyboardInterrupt:  # Ctrl-C ends an open-ended recording, keeping it
            return Path(path)

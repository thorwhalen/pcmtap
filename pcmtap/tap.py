"""A live tap on what processes are playing: a context manager yielding PCM chunks.

>>> with Tap(app="Spotify", mute=True) as tap:  # doctest: +SKIP
...     print(tap.format)
...     for chunk in tap:          # bytes of interleaved float32 frames
...         ...

``Tap`` runs the native helper (:mod:`pcmtap.helper_build`) as a subprocess and
reads its stdout. Chunks always hold whole frames.
"""

from __future__ import annotations

import json
import queue
import subprocess
import threading
from dataclasses import dataclass
from typing import Iterator, Sequence

from pcmtap.helper_build import helper_path

#: Sample formats the helper emits (interleaved little-endian float32).
SAMPLE_FORMAT = "f32le"
BYTES_PER_SAMPLE = 4
_READ_SIZE = 1 << 16
_FORMAT_TIMEOUT_S = 10.0


@dataclass(frozen=True)
class AudioFormat:
    """The PCM layout of a tap's output."""

    sample_rate: int
    channels: int
    sample_format: str = SAMPLE_FORMAT

    @property
    def frame_bytes(self) -> int:
        """Bytes per frame (one sample of every channel)."""
        return self.channels * BYTES_PER_SAMPLE

    def frames_to_bytes(self, frames: int) -> int:
        """How many bytes ``frames`` frames take."""
        return frames * self.frame_bytes

    def seconds_to_frames(self, seconds: float) -> int:
        """How many frames ``seconds`` seconds take (rounded)."""
        return round(seconds * self.sample_rate)


class TapError(RuntimeError):
    """The helper could not start or keep the tap."""


class PermissionMissing(TapError):
    """macOS has not granted *System Audio Recording* to pcmtap's helper."""


def _run_helper(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([str(helper_path()), *args], capture_output=True, text=True)


def permission_status() -> str:
    """``"granted"``, ``"denied"``, ``"not_determined"`` or ``"unknown"``."""
    return _run_helper("--permission").stdout.strip() or "unknown"


def request_permission() -> bool:
    """Ask macOS for *System Audio Recording* (a dialog on the Mac's screen); blocks
    until it is answered. Returns whether it is granted."""
    return _run_helper("--request-permission").returncode == 0


def audio_processes() -> list[dict]:
    """The processes Core Audio knows: ``pid``, ``bundle_id``, ``running_output``."""
    run = _run_helper("--list")
    if run.returncode != 0:
        raise TapError(run.stderr.strip())
    return json.loads(run.stdout)


def resolve_app(app: str) -> str:
    """A bundle id (prefix) for ``app``: a bundle id is kept; an app name is looked up.

    >>> resolve_app("com.spotify.client")
    'com.spotify.client'
    """
    if "." in app:
        return app
    run = subprocess.run(
        ["osascript", "-e", f'id of application "{app}"'],
        capture_output=True,
        text=True,
    )
    if run.returncode != 0 or not run.stdout.strip():
        raise TapError(f"No application named {app!r} (give its bundle id instead).")
    return run.stdout.strip()


def _selection_args(
    app: str | Sequence[str] | None, pid: int | Sequence[int] | None, exclude: bool
) -> list[str]:
    apps = [app] if isinstance(app, str) else list(app or ())
    pids = [pid] if isinstance(pid, int) else list(pid or ())
    args = [a for b in apps for a in ("--bundle-id", resolve_app(b))]
    args += [a for p in pids for a in ("--pid", str(p))]
    return args + (["--exclude"] if exclude else [])


class Tap:
    """Capture what processes play, as an iterator of PCM chunks (``bytes``).

    Args:
        app: Bundle id(s) or app name(s) to record; all of their processes are
            included (``"com.spotify.client"`` also matches its helper processes).
        pid: Process id(s) to record.
        exclude: Record everything *except* the selected processes.
        mute: Silence the recorded processes on the speakers while recording.
        seconds: Stop after this long (otherwise when closed).

    With no ``app`` and no ``pid``, records every process on the Mac.
    """

    def __init__(
        self,
        app: str | Sequence[str] | None = None,
        *,
        pid: int | Sequence[int] | None = None,
        exclude: bool = False,
        mute: bool = False,
        seconds: float | None = None,
    ):
        self.args = _selection_args(app, pid, exclude)
        if mute:
            self.args.append("--mute")
        if seconds:
            self.args += ["--seconds", str(seconds)]
        self.format: AudioFormat | None = None
        self._proc: subprocess.Popen | None = None
        self._events: queue.Queue = queue.Queue()
        self.events: list[dict] = []

    def __enter__(self) -> "Tap":
        self.open()
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def open(self) -> "Tap":
        """Start the helper and wait for it to report its audio format."""
        self._proc = subprocess.Popen(
            [str(helper_path()), *self.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        threading.Thread(target=self._read_events, daemon=True).start()
        try:
            event = self._events.get(timeout=_FORMAT_TIMEOUT_S)
        except queue.Empty:
            self.close()
            raise TapError("The helper did not start the tap in time.") from None
        if event.get("event") != "format":
            self.close()
            message = event.get("message") or str(event)
            error = PermissionMissing if "denied" in message else TapError
            raise error(message)
        self.format = AudioFormat(int(event["sample_rate"]), int(event["channels"]))
        return self

    def _read_events(self) -> None:
        for line in self._proc.stderr:
            try:
                event = json.loads(line)
            except ValueError:
                event = {
                    "event": "log",
                    "message": line.decode(errors="replace").strip(),
                }
            self.events.append(event)
            self._events.put(event)
        self._events.put({"event": "exited", "message": "helper exited"})

    def __iter__(self) -> Iterator[bytes]:
        if self._proc is None:
            self.open()
        frame = self.format.frame_bytes
        pending = b""
        while True:
            data = self._proc.stdout.read1(_READ_SIZE)
            if not data:
                break
            data = pending + data
            cut = len(data) - len(data) % frame
            pending = data[cut:]
            if cut:
                yield data[:cut]

    def close(self) -> None:
        """Stop the capture and the helper."""
        proc, self._proc = self._proc, None
        if proc is None:
            return
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        for stream in (proc.stdin, proc.stdout):
            if stream:
                stream.close()

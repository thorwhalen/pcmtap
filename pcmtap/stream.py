"""Operations on a stream of PCM chunks (interleaved float32 ``bytes``).

Each takes an iterable of chunks and an :class:`pcmtap.tap.AudioFormat` and returns a
new iterator, so they compose: ``take_seconds(skip_silence(tap, fmt), fmt, 30)``.

>>> from pcmtap.tap import AudioFormat
>>> from array import array
>>> fmt = AudioFormat(sample_rate=4, channels=1)
>>> chunks = [array("f", [0, 0]).tobytes(), array("f", [0, .5, .5, .5]).tobytes()]
>>> b"".join(take_frames(skip_silence(chunks, fmt), fmt, 2)) == array("f", [.5, .5]).tobytes()
True
"""

from __future__ import annotations

import time
from array import array
from typing import Callable, Iterable, Iterator

from pcmtap.tap import AudioFormat

#: Peak amplitude below which audio counts as silence (about -60 dBFS).
DEFAULT_SILENCE_THRESHOLD = 1e-3


def samples(chunk: bytes) -> array:
    """The float32 samples in ``chunk``."""
    a = array("f")
    a.frombytes(chunk)
    return a


def peak(chunk: bytes) -> float:
    """The largest absolute sample in ``chunk`` (0.0 for an empty one)."""
    a = samples(chunk)
    return max(max(a), -min(a)) if a else 0.0


class SilenceTimeout(TimeoutError):
    """No sound arrived within the allowed time."""


def skip_silence(
    chunks: Iterable[bytes],
    fmt: AudioFormat,
    *,
    threshold: float = DEFAULT_SILENCE_THRESHOLD,
    timeout_s: float | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> Iterator[bytes]:
    """Drop the leading silence: start at the first frame louder than ``threshold``.

    Raises :class:`SilenceTimeout` if ``timeout_s`` passes (by ``clock``) first.
    """
    start = clock()
    it = iter(chunks)
    for chunk in it:
        a = samples(chunk)
        for i, s in enumerate(a):
            if abs(s) > threshold:
                first = (i // fmt.channels) * fmt.frame_bytes
                yield chunk[first:]
                yield from it
                return
        if timeout_s is not None and clock() - start > timeout_s:
            raise SilenceTimeout(f"No sound above {threshold} within {timeout_s} s.")


def take_frames(
    chunks: Iterable[bytes], fmt: AudioFormat, frames: int
) -> Iterator[bytes]:
    """The first ``frames`` frames of the stream, then stop (the source is not drained)."""
    remaining = fmt.frames_to_bytes(frames)
    for chunk in chunks:
        if remaining <= 0:
            return
        piece = chunk[:remaining]
        remaining -= len(piece)
        yield piece
        if remaining <= 0:
            return


def take_seconds(
    chunks: Iterable[bytes], fmt: AudioFormat, seconds: float
) -> Iterator[bytes]:
    """The first ``seconds`` seconds of the stream."""
    return take_frames(chunks, fmt, fmt.seconds_to_frames(seconds))


def take_until(chunks: Iterable[bytes], stop: Callable[[], bool]) -> Iterator[bytes]:
    """Chunks until ``stop()`` returns true (checked before each chunk)."""
    for chunk in chunks:
        if stop():
            return
        yield chunk

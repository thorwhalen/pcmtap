"""Write a stream of PCM chunks to an audio file.

``.wav`` is written natively (32-bit float WAV, the tap's exact samples, no
dependency). Any other extension (``.flac``, ``.mp3``, ``.m4a``, ``.ogg``...) is
encoded by ``ffmpeg`` as the chunks arrive.
"""

from __future__ import annotations

import shutil
import struct
import subprocess
from pathlib import Path
from typing import Iterable

from pcmtap.tap import BYTES_PER_SAMPLE, AudioFormat

_WAVE_FORMAT_IEEE_FLOAT = 3


def _wav_header(fmt: AudioFormat, data_bytes: int) -> bytes:
    frames = data_bytes // fmt.frame_bytes
    fmt_chunk = struct.pack(
        "<HHIIHHH",
        _WAVE_FORMAT_IEEE_FLOAT,
        fmt.channels,
        fmt.sample_rate,
        fmt.sample_rate * fmt.frame_bytes,
        fmt.frame_bytes,
        BYTES_PER_SAMPLE * 8,
        0,  # cbSize
    )
    body = (
        b"WAVE"
        + b"fmt "
        + struct.pack("<I", len(fmt_chunk))
        + fmt_chunk
        + b"fact"
        + struct.pack("<II", 4, frames)
        + b"data"
        + struct.pack("<I", data_bytes)
    )
    return b"RIFF" + struct.pack("<I", len(body) + data_bytes) + body


def write_wav(path: str | Path, chunks: Iterable[bytes], fmt: AudioFormat) -> Path:
    """Write ``chunks`` to a 32-bit float WAV at ``path``; returns the path."""
    path = Path(path)
    with path.open("wb") as f:
        f.write(_wav_header(fmt, 0))
        n = 0
        for chunk in chunks:
            f.write(chunk)
            n += len(chunk)
        f.seek(0)
        f.write(_wav_header(fmt, n))
    return path


def write_with_ffmpeg(
    path: str | Path,
    chunks: Iterable[bytes],
    fmt: AudioFormat,
    *,
    bitrate: str | None = None,
    ffmpeg: str | None = None,
) -> Path:
    """Encode ``chunks`` into ``path`` with ffmpeg (format from its extension)."""
    ffmpeg = ffmpeg or shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError(
            f"Writing {Path(path).suffix} needs ffmpeg (brew install ffmpeg); "
            "'.wav' needs nothing."
        )
    cmd = [
        ffmpeg, "-loglevel", "error", "-y",
        "-f", fmt.sample_format, "-ar", str(fmt.sample_rate), "-ac", str(fmt.channels),
        "-i", "pipe:0",
    ]  # fmt: skip
    if bitrate:
        cmd += ["-b:a", bitrate]
    proc = subprocess.Popen(
        [*cmd, str(path)], stdin=subprocess.PIPE, stderr=subprocess.PIPE
    )
    try:
        for chunk in chunks:
            proc.stdin.write(chunk)
    finally:
        proc.stdin.close()
        err = proc.stderr.read().decode(errors="replace")
        proc.wait()
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg failed writing {path}: {err.strip()}")
    return Path(path)


def write_audio(
    path: str | Path,
    chunks: Iterable[bytes],
    fmt: AudioFormat,
    *,
    bitrate: str | None = None,
) -> Path:
    """Write ``chunks`` to ``path``: natively for ``.wav``, through ffmpeg otherwise."""
    if Path(path).suffix.lower() == ".wav":
        return write_wav(path, chunks, fmt)
    return write_with_ffmpeg(path, chunks, fmt, bitrate=bitrate)

"""Record what an app (or the whole Mac) is playing, as PCM, via Core Audio process taps.

>>> from pcmtap import record  # doctest: +SKIP
>>> record("song.wav", 30, app="Spotify", mute=True)  # doctest: +SKIP
PosixPath('song.wav')

For streaming, :class:`Tap` yields chunks of interleaved float32 frames, and
:mod:`pcmtap.stream` composes over them (skip the leading silence, take N seconds).
macOS 14.2+; the first recording asks for the *System Audio Recording* permission
(:func:`request_permission`, ``pcmtap permission --request``).
"""

from pcmtap.base import record
from pcmtap.helper_build import HelperUnavailable, helper_path
from pcmtap.requirements import check_requirements
from pcmtap.stream import peak, skip_silence, take_frames, take_seconds, take_until
from pcmtap.tap import (
    AudioFormat,
    PermissionMissing,
    Tap,
    TapError,
    audio_processes,
    permission_status,
    request_permission,
    resolve_app,
)
from pcmtap.write import write_audio, write_wav

__all__ = [
    "AudioFormat",
    "HelperUnavailable",
    "PermissionMissing",
    "Tap",
    "TapError",
    "audio_processes",
    "check_requirements",
    "helper_path",
    "peak",
    "permission_status",
    "record",
    "request_permission",
    "resolve_app",
    "skip_silence",
    "take_frames",
    "take_seconds",
    "take_until",
    "write_audio",
    "write_wav",
]

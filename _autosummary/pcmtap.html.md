# pcmtap

Record what an app (or the whole Mac) is playing, as PCM, via Core Audio process taps.

```pycon
>>> from pcmtap import record
>>> record("song.wav", 30, app="Spotify", mute=True)
PosixPath('song.wav')
```

For streaming, [`Tap`](#pcmtap.Tap) yields chunks of interleaved float32 frames, and
[`pcmtap.stream`](pcmtap.stream.html.md#module-pcmtap.stream) composes over them (skip the leading silence, take N seconds).
macOS 14.2+; the first recording asks for the *System Audio Recording* permission
([`request_permission()`](#pcmtap.request_permission), `pcmtap permission --request`).

### Functions

| [`audio_processes`](#pcmtap.audio_processes)()                               | The processes Core Audio knows: `pid`, `bundle_id`, `running_output`.                               |
|--------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| [`check_requirements`](#pcmtap.check_requirements)(\*[, request])               | Problems (each with its remedy) that stop pcmtap from recording; empty means ready.                 |
| [`helper_path`](#pcmtap.helper_path)(\*[, rebuild])                      | The helper binary, building it first if this version has not been built yet.                        |
| [`peak`](#pcmtap.peak)(chunk)                                     | The largest absolute sample in `chunk` (0.0 for an empty one).                                      |
| [`permission_status`](#pcmtap.permission_status)()                             | `"granted"`, `"denied"`, `"not_determined"` or `"unknown"`.                                         |
| [`record`](#pcmtap.record)(path[, seconds, app, pid, exclude, ...]) | Record what `app` (default: every process) plays into `path`; returns the path.                     |
| [`request_permission`](#pcmtap.request_permission)()                            | Ask macOS for *System Audio Recording* (a dialog on the Mac's screen); blocks until it is answered. |
| [`resolve_app`](#pcmtap.resolve_app)(app)                                | A bundle id (prefix) for `app`: a bundle id is kept; an app name is looked up.                      |
| [`skip_silence`](#pcmtap.skip_silence)(chunks, fmt, \*[, threshold, ...]) | Drop the leading silence: start at the first frame louder than `threshold`.                         |
| [`take_frames`](#pcmtap.take_frames)(chunks, fmt, frames)                | The first `frames` frames of the stream, then stop (the source is not drained).                     |
| [`take_seconds`](#pcmtap.take_seconds)(chunks, fmt, seconds)              | The first `seconds` seconds of the stream.                                                          |
| [`take_until`](#pcmtap.take_until)(chunks, stop)                        | Chunks until `stop()` returns true (checked before each chunk).                                     |
| [`write_audio`](#pcmtap.write_audio)(path, chunks, fmt, \*[, bitrate])   | Write `chunks` to `path`: natively for `.wav`, through ffmpeg otherwise.                            |
| [`write_wav`](#pcmtap.write_wav)(path, chunks, fmt)                    | Write `chunks` to a 32-bit float WAV at `path`; returns the path.                                   |

### Classes

| [`AudioFormat`](#pcmtap.AudioFormat)(sample_rate, channels[, ...])   | The PCM layout of a tap's output.                                    |
|----------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| [`Tap`](#pcmtap.Tap)([app, pid, exclude, mute, seconds])     | Capture what processes play, as an iterator of PCM chunks (`bytes`). |

### Exceptions

| [`HelperUnavailable`](#pcmtap.HelperUnavailable)   | The native helper cannot be found or built on this machine.        |
|----------------------------------------------------------------------|--------------------------------------------------------------------|
| [`PermissionMissing`](#pcmtap.PermissionMissing)   | macOS has not granted *System Audio Recording* to pcmtap's helper. |
| [`TapError`](#pcmtap.TapError)            | The helper could not start or keep the tap.                        |

### *class* pcmtap.AudioFormat(sample_rate, channels, sample_format='f32le')

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

The PCM layout of a tap’s output.

#### *property* frame_bytes *: [int](https://docs.python.org/3/builtins/functions.html#int)*

Bytes per frame (one sample of every channel).

#### frames_to_bytes(frames)

How many bytes `frames` frames take.

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)

#### seconds_to_frames(seconds)

How many frames `seconds` seconds take (rounded).

* **Return type:**
  [`int`](https://docs.python.org/3/builtins/functions.html#int)

### *exception* pcmtap.HelperUnavailable

Bases: [`RuntimeError`](https://docs.python.org/3/builtins/exceptions.html#RuntimeError)

The native helper cannot be found or built on this machine.

### *exception* pcmtap.PermissionMissing

Bases: [`TapError`](pcmtap.tap.html.md#pcmtap.tap.TapError)

macOS has not granted *System Audio Recording* to pcmtap’s helper.

### *class* pcmtap.Tap(app=None, , pid=None, exclude=False, mute=False, seconds=None)

Bases: [`object`](https://docs.python.org/3/builtins/functions.html#object)

Capture what processes play, as an iterator of PCM chunks (`bytes`).

* **Parameters:**
  * **app** ([`Union`](https://docs.python.org/3/library/typing.html#typing.Union)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)], [`None`](https://docs.python.org/3/builtins/constants.html#None)]) – Bundle id(s) or app name(s) to record; all of their processes are
    included (`"com.spotify.client"` also matches its helper processes).
  * **pid** ([`Union`](https://docs.python.org/3/library/typing.html#typing.Union)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`int`](https://docs.python.org/3/builtins/functions.html#int)], [`None`](https://docs.python.org/3/builtins/constants.html#None)]) – Process id(s) to record.
  * **exclude** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Record everything *except* the selected processes.
  * **mute** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Silence the recorded processes on the speakers while recording.
  * **seconds** ([`float`](https://docs.python.org/3/builtins/functions.html#float) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – Stop after this long (otherwise when closed).

With no `app` and no `pid`, records every process on the Mac.

#### close()

Stop the capture and the helper.

* **Return type:**
  [`None`](https://docs.python.org/3/builtins/constants.html#None)

#### open()

Start the helper and wait for it to report its audio format.

* **Return type:**
  [`Tap`](pcmtap.tap.html.md#pcmtap.tap.Tap)

### *exception* pcmtap.TapError

Bases: [`RuntimeError`](https://docs.python.org/3/builtins/exceptions.html#RuntimeError)

The helper could not start or keep the tap.

### pcmtap.audio_processes()

The processes Core Audio knows: `pid`, `bundle_id`, `running_output`.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]

### pcmtap.check_requirements(, request=False)

Problems (each with its remedy) that stop pcmtap from recording; empty means ready.

With `request=True`, a missing permission is asked for (a dialog on the Mac).

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)]

### pcmtap.helper_path(, rebuild=False)

The helper binary, building it first if this version has not been built yet.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### pcmtap.peak(chunk)

The largest absolute sample in `chunk` (0.0 for an empty one).

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### pcmtap.permission_status()

`"granted"`, `"denied"`, `"not_determined"` or `"unknown"`.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### pcmtap.record(path, seconds=None, , app=None, pid=None, exclude=False, mute=False, skip_leading_silence=False, silence_threshold=0.001, silence_timeout_s=30.0, until=None, bitrate=None)

Record what `app` (default: every process) plays into `path`; returns the path.

```pycon
>>> record("out.wav", 10, app="Spotify")
```

* **Parameters:**
  * **path** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)) – Output file; `.wav` needs nothing, other formats need ffmpeg.
  * **seconds** ([`float`](https://docs.python.org/3/builtins/functions.html#float) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – How long to record (of sound, if `skip_leading_silence`). With
    neither `seconds` nor `until`, records until interrupted (Ctrl-C).
  * **app** ([`Union`](https://docs.python.org/3/library/typing.html#typing.Union)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str), [`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`str`](https://docs.python.org/3/builtins/stdtypes.html#str)], [`None`](https://docs.python.org/3/builtins/constants.html#None)]) – Which processes to record; see [`pcmtap.tap.Tap`](pcmtap.tap.html.md#pcmtap.tap.Tap).
  * **pid** ([`Union`](https://docs.python.org/3/library/typing.html#typing.Union)[[`int`](https://docs.python.org/3/builtins/functions.html#int), [`Sequence`](https://docs.python.org/3/library/typing.html#typing.Sequence)[[`int`](https://docs.python.org/3/builtins/functions.html#int)], [`None`](https://docs.python.org/3/builtins/constants.html#None)]) – Which processes to record; see [`pcmtap.tap.Tap`](pcmtap.tap.html.md#pcmtap.tap.Tap).
  * **exclude** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Which processes to record; see [`pcmtap.tap.Tap`](pcmtap.tap.html.md#pcmtap.tap.Tap).
  * **mute** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Which processes to record; see [`pcmtap.tap.Tap`](pcmtap.tap.html.md#pcmtap.tap.Tap).
  * **skip_leading_silence** ([`bool`](https://docs.python.org/3/builtins/functions.html#bool)) – Start the file at the first sound, waiting up to
    `silence_timeout_s` for it.
  * **until** ([`Optional`](https://docs.python.org/3/library/typing.html#typing.Optional)[[`Callable`](https://docs.python.org/3/library/typing.html#typing.Callable)[[], [`bool`](https://docs.python.org/3/builtins/functions.html#bool)]]) – Stop as soon as this returns true (checked about every 10 ms).
  * **bitrate** ([`str`](https://docs.python.org/3/builtins/stdtypes.html#str) | [`None`](https://docs.python.org/3/builtins/constants.html#None)) – For lossy formats, e.g. `"320k"`.
* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### pcmtap.request_permission()

Ask macOS for *System Audio Recording* (a dialog on the Mac’s screen); blocks
until it is answered. Returns whether it is granted.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### pcmtap.resolve_app(app)

A bundle id (prefix) for `app`: a bundle id is kept; an app name is looked up.

```pycon
>>> resolve_app("com.spotify.client")
'com.spotify.client'
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### pcmtap.skip_silence(chunks, fmt, \*, threshold=0.001, timeout_s=None, clock=<built-in function monotonic>)

Drop the leading silence: start at the first frame louder than `threshold`.

Raises `SilenceTimeout` if `timeout_s` passes (by `clock`) first.

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/typing.html#typing.Iterator)[[`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)]

### pcmtap.take_frames(chunks, fmt, frames)

The first `frames` frames of the stream, then stop (the source is not drained).

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/typing.html#typing.Iterator)[[`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)]

### pcmtap.take_seconds(chunks, fmt, seconds)

The first `seconds` seconds of the stream.

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/typing.html#typing.Iterator)[[`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)]

### pcmtap.take_until(chunks, stop)

Chunks until `stop()` returns true (checked before each chunk).

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/typing.html#typing.Iterator)[[`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)]

### pcmtap.write_audio(path, chunks, fmt, , bitrate=None)

Write `chunks` to `path`: natively for `.wav`, through ffmpeg otherwise.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### pcmtap.write_wav(path, chunks, fmt)

Write `chunks` to a 32-bit float WAV at `path`; returns the path.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### Modules

| [`base`](pcmtap.base.html.md#module-pcmtap.base)                 | `record`: what an app (or the whole Mac) plays, into an audio file, in one call.   |
|------------------------------------------------------------------------------------------|------------------------------------------------------------------------------------|
| [`helper_build`](pcmtap.helper_build.html.md#module-pcmtap.helper_build) | Find or build the native helper (`pcmtap-helper`) that does the real-time capture. |
| [`requirements`](pcmtap.requirements.html.md#module-pcmtap.requirements) | `check_requirements`: what this machine still needs for pcmtap, and how to get it. |
| [`stream`](pcmtap.stream.html.md#module-pcmtap.stream)             | Operations on a stream of PCM chunks (interleaved float32 `bytes`).                |
| [`tap`](pcmtap.tap.html.md#module-pcmtap.tap)                   | A live tap on what processes are playing: a context manager yielding PCM chunks.   |
| [`write`](pcmtap.write.html.md#module-pcmtap.write)               | Write a stream of PCM chunks to an audio file.                                     |

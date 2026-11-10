# pcmtap.tap

A live tap on what processes are playing: a context manager yielding PCM chunks.

```pycon
>>> with Tap(app="Spotify", mute=True) as tap:
...     print(tap.format)
...     for chunk in tap:          # bytes of interleaved float32 frames
...         ...
```

`Tap` runs the native helper ([`pcmtap.helper_build`](pcmtap.helper_build.html.md#module-pcmtap.helper_build)) as a subprocess and
reads its stdout. Chunks always hold whole frames.

### Module Attributes

| [`SAMPLE_FORMAT`](#pcmtap.tap.SAMPLE_FORMAT)   | Sample formats the helper emits (interleaved little-endian float32).   |
|------------------------------------------------------------------|------------------------------------------------------------------------|

### Functions

| [`audio_processes`](#pcmtap.tap.audio_processes)()    | The processes Core Audio knows: `pid`, `bundle_id`, `running_output`.                               |
|-----------------------------------------------------------------------|-----------------------------------------------------------------------------------------------------|
| [`permission_status`](#pcmtap.tap.permission_status)()  | `"granted"`, `"denied"`, `"not_determined"` or `"unknown"`.                                         |
| [`request_permission`](#pcmtap.tap.request_permission)() | Ask macOS for *System Audio Recording* (a dialog on the Mac's screen); blocks until it is answered. |
| [`resolve_app`](#pcmtap.tap.resolve_app)(app)     | A bundle id (prefix) for `app`: a bundle id is kept; an app name is looked up.                      |

### Classes

| [`AudioFormat`](#pcmtap.tap.AudioFormat)(sample_rate, channels[, ...])   | The PCM layout of a tap's output.                                    |
|----------------------------------------------------------------------------------------------|----------------------------------------------------------------------|
| [`Tap`](#pcmtap.tap.Tap)([app, pid, exclude, mute, seconds])     | Capture what processes play, as an iterator of PCM chunks (`bytes`). |

### Exceptions

| [`PermissionMissing`](#pcmtap.tap.PermissionMissing)   | macOS has not granted *System Audio Recording* to pcmtap's helper.   |
|----------------------------------------------------------------------|----------------------------------------------------------------------|
| [`TapError`](#pcmtap.tap.TapError)            | The helper could not start or keep the tap.                          |

### *class* pcmtap.tap.AudioFormat(sample_rate, channels, sample_format='f32le')

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

### *exception* pcmtap.tap.PermissionMissing

Bases: [`TapError`](#pcmtap.tap.TapError)

macOS has not granted *System Audio Recording* to pcmtap’s helper.

### pcmtap.tap.SAMPLE_FORMAT *= 'f32le'*

Sample formats the helper emits (interleaved little-endian float32).

### *class* pcmtap.tap.Tap(app=None, , pid=None, exclude=False, mute=False, seconds=None)

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
  [`Tap`](#pcmtap.tap.Tap)

### *exception* pcmtap.tap.TapError

Bases: [`RuntimeError`](https://docs.python.org/3/builtins/exceptions.html#RuntimeError)

The helper could not start or keep the tap.

### pcmtap.tap.audio_processes()

The processes Core Audio knows: `pid`, `bundle_id`, `running_output`.

* **Return type:**
  [`list`](https://docs.python.org/3/builtins/stdtypes.html#list)[[`dict`](https://docs.python.org/3/builtins/stdtypes.html#dict)]

### pcmtap.tap.permission_status()

`"granted"`, `"denied"`, `"not_determined"` or `"unknown"`.

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

### pcmtap.tap.request_permission()

Ask macOS for *System Audio Recording* (a dialog on the Mac’s screen); blocks
until it is answered. Returns whether it is granted.

* **Return type:**
  [`bool`](https://docs.python.org/3/builtins/functions.html#bool)

### pcmtap.tap.resolve_app(app)

A bundle id (prefix) for `app`: a bundle id is kept; an app name is looked up.

```pycon
>>> resolve_app("com.spotify.client")
'com.spotify.client'
```

* **Return type:**
  [`str`](https://docs.python.org/3/builtins/stdtypes.html#str)

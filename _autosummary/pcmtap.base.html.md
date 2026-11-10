# pcmtap.base

`record`: what an app (or the whole Mac) plays, into an audio file, in one call.

### Module Attributes

| [`SILENCE_CHECK_S`](#pcmtap.base.SILENCE_CHECK_S)   | Seconds of exact digital silence after which a missing permission is suspected.   |
|--------------------------------------------------------------------|-----------------------------------------------------------------------------------|

### Functions

| [`record`](#pcmtap.base.record)(path[, seconds, app, pid, exclude, ...])   | Record what `app` (default: every process) plays into `path`; returns the path.   |
|----------------------------------------------------------------------------------------------------|-----------------------------------------------------------------------------------|

### pcmtap.base.SILENCE_CHECK_S *= 3.0*

Seconds of exact digital silence after which a missing permission is suspected.

### pcmtap.base.record(path, seconds=None, , app=None, pid=None, exclude=False, mute=False, skip_leading_silence=False, silence_threshold=0.001, silence_timeout_s=30.0, until=None, bitrate=None)

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

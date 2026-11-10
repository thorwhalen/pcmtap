# pcmtap.stream

Operations on a stream of PCM chunks (interleaved float32 `bytes`).

Each takes an iterable of chunks and an [`pcmtap.tap.AudioFormat`](pcmtap.tap.html.md#pcmtap.tap.AudioFormat) and returns a
new iterator, so they compose: `take_seconds(skip_silence(tap, fmt), fmt, 30)`.

```pycon
>>> from pcmtap.tap import AudioFormat
>>> from array import array
>>> fmt = AudioFormat(sample_rate=4, channels=1)
>>> chunks = [array("f", [0, 0]).tobytes(), array("f", [0, .5, .5, .5]).tobytes()]
>>> b"".join(take_frames(skip_silence(chunks, fmt), fmt, 2)) == array("f", [.5, .5]).tobytes()
True
```

### Module Attributes

| [`DEFAULT_SILENCE_THRESHOLD`](#pcmtap.stream.DEFAULT_SILENCE_THRESHOLD)   | Peak amplitude below which audio counts as silence (about -60 dBFS).   |
|------------------------------------------------------------------------------|------------------------------------------------------------------------|

### Functions

| [`peak`](#pcmtap.stream.peak)(chunk)                                     | The largest absolute sample in `chunk` (0.0 for an empty one).                  |
|--------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------------|
| [`samples`](#pcmtap.stream.samples)(chunk)                                  | The float32 samples in `chunk`.                                                 |
| [`skip_silence`](#pcmtap.stream.skip_silence)(chunks, fmt, \*[, threshold, ...]) | Drop the leading silence: start at the first frame louder than `threshold`.     |
| [`take_frames`](#pcmtap.stream.take_frames)(chunks, fmt, frames)                | The first `frames` frames of the stream, then stop (the source is not drained). |
| [`take_seconds`](#pcmtap.stream.take_seconds)(chunks, fmt, seconds)              | The first `seconds` seconds of the stream.                                      |
| [`take_until`](#pcmtap.stream.take_until)(chunks, stop)                        | Chunks until `stop()` returns true (checked before each chunk).                 |

### Exceptions

| [`SilenceTimeout`](#pcmtap.stream.SilenceTimeout)   | No sound arrived within the allowed time.   |
|-------------------------------------------------------------------|---------------------------------------------|

### pcmtap.stream.DEFAULT_SILENCE_THRESHOLD *= 0.001*

Peak amplitude below which audio counts as silence (about -60 dBFS).

### *exception* pcmtap.stream.SilenceTimeout

Bases: [`TimeoutError`](https://docs.python.org/3/builtins/exceptions.html#TimeoutError)

No sound arrived within the allowed time.

### pcmtap.stream.peak(chunk)

The largest absolute sample in `chunk` (0.0 for an empty one).

* **Return type:**
  [`float`](https://docs.python.org/3/builtins/functions.html#float)

### pcmtap.stream.samples(chunk)

The float32 samples in `chunk`.

* **Return type:**
  [`array`](https://docs.python.org/3/library/array.html#array.array)

### pcmtap.stream.skip_silence(chunks, fmt, \*, threshold=0.001, timeout_s=None, clock=<built-in function monotonic>)

Drop the leading silence: start at the first frame louder than `threshold`.

Raises [`SilenceTimeout`](#pcmtap.stream.SilenceTimeout) if `timeout_s` passes (by `clock`) first.

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/typing.html#typing.Iterator)[[`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)]

### pcmtap.stream.take_frames(chunks, fmt, frames)

The first `frames` frames of the stream, then stop (the source is not drained).

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/typing.html#typing.Iterator)[[`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)]

### pcmtap.stream.take_seconds(chunks, fmt, seconds)

The first `seconds` seconds of the stream.

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/typing.html#typing.Iterator)[[`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)]

### pcmtap.stream.take_until(chunks, stop)

Chunks until `stop()` returns true (checked before each chunk).

* **Return type:**
  [`Iterator`](https://docs.python.org/3/library/typing.html#typing.Iterator)[[`bytes`](https://docs.python.org/3/builtins/stdtypes.html#bytes)]

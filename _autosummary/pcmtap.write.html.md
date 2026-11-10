# pcmtap.write

Write a stream of PCM chunks to an audio file.

`.wav` is written natively (32-bit float WAV, the tap’s exact samples, no
dependency). Any other extension (`.flac`, `.mp3`, `.m4a`, `.ogg`…) is
encoded by `ffmpeg` as the chunks arrive.

### Functions

| [`write_audio`](#pcmtap.write.write_audio)(path, chunks, fmt, \*[, bitrate])   | Write `chunks` to `path`: natively for `.wav`, through ffmpeg otherwise.   |
|--------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------|
| [`write_wav`](#pcmtap.write.write_wav)(path, chunks, fmt)                    | Write `chunks` to a 32-bit float WAV at `path`; returns the path.          |
| [`write_with_ffmpeg`](#pcmtap.write.write_with_ffmpeg)(path, chunks, fmt, \*[, ...]) | Encode `chunks` into `path` with ffmpeg (format from its extension).       |

### pcmtap.write.write_audio(path, chunks, fmt, , bitrate=None)

Write `chunks` to `path`: natively for `.wav`, through ffmpeg otherwise.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### pcmtap.write.write_wav(path, chunks, fmt)

Write `chunks` to a 32-bit float WAV at `path`; returns the path.

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

### pcmtap.write.write_with_ffmpeg(path, chunks, fmt, , bitrate=None, ffmpeg=None)

Encode `chunks` into `path` with ffmpeg (format from its extension).

* **Return type:**
  [`Path`](https://docs.python.org/3/library/pathlib.html#pathlib.Path)

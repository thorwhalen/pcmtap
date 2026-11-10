---
name: pcmtap
description: >-
  Record what an app, or the whole Mac, is playing, as PCM audio, with the pcmtap Python package or its `pcmtap` CLI (Core Audio process taps, macOS 14.2+, no BlackHole or virtual device). Use when asked to record system audio, capture an app's sound output (Spotify, a browser, Zoom, a game), make a loopback or "what you hear" recording, tap audio from a process, get the PCM of what is playing, record a stream, mute an app while recording it, or check or grant the macOS System Audio Recording permission. Triggers on "record what's playing", "capture system audio", "audio loopback on mac", "tap Spotify's audio", "record app audio", "pcmtap".
license: MIT
compatibility: macOS 14.2 or later; the Swift compiler (Xcode command line tools) to build the helper on first use; ffmpeg only for non-WAV formats.
metadata:
  audience: consumers
---

# pcmtap: record what an app is playing

## Do this first

```bash
pcmtap check        # "ready", or what is missing and how to fix it
```

If it says the permission is `not_determined`: `pcmtap permission --request` puts a macOS dialog on the screen and blocks until a human answers it. **An agent cannot click it.** Tell the user what to click ("Allow" for pcmtap-helper, or System Settings > Privacy & Security > Screen & System Audio Recording > pcmtap-helper), and if you file a hand-off, make it a `manual-task`. Without the permission a tap returns silence, not an error. pcmtap detects that and raises `PermissionMissing`.

## Recording

```python
from pcmtap import record
record("out.wav", 30, app="Spotify", mute=True)          # 30 s of the Spotify app only
record("all.flac", 10)                                    # everything the Mac plays
record("x.mp3", 60, app="com.google.Chrome", bitrate="320k", skip_leading_silence=True)
```

```bash
pcmtap record out.wav --seconds 30 --app Spotify --mute
pcmtap list --playing          # JSON: which processes are making sound right now
```

- `app`: an app name or bundle id (a prefix: `com.spotify.client` includes its helper processes). `pid=` also works. Neither means the whole Mac. `exclude=True` inverts the selection.
- `mute=True` silences the recorded app on the speakers while it is recorded; the capture still gets full-level audio. Use it whenever the user might be listening to something else.
- `.wav` is written natively as 32-bit float, with nothing to install. Any other extension goes through ffmpeg.
- An app must already have an audio stream open (have played something since launch) to be tapped by name. Otherwise you get "no audio process matches".

## Streaming

`Tap` yields chunks of interleaved float32 frames (`tap.format` gives the rate and channels). The `pcmtap.stream` functions compose over those chunks:

```python
from pcmtap import Tap, skip_silence, take_seconds, write_audio
with Tap(app="Spotify", mute=True) as tap:
    chunks = take_seconds(skip_silence(iter(tap), tap.format, timeout_s=20), tap.format, 180)
    write_audio("song.flac", chunks, tap.format)
```

## Gotchas

- Real time: an hour of audio takes an hour.
- The permission belongs to the helper binary. A new pcmtap version rebuilds the helper, and macOS then asks once more.
- Taps capture the app's output *after* its own volume slider: set it to 100 for full level.

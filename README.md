
# pcmtap

Record what an app, or the whole Mac, is playing, as PCM audio. It uses Core Audio process taps (macOS 14.2+), so there is no BlackHole, no virtual device and no change to your audio routing.

```python
from pcmtap import record

record("spotify.wav", 30, app="Spotify", mute=True)   # 30 s of Spotify alone, silent on the speakers
record("everything.flac", 10)                          # whatever the Mac plays
```

```bash
pip install pcmtap
pcmtap check                                           # what is missing, with the fix
pcmtap record out.wav --seconds 30 --app Spotify --mute
pcmtap list --playing                                  # which processes are making sound
```

## The first run

The first run needs two things from macOS.

1. **The helper is built.** The real-time capture is a small Swift program shipped as source. On first use pcmtap compiles it with `swiftc` (from the Xcode command line tools: `xcode-select --install`) into `~/.local/share/pcmtap/bin/`.
2. **The permission is granted.** macOS asks once whether *pcmtap-helper* may record system audio: `pcmtap permission --request` shows the dialog. You can also allow it later in System Settings > Privacy & Security > Screen & System Audio Recording. Without the permission, macOS hands a tap silence rather than an error; pcmtap notices and raises `PermissionMissing`.

The helper makes itself responsible for its own privacy permissions. So the grant is remembered for pcmtap-helper, whichever terminal, IDE or detached tmux session runs it. A new pcmtap version with a changed helper asks once more.

## Choosing what to record

- `app="Spotify"` or `app="com.spotify.client"`: an app by name or bundle id. A bundle id is a prefix, so an app's helper processes are included.
- `pid=1234`: one process. Lists work for both.
- Neither: the whole Mac. `exclude=True` records everything *except* the selection.
- `mute=True` keeps the recorded processes off the speakers while they are recorded; the recording itself stays at full level.

An app can be tapped once it has opened an audio stream (played something since it launched).

## Streaming

`Tap` is a context manager that yields chunks of interleaved float32 frames. The functions in `pcmtap.stream` compose over them:

```python
from pcmtap import Tap, skip_silence, take_seconds, write_audio

with Tap(app="Spotify", mute=True) as tap:
    fmt = tap.format                                    # AudioFormat(sample_rate=44100, channels=2)
    chunks = skip_silence(iter(tap), fmt, timeout_s=20)
    write_audio("song.flac", take_seconds(chunks, fmt, 180), fmt)
```

`.wav` is written natively (32-bit float, the exact samples). Other formats go through `ffmpeg`.

## Agents

The package ships an agent skill (`pcmtap/data/skills/pcmtap/SKILL.md`): `gh skill install thorwhalen/pcmtap pcmtap`. `CLAUDE.md` is the map for agents developing pcmtap.

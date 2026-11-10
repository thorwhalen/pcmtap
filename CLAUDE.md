# pcmtap: agent map

Records what macOS processes play, through Core Audio process taps. Two layers:

- `pcmtap/helper/pcmtap_helper.swift`: the native helper, built on first use by `pcmtap/helper_build.py` into `~/.local/share/pcmtap/bin/pcmtap-helper`. The path is stable because macOS keys the permission to it; the source hash sits in the `pcmtap-helper.source-hash` sidecar, and a changed hash means rebuilding in place. It re-spawns itself with responsibility disclaimed so macOS attributes the *System Audio Recording* permission to it, not to the terminal. Protocol: raw interleaved f32le on stdout; JSON events on stderr (`format` first, then `stopped` or `error`). Modes: `--list`, `--permission`, `--request-permission`.
- Python: `tap.py` (`Tap`, the subprocess reader), `stream.py` (pure chunk operations), `write.py` (WAV natively, the rest through ffmpeg), `base.py` (`record`), `requirements.py` (`check_requirements`), `__main__.py` (CLI).

Rules:
- Changing the Swift source rebuilds the helper, and every user then re-grants the permission (the ad hoc signature changes). Batch helper changes. Never rename `HELPER_NAME` or move `helper_dir()`: a new path also means a new grant.
- Tests never need audio. `tests/` swaps the helper for a fake through `$PCMTAP_HELPER`; keep it that way, since CI runs on Linux.
- A live check needs the permission: `pcmtap check`. Play a tone with `afplay`, then `pcmtap record x.wav -s 2 --pid <afplay pid> --mute`.
- Consumer skill (shipped with pip): `pcmtap/data/skills/pcmtap/SKILL.md`, linked from `.claude/skills/pcmtap`.

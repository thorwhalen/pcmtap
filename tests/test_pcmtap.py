"""Offline tests (no Mac audio needed): the stream operations, the writers, and the
helper's command line, with the helper replaced by a fake that prints a tone."""

import json
import math
import stat
import sys
import textwrap
import wave
from array import array

import pytest

from pcmtap import AudioFormat, peak, skip_silence, take_seconds, write_wav
from pcmtap.stream import SilenceTimeout
from pcmtap.write import _wav_header

FMT = AudioFormat(sample_rate=8000, channels=2)


def tone(seconds, amp=0.5, rate=8000):
    return array(
        "f",
        [
            amp * math.sin(2 * math.pi * 440 * i / rate)
            for i in range(int(seconds * rate))
            for _ in (0, 1)
        ],
    ).tobytes()


def test_skip_silence_and_take_seconds():
    silence = array("f", [0.0] * 2 * 800).tobytes()  # 0.1 s
    out = b"".join(take_seconds(skip_silence([silence, tone(1.0)], FMT), FMT, 0.5))
    assert len(out) == FMT.frames_to_bytes(4000)
    assert peak(out[:8]) <= 0.5


def test_skip_silence_times_out():
    ticks = iter(range(100))
    with pytest.raises(SilenceTimeout):
        list(
            skip_silence([b"\0" * 8] * 10, FMT, timeout_s=3, clock=lambda: next(ticks))
        )


def test_write_wav_header_is_float(tmp_path):
    data = tone(0.25)
    path = write_wav(tmp_path / "t.wav", [data[:1000], data[1000:]], FMT)
    raw = path.read_bytes()
    assert raw[:4] == b"RIFF" and raw[8:12] == b"WAVE"
    assert int.from_bytes(raw[20:22], "little") == 3  # IEEE float
    assert raw.endswith(data) and len(raw) == len(_wav_header(FMT, len(data))) + len(
        data
    )


@pytest.fixture
def fake_helper(tmp_path, monkeypatch):
    """A stand-in for pcmtap-helper: reports a format, then writes 1 s of tone."""
    script = tmp_path / "fake-helper"
    script.write_text(
        textwrap.dedent(
            f"""\
            #!{sys.executable}
            import json, math, sys
            from array import array
            args = sys.argv[1:]
            if "--permission" in args:
                print("granted"); sys.exit(0)
            if "--list" in args:
                print(json.dumps([{{"pid": 1, "bundle_id": "com.x", "running_output": True}}])); sys.exit(0)
            sys.stderr.write(json.dumps({{"event": "format", "sample_rate": 8000, "channels": 2}}) + "\\n")
            sys.stderr.flush()
            data = array("f", [0.0] * 1600 + [0.5 * math.sin(i / 3) for i in range(16000)])
            sys.stdout.buffer.write(data.tobytes())
            """
        )
    )
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("PCMTAP_HELPER", str(script))
    from pcmtap.helper_build import helper_path

    helper_path.cache_clear()
    yield script
    helper_path.cache_clear()


def test_record_through_fake_helper(fake_helper, tmp_path):
    from pcmtap import audio_processes, permission_status, record

    assert permission_status() == "granted"
    assert audio_processes()[0]["bundle_id"] == "com.x"
    out = record(tmp_path / "r.wav", 0.5, pid=1, skip_leading_silence=True)
    raw = out.read_bytes()
    assert len(raw) - 58 == FMT.frames_to_bytes(4000)
    with pytest.raises(
        wave.Error
    ):  # stdlib wave reads only integer PCM: proof it's float
        wave.open(str(out))


def test_cli_list(fake_helper, capsys):
    from pcmtap.__main__ import main

    assert main(["list", "--playing"]) == 0
    assert json.loads(capsys.readouterr().out)[0]["pid"] == 1

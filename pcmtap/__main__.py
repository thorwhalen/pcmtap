"""Command line for pcmtap.

pcmtap record OUT [--seconds S] [--app NAME_OR_BUNDLE_ID]... [--pid N]... [--exclude]
                  [--mute] [--skip-silence] [--bitrate 320k]
pcmtap list [--playing]          audio processes as JSON
pcmtap permission [--request]    the System Audio Recording permission
pcmtap check                     what is missing, with remedies
"""

from __future__ import annotations

import argparse
import json
import sys


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="pcmtap", description="Record what apps play (macOS)."
    )
    sub = p.add_subparsers(dest="command", required=True)
    r = sub.add_parser("record", help="record into a file (.wav, or any ffmpeg format)")
    r.add_argument("out")
    r.add_argument("-s", "--seconds", type=float, default=None)
    r.add_argument(
        "-a", "--app", action="append", default=None, help="name or bundle id"
    )
    r.add_argument("-p", "--pid", action="append", type=int, default=None)
    r.add_argument(
        "--exclude", action="store_true", help="everything but the selection"
    )
    r.add_argument("--mute", action="store_true", help="silence it on the speakers")
    r.add_argument(
        "--skip-silence", action="store_true", help="start at the first sound"
    )
    r.add_argument("-b", "--bitrate", default=None)
    lst = sub.add_parser("list", help="audio processes, as JSON")
    lst.add_argument("--playing", action="store_true", help="only those playing now")
    perm = sub.add_parser("permission", help="System Audio Recording permission")
    perm.add_argument("--request", action="store_true", help="ask for it (dialog)")
    sub.add_parser("check", help="what is missing")
    return p


def main(argv: list[str] | None = None) -> int:
    """Run the command line; returns the exit status."""
    from pcmtap import (
        audio_processes,
        check_requirements,
        permission_status,
        record,
        request_permission,
    )

    args = _parser().parse_args(argv)
    try:
        if args.command == "record":
            print(
                record(
                    args.out,
                    args.seconds,
                    app=args.app,
                    pid=args.pid,
                    exclude=args.exclude,
                    mute=args.mute,
                    skip_leading_silence=args.skip_silence,
                    bitrate=args.bitrate,
                )
            )
        elif args.command == "list":
            rows = audio_processes()
            if args.playing:
                rows = [r for r in rows if r["running_output"]]
            print(json.dumps(rows, indent=1))
        elif args.command == "permission":
            if args.request:
                print("granted" if request_permission() else permission_status())
            else:
                print(permission_status())
        elif args.command == "check":
            problems = check_requirements()
            print("\n".join(problems) if problems else "ready")
            return 1 if any(not p.startswith("Optional") for p in problems) else 0
    except Exception as exc:
        print(f"pcmtap: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""Command-line entry point for console-gen."""

from __future__ import annotations

import argparse
from pathlib import Path

from .renderer import COLOR_PROFILES, RenderOptions, THEMES, render_log_file


def render_command(args: argparse.Namespace) -> int:
    options = RenderOptions(
        width_chars=args.width,
        font_size=args.font_size,
        title=args.title,
        theme_name=args.theme,
        frame=args.frame,
        color_profile=args.color_profile,
    )
    render_log_file(Path(args.input).resolve(), Path(args.output).resolve(), options)
    print(f"Rendered {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="console-gen",
        description="Render console logs as realistic terminal screenshots",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    render_parser = subparsers.add_parser("render", help="Render a log file to PNG")
    render_parser.add_argument("-i", "--input", required=True, help="Input console log")
    render_parser.add_argument("-o", "--output", required=True, help="Output PNG path")
    render_parser.add_argument("--title", default="Terminal", help="Terminal window title")
    render_parser.add_argument("--width", type=int, default=100, help="Terminal width in characters")
    render_parser.add_argument("--font-size", type=int, default=16, help="Terminal font size in pixels")
    render_parser.add_argument("--theme", choices=sorted(THEMES), default="auto", help="Terminal color theme")
    render_parser.add_argument(
        "--frame",
        choices=["windows", "mac", "ubuntu", "frameless"],
        default="windows",
        help="Terminal window frame style",
    )
    render_parser.add_argument(
        "--color-profile",
        choices=COLOR_PROFILES,
        default="auto",
        help="Automatic log coloring profile",
    )
    render_parser.set_defaults(func=render_command)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except Exception as exc:
        print(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

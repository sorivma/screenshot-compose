"""Command-line entry point for screenshot-compose."""

from __future__ import annotations

import argparse
from pathlib import Path

from .project import load_options_config, render_project
from .renderer import RenderOptions, render_log_file
from .themes import list_syntax_theme_names, list_terminal_theme_names


def render_command(args: argparse.Namespace) -> int:
    options = _build_options(args)
    render_log_file(Path(args.input).resolve(), Path(args.output).resolve(), options)
    print(f"Rendered {args.output}")
    return 0


def themes_command(args: argparse.Namespace) -> int:
    terminal_themes = list_terminal_theme_names(args.theme_file)
    syntax_themes = list_syntax_theme_names(args.theme_file)
    print("Terminal themes:")
    for name in terminal_themes:
        print(f"  {name}")
    print("Syntax themes:")
    for name in syntax_themes:
        print(f"  {name}")
    return 0


def apply_command(args: argparse.Namespace) -> int:
    outputs = render_project(args.file, args.names)
    for output in outputs:
        print(f"Rendered {output}")
    return 0


def _build_options(args: argparse.Namespace) -> RenderOptions:
    values = load_options_config(args.config)
    cli_values = {
        "width_chars": args.width,
        "wrap_lines": args.wrap_lines,
        "font_size": args.font_size,
        "line_spacing": args.line_spacing,
        "padding_x": args.padding_x,
        "padding_y": args.padding_y,
        "margin": args.margin,
        "titlebar_height": args.titlebar_height,
        "radius": args.radius,
        "rounded_corners": args.rounded_corners,
        "title": args.title,
        "theme_name": args.theme,
        "frame": args.frame,
        "content_type": args.content_type,
        "language": args.language,
        "syntax_theme": args.syntax_theme,
        "guess_language": args.guess_language,
        "theme_file": args.theme_file,
        "line_numbers": args.line_numbers,
        "line_number_start": args.line_number_start,
        "line_number_style": args.line_number_style,
        "indent_guides": args.indent_guides,
        "indent_size": args.indent_size,
        "command_highlight": args.command_highlight,
    }
    values.update({key: value for key, value in cli_values.items() if value is not None})
    return RenderOptions(**values)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="screenshot-compose",
        description="Render terminal logs and source code screenshots from declarative project files",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    render_parser = subparsers.add_parser("render", help="Render a log file to PNG")
    render_parser.add_argument("-i", "--input", required=True, help="Input console log")
    render_parser.add_argument("-o", "--output", required=True, help="Output PNG path")
    render_parser.add_argument("--config", help="JSON or YAML render config. CLI options override config values.")
    render_parser.add_argument("--theme-file", help="JSON file with custom terminal and syntax themes")
    render_parser.add_argument("--title", help="Terminal window title")
    render_parser.add_argument("--width", type=int, help="Terminal width in characters")
    render_parser.add_argument(
        "--wrap-lines",
        action="store_true",
        dest="wrap_lines",
        default=None,
        help="Wrap lines longer than --width",
    )
    render_parser.add_argument(
        "--no-wrap-lines",
        action="store_false",
        dest="wrap_lines",
        help="Expand image width for long lines",
    )
    render_parser.add_argument("--font-size", type=int, help="Terminal font size in pixels")
    render_parser.add_argument("--line-spacing", type=int, help="Extra pixels between text lines")
    render_parser.add_argument("--padding-x", type=int, help="Horizontal content padding in pixels")
    render_parser.add_argument("--padding-y", type=int, help="Vertical content padding in pixels")
    render_parser.add_argument("--margin", type=int, help="Transparent outer image margin in pixels")
    render_parser.add_argument("--titlebar-height", type=int, help="Titlebar height in pixels")
    render_parser.add_argument("--radius", type=int, help="Window corner radius in pixels")
    render_parser.add_argument(
        "--rounded-corners",
        action="store_true",
        default=None,
        help="Enable rounded window corners using --radius",
    )
    render_parser.add_argument("--theme", help="Terminal color theme")
    render_parser.add_argument(
        "--frame",
        choices=["windows", "mac", "ubuntu", "frameless"],
        help="Terminal window frame style",
    )
    render_parser.add_argument(
        "--content-type",
        choices=["log", "code"],
        help="Render input as an ANSI log or syntax-highlighted source code",
    )
    render_parser.add_argument("--language", help="Pygments lexer alias, for example python, yaml, ruby, terraform")
    render_parser.add_argument(
        "--syntax-theme",
        help="Syntax highlighting preset for --content-type code",
    )
    render_parser.add_argument(
        "--no-guess-language",
        action="store_false",
        dest="guess_language",
        default=None,
        help="Disable automatic language detection for code rendering",
    )
    render_parser.add_argument(
        "--line-numbers",
        action="store_true",
        default=None,
        help="Render editor-style line numbers in a left gutter",
    )
    render_parser.add_argument("--line-number-start", type=int, help="First rendered line number")
    render_parser.add_argument(
        "--line-number-style",
        choices=["plain", "vscode", "idea"],
        help="Line number gutter style",
    )
    render_parser.add_argument(
        "--indent-guides",
        action="store_true",
        dest="indent_guides",
        default=None,
        help="Render vertical indentation guides",
    )
    render_parser.add_argument(
        "--no-indent-guides",
        action="store_false",
        dest="indent_guides",
        help="Disable vertical indentation guides",
    )
    render_parser.add_argument("--indent-size", type=int, help="Indent guide step in spaces")
    render_parser.add_argument(
        "--command-highlight",
        choices=["powershell", "cmd", "wsl", "ubuntu"],
        help="Syntax-highlight entered commands after shell prompts",
    )
    render_parser.set_defaults(func=render_command)

    themes_parser = subparsers.add_parser("themes", help="List built-in and custom themes")
    themes_parser.add_argument("--theme-file", help="JSON file with custom terminal and syntax themes")
    themes_parser.set_defaults(func=themes_command)

    apply_parser = subparsers.add_parser("apply", help="Render resources from a YAML project file")
    apply_parser.add_argument("-f", "--file", default="screenshot-compose.yml", help="Project file path")
    apply_parser.add_argument("names", nargs="*", help="Optional render resource names to render")
    apply_parser.set_defaults(func=apply_command)

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

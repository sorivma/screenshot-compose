"""Command-line entry point for screenshot-compose."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

from .cli_output import error_payload, print_json, success_payload
from .manifest import write_manifest
from .project import OutputWriteError, check_output_path, load_options_config, load_project, render_project, validate_project
from .renderer import RenderOptions, render_log_file
from .schemas import load_schema
from .themes import list_syntax_theme_names, list_terminal_theme_names


class MachineArgumentParser(argparse.ArgumentParser):
    """Argument parser that preserves the JSON contract for syntax errors."""

    def error(self, message: str) -> None:
        if "--json" in sys.argv[1:]:
            command = next((arg for arg in sys.argv[1:] if not arg.startswith("-")), "cli")
            print_json(error_payload(command, "invalid_arguments", message), error=True)
            self.exit(2)
        super().error(message)


def render_command(args: argparse.Namespace) -> int:
    options = _build_options(args)
    input_path = Path(args.input).resolve()
    output_path = Path(args.output).resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    check_output_path(output_path, args.output_root, args.force, verify_write=not args.dry_run)
    if args.manifest:
        check_output_path(Path(args.manifest), args.output_root, args.force, verify_write=not args.dry_run)
    if not args.dry_run:
        output_path = render_log_file(input_path, output_path, options)
    manifest = None
    if args.manifest and not args.dry_run:
        manifest = write_manifest(args.manifest, command="screenshot-compose render", inputs=[input_path], outputs=[output_path])
    if args.json:
        print_json(
            success_payload(
                "render",
                outputs=[output_path, *([manifest] if manifest else [])],
                data={"input": str(input_path), "dry_run": args.dry_run, "manifest": str(manifest) if manifest else None},
            )
        )
    else:
        print(f"{'Planned' if args.dry_run else 'Rendered'} {args.output}")
    return 0


def themes_command(args: argparse.Namespace) -> int:
    terminal_themes = list_terminal_theme_names(args.theme_file)
    syntax_themes = list_syntax_theme_names(args.theme_file)
    if args.json:
        print_json(
            success_payload(
                "themes",
                data={"terminal_themes": terminal_themes, "syntax_themes": syntax_themes},
            )
        )
    else:
        print("Terminal themes:")
        for name in terminal_themes:
            print(f"  {name}")
        print("Syntax themes:")
        for name in syntax_themes:
            print(f"  {name}")
    return 0


def apply_command(args: argparse.Namespace) -> int:
    if args.manifest:
        check_output_path(Path(args.manifest), args.output_root, args.force, verify_write=not args.dry_run)
    outputs = render_project(
        args.file,
        args.names,
        dry_run=args.dry_run,
        force=args.force,
        output_root=args.output_root,
    )
    manifest = None
    if args.manifest and not args.dry_run:
        resources = validate_project(args.file, args.names)
        manifest = write_manifest(
            args.manifest,
            command="screenshot-compose apply",
            inputs=[Path(args.file).resolve(), *(resource.input_path for resource in resources)],
            outputs=outputs,
        )
    if args.json:
        print_json(
            success_payload(
                "apply",
                outputs=[*outputs, *([manifest] if manifest else [])],
                data={
                    "project": str(Path(args.file).resolve()),
                    "resource_count": len(outputs),
                    "dry_run": args.dry_run,
                    "manifest": str(manifest) if manifest else None,
                },
            )
        )
    else:
        for output in outputs:
            print(f"{'Planned' if args.dry_run else 'Rendered'} {output}")
    return 0


def validate_command(args: argparse.Namespace) -> int:
    project_path = Path(args.file).resolve()
    resources = validate_project(project_path, args.names)
    data = {
        "project": str(project_path),
        "resource_count": len(resources),
        "resources": [resource.name for resource in resources],
    }
    if args.json:
        print_json(success_payload("validate", data=data))
    else:
        print(f"Project is valid: {project_path}")
        print(f"Resources: {len(resources)}")
    return 0


def schema_command(args: argparse.Namespace) -> int:
    """Print the bundled JSON Schema for a project version."""
    schema = load_schema(args.version)
    if args.json:
        print_json(success_payload("schema", data={"schema": schema, "version": args.version}))
    else:
        print_json(schema)
    return 0


def inspect_command(args: argparse.Namespace) -> int:
    """Describe installed capabilities and optionally a project file."""
    schema = load_schema()
    data = {
        "project_version": 1,
        "options": schema["$defs"]["options"]["properties"],
        "terminal_themes": list_terminal_theme_names(args.theme_file),
        "syntax_themes": list_syntax_theme_names(args.theme_file),
        "resources": [],
    }
    if args.file:
        data["resources"] = [
            {
                "name": resource.name,
                "input": str(resource.input_path),
                "output": str(resource.output_path),
            }
            for resource in load_project(args.file)
        ]
    if args.json:
        print_json(success_payload("inspect", data=data))
    else:
        print(f"Project version: {data['project_version']}")
        print(f"Options: {', '.join(sorted(data['options']))}")
        print(f"Resources: {len(data['resources'])}")
    return 0


def _add_json_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--json", action="store_true", help="Print a stable JSON response")


def _add_project_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-f", "--file", default="screenshot-compose.yml", help="Project file path")
    parser.add_argument("names", nargs="*", help="Optional render resource names")


def _add_write_safety_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dry-run", action="store_true", help="Validate and plan outputs without writing files")
    parser.add_argument("--force", action="store_true", help="Allow overwriting existing output files")
    parser.add_argument("--output-root", help="Reject outputs outside this directory")
    parser.add_argument("--manifest", help="Write a SHA-256 manifest after successful rendering")


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
    parser = MachineArgumentParser(
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
    render_parser.add_argument("--language", help="Language alias, for example python, go, yaml, ruby, or terraform")
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
    _add_json_argument(render_parser)
    _add_write_safety_arguments(render_parser)
    render_parser.set_defaults(func=render_command)

    themes_parser = subparsers.add_parser("themes", help="List built-in and custom themes")
    themes_parser.add_argument("--theme-file", help="JSON file with custom terminal and syntax themes")
    _add_json_argument(themes_parser)
    themes_parser.set_defaults(func=themes_command)

    apply_parser = subparsers.add_parser("apply", help="Render resources from a YAML project file")
    _add_project_arguments(apply_parser)
    _add_json_argument(apply_parser)
    _add_write_safety_arguments(apply_parser)
    apply_parser.set_defaults(func=apply_command)

    validate_parser = subparsers.add_parser("validate", help="Validate a YAML project file and its inputs")
    _add_project_arguments(validate_parser)
    _add_json_argument(validate_parser)
    validate_parser.set_defaults(func=validate_command)

    schema_parser = subparsers.add_parser("schema", help="Print the project JSON Schema")
    schema_parser.add_argument("--version", type=int, default=1, help="Schema version")
    _add_json_argument(schema_parser)
    schema_parser.set_defaults(func=schema_command)

    inspect_parser = subparsers.add_parser("inspect", help="Describe installed capabilities and project resources")
    inspect_parser.add_argument("-f", "--file", help="Optional project file to inspect")
    inspect_parser.add_argument("--theme-file", help="JSON file with custom terminal and syntax themes")
    _add_json_argument(inspect_parser)
    inspect_parser.set_defaults(func=inspect_command)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except OutputWriteError as exc:
        if getattr(args, "json", False):
            print_json(error_payload(args.command, "output_write_failed", str(exc)), error=True)
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 2
    except (FileNotFoundError, FileExistsError, ValueError, json.JSONDecodeError, yaml.YAMLError) as exc:
        if getattr(args, "json", False):
            print_json(error_payload(args.command, "invalid_input", str(exc)), error=True)
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:
        if getattr(args, "json", False):
            print_json(error_payload(args.command, "internal_error", str(exc)), error=True)
        else:
            print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

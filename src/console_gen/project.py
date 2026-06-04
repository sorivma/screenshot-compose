"""Project-file support for batch console screenshot rendering."""

from __future__ import annotations

import json
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any

import yaml

from .renderer import RenderOptions, render_log_file, validate_render_options
from .schemas import validate_instance


@dataclass(frozen=True)
class RenderResource:
    name: str
    input_path: Path
    output_path: Path
    options: RenderOptions


_ALIASES = {
    "width": "width_chars",
    "theme": "theme_name",
}

_VALID_OPTION_FIELDS = {field.name for field in fields(RenderOptions)}


def load_options_config(config_path: str | Path | None) -> dict[str, object]:
    if not config_path:
        return {}

    path = Path(config_path)
    raw = _load_structured_file(path)
    if not isinstance(raw, dict):
        raise ValueError("Config file must contain an object")

    return normalize_options(raw, path.parent)


def load_project(project_path: str | Path) -> list[RenderResource]:
    path = Path(project_path)
    raw = _load_structured_file(path)
    if not isinstance(raw, dict):
        raise ValueError("Project file must contain an object")

    version = raw.get("version", 1)
    validate_instance(raw, int(version) if str(version).isdigit() else version)
    if str(version) != "1":
        raise ValueError(f"Unsupported project version: {version}")

    defaults = _read_defaults(raw, path.parent)
    renders = raw.get("renders")
    if not isinstance(renders, dict) or not renders:
        raise ValueError("Project file must contain a non-empty 'renders' object")

    resources: list[RenderResource] = []
    for name, value in renders.items():
        if not isinstance(name, str):
            raise ValueError("Render resource names must be strings")
        if not isinstance(value, dict):
            raise ValueError(f"Render resource '{name}' must contain an object")

        input_value = value.get("input")
        output_value = value.get("output")
        if not isinstance(input_value, str) or not input_value:
            raise ValueError(f"Render resource '{name}' must define a non-empty input")
        if not isinstance(output_value, str) or not output_value:
            raise ValueError(f"Render resource '{name}' must define a non-empty output")

        resource_options = _read_resource_options(name, value, path.parent)
        options = RenderOptions(**(defaults | resource_options))
        resources.append(
            RenderResource(
                name=name,
                input_path=_resolve_path(path.parent, input_value),
                output_path=_resolve_path(path.parent, output_value),
                options=options,
            )
        )

    return resources


def render_project(
    project_path: str | Path,
    names: list[str] | None = None,
    *,
    dry_run: bool = False,
    force: bool = True,
    output_root: str | Path | None = None,
) -> list[Path]:
    resources = select_resources(load_project(project_path), names)
    _validate_inputs(resources)
    for resource in resources:
        check_output_path(resource.output_path, output_root, force)

    if dry_run:
        return [resource.output_path for resource in resources]

    outputs: list[Path] = []
    for resource in resources:
        outputs.append(render_log_file(resource.input_path, resource.output_path, resource.options))
    return outputs


def validate_project(project_path: str | Path, names: list[str] | None = None) -> list[RenderResource]:
    """Validate a project and ensure all selected input files exist."""
    resources = select_resources(load_project(project_path), names)
    _validate_inputs(resources)
    return resources


def _validate_inputs(resources: list[RenderResource]) -> None:
    for resource in resources:
        validate_render_options(resource.options)
    missing_inputs = [resource.input_path for resource in resources if not resource.input_path.is_file()]
    if missing_inputs:
        formatted = ", ".join(str(path) for path in missing_inputs)
        raise ValueError(f"Missing input file(s): {formatted}")


def check_output_path(output: Path, output_root: str | Path | None, force: bool) -> None:
    """Reject unsafe output paths and accidental overwrites."""
    output = output.resolve()
    if output_root:
        root = Path(output_root).resolve()
        if not output.is_relative_to(root):
            raise ValueError(f"Output path is outside --output-root: {output}")
    if output.exists() and not force:
        raise FileExistsError(f"Output already exists; use --force to overwrite: {output}")


def select_resources(resources: list[RenderResource], names: list[str] | None = None) -> list[RenderResource]:
    """Return selected resources, rejecting unknown names."""
    selected_names = set(names or [])
    unknown_names = sorted(selected_names - {resource.name for resource in resources})
    if unknown_names:
        raise ValueError(f"Unknown render resource(s): {', '.join(unknown_names)}")
    if not selected_names:
        return resources
    return [resource for resource in resources if resource.name in selected_names]


def normalize_options(raw: dict[str, Any], base_dir: Path) -> dict[str, object]:
    values: dict[str, object] = {}
    for key, value in raw.items():
        normalized_key = _ALIASES.get(key, key)
        if normalized_key not in _VALID_OPTION_FIELDS:
            raise ValueError(f"Unknown config option: {key}")
        if normalized_key == "theme_file" and isinstance(value, str):
            value = str(_resolve_path(base_dir, value))
        values[normalized_key] = value
    return values


def _load_structured_file(path: Path) -> object:
    with path.open("r", encoding="utf-8-sig") as handle:
        if path.suffix.lower() in {".yml", ".yaml"}:
            return yaml.safe_load(handle)
        return json.load(handle)


def _read_defaults(raw: dict[str, Any], base_dir: Path) -> dict[str, object]:
    defaults = raw.get("defaults", {})
    if defaults is None:
        return {}
    if not isinstance(defaults, dict):
        raise ValueError("Project defaults must contain an object")
    if "render" in defaults:
        render_defaults = defaults["render"]
        if not isinstance(render_defaults, dict):
            raise ValueError("Project defaults.render must contain an object")
        defaults = render_defaults
    return normalize_options(defaults, base_dir)


def _read_resource_options(name: str, raw: dict[str, Any], base_dir: Path) -> dict[str, object]:
    option_values = {key: value for key, value in raw.items() if key not in {"input", "output", "options"}}
    nested_options = raw.get("options", {})
    if nested_options is None:
        nested_options = {}
    if not isinstance(nested_options, dict):
        raise ValueError(f"Render resource '{name}' options must contain an object")
    option_values.update(nested_options)
    return normalize_options(option_values, base_dir)


def _resolve_path(base_dir: Path, value: str) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return (base_dir / path).resolve()

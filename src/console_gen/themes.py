"""Theme loading for terminal and syntax rendering."""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any

from pygments.token import Token

from .highlighting.model import TokenKind
from .highlighting.pygments_provider import token_kind


@dataclass(frozen=True)
class TerminalTheme:
    background: str
    titlebar: str
    title_text: str
    text: str
    muted: str
    border: str
    shadow: str


@dataclass(frozen=True)
class SyntaxTheme:
    background: str
    text: str
    colors: tuple[tuple[TokenKind, str, bool], ...]


@dataclass(frozen=True)
class ThemeCatalog:
    terminal_themes: dict[str, TerminalTheme]
    auto_themes: dict[str, str]
    syntax_themes: dict[str, SyntaxTheme]


def load_theme_catalog(theme_file: str | Path | None = None) -> ThemeCatalog:
    raw = _load_builtin_raw()
    if theme_file:
        raw = _merge_theme_data(raw, _load_json(Path(theme_file)))
    return _parse_catalog(raw)


def list_terminal_theme_names(theme_file: str | Path | None = None) -> list[str]:
    return sorted(load_theme_catalog(theme_file).terminal_themes)


def list_syntax_theme_names(theme_file: str | Path | None = None) -> list[str]:
    return sorted(load_theme_catalog(theme_file).syntax_themes)


def _load_builtin_raw() -> dict[str, Any]:
    data = resources.files(__package__).joinpath("themes.json").read_text(encoding="utf-8")
    return json.loads(data)


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8-sig") as handle:
        raw = json.load(handle)
    if not isinstance(raw, dict):
        raise ValueError("Theme file must contain a JSON object")
    return raw


def _merge_theme_data(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = {
        "terminal_themes": dict(base.get("terminal_themes", {})),
        "auto_themes": dict(base.get("auto_themes", {})),
        "syntax_themes": dict(base.get("syntax_themes", {})),
    }
    for key in merged:
        value = override.get(key, {})
        if value is None:
            continue
        if not isinstance(value, dict):
            raise ValueError(f"Theme file section must be an object: {key}")
        merged[key].update(value)
    unknown = set(override) - set(merged)
    if unknown:
        raise ValueError(f"Unknown theme file section: {sorted(unknown)[0]}")
    return merged


def _parse_catalog(raw: dict[str, Any]) -> ThemeCatalog:
    return ThemeCatalog(
        terminal_themes=_parse_terminal_themes(raw.get("terminal_themes", {})),
        auto_themes=_parse_auto_themes(raw.get("auto_themes", {})),
        syntax_themes=_parse_syntax_themes(raw.get("syntax_themes", {})),
    )


def _parse_terminal_themes(raw: object) -> dict[str, TerminalTheme]:
    if not isinstance(raw, dict):
        raise ValueError("terminal_themes must be an object")
    return {name: _parse_terminal_theme(name, value) for name, value in raw.items()}


def _parse_terminal_theme(name: str, raw: object) -> TerminalTheme:
    if not isinstance(raw, dict):
        raise ValueError(f"Terminal theme must be an object: {name}")
    fields = ("background", "titlebar", "title_text", "text", "muted", "border", "shadow")
    values = {field: _read_color(raw, field, f"terminal_themes.{name}") for field in fields}
    return TerminalTheme(**values)


def _parse_auto_themes(raw: object) -> dict[str, str]:
    if not isinstance(raw, dict):
        raise ValueError("auto_themes must be an object")
    values: dict[str, str] = {}
    for frame, theme_name in raw.items():
        if not isinstance(theme_name, str):
            raise ValueError(f"auto_themes.{frame} must be a theme name")
        values[str(frame)] = theme_name
    return values


def _parse_syntax_themes(raw: object) -> dict[str, SyntaxTheme]:
    if not isinstance(raw, dict):
        raise ValueError("syntax_themes must be an object")
    return {name: _parse_syntax_theme(name, value) for name, value in raw.items()}


def _parse_syntax_theme(name: str, raw: object) -> SyntaxTheme:
    if not isinstance(raw, dict):
        raise ValueError(f"Syntax theme must be an object: {name}")
    colors = raw.get("colors", [])
    if not isinstance(colors, list):
        raise ValueError(f"syntax_themes.{name}.colors must be a list")
    return SyntaxTheme(
        background=_read_color(raw, "background", f"syntax_themes.{name}"),
        text=_read_color(raw, "text", f"syntax_themes.{name}"),
        colors=tuple(_parse_token_color(name, item) for item in colors),
    )


def _parse_token_color(theme_name: str, raw: object) -> tuple[TokenKind, str, bool]:
    if not isinstance(raw, dict):
        raise ValueError(f"syntax_themes.{theme_name}.colors entries must be objects")
    token_name = raw.get("token")
    if not isinstance(token_name, str):
        raise ValueError(f"syntax_themes.{theme_name}.colors[].token must be a string")
    color = _read_color(raw, "color", f"syntax_themes.{theme_name}.colors[{token_name}]")
    return _resolve_token(token_name), color, bool(raw.get("bold", False))


def _resolve_token(token_name: str) -> TokenKind:
    normalized = token_name.lower()
    aliases = {
        "text": TokenKind.TEXT,
        "comment": TokenKind.COMMENT,
        "keyword": TokenKind.KEYWORD,
        "keyword.namespace": TokenKind.KEYWORD,
        "keyword.type": TokenKind.TYPE,
        "name": TokenKind.VARIABLE,
        "name.other": TokenKind.VARIABLE,
        "name.function": TokenKind.FUNCTION,
        "name.class": TokenKind.TYPE,
        "name.builtin": TokenKind.BUILTIN,
        "name.decorator": TokenKind.DECORATOR,
        "name.tag": TokenKind.TAG,
        "name.attribute": TokenKind.ATTRIBUTE,
        "name.variable": TokenKind.VARIABLE,
        "name.namespace": TokenKind.NAMESPACE,
        "string": TokenKind.STRING,
        "number": TokenKind.NUMBER,
        "literal": TokenKind.NUMBER,
        "operator": TokenKind.OPERATOR,
        "punctuation": TokenKind.PUNCTUATION,
        "generic.heading": TokenKind.HEADING,
        "generic.subheading": TokenKind.SUBHEADING,
        "generic.deleted": TokenKind.DELETED,
        "generic.inserted": TokenKind.INSERTED,
        "error": TokenKind.ERROR,
    }
    try:
        return TokenKind(normalized)
    except ValueError:
        pass
    try:
        return aliases[normalized]
    except KeyError:
        pass
    try:
        pygments_token = Token
        for part in token_name.split("."):
            if not part:
                raise ValueError
            pygments_token = getattr(pygments_token, part)
        return token_kind(pygments_token)
    except (AttributeError, ValueError) as exc:
        available = ", ".join(kind.value for kind in TokenKind)
        raise ValueError(f"Unknown syntax token: {token_name}. Available semantic tokens: {available}") from exc


def _read_color(raw: dict[str, Any], key: str, context: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not _is_hex_color(value):
        raise ValueError(f"{context}.{key} must be a hex color like #ffffff")
    return value


def _is_hex_color(value: str) -> bool:
    if len(value) != 7 or value[0] != "#":
        return False
    return all(char in "0123456789abcdefABCDEF" for char in value[1:])


BUILTIN_CATALOG = load_theme_catalog()
THEMES = BUILTIN_CATALOG.terminal_themes
AUTO_THEMES = BUILTIN_CATALOG.auto_themes
SYNTAX_THEMES = BUILTIN_CATALOG.syntax_themes

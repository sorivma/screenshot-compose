"""Small ANSI SGR parser used by the terminal renderer."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable


SGR_PATTERN = re.compile(r"\x1b\[([0-9;]*)m")


@dataclass(frozen=True)
class TextStyle:
    fg: str
    bg: str | None = None
    bold: bool = False


@dataclass(frozen=True)
class TextSpan:
    text: str
    style: TextStyle


ANSI_FG = {
    30: "#2e3436",
    31: "#cc0000",
    32: "#4e9a06",
    33: "#c4a000",
    34: "#3465a4",
    35: "#75507b",
    36: "#06989a",
    37: "#d3d7cf",
    90: "#555753",
    91: "#ef2929",
    92: "#8ae234",
    93: "#fce94f",
    94: "#729fcf",
    95: "#ad7fa8",
    96: "#34e2e2",
    97: "#eeeeec",
}


def parse_ansi(text: str, default_fg: str) -> list[TextSpan]:
    """Parse a string with SGR escapes into styled spans."""
    spans: list[TextSpan] = []
    style = TextStyle(default_fg)
    cursor = 0

    for match in SGR_PATTERN.finditer(text):
        if match.start() > cursor:
            spans.append(TextSpan(text[cursor : match.start()], style))

        codes = _parse_codes(match.group(1))
        style = _apply_codes(style, codes, default_fg)
        cursor = match.end()

    if cursor < len(text):
        spans.append(TextSpan(text[cursor:], style))

    return _merge_adjacent(spans)


def strip_ansi(text: str) -> str:
    return SGR_PATTERN.sub("", text)


def _parse_codes(raw: str) -> list[int]:
    if not raw:
        return [0]
    return [int(part) if part else 0 for part in raw.split(";")]


def _apply_codes(style: TextStyle, codes: Iterable[int], default_fg: str) -> TextStyle:
    fg = style.fg
    bg = style.bg
    bold = style.bold
    code_list = list(codes)
    index = 0

    while index < len(code_list):
        code = code_list[index]
        if code == 0:
            fg = default_fg
            bg = None
            bold = False
        elif code == 1:
            bold = True
        elif code == 22:
            bold = False
        elif code == 39:
            fg = default_fg
        elif code in ANSI_FG:
            fg = ANSI_FG[code]
        elif code == 49:
            bg = None
        elif 40 <= code <= 47:
            bg = ANSI_FG.get(code - 10, bg)
        elif 100 <= code <= 107:
            bg = ANSI_FG.get(code - 10, bg)
        elif code in (38, 48):
            parsed = _parse_extended_color(code_list, index)
            if parsed:
                color, consumed = parsed
                if code == 38:
                    fg = color
                else:
                    bg = color
                index += consumed
        index += 1

    return TextStyle(fg=fg, bg=bg, bold=bold)


def _parse_extended_color(codes: list[int], index: int) -> tuple[str, int] | None:
    if index + 2 >= len(codes):
        return None

    mode = codes[index + 1]
    if mode == 5:
        return _ansi_256_to_hex(codes[index + 2]), 2

    if mode == 2 and index + 4 < len(codes):
        r, g, b = codes[index + 2 : index + 5]
        return f"#{_clamp_channel(r):02x}{_clamp_channel(g):02x}{_clamp_channel(b):02x}", 4

    return None


def _ansi_256_to_hex(value: int) -> str:
    value = max(0, min(value, 255))
    if value < 16:
        return ANSI_FG.get(30 + value, "#eeeeec") if value < 8 else ANSI_FG.get(90 + value - 8, "#eeeeec")
    if value < 232:
        value -= 16
        r = value // 36
        g = (value % 36) // 6
        b = value % 6
        return f"#{_cube_channel(r):02x}{_cube_channel(g):02x}{_cube_channel(b):02x}"
    gray = 8 + (value - 232) * 10
    return f"#{gray:02x}{gray:02x}{gray:02x}"


def _cube_channel(value: int) -> int:
    return 0 if value == 0 else 55 + value * 40


def _clamp_channel(value: int) -> int:
    return max(0, min(value, 255))


def _merge_adjacent(spans: list[TextSpan]) -> list[TextSpan]:
    merged: list[TextSpan] = []
    for span in spans:
        if not span.text:
            continue
        if merged and merged[-1].style == span.style:
            previous = merged[-1]
            merged[-1] = TextSpan(previous.text + span.text, previous.style)
        else:
            merged.append(span)
    return merged

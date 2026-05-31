"""Render terminal-like screenshots from console logs."""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from .ansi import SGR_PATTERN, TextSpan, TextStyle, parse_ansi, strip_ansi

try:
    from pygments import lex
    from pygments.lexers.shell import BashLexer, PowerShellLexer
    from pygments.token import Comment, Error, Generic, Keyword, Literal, Name, Number, Operator, String, Text, Token
except ImportError:  # pragma: no cover - fallback for minimal runtime environments.
    lex = None
    BashLexer = None
    PowerShellLexer = None
    Comment = Error = Generic = Keyword = Literal = Name = Number = Operator = String = Text = Token = None


@dataclass(frozen=True)
class TerminalTheme:
    background: str
    titlebar: str
    title_text: str
    text: str
    muted: str
    border: str
    shadow: str


THEMES = {
    "auto": TerminalTheme(
        background="#111316",
        titlebar="#24272c",
        title_text="#d7dae0",
        text="#e6e6e6",
        muted="#8b949e",
        border="#343942",
        shadow="#000000",
    ),
    "dark": TerminalTheme(
        background="#111316",
        titlebar="#24272c",
        title_text="#d7dae0",
        text="#e6e6e6",
        muted="#8b949e",
        border="#343942",
        shadow="#000000",
    ),
    "light": TerminalTheme(
        background="#f7f7f7",
        titlebar="#e6e8eb",
        title_text="#2f3337",
        text="#202327",
        muted="#69707a",
        border="#c9cdd3",
        shadow="#808080",
    ),
    "ubuntu": TerminalTheme(
        background="#300a24",
        titlebar="#2c2c2c",
        title_text="#eeeeec",
        text="#eeeeec",
        muted="#ad7fa8",
        border="#4a223c",
        shadow="#000000",
    ),
    "powershell": TerminalTheme(
        background="#012456",
        titlebar="#1f1f1f",
        title_text="#f3f3f3",
        text="#f3f3f3",
        muted="#9cdcfe",
        border="#153a70",
        shadow="#000000",
    ),
    "macos": TerminalTheme(
        background="#1e1e1e",
        titlebar="#343434",
        title_text="#ededed",
        text="#f2f2f2",
        muted="#9b9b9b",
        border="#555555",
        shadow="#000000",
    ),
}

AUTO_THEMES = {
    "frameless": "ubuntu",
    "mac": "macos",
    "ubuntu": "ubuntu",
    "windows": "powershell",
}

COLOR_PROFILES = ("auto", "none", "ubuntu", "powershell", "macos")


@dataclass(frozen=True)
class RenderOptions:
    width_chars: int = 100
    font_size: int = 16
    line_spacing: int = 5
    padding_x: int = 22
    padding_y: int = 18
    titlebar_height: int = 38
    radius: int = 10
    title: str = "Terminal"
    theme_name: str = "auto"
    frame: str = "windows"
    color_profile: str = "auto"


def render_log_file(input_path: Path, output_path: Path, options: RenderOptions) -> Path:
    text = input_path.read_text(encoding="utf-8-sig")
    image = render_log(text, options)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return output_path


def render_log(text: str, options: RenderOptions | None = None) -> Image.Image:
    options = options or RenderOptions()
    theme = _resolve_theme(options)
    color_profile = _resolve_color_profile(options)
    regular_font, bold_font = load_fonts(options.font_size)
    metrics = _font_metrics(regular_font)

    visual_lines = _build_visual_lines(text, options.width_chars, theme.text, color_profile)
    if not visual_lines:
        visual_lines = [[]]

    char_width = int(round(regular_font.getlength("M")))
    line_height = metrics["height"] + options.line_spacing
    content_width = options.width_chars * char_width
    window_width = content_width + options.padding_x * 2
    content_height = len(visual_lines) * line_height - options.line_spacing
    titlebar_height = 0 if options.frame == "frameless" else options.titlebar_height
    window_height = titlebar_height + options.padding_y * 2 + content_height

    margin = 14 if options.frame == "frameless" else 24
    image = Image.new("RGBA", (window_width + margin * 2, window_height + margin * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    window_box = (margin, margin, margin + window_width, margin + window_height)
    if options.frame != "frameless":
        _draw_shadow(image, window_box, options.radius)
    _draw_window(draw, window_box, options, theme)
    if options.frame != "frameless":
        _draw_titlebar(draw, window_box, options, theme, regular_font)

    text_x = margin + options.padding_x
    text_y = margin + titlebar_height + options.padding_y
    _draw_text_lines(
        draw=draw,
        lines=visual_lines,
        x=text_x,
        y=text_y,
        line_height=line_height,
        regular_font=regular_font,
        bold_font=bold_font,
        char_width=char_width,
    )

    return image


def _resolve_theme(options: RenderOptions) -> TerminalTheme:
    theme_name = options.theme_name
    if theme_name == "auto":
        theme_name = AUTO_THEMES.get(options.frame, "dark")
    return THEMES[theme_name]


def _resolve_color_profile(options: RenderOptions) -> str:
    if options.color_profile == "auto":
        return {
            "frameless": "ubuntu",
            "mac": "macos",
            "ubuntu": "ubuntu",
            "windows": "powershell",
        }.get(options.frame, "ubuntu")
    return options.color_profile


def load_fonts(size: int) -> tuple[ImageFont.FreeTypeFont | ImageFont.ImageFont, ImageFont.FreeTypeFont | ImageFont.ImageFont]:
    candidates = [
        ("C:/Windows/Fonts/CascadiaMono.ttf", "C:/Windows/Fonts/CascadiaMono.ttf"),
        ("C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/consolab.ttf"),
        ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"),
        ("/Library/Fonts/Menlo.ttc", "/Library/Fonts/Menlo.ttc"),
    ]
    for regular_path, bold_path in candidates:
        if Path(regular_path).exists():
            regular = ImageFont.truetype(regular_path, size=size)
            bold = ImageFont.truetype(bold_path if Path(bold_path).exists() else regular_path, size=size)
            return regular, bold
    return ImageFont.load_default(), ImageFont.load_default()


def _build_visual_lines(text: str, width_chars: int, default_fg: str, color_profile: str) -> list[list[TextSpan]]:
    visual_lines: list[list[TextSpan]] = []
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").expandtabs(4)

    for raw_line in normalized.split("\n"):
        spans = _parse_line(raw_line, default_fg, color_profile)
        if not spans:
            visual_lines.append([])
            continue

        current: list[TextSpan] = []
        current_len = 0
        for span in spans:
            for chunk in _wrap_span(span, width_chars, current_len):
                if chunk == "\n":
                    visual_lines.append(current)
                    current = []
                    current_len = 0
                    continue
                current.append(TextSpan(chunk, span.style))
                current_len += len(strip_ansi(chunk))
        visual_lines.append(current)

    return visual_lines


def _parse_line(raw_line: str, default_fg: str, color_profile: str) -> list[TextSpan]:
    if color_profile == "none" or SGR_PATTERN.search(raw_line):
        return parse_ansi(raw_line, default_fg)
    return _auto_color_line(raw_line, default_fg, color_profile)


def _auto_color_line(raw_line: str, default_fg: str, color_profile: str) -> list[TextSpan]:
    if not raw_line:
        return []

    palette = _profile_palette(color_profile)
    base = TextStyle(default_fg)
    spans: list[TextSpan] = []

    prompt_match = _match_prompt(raw_line, color_profile)
    cursor = 0
    if prompt_match:
        for start, end, color, bold in prompt_match:
            if start > cursor:
                spans.append(TextSpan(raw_line[cursor:start], base))
            spans.append(TextSpan(raw_line[start:end], TextStyle(color, bold=bold)))
            cursor = end

    tail = raw_line[cursor:]
    if tail:
        spans.extend(_highlight_code(tail, base, palette, color_profile))

    return spans


def _match_prompt(raw_line: str, color_profile: str) -> list[tuple[int, int, str, bool]]:
    if color_profile == "powershell":
        match = re.match(r"^(PS )([^>]+)(>)\s?", raw_line)
        if not match:
            return []
        return [
            (match.start(1), match.end(1), "#f3f3f3", True),
            (match.start(2), match.end(2), "#9cdcfe", False),
            (match.start(3), match.end(3), "#f3f3f3", True),
        ]

    match = re.match(r"^([\w.-]+@[\w.-]+)(:)([^#$]*)([#$])\s?", raw_line)
    if match:
        return [
            (match.start(1), match.end(1), "#8ae234", True),
            (match.start(2), match.end(2), "#eeeeec", False),
            (match.start(3), match.end(3), "#729fcf", True),
            (match.start(4), match.end(4), "#eeeeec", True),
        ]

    match = re.match(r"^([\w.-]+@[\w.-]+)(\s+)([^%]+)(\s+%)(\s?)", raw_line)
    if match:
        return [
            (match.start(1), match.end(1), "#a6e22e", True),
            (match.start(3), match.end(3), "#66d9ef", True),
            (match.start(4), match.end(4), "#f2f2f2", True),
        ]

    match = re.match(r"^([$#%])\s?", raw_line)
    if match:
        return [(match.start(1), match.end(1), "#8ae234" if color_profile == "ubuntu" else "#f2f2f2", True)]

    return []


def _profile_palette(color_profile: str) -> dict[str, str]:
    if color_profile == "powershell":
        return {
            "success": "#16c60c",
            "warning": "#f9f1a5",
            "error": "#f14c4c",
            "path": "#9cdcfe",
            "command": "#c586c0",
            "number": "#b5cea8",
            "muted": "#c8c8c8",
            "keyword": "#569cd6",
            "string": "#ce9178",
            "variable": "#9cdcfe",
            "comment": "#6a9955",
            "operator": "#d4d4d4",
        }
    if color_profile == "macos":
        return {
            "success": "#a6e22e",
            "warning": "#e6db74",
            "error": "#f92672",
            "path": "#66d9ef",
            "command": "#ae81ff",
            "number": "#ae81ff",
            "muted": "#a6a6a6",
            "keyword": "#66d9ef",
            "string": "#e6db74",
            "variable": "#fd971f",
            "comment": "#75715e",
            "operator": "#f92672",
        }
    return {
        "success": "#8ae234",
        "warning": "#fce94f",
        "error": "#ef2929",
        "path": "#729fcf",
        "command": "#ad7fa8",
        "number": "#fce94f",
        "muted": "#d3d7cf",
        "keyword": "#729fcf",
        "string": "#ad7fa8",
        "variable": "#fce94f",
        "comment": "#888a85",
        "operator": "#eeeeec",
    }


TOKEN_PATTERN = re.compile(
    r"(https?://\S+|(?:[A-Za-z]:\\[^\s]+|/[\w./~+-]+)|\b(?:error|failed|failure|fatal|exception)\b|\b(?:warn|warning)\b|\b(?:success|successful|passed|ok|done|installed|initialized)\b|\b\d+(?:\.\d+)?%?\b|^\s*(?:\$|#|%|PS\s+[^>]+>)\s*\w[\w.-]*)",
    re.IGNORECASE,
)


def _highlight_code(text: str, base: TextStyle, palette: dict[str, str], color_profile: str) -> list[TextSpan]:
    spans = _highlight_with_pygments(text, base, palette, color_profile)
    if spans is not None:
        return _merge_spans(_post_highlight_log_tokens(spans, base, palette))
    return _highlight_tokens(text, base, palette)


def _highlight_with_pygments(
    text: str,
    base: TextStyle,
    palette: dict[str, str],
    color_profile: str,
) -> list[TextSpan] | None:
    if lex is None or BashLexer is None or PowerShellLexer is None:
        return None

    lexer = PowerShellLexer() if color_profile == "powershell" else BashLexer()
    spans: list[TextSpan] = []
    try:
        tokens = lex(text, lexer)
        for token_type, value in tokens:
            if not value:
                continue
            if value == "\n" and not text.endswith("\n"):
                continue
            spans.append(TextSpan(value, _style_for_token(token_type, base, palette)))
    except Exception:
        return None

    return spans


def _style_for_token(token_type, base: TextStyle, palette: dict[str, str]) -> TextStyle:
    if Text is not None and token_type in Text:
        return base
    if Error is not None and token_type in Error:
        return TextStyle(palette["error"], bold=True)
    if Comment is not None and token_type in Comment:
        return TextStyle(palette["comment"])
    if Keyword is not None and token_type in Keyword:
        return TextStyle(palette["keyword"], bold=True)
    if String is not None and token_type in String:
        return TextStyle(palette["string"])
    if Number is not None and token_type in Number:
        return TextStyle(palette["number"])
    if Token is not None and token_type in Token.Name.Builtin:
        return TextStyle(palette["keyword"], bold=True)
    if Name is not None and token_type in Name:
        return TextStyle(palette["variable"] if _is_variable_token(token_type) else palette["command"])
    if Operator is not None and token_type in Operator:
        return TextStyle(palette["operator"])
    if Literal is not None and token_type in Literal:
        return TextStyle(palette["string"])
    if Generic is not None and token_type in Generic:
        return base
    return base


def _is_variable_token(token_type) -> bool:
    return Token is not None and token_type in Token.Name.Variable


def _post_highlight_log_tokens(spans: list[TextSpan], base: TextStyle, palette: dict[str, str]) -> list[TextSpan]:
    result: list[TextSpan] = []
    for span in spans:
        if span.style == base:
            result.extend(_highlight_tokens(span.text, span.style, palette))
        else:
            result.append(span)
    return result


def _highlight_tokens(text: str, base: TextStyle, palette: dict[str, str]) -> list[TextSpan]:
    spans: list[TextSpan] = []
    cursor = 0
    for match in TOKEN_PATTERN.finditer(text):
        if match.start() > cursor:
            spans.append(TextSpan(text[cursor : match.start()], base))
        token = match.group(0)
        spans.append(TextSpan(token, TextStyle(_token_color(token, palette), bold=_is_strong_token(token))))
        cursor = match.end()
    if cursor < len(text):
        spans.append(TextSpan(text[cursor:], base))
    return spans


def _merge_spans(spans: list[TextSpan]) -> list[TextSpan]:
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


def _token_color(token: str, palette: dict[str, str]) -> str:
    lower = token.lower()
    if any(word in lower for word in ("error", "failed", "failure", "fatal", "exception")):
        return palette["error"]
    if "warn" in lower:
        return palette["warning"]
    if any(word in lower for word in ("success", "successful", "passed", "ok", "done", "installed", "initialized")):
        return palette["success"]
    if token.startswith(("http://", "https://", "/", "~")) or re.match(r"^[A-Za-z]:\\", token):
        return palette["path"]
    if re.match(r"^\s*(?:\$|#|%|PS\s+[^>]+>)\s*\w", token):
        return palette["command"]
    if re.match(r"^\d", token):
        return palette["number"]
    return palette["muted"]


def _is_strong_token(token: str) -> bool:
    lower = token.lower()
    return any(word in lower for word in ("error", "failed", "fatal", "success", "passed", "warning"))


def _wrap_span(span: TextSpan, width_chars: int, current_len: int) -> list[str]:
    chunks: list[str] = []
    text = span.text
    while text:
        room = width_chars - current_len
        if room <= 0:
            chunks.append("\n")
            current_len = 0
            room = width_chars

        piece = text[:room]
        chunks.append(piece)
        text = text[room:]
        current_len += len(piece)

    return chunks


def _font_metrics(font: ImageFont.ImageFont) -> dict[str, int]:
    bbox = font.getbbox("Ag")
    return {"height": bbox[3] - bbox[1], "baseline_offset": -bbox[1]}


def _draw_shadow(image: Image.Image, box: tuple[int, int, int, int], radius: int) -> None:
    shadow = Image.new("RGBA", image.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    offset_box = (box[0] + 2, box[1] + 8, box[2] + 2, box[3] + 8)
    shadow_draw.rounded_rectangle(offset_box, radius=radius, fill=(0, 0, 0, 90))
    blurred = shadow.filter(ImageFilter.GaussianBlur(10))
    image.alpha_composite(blurred)


def _draw_window(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    options: RenderOptions,
    theme: TerminalTheme,
) -> None:
    draw.rounded_rectangle(box, radius=options.radius, fill=theme.background, outline=theme.border, width=1)


def _draw_titlebar(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    options: RenderOptions,
    theme: TerminalTheme,
    font: ImageFont.ImageFont,
) -> None:
    x1, y1, x2, _ = box
    title_box = (x1, y1, x2, y1 + options.titlebar_height)
    draw.rounded_rectangle(title_box, radius=options.radius, fill=theme.titlebar)
    draw.rectangle((x1, y1 + options.radius, x2, y1 + options.titlebar_height), fill=theme.titlebar)
    draw.line((x1, y1 + options.titlebar_height, x2, y1 + options.titlebar_height), fill=theme.border)

    if options.frame == "mac":
        _draw_mac_controls(draw, x1, y1, options)
    elif options.frame == "ubuntu":
        _draw_ubuntu_controls(draw, x1, y1, options)
    else:
        _draw_windows_controls(draw, x2, y1, options, theme)

    title = textwrap.shorten(options.title, width=72, placeholder="...")
    bbox = draw.textbbox((0, 0), title, font=font)
    title_x = x1 + (x2 - x1 - (bbox[2] - bbox[0])) / 2
    if options.frame == "windows":
        title_x = max(title_x, x1 + 18)
    draw.text((title_x, y1 + 10), title, fill=theme.title_text, font=font)


def _draw_mac_controls(
    draw: ImageDraw.ImageDraw,
    x1: int,
    y1: int,
    options: RenderOptions,
) -> None:
    button_y = y1 + options.titlebar_height // 2
    for index, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        cx = x1 + 19 + index * 18
        draw.ellipse((cx - 5, button_y - 5, cx + 5, button_y + 5), fill=color)


def _draw_ubuntu_controls(
    draw: ImageDraw.ImageDraw,
    x1: int,
    y1: int,
    options: RenderOptions,
) -> None:
    button_y = y1 + options.titlebar_height // 2
    colors = ("#e95420", "#f4c430", "#3eb489")
    symbols = ("x", "-", "+")
    for index, color in enumerate(colors):
        cx = x1 + 20 + index * 20
        draw.ellipse((cx - 6, button_y - 6, cx + 6, button_y + 6), fill=color)
        if symbols[index] == "x":
            draw.line((cx - 3, button_y - 3, cx + 3, button_y + 3), fill="#ffffff", width=1)
            draw.line((cx + 3, button_y - 3, cx - 3, button_y + 3), fill="#ffffff", width=1)
        elif symbols[index] == "-":
            draw.line((cx - 4, button_y, cx + 4, button_y), fill="#3a2f2a", width=1)
        else:
            draw.line((cx - 4, button_y, cx + 4, button_y), fill="#ffffff", width=1)
            draw.line((cx, button_y - 4, cx, button_y + 4), fill="#ffffff", width=1)


def _draw_windows_controls(
    draw: ImageDraw.ImageDraw,
    x2: int,
    y1: int,
    options: RenderOptions,
    theme: TerminalTheme,
) -> None:
    control_w = 46
    top = y1
    bottom = y1 + options.titlebar_height
    close_left = x2 - control_w
    max_left = close_left - control_w
    min_left = max_left - control_w
    cy = y1 + options.titlebar_height // 2

    draw.rectangle((close_left, top + 1, x2 - 1, bottom - 1), fill="#c42b1c")
    draw.line((min_left + 17, cy + 5, min_left + 29, cy + 5), fill=theme.title_text, width=1)
    draw.rectangle((max_left + 18, cy - 5, max_left + 29, cy + 6), outline=theme.title_text, width=1)
    draw.line((close_left + 18, cy - 5, close_left + 29, cy + 6), fill="#ffffff", width=1)
    draw.line((close_left + 29, cy - 5, close_left + 18, cy + 6), fill="#ffffff", width=1)


def _draw_text_lines(
    draw: ImageDraw.ImageDraw,
    lines: list[list[TextSpan]],
    x: int,
    y: int,
    line_height: int,
    regular_font: ImageFont.ImageFont,
    bold_font: ImageFont.ImageFont,
    char_width: int,
) -> None:
    cursor_y = y
    for line in lines:
        cursor_x = x
        for span in line:
            font = bold_font if span.style.bold else regular_font
            if span.style.bg:
                draw.rectangle(
                    (cursor_x, cursor_y - 1, cursor_x + len(span.text) * char_width, cursor_y + line_height - 2),
                    fill=span.style.bg,
                )
            draw.text((cursor_x, cursor_y), span.text, fill=span.style.fg, font=font)
            cursor_x += len(span.text) * char_width
        cursor_y += line_height

"""Render terminal-like screenshots from console logs."""

from __future__ import annotations

import textwrap
from dataclasses import dataclass, replace
from math import ceil
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont
from pygments import lex
from pygments.lexers import TextLexer, get_lexer_by_name, guess_lexer, guess_lexer_for_filename
from pygments.token import Keyword, Name, Text, Token

from .ansi import TextSpan, TextStyle, parse_ansi, strip_ansi
from .themes import AUTO_THEMES, SYNTAX_THEMES, THEMES, SyntaxTheme, TerminalTheme, load_theme_catalog


@dataclass(frozen=True)
class RenderOptions:
    width_chars: int = 100
    wrap_lines: bool = False
    font_size: int = 16
    line_spacing: int | None = None
    padding_x: int = 22
    padding_y: int = 18
    margin: int | None = None
    titlebar_height: int = 38
    radius: int = 10
    rounded_corners: bool = False
    title: str = "Terminal"
    theme_name: str = "auto"
    frame: str = "windows"
    content_type: str = "log"
    language: str | None = None
    syntax_theme: str = "vscode-dark"
    guess_language: bool = True
    theme_file: str | None = None
    line_numbers: bool = False
    line_number_start: int = 1
    line_number_style: str = "plain"
    indent_guides: bool | None = None
    indent_size: int = 4
    command_highlight: str | None = None


@dataclass(frozen=True)
class LineNumberStyle:
    foreground: str
    background: str | None = None
    separator: str | None = None
    padding_left_chars: float = 1
    padding_right_chars: float = 2
    separator_gap_chars: float = 0
    align: str = "right"


def render_log_file(input_path: Path, output_path: Path, options: RenderOptions) -> Path:
    return render_text_file(input_path, output_path, options)


def render_code_file(input_path: Path, output_path: Path, options: RenderOptions | None = None) -> Path:
    options = options or RenderOptions(content_type="code", title=input_path.name)
    if options.content_type == "log":
        options = replace(options, content_type="code")
    return render_text_file(input_path, output_path, options)


def render_text_file(input_path: Path, output_path: Path, options: RenderOptions) -> Path:
    text = input_path.read_text(encoding="utf-8-sig")
    image = render_text(text, options, filename=input_path.name)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(output_path)
    return output_path


def render_log(text: str, options: RenderOptions | None = None) -> Image.Image:
    return render_text(text, options or RenderOptions(content_type="log"))


def render_code(text: str, options: RenderOptions | None = None, filename: str | None = None) -> Image.Image:
    options = options or RenderOptions(content_type="code", title=filename or "Code")
    if options.content_type == "log":
        options = replace(options, content_type="code")
    return render_text(text, options, filename=filename)


def render_text(text: str, options: RenderOptions | None = None, filename: str | None = None) -> Image.Image:
    options = options or RenderOptions()
    theme = _resolve_theme(options)
    regular_font, bold_font = load_fonts(options.font_size)
    metrics = _font_metrics(regular_font)

    default_fg = _resolve_syntax_theme(options).text if options.content_type == "code" else theme.text
    numbered_visual_lines = _build_numbered_visual_lines(text, options.width_chars, default_fg, options, filename)
    if not numbered_visual_lines:
        numbered_visual_lines = [([], None)]
    visual_lines = [line for line, _ in numbered_visual_lines]

    char_width = int(round(regular_font.getlength("M")))
    line_spacing = _resolve_line_spacing(options)
    line_height = metrics["height"] + line_spacing
    content_chars = _content_width_chars(visual_lines, options.width_chars)
    content_width = content_chars * char_width
    line_number_style = _resolve_line_number_style(options, theme)
    line_number_width = _line_number_width(numbered_visual_lines, options, line_number_style, char_width)
    window_width = content_width + line_number_width + options.padding_x * 2
    content_height = len(visual_lines) * line_height - line_spacing
    titlebar_height = 0 if options.frame == "frameless" else options.titlebar_height
    window_height = titlebar_height + options.padding_y * 2 + content_height

    margin = _resolve_margin(options)
    draw_options = replace(options, radius=_resolve_radius(options))
    image = Image.new("RGBA", (window_width + margin * 2, window_height + margin * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    window_box = (margin, margin, margin + window_width, margin + window_height)
    if options.frame != "frameless":
        _draw_shadow(image, window_box, draw_options.radius)
    _draw_window(draw, window_box, draw_options, theme)
    if options.frame != "frameless":
        _draw_titlebar(image, draw, window_box, draw_options, theme, regular_font)

    gutter_x = margin + options.padding_x
    text_x = gutter_x + line_number_width
    text_y = margin + titlebar_height + options.padding_y
    if options.line_numbers:
        _draw_line_numbers(
            draw=draw,
            numbered_lines=numbered_visual_lines,
            x=gutter_x,
            y=text_y,
            line_height=line_height,
            font=regular_font,
            char_width=char_width,
            style=line_number_style,
            text_y=text_y,
            text_height=content_height,
        )
    if _resolve_indent_guides(options):
        _draw_indent_guides(
            draw=draw,
            lines=visual_lines,
            x=text_x,
            y=text_y,
            line_height=line_height,
            char_width=char_width,
            indent_size=options.indent_size,
            color=_indent_guide_color(theme),
            y_inset=max(1, line_spacing // 2),
        )
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
    catalog = load_theme_catalog(options.theme_file)
    theme_name = options.theme_name
    if theme_name == "auto":
        theme_name = catalog.auto_themes.get(options.frame, "dark")
    try:
        theme = catalog.terminal_themes[theme_name]
    except KeyError as exc:
        available = ", ".join(sorted(catalog.terminal_themes))
        raise ValueError(f"Unknown terminal theme: {theme_name}. Available themes: {available}") from exc
    if options.content_type != "code":
        return theme

    syntax_theme = _resolve_syntax_theme(options)
    return TerminalTheme(
        background=syntax_theme.background,
        titlebar=theme.titlebar,
        title_text=theme.title_text,
        text=syntax_theme.text,
        muted=theme.muted,
        border=theme.border,
        shadow=theme.shadow,
    )


def _resolve_syntax_theme(options: RenderOptions) -> SyntaxTheme:
    catalog = load_theme_catalog(options.theme_file)
    try:
        return catalog.syntax_themes[options.syntax_theme]
    except KeyError as exc:
        available = ", ".join(sorted(catalog.syntax_themes))
        raise ValueError(f"Unknown syntax theme: {options.syntax_theme}. Available syntax themes: {available}") from exc


def _resolve_margin(options: RenderOptions) -> int:
    if options.margin is not None:
        return options.margin
    return 14 if options.frame == "frameless" else 24


def _resolve_radius(options: RenderOptions) -> int:
    return options.radius if options.rounded_corners else 0


def _resolve_line_spacing(options: RenderOptions) -> int:
    if options.line_spacing is not None:
        return options.line_spacing
    if options.line_number_style == "idea":
        return 8
    return 5


def _resolve_indent_guides(options: RenderOptions) -> bool:
    if options.indent_guides is not None:
        return options.indent_guides
    return options.content_type == "code" and options.line_number_style == "vscode"


def _resolve_line_number_style(options: RenderOptions, theme: TerminalTheme) -> LineNumberStyle:
    is_light = _is_light_color(theme.background)
    if options.line_number_style == "plain":
        return LineNumberStyle(foreground=theme.muted)
    if options.line_number_style == "vscode":
        return LineNumberStyle(
            foreground="#237893" if is_light else "#858585",
            padding_left_chars=1,
            padding_right_chars=3,
            align="left",
        )
    if options.line_number_style == "idea":
        return LineNumberStyle(
            foreground="#999999" if is_light else "#606366",
            background=None,
            separator="#d9d9d9" if is_light else "#3c3f41",
            padding_left_chars=0.5,
            padding_right_chars=6,
            separator_gap_chars=3,
        )

    raise ValueError("Unknown line number style: " f"{options.line_number_style}. Available styles: plain, vscode, idea")


def _is_light_color(color: str) -> bool:
    red = int(color[1:3], 16)
    green = int(color[3:5], 16)
    blue = int(color[5:7], 16)
    luminance = (0.2126 * red + 0.7152 * green + 0.0722 * blue) / 255
    return luminance >= 0.5


def _indent_guide_color(theme: TerminalTheme) -> str:
    return "#d3d3d3" if _is_light_color(theme.background) else "#404040"


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


def _build_visual_lines(
    text: str,
    width_chars: int,
    default_fg: str,
    options: RenderOptions | None = None,
    filename: str | None = None,
) -> list[list[TextSpan]]:
    return [line for line, _ in _build_numbered_visual_lines(text, width_chars, default_fg, options, filename)]


def _build_numbered_visual_lines(
    text: str,
    width_chars: int,
    default_fg: str,
    options: RenderOptions | None = None,
    filename: str | None = None,
) -> list[tuple[list[TextSpan], int | None]]:
    options = options or RenderOptions()
    if options.content_type == "code":
        logical_lines = _highlight_code_lines(text, default_fg, options, filename)
    else:
        logical_lines = _parse_logical_log_lines(text, default_fg, options)
    return _wrap_logical_lines(logical_lines, width_chars, options.line_number_start, options.wrap_lines)


def _parse_logical_log_lines(text: str, default_fg: str, options: RenderOptions) -> list[list[TextSpan]]:
    logical_lines: list[list[TextSpan]] = []
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").expandtabs(4)

    command_lexer = _command_lexer(options.command_highlight)
    syntax_theme = _resolve_syntax_theme(options) if options.command_highlight else None
    for raw_line in normalized.split("\n"):
        logical_lines.append(_parse_log_line(raw_line, default_fg, options, command_lexer, syntax_theme))

    return logical_lines


def _parse_log_line(
    raw_line: str,
    default_fg: str,
    options: RenderOptions,
    command_lexer: object | None,
    syntax_theme: SyntaxTheme | None,
) -> list[TextSpan]:
    if not options.command_highlight:
        return _parse_line(raw_line, default_fg)
    if command_lexer is None or syntax_theme is None:
        raise ValueError(
            "Unknown command highlight shell: "
            f"{options.command_highlight}. Available shells: powershell, cmd, wsl, ubuntu"
        )
    if "\x1b[" in raw_line:
        return _parse_line(raw_line, default_fg)

    command_start = _command_start_index(raw_line, options.command_highlight)
    if command_start is None:
        return _parse_line(raw_line, default_fg)

    prompt = raw_line[:command_start]
    command = raw_line[command_start:]
    spans = _highlight_prompt(prompt, options.command_highlight, default_fg)
    spans.extend(_highlight_inline_code(command, default_fg, command_lexer, syntax_theme, options.command_highlight))
    return spans


def _command_lexer(shell: str | None) -> object | None:
    if shell is None:
        return None

    aliases = {
        "powershell": "powershell",
        "cmd": "batch",
        "wsl": "bash",
        "ubuntu": "bash",
    }
    lexer_name = aliases.get(shell)
    if lexer_name is None:
        return None
    try:
        return get_lexer_by_name(lexer_name)
    except Exception:
        return TextLexer()


def _command_start_index(raw_line: str, shell: str) -> int | None:
    import re

    patterns = {
        "powershell": r"^PS [^>]*>\s*",
        "cmd": r"^(?:[A-Za-z]:\\[^>]*|\\\\[^>]+|)>\s*",
        "wsl": r"^(?:[^@\s]+@[^:\s]+:[^#$]*[#$]|[#$])\s+",
        "ubuntu": r"^(?:[^@\s]+@[^:\s]+:[^#$]*[#$]|[#$])\s+",
    }
    pattern = patterns.get(shell)
    if not pattern:
        return None
    match = re.match(pattern, raw_line)
    return match.end() if match else None


def _highlight_inline_code(
    text: str,
    default_fg: str,
    lexer: object,
    syntax_theme: SyntaxTheme,
    shell: str,
) -> list[TextSpan]:
    if shell in {"cmd", "wsl", "ubuntu"}:
        return _highlight_shell_words(text, default_fg, syntax_theme)

    spans: list[TextSpan] = []
    for token_type, token_text in lex(text, lexer):
        if "\n" in token_text:
            token_text = token_text.replace("\n", "")
        if token_text:
            spans.append(TextSpan(token_text, _style_for_token(token_type, syntax_theme, default_fg)))
    spans = _merge_adjacent_spans(spans)
    if not spans or any(span.text.strip() and span.style.fg != default_fg for span in spans):
        return spans
    return _highlight_shell_words(text, default_fg, syntax_theme)


def _highlight_prompt(prompt: str, shell: str, default_fg: str) -> list[TextSpan]:
    import re

    if shell in {"wsl", "ubuntu"}:
        match = re.match(r"^([^@\s]+@[^:\s]+)(:)([^#$]*)([#$])(\s*)$", prompt)
        if match:
            user_host, separator, path, marker, trailing = match.groups()
            return _merge_adjacent_spans(
                [
                    TextSpan(user_host, TextStyle("#8ae234", bold=True)),
                    TextSpan(separator, TextStyle(default_fg)),
                    TextSpan(path, TextStyle("#729fcf", bold=True)),
                    TextSpan(marker, TextStyle(default_fg)),
                    TextSpan(trailing, TextStyle(default_fg)),
                ]
            )
    return _parse_line(prompt, default_fg)


def _highlight_shell_words(text: str, default_fg: str, syntax_theme: SyntaxTheme) -> list[TextSpan]:
    import re

    spans: list[TextSpan] = []
    command_style = _style_for_token(Name.Function, syntax_theme, default_fg)
    option_style = _style_for_token(Keyword, syntax_theme, default_fg)
    cursor = 0
    word_index = 0
    for match in re.finditer(r"\S+", text):
        if match.start() > cursor:
            spans.append(TextSpan(text[cursor : match.start()], TextStyle(default_fg)))
        word = match.group(0)
        if word_index == 0:
            style = command_style
        elif word.startswith(("-", "/")):
            style = option_style
        else:
            style = TextStyle(default_fg)
        spans.append(TextSpan(word, style))
        cursor = match.end()
        word_index += 1
    if cursor < len(text):
        spans.append(TextSpan(text[cursor:], TextStyle(default_fg)))
    return _merge_adjacent_spans(spans)


def _merge_adjacent_spans(spans: list[TextSpan]) -> list[TextSpan]:
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


def _wrap_logical_lines(
    logical_lines: list[list[TextSpan]],
    width_chars: int,
    line_number_start: int = 1,
    wrap_lines: bool = False,
) -> list[tuple[list[TextSpan], int | None]]:
    visual_lines: list[tuple[list[TextSpan], int | None]] = []

    for line_index, spans in enumerate(logical_lines):
        line_number = line_number_start + line_index
        first_visual_line = True
        if not spans:
            visual_lines.append(([], line_number))
            continue

        current: list[TextSpan] = []
        current_len = 0
        for span in spans:
            chunks = _wrap_span(span, width_chars, current_len) if wrap_lines else [span.text]
            for chunk in chunks:
                if chunk == "\n":
                    visual_lines.append((current, line_number if first_visual_line else None))
                    first_visual_line = False
                    current = []
                    current_len = 0
                    continue
                current.append(TextSpan(chunk, span.style))
                current_len += len(strip_ansi(chunk))
        visual_lines.append((current, line_number if first_visual_line else None))

    return visual_lines


def _content_width_chars(lines: list[list[TextSpan]], minimum_width_chars: int) -> int:
    max_line_length = max((_line_text_length(line) for line in lines), default=0)
    return max(minimum_width_chars, max_line_length)


def _line_text_length(line: list[TextSpan]) -> int:
    return sum(len(strip_ansi(span.text)) for span in line)


def _line_number_width(
    numbered_lines: list[tuple[list[TextSpan], int | None]],
    options: RenderOptions,
    style: LineNumberStyle,
    char_width: int,
) -> int:
    if not options.line_numbers:
        return 0

    line_numbers = [line_number for _, line_number in numbered_lines if line_number is not None]
    max_digits = max((len(str(line_number)) for line_number in line_numbers), default=1)
    return ceil((max_digits + style.padding_left_chars + style.padding_right_chars + style.separator_gap_chars) * char_width)


def _highlight_code_lines(
    text: str,
    default_fg: str,
    options: RenderOptions,
    filename: str | None = None,
) -> list[list[TextSpan]]:
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").expandtabs(4)
    lexer = _select_lexer(normalized, options, filename)
    lines: list[list[TextSpan]] = [[]]
    syntax_theme = _resolve_syntax_theme(options)

    for token_type, token_text in lex(normalized, lexer):
        style = _style_for_token(token_type, syntax_theme, default_fg)
        parts = token_text.split("\n")
        for index, part in enumerate(parts):
            if index:
                lines.append([])
            if part:
                lines[-1].append(TextSpan(part, style))

    return lines


def _select_lexer(text: str, options: RenderOptions, filename: str | None = None):
    if options.language:
        return get_lexer_by_name(options.language)
    if options.guess_language and filename:
        try:
            return guess_lexer_for_filename(filename, text)
        except Exception:
            pass
    if options.guess_language:
        try:
            return guess_lexer(text)
        except Exception:
            pass
    return TextLexer()


def _style_for_token(token_type: object, syntax_theme: SyntaxTheme, default_fg: str) -> TextStyle:
    for parent, color, bold in syntax_theme.colors:
        if token_type in parent:
            return TextStyle(color, bold=bold)
    if token_type in Text or token_type is Token:
        return TextStyle(default_fg)
    return TextStyle(default_fg)


def _parse_line(raw_line: str, default_fg: str) -> list[TextSpan]:
    return parse_ansi(raw_line, default_fg)


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
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    options: RenderOptions,
    theme: TerminalTheme,
    font: ImageFont.ImageFont,
) -> None:
    x1, y1, x2, _ = box
    title_box = (x1, y1, x2, y1 + options.titlebar_height)
    titlebar_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    titlebar_draw = ImageDraw.Draw(titlebar_layer)
    titlebar_draw.rectangle(title_box, fill=theme.titlebar)
    _clip_layer_to_window(titlebar_layer, box, options.radius)
    image.alpha_composite(titlebar_layer)
    draw.line((x1, y1 + options.titlebar_height, x2, y1 + options.titlebar_height), fill=theme.border)

    if options.frame == "mac":
        _draw_mac_controls(image, x1, y1, options)
    elif options.frame == "ubuntu":
        _draw_ubuntu_controls(image, draw, x1, y1, options)
    else:
        _draw_windows_controls(image, draw, box, options, theme)

    title = textwrap.shorten(options.title, width=72, placeholder="...")
    bbox = draw.textbbox((0, 0), title, font=font)
    title_x = x1 + (x2 - x1 - (bbox[2] - bbox[0])) / 2
    if options.frame == "windows":
        title_x = max(title_x, x1 + 18)
    draw.text((title_x, y1 + 10), title, fill=theme.title_text, font=font)


def _draw_mac_controls(
    image: Image.Image,
    x1: int,
    y1: int,
    options: RenderOptions,
) -> None:
    button_y = y1 + options.titlebar_height // 2
    for index, color in enumerate(("#ff5f56", "#ffbd2e", "#27c93f")):
        cx = x1 + 19 + index * 18
        _draw_antialiased_ellipse(image, (cx - 5, button_y - 5, cx + 5, button_y + 5), color)


def _draw_ubuntu_controls(
    image: Image.Image,
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
        _draw_antialiased_ellipse(image, (cx - 6, button_y - 6, cx + 6, button_y + 6), color)
        if symbols[index] == "x":
            draw.line((cx - 3, button_y - 3, cx + 3, button_y + 3), fill="#ffffff", width=1)
            draw.line((cx + 3, button_y - 3, cx - 3, button_y + 3), fill="#ffffff", width=1)
        elif symbols[index] == "-":
            draw.line((cx - 4, button_y, cx + 4, button_y), fill="#3a2f2a", width=1)
        else:
            draw.line((cx - 4, button_y, cx + 4, button_y), fill="#ffffff", width=1)
            draw.line((cx, button_y - 4, cx, button_y + 4), fill="#ffffff", width=1)


def _draw_windows_controls(
    image: Image.Image,
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    options: RenderOptions,
    theme: TerminalTheme,
) -> None:
    _, y1, x2, _ = box
    control_w = 46
    top = y1
    bottom = y1 + options.titlebar_height
    close_left = x2 - control_w
    max_left = close_left - control_w
    min_left = max_left - control_w
    cy = y1 + options.titlebar_height // 2

    close_layer = Image.new("RGBA", image.size, (0, 0, 0, 0))
    close_draw = ImageDraw.Draw(close_layer)
    close_draw.rectangle((close_left, top, x2, bottom), fill="#c42b1c")
    _clip_layer_to_window(close_layer, box, options.radius)
    image.alpha_composite(close_layer)
    draw.line((min_left + 17, cy + 5, min_left + 29, cy + 5), fill=theme.title_text, width=1)
    draw.rectangle((max_left + 18, cy - 5, max_left + 29, cy + 6), outline=theme.title_text, width=1)
    draw.line((close_left + 18, cy - 5, close_left + 29, cy + 6), fill="#ffffff", width=1)
    draw.line((close_left + 29, cy - 5, close_left + 18, cy + 6), fill="#ffffff", width=1)


def _window_clip_mask(size: tuple[int, int], box: tuple[int, int, int, int], radius: int) -> Image.Image:
    scale = 4
    mask = Image.new("L", (size[0] * scale, size[1] * scale), 0)
    mask_draw = ImageDraw.Draw(mask)
    scaled_box = tuple(value * scale for value in box)
    mask_draw.rounded_rectangle(scaled_box, radius=radius * scale, fill=255)
    return mask.resize(size, Image.Resampling.LANCZOS)


def _clip_layer_to_window(layer: Image.Image, box: tuple[int, int, int, int], radius: int) -> None:
    clip_mask = _window_clip_mask(layer.size, box, radius)
    alpha = layer.getchannel("A")
    layer.putalpha(ImageChops.multiply(alpha, clip_mask))


def _draw_antialiased_ellipse(image: Image.Image, box: tuple[int, int, int, int], fill: str) -> None:
    scale = 4
    target_width = box[2] - box[0] + 1
    target_height = box[3] - box[1] + 1
    width = max(target_width * scale, 1)
    height = max(target_height * scale, 1)
    layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    layer_draw = ImageDraw.Draw(layer)
    layer_draw.ellipse((0, 0, width - 1, height - 1), fill=fill)
    layer = layer.resize((target_width, target_height), Image.Resampling.LANCZOS)
    image.alpha_composite(layer, (box[0], box[1]))


def _draw_line_numbers(
    draw: ImageDraw.ImageDraw,
    numbered_lines: list[tuple[list[TextSpan], int | None]],
    x: int,
    y: int,
    line_height: int,
    font: ImageFont.ImageFont,
    char_width: int,
    style: LineNumberStyle,
    text_y: int,
    text_height: int,
) -> None:
    line_numbers = [line_number for _, line_number in numbered_lines if line_number is not None]
    max_digits = max((len(str(line_number)) for line_number in line_numbers), default=1)
    number_area_width = ceil((max_digits + style.padding_left_chars + style.padding_right_chars) * char_width)
    gutter_width = number_area_width + ceil(style.separator_gap_chars * char_width)
    if style.background:
        draw.rectangle(
            (x, text_y, x + gutter_width, text_y + text_height),
            fill=style.background,
        )
    if style.separator:
        separator_x = x + number_area_width - 1
        draw.line((separator_x, text_y, separator_x, text_y + text_height), fill=style.separator)

    number_x = x + style.padding_left_chars * char_width
    cursor_y = y
    for _, line_number in numbered_lines:
        if line_number is not None:
            text = str(line_number) if style.align == "left" else f"{line_number:>{max_digits}}"
            draw.text((number_x, cursor_y), text, fill=style.foreground, font=font)
        cursor_y += line_height


def _draw_indent_guides(
    draw: ImageDraw.ImageDraw,
    lines: list[list[TextSpan]],
    x: int,
    y: int,
    line_height: int,
    char_width: int,
    indent_size: int,
    color: str,
    y_inset: int,
) -> None:
    if indent_size <= 0:
        return

    for indent_column, start_index, end_index in _indent_guide_segments(lines):
        guide_x = x + indent_column * char_width
        guide_y1 = y + start_index * line_height + line_height - 1
        guide_y2 = y + end_index * line_height + line_height - 1 - y_inset
        draw.line((guide_x, guide_y1, guide_x, guide_y2), fill=color, width=1)


def _indent_guide_segments(lines: list[list[TextSpan]]) -> list[tuple[int, int, int]]:
    indents = [_leading_space_count(line) for line in lines]
    segments: list[tuple[int, int, int]] = []

    for index, indent in enumerate(indents[:-1]):
        next_indent = indents[index + 1]
        if next_indent <= indent:
            continue

        end_index = index + 1
        while end_index + 1 < len(indents) and indents[end_index + 1] > indent:
            end_index += 1
        segments.append((indent, index, end_index))

    return _merge_indent_guide_segments(segments)


def _merge_indent_guide_segments(segments: list[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
    merged: list[tuple[int, int, int]] = []
    for indent, start_index, end_index in sorted(segments):
        if not merged:
            merged.append((indent, start_index, end_index))
            continue
        previous_indent, previous_start, previous_end = merged[-1]
        if indent == previous_indent and start_index <= previous_end + 1:
            merged[-1] = (previous_indent, previous_start, max(previous_end, end_index))
            continue
        merged.append((indent, start_index, end_index))
    return merged


def _leading_space_count(line: list[TextSpan]) -> int:
    count = 0
    for span in line:
        for char in span.text:
            if char != " ":
                return count
            count += 1
    return count


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

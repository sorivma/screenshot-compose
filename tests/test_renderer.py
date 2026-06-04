from pathlib import Path

from PIL import Image
from pygments.token import Name

from console_gen.renderer import (
    RenderOptions,
    _build_numbered_visual_lines,
    _indent_guide_segments,
    _leading_space_count,
    _parse_line,
    _resolve_indent_guides,
    _resolve_line_spacing,
    _resolve_line_number_style,
    _resolve_syntax_theme,
    _resolve_theme,
    _style_for_token,
    render_code,
    render_log,
    render_log_file,
)
from console_gen.themes import load_theme_catalog


def test_render_log_returns_image():
    image = render_log("$ echo hello\nhello", RenderOptions(width_chars=40, font_size=14))

    assert image.size[0] > 400
    assert image.size[1] > 100


def test_render_log_file_writes_png(tmp_path: Path):
    source = tmp_path / "lab.log"
    output = tmp_path / "screen.png"
    source.write_text("$ pytest\n\x1b[32m2 passed\x1b[0m\n", encoding="utf-8")

    render_log_file(source, output, RenderOptions(width_chars=50, font_size=14))

    with Image.open(output) as image:
        assert image.format == "PNG"
        assert image.mode == "RGBA"
        assert image.size[0] > 0


def test_frameless_render_has_no_titlebar_height():
    framed = render_log("$ echo hello\nhello", RenderOptions(width_chars=40, font_size=14, frame="ubuntu"))
    frameless = render_log("$ echo hello\nhello", RenderOptions(width_chars=40, font_size=14, frame="frameless"))

    assert frameless.size[1] < framed.size[1]


def test_margin_can_remove_transparent_outer_gap():
    default_margin = render_log("$ echo hello\nhello", RenderOptions(width_chars=40, font_size=14, frame="frameless"))
    no_margin = render_log("$ echo hello\nhello", RenderOptions(width_chars=40, font_size=14, frame="frameless", margin=0))

    assert no_margin.size[0] == default_margin.size[0] - 28
    assert no_margin.size[1] == default_margin.size[1] - 28


def test_windows_close_button_is_clipped_to_window_radius():
    image = render_log(
        "$ echo hello\nhello",
        RenderOptions(width_chars=40, font_size=14, frame="windows", rounded_corners=True),
    )
    margin = 24
    right = image.size[0] - margin

    assert image.getpixel((right - 10, margin + 1))[:3] == (196, 43, 28)
    assert image.getpixel((right - 1, margin))[3] < 128


def test_window_corners_are_square_by_default():
    image = render_log("$ echo hello\nhello", RenderOptions(width_chars=40, font_size=14, frame="windows"))
    margin = 24
    right = image.size[0] - margin

    assert image.getpixel((right - 1, margin))[3] == 255


def test_plain_text_uses_theme_color_without_auto_coloring():
    spans = _parse_line("sorivma@ubuntu:~/lab$ pytest", "#eeeeec")

    assert [span.text for span in spans] == ["sorivma@ubuntu:~/lab$ pytest"]
    assert spans[0].style.fg == "#eeeeec"
    assert not spans[0].style.bold


def test_command_highlight_colors_powershell_entered_command():
    numbered_lines = _build_numbered_visual_lines(
        "PS C:\\Users\\me> Get-ChildItem -Force",
        width_chars=80,
        default_fg="#eeeeec",
        options=RenderOptions(command_highlight="powershell", syntax_theme="vscode-dark"),
    )
    spans = numbered_lines[0][0]

    assert spans[0].text == "PS C:\\Users\\me> "
    assert spans[0].style.fg == "#eeeeec"
    assert any(span.text.strip() and span.style.fg != "#eeeeec" for span in spans[1:])


def test_command_highlight_supports_cmd_wsl_and_ubuntu_prompts():
    cmd_lines = _build_numbered_visual_lines(
        "C:\\Users\\me> dir /b",
        width_chars=80,
        default_fg="#eeeeec",
        options=RenderOptions(command_highlight="cmd", syntax_theme="vscode-dark"),
    )
    wsl_lines = _build_numbered_visual_lines(
        "me@ubuntu:~/lab$ pytest -q",
        width_chars=80,
        default_fg="#eeeeec",
        options=RenderOptions(command_highlight="wsl", syntax_theme="vscode-dark"),
    )
    ubuntu_lines = _build_numbered_visual_lines(
        "sorivma@ubuntu:~/lab$ terraform plan",
        width_chars=80,
        default_fg="#eeeeec",
        options=RenderOptions(command_highlight="ubuntu", syntax_theme="vscode-dark"),
    )

    assert cmd_lines[0][0][0].text == "C:\\Users\\me> "
    assert [span.text for span in wsl_lines[0][0][:4]] == ["me@ubuntu", ":", "~/lab", "$ "]
    assert [span.text for span in ubuntu_lines[0][0][:4]] == ["sorivma@ubuntu", ":", "~/lab", "$ "]
    assert any(span.style.fg != "#eeeeec" for span in cmd_lines[0][0][1:])
    assert any(span.style.fg != "#eeeeec" for span in wsl_lines[0][0][1:])
    assert any(span.style.fg != "#eeeeec" for span in ubuntu_lines[0][0][1:])


def test_ubuntu_prompt_colors_user_host_and_path():
    numbered_lines = _build_numbered_visual_lines(
        "sorivma@DESKTOP-LR9G161:~$ ls -la",
        width_chars=80,
        default_fg="#eeeeec",
        options=RenderOptions(command_highlight="ubuntu", syntax_theme="vscode-dark"),
    )
    spans = numbered_lines[0][0]

    assert spans[0].text == "sorivma@DESKTOP-LR9G161"
    assert spans[0].style.fg == "#8ae234"
    assert spans[2].text == "~"
    assert spans[2].style.fg == "#729fcf"
    assert spans[3].text == "$ "


def test_command_highlight_colors_common_option_forms():
    wsl_lines = _build_numbered_visual_lines(
        "sorivma@ubuntu:~$ docker run -t ubuntu --version",
        width_chars=100,
        default_fg="#eeeeec",
        options=RenderOptions(command_highlight="ubuntu", syntax_theme="vscode-dark"),
    )
    cmd_lines = _build_numbered_visual_lines(
        "C:\\Users\\me> dir /b",
        width_chars=80,
        default_fg="#eeeeec",
        options=RenderOptions(command_highlight="cmd", syntax_theme="vscode-dark"),
    )

    wsl_options = {span.text: span.style.fg for span in wsl_lines[0][0] if span.text in {"-t", "--version"}}
    cmd_options = {span.text: span.style.fg for span in cmd_lines[0][0] if span.text == "/b"}

    assert wsl_options["-t"] != "#eeeeec"
    assert wsl_options["--version"] != "#eeeeec"
    assert cmd_options["/b"] != "#eeeeec"


def test_command_highlight_does_not_color_regular_output():
    numbered_lines = _build_numbered_visual_lines(
        "response > cached",
        width_chars=80,
        default_fg="#eeeeec",
        options=RenderOptions(command_highlight="cmd", syntax_theme="vscode-dark"),
    )

    assert [span.text for span in numbered_lines[0][0]] == ["response > cached"]
    assert numbered_lines[0][0][0].style.fg == "#eeeeec"


def test_log_render_without_command_highlight_does_not_resolve_syntax_theme():
    image = render_log("plain output", RenderOptions(width_chars=40, font_size=14, syntax_theme="missing"))

    assert image.size[0] > 0


def test_parse_line_preserves_ansi_colors():
    spans = _parse_line("ok \x1b[31mfail\x1b[0m", "#eeeeec")

    assert [span.text for span in spans] == ["ok ", "fail"]
    assert spans[0].style.fg == "#eeeeec"
    assert spans[1].style.fg != "#eeeeec"


def test_render_code_returns_image_with_syntax_theme():
    image = render_code(
        "def main():\n    return 'ok'\n",
        RenderOptions(width_chars=40, font_size=14, content_type="code", language="python"),
        filename="example.py",
    )

    assert image.size[0] > 400
    assert image.size[1] > 100


def test_syntax_theme_highlights_decorators_and_jsx_tokens():
    vscode_theme = _resolve_syntax_theme(RenderOptions(syntax_theme="vscode-dark"))
    intellij_theme = _resolve_syntax_theme(RenderOptions(syntax_theme="intellij-dark"))

    assert _style_for_token(Name.Decorator, vscode_theme, vscode_theme.text).fg == "#dcdcaa"
    assert _style_for_token(Name.Decorator, intellij_theme, intellij_theme.text).fg == "#ffc66d"
    assert _style_for_token(Name.Tag, vscode_theme, vscode_theme.text).fg == "#569cd6"
    assert _style_for_token(Name.Attribute, vscode_theme, vscode_theme.text).fg == "#9cdcfe"


def test_line_numbers_add_left_gutter_width():
    plain = render_code(
        "print('ok')\n",
        RenderOptions(width_chars=40, font_size=14, content_type="code", language="python"),
        filename="example.py",
    )
    numbered = render_code(
        "print('ok')\n",
        RenderOptions(width_chars=40, font_size=14, content_type="code", language="python", line_numbers=True),
        filename="example.py",
    )

    assert numbered.size[0] > plain.size[0]
    assert numbered.size[1] == plain.size[1]


def test_long_lines_expand_image_width_by_default():
    short = render_log("abcdefghij", RenderOptions(width_chars=10, font_size=14, frame="frameless", margin=0))
    long = render_log("abcdefghij" * 4, RenderOptions(width_chars=10, font_size=14, frame="frameless", margin=0))

    assert long.size[0] > short.size[0]
    assert long.size[1] == short.size[1]


def test_wrap_lines_can_keep_width_and_increase_height():
    no_wrap = render_log(
        "abcdefghij" * 4,
        RenderOptions(width_chars=10, font_size=14, frame="frameless", margin=0),
    )
    wrapped = render_log(
        "abcdefghij" * 4,
        RenderOptions(width_chars=10, font_size=14, frame="frameless", margin=0, wrap_lines=True),
    )

    assert wrapped.size[0] < no_wrap.size[0]
    assert wrapped.size[1] > no_wrap.size[1]


def test_line_number_styles_render_successfully():
    text = "print('ok')\n"
    base_options = {
        "width_chars": 40,
        "font_size": 14,
        "content_type": "code",
        "language": "python",
        "line_numbers": True,
    }

    vscode = render_code(text, RenderOptions(**base_options, line_number_style="vscode"), filename="example.py")
    idea = render_code(text, RenderOptions(**base_options, line_number_style="idea"), filename="example.py")

    assert idea.size[0] > vscode.size[0]
    assert idea.size[1] > vscode.size[1]


def test_unknown_line_number_style_fails():
    try:
        render_log("ok", RenderOptions(line_numbers=True, line_number_style="unknown"))
    except ValueError as exc:
        assert "Unknown line number style" in str(exc)
    else:
        raise AssertionError("Expected unknown line number style to fail")


def test_idea_line_number_style_has_larger_default_line_spacing():
    vscode_options = RenderOptions(line_numbers=True, line_number_style="vscode")
    idea_options = RenderOptions(line_numbers=True, line_number_style="idea")

    assert _resolve_line_spacing(vscode_options) == 5
    assert _resolve_line_spacing(idea_options) == 8


def test_explicit_line_spacing_overrides_style_default():
    options = RenderOptions(line_numbers=True, line_number_style="idea", line_spacing=2)

    assert _resolve_line_spacing(options) == 2


def test_vscode_line_numbers_align_left_and_idea_aligns_right():
    vscode_options = RenderOptions(line_numbers=True, line_number_style="vscode", syntax_theme="vscode-dark")
    idea_options = RenderOptions(line_numbers=True, line_number_style="idea", syntax_theme="intellij-dark")

    assert _resolve_line_number_style(vscode_options, _resolve_theme(vscode_options)).align == "left"
    assert _resolve_line_number_style(idea_options, _resolve_theme(idea_options)).align == "right"


def test_indent_guides_default_to_vscode_code_style():
    vscode_options = RenderOptions(content_type="code", line_number_style="vscode")
    idea_options = RenderOptions(content_type="code", line_number_style="idea")
    explicit_off = RenderOptions(content_type="code", line_number_style="vscode", indent_guides=False)

    assert _resolve_indent_guides(vscode_options)
    assert not _resolve_indent_guides(idea_options)
    assert not _resolve_indent_guides(explicit_off)


def test_leading_space_count_uses_rendered_spans():
    numbered_lines = _build_numbered_visual_lines(
        "    if ok:\n        return ok",
        width_chars=40,
        default_fg="#ffffff",
        options=RenderOptions(content_type="code", language="python"),
    )

    assert _leading_space_count(numbered_lines[0][0]) == 4
    assert _leading_space_count(numbered_lines[1][0]) == 8


def test_indent_guides_start_on_parent_block_lines():
    numbered_lines = _build_numbered_visual_lines(
        "type Metric = {\n  label: string;\n};\n\nexport function App() {\n  return null;\n}\n",
        width_chars=80,
        default_fg="#ffffff",
        options=RenderOptions(content_type="code", language="tsx", line_number_style="vscode"),
    )
    lines = [line for line, _ in numbered_lines]

    assert _indent_guide_segments(lines) == [(0, 0, 1), (0, 4, 5)]


def test_line_numbers_start_is_configurable_and_wrapped_lines_are_blank():
    numbered_lines = _build_numbered_visual_lines(
        "abcdefghij\nok",
        width_chars=4,
        default_fg="#ffffff",
        options=RenderOptions(line_numbers=True, line_number_start=42, wrap_lines=True),
    )

    assert [line_number for _, line_number in numbered_lines] == [42, None, None, 43]


def test_render_log_file_can_render_code(tmp_path: Path):
    source = tmp_path / "playbook.yml"
    output = tmp_path / "playbook.png"
    source.write_text("- hosts: all\n  tasks:\n    - debug:\n        msg: ok\n", encoding="utf-8")

    render_log_file(
        source,
        output,
        RenderOptions(width_chars=60, font_size=14, content_type="code", language="yaml", syntax_theme="intellij-light"),
    )

    with Image.open(output) as image:
        assert image.format == "PNG"
        assert image.mode == "RGBA"


def test_builtin_themes_load_from_json_resource():
    catalog = load_theme_catalog()

    assert "powershell" in catalog.terminal_themes
    assert "vscode-dark" in catalog.syntax_themes


def test_render_can_use_custom_theme_file(tmp_path: Path):
    theme_file = tmp_path / "themes.json"
    theme_file.write_text(
        """
        {
          "terminal_themes": {
            "lab": {
              "background": "#101820",
              "titlebar": "#1b2a33",
              "title_text": "#f7f7f7",
              "text": "#f2aa4c",
              "muted": "#99aabb",
              "border": "#334455",
              "shadow": "#000000"
            }
          },
          "syntax_themes": {
            "lab-code": {
              "background": "#101820",
              "text": "#f7f7f7",
              "colors": [
                {"token": "Keyword", "color": "#f2aa4c", "bold": true},
                {"token": "String", "color": "#99ddff"}
              ]
            }
          }
        }
        """,
        encoding="utf-8",
    )

    log_image = render_log(
        "$ echo custom\ncustom",
        RenderOptions(width_chars=40, font_size=14, theme_name="lab", theme_file=str(theme_file)),
    )
    code_image = render_code(
        "def main():\n    return 'ok'\n",
        RenderOptions(
            width_chars=40,
            font_size=14,
            content_type="code",
            language="python",
            theme_name="lab",
            syntax_theme="lab-code",
            theme_file=str(theme_file),
        ),
        filename="example.py",
    )

    assert log_image.size[0] > 400
    assert code_image.size[0] > 400

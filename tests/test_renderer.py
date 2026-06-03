from pathlib import Path

from PIL import Image

from console_gen.renderer import RenderOptions, _parse_line, render_code, render_log, render_log_file
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


def test_plain_text_uses_theme_color_without_auto_coloring():
    spans = _parse_line("sorivma@ubuntu:~/lab$ pytest", "#eeeeec")

    assert [span.text for span in spans] == ["sorivma@ubuntu:~/lab$ pytest"]
    assert spans[0].style.fg == "#eeeeec"
    assert not spans[0].style.bold


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

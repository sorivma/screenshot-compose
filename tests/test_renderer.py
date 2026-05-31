from pathlib import Path

from PIL import Image

from console_gen.renderer import RenderOptions, _parse_line, render_log, render_log_file


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

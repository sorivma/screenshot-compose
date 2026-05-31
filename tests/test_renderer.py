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


def test_auto_coloring_highlights_ubuntu_prompt():
    spans = _parse_line("sorivma@ubuntu:~/lab$ pytest", "#eeeeec", "ubuntu")

    assert spans[0].text == "sorivma@ubuntu"
    assert spans[0].style.fg == "#8ae234"
    assert any(span.style.fg != "#eeeeec" for span in spans)


def test_auto_coloring_highlights_macos_prompt():
    spans = _parse_line("sorivma@MacBook-Pro lab % pytest", "#f2f2f2", "macos")

    assert spans[0].text == "sorivma@MacBook-Pro"
    assert spans[0].style.fg == "#a6e22e"


def test_auto_coloring_uses_shell_lexer_for_commands():
    spans = _parse_line("$ export NAME='lab'", "#eeeeec", "ubuntu")

    assert any(span.text == "export" and span.style.fg == "#729fcf" for span in spans)
    assert any(span.text == "'lab'" and span.style.fg == "#ad7fa8" for span in spans)


def test_auto_coloring_uses_powershell_lexer_for_commands():
    spans = _parse_line("PS C:\\lab> Write-Host 'ok'", "#f3f3f3", "powershell")

    assert any(span.text == "Write-Host" and span.style.fg == "#569cd6" for span in spans)
    assert any(span.text == "'ok'" and span.style.fg == "#ce9178" for span in spans)

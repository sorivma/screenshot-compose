from console_gen.ansi import parse_ansi, strip_ansi


def test_strip_ansi_removes_sgr_sequences():
    assert strip_ansi("\x1b[31merror\x1b[0m") == "error"


def test_parse_ansi_preserves_plain_text_and_color():
    spans = parse_ansi("ok \x1b[31mfail\x1b[0m", "#ffffff")

    assert [span.text for span in spans] == ["ok ", "fail"]
    assert spans[0].style.fg == "#ffffff"
    assert spans[1].style.fg != "#ffffff"


def test_parse_ansi_supports_truecolor():
    spans = parse_ansi("\x1b[38;2;12;34;56mcolor", "#ffffff")

    assert spans[0].style.fg == "#0c2238"

"""Tests for the command-line machine contract."""

from __future__ import annotations

import json
import sys

import pytest

from console_gen.cli import main


def _write_project(tmp_path):
    source = tmp_path / "input.log"
    source.write_text("$ echo hello\nhello\n", encoding="utf-8")
    output = tmp_path / "build" / "output.png"
    project = tmp_path / "screenshot-compose.yml"
    project.write_text(
        """
version: 1
renders:
  example:
    input: input.log
    output: build/output.png
""",
        encoding="utf-8",
    )
    return project, output


def _run(monkeypatch, *args: str) -> int:
    monkeypatch.setattr(sys, "argv", ["screenshot-compose", *args])
    return main()


def test_argument_error_preserves_json_contract(monkeypatch, capsys):
    with pytest.raises(SystemExit) as exc:
        _run(monkeypatch, "apply", "--unknown", "--json")

    assert exc.value.code == 2
    payload = json.loads(capsys.readouterr().err)
    assert payload["errors"][0]["code"] == "invalid_arguments"


def test_validate_json_success(tmp_path, monkeypatch, capsys):
    project, _ = _write_project(tmp_path)

    assert _run(monkeypatch, "validate", "-f", str(project), "--json") == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert captured.err == ""
    assert payload["status"] == "success"
    assert payload["command"] == "validate"
    assert payload["data"]["resources"] == ["example"]


def test_validate_rejects_missing_input(tmp_path, monkeypatch, capsys):
    project, _ = _write_project(tmp_path)
    (tmp_path / "input.log").unlink()

    assert _run(monkeypatch, "validate", "-f", str(project), "--json") == 2

    captured = capsys.readouterr()
    payload = json.loads(captured.err)
    assert captured.out == ""
    assert payload["status"] == "error"
    assert payload["errors"][0]["code"] == "invalid_input"
    assert "Missing input file" in payload["errors"][0]["message"]


def test_plain_error_goes_to_stderr(tmp_path, monkeypatch, capsys):
    assert _run(monkeypatch, "validate", "-f", str(tmp_path / "missing.yml")) == 2

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "Error:" in captured.err


def test_apply_json_has_single_machine_readable_response(tmp_path, monkeypatch, capsys):
    project, output = _write_project(tmp_path)

    assert _run(monkeypatch, "apply", "-f", str(project), "--json") == 0

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert captured.err == ""
    assert payload["status"] == "success"
    assert payload["outputs"] == [str(output.resolve())]


def test_apply_dry_run_does_not_write_outputs(tmp_path, monkeypatch, capsys):
    project, output = _write_project(tmp_path)

    assert _run(monkeypatch, "apply", "-f", str(project), "--dry-run", "--json") == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["data"]["dry_run"] is True
    assert not output.exists()


def test_apply_refuses_overwrite_without_force(tmp_path, monkeypatch, capsys):
    project, output = _write_project(tmp_path)
    output.parent.mkdir()
    output.write_text("existing", encoding="utf-8")

    assert _run(monkeypatch, "apply", "-f", str(project), "--json") == 2
    assert "use --force" in json.loads(capsys.readouterr().err)["errors"][0]["message"]


def test_apply_rejects_output_outside_root(tmp_path, monkeypatch, capsys):
    project, _ = _write_project(tmp_path)

    assert _run(
        monkeypatch,
        "apply",
        "-f",
        str(project),
        "--output-root",
        str(tmp_path / "allowed"),
        "--json",
    ) == 2
    assert "outside --output-root" in json.loads(capsys.readouterr().err)["errors"][0]["message"]


def test_apply_writes_sha256_manifest(tmp_path, monkeypatch, capsys):
    project, _ = _write_project(tmp_path)
    manifest = tmp_path / "build" / "manifest.json"

    assert _run(
        monkeypatch,
        "apply",
        "-f",
        str(project),
        "--manifest",
        str(manifest),
        "--json",
    ) == 0

    payload = json.loads(capsys.readouterr().out)
    manifest_payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["data"]["manifest"] == str(manifest.resolve())
    assert manifest_payload["command"] == "screenshot-compose apply"
    assert all(len(record["sha256"]) == 64 for record in manifest_payload["inputs"] + manifest_payload["outputs"])


def test_apply_manifest_must_stay_inside_output_root(tmp_path, monkeypatch, capsys):
    project, _ = _write_project(tmp_path)

    assert _run(
        monkeypatch,
        "apply",
        "-f",
        str(project),
        "--manifest",
        str(tmp_path / "outside.json"),
        "--output-root",
        str(tmp_path / "build"),
        "--json",
    ) == 2
    assert "outside --output-root" in json.loads(capsys.readouterr().err)["errors"][0]["message"]


def test_themes_json(tmp_path, monkeypatch, capsys):
    assert _run(monkeypatch, "themes", "--json") == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "success"
    assert "dark" in payload["data"]["terminal_themes"]


def test_schema_json_exposes_versioned_schema(monkeypatch, capsys):
    assert _run(monkeypatch, "schema", "--json") == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "success"
    assert payload["data"]["version"] == 1
    assert "renders" in payload["data"]["schema"]["properties"]


def test_inspect_json_describes_options_themes_and_resources(tmp_path, monkeypatch, capsys):
    project, _ = _write_project(tmp_path)

    assert _run(monkeypatch, "inspect", "-f", str(project), "--json") == 0

    payload = json.loads(capsys.readouterr().out)
    assert "font_size" in payload["data"]["options"]
    assert "dark" in payload["data"]["terminal_themes"]
    assert payload["data"]["resources"][0]["name"] == "example"

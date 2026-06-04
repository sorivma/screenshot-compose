"""Tests for the bundled JSON Schema."""

from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

from console_gen.schemas import load_schema


def test_schema_is_valid():
    Draft202012Validator.check_schema(load_schema())


def test_example_project_conforms_to_schema():
    raw = yaml.safe_load(Path("examples/screenshot-compose.yml").read_text(encoding="utf-8"))

    assert list(Draft202012Validator(load_schema()).iter_errors(raw)) == []

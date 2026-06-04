from pathlib import Path

from PIL import Image
import pytest

from console_gen.project import load_options_config, load_project, render_project


def test_load_project_resolves_defaults_aliases_and_paths():
    resources = load_project(Path("examples/screenshot-compose.yml"))

    python = resources[0]
    terminal = resources[2]

    assert len(resources) >= 60
    assert python.name == "project-python"
    assert python.input_path.name == "example.py"
    assert python.options.width_chars == 88
    assert python.options.theme_name == "auto"
    assert python.options.content_type == "code"
    assert python.options.language == "python"
    assert terminal.options.theme_name == "ubuntu"
    assert terminal.options.command_highlight == "ubuntu"
    assert not terminal.options.line_numbers


def test_example_pngs_are_declared_in_gallery_project():
    project_path = Path("examples/screenshot-compose.yml")
    resources = load_project(project_path)
    example_root = project_path.parent.resolve()

    declared_outputs = {
        resource.output_path
        for resource in resources
        if resource.output_path.is_relative_to(example_root)
    }
    existing_pngs = {path.resolve() for path in example_root.glob("**/*.png")}

    assert existing_pngs <= declared_outputs


def test_language_gallery_covers_supported_provider_matrix():
    resources = load_project(Path("examples/screenshot-compose.yml"))
    supported_languages = {"go", "python", "java", "javascript", "jsx", "typescript", "tsx", "vue"}
    editor_themes = {"vscode-dark", "vscode-light", "intellij-dark", "intellij-light"}
    matrix = {
        (resource.options.language, resource.options.syntax_theme)
        for resource in resources
        if resource.name.startswith("language-")
    }

    assert matrix == {(language, theme) for language in supported_languages for theme in editor_themes}


def test_yaml_options_config_uses_same_shape_as_json(tmp_path: Path):
    config = tmp_path / "render.yml"
    config.write_text(
        """
        width: 72
        theme: dracula
        content_type: code
        language: python
        """,
        encoding="utf-8",
    )

    values = load_options_config(config)

    assert values["width_chars"] == 72
    assert values["theme_name"] == "dracula"
    assert values["content_type"] == "code"


def test_render_project_can_render_selected_resource(tmp_path: Path):
    source = tmp_path / "hello.py"
    source.write_text("print('hello')\n", encoding="utf-8")
    project = tmp_path / "screenshot-compose.yml"
    output = tmp_path / "hello.png"
    skipped = tmp_path / "skipped.png"
    project.write_text(
        f"""
        version: 1
        defaults:
          render:
            content_type: code
            language: python
            width: 40
            font_size: 14
        renders:
          hello:
            input: {source.name}
            output: {output.name}
          skipped:
            input: {source.name}
            output: {skipped.name}
        """,
        encoding="utf-8",
    )

    outputs = render_project(project, ["hello"])

    assert outputs == [output.resolve()]
    assert output.exists()
    assert not skipped.exists()
    with Image.open(output) as image:
        assert image.format == "PNG"


def test_validate_project_rejects_unknown_theme(tmp_path: Path):
    source = tmp_path / "input.log"
    source.write_text("hello", encoding="utf-8")
    project = tmp_path / "project.yml"
    project.write_text(
        """
version: 1
renders:
  bad:
    input: input.log
    output: output.png
    theme: missing-theme
""",
        encoding="utf-8",
    )

    from console_gen.project import validate_project

    with pytest.raises(ValueError, match="Unknown terminal theme"):
        validate_project(project)

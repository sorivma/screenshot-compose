# screenshot-compose

`screenshot-compose` renders terminal logs and source code into polished PNG screenshots from CLI flags or compose-style YAML project files. It is built for documentation, coursework, reports, and repeatable screenshot pipelines where plain pasted text is not enough.

## Features

- PNG output with transparent outer margins.
- Window frames for Windows Terminal, macOS Terminal, Ubuntu Terminal, and frameless terminal blocks.
- Automatic terminal theme selection with `--theme auto`.
- ANSI SGR support: real colorized command output is preserved when the input log contains escape codes.
- Logs without ANSI escape codes are rendered with the selected theme text color.
- Source code rendering with syntax highlighting for any language supported by Pygments.
- Syntax presets inspired by VS Code and IntelliJ IDEA.
- Optional editor-style line numbers with configurable start number and VS Code or IntelliJ IDEA gutter styling.
- VS Code-style vertical indentation guides for source code previews.
- Tight output mode with configurable outer margin and content padding.
- Square corners by default, with optional rounded corners.
- Built-in themes are stored as JSON resources and can be extended or overridden with custom JSON theme files.
- JSON render configs for reusable frame, typography, spacing, and syntax settings.
- Compose-style YAML project files for rendering multiple named resources with shared defaults.
- Long lines expand the image width by default. Optional wrapping can be enabled with `--wrap-lines`.

## Examples

Frame examples:

| Windows | macOS |
| --- | --- |
| ![Windows terminal screenshot](examples/frames/sample-windows.png) | ![macOS terminal screenshot](examples/frames/sample-macos.png) |

| Ubuntu | Frameless |
| --- | --- |
| ![Ubuntu terminal screenshot](examples/frames/sample-ubuntu.png) | ![Frameless terminal block](examples/frames/sample-frameless.png) |

Code examples:

| Python | Vagrantfile | Ansible |
| --- | --- | --- |
| ![Python code screenshot](examples/frames/sample-python-code.png) | ![Vagrantfile screenshot](examples/frames/sample-vagrantfile.png) | ![Ansible playbook screenshot](examples/frames/sample-ansible-playbook.png) |

Line number styles:

| VS Code | IntelliJ IDEA |
| --- | --- |
| ![VS Code line numbers](examples/syntax/syntax-vscode-line-numbers.png) | ![IntelliJ IDEA line numbers](examples/syntax/syntax-idea-line-numbers.png) |

Tight output with `--margin 0 --padding-x 0 --padding-y 0`:

| Frameless | VS Code Lines | IntelliJ IDEA Lines |
| --- | --- | --- |
| ![Tight frameless terminal block](examples/frames/sample-frameless-tight.png) | ![Tight VS Code line numbers](examples/syntax/syntax-vscode-line-numbers-tight.png) | ![Tight IntelliJ IDEA line numbers](examples/syntax/syntax-idea-line-numbers-tight.png) |

Language examples:

| TypeScript / VS Code | Go / IntelliJ IDEA |
| --- | --- |
| ![TypeScript rendered with VS Code styling](examples/languages/language-typescript-vscode.png) | ![Go rendered with IntelliJ IDEA styling](examples/languages/language-go-idea.png) |

| SQL / GitHub Light | TOML / Catppuccin Mocha |
| --- | --- |
| ![SQL rendered with GitHub Light](examples/languages/language-sql-github-light.png) | ![TOML rendered with Catppuccin Mocha](examples/languages/language-toml-catppuccin.png) |

Framework examples:

| React / VS Code | Vue / VS Code Light |
| --- | --- |
| ![React rendered with VS Code styling](examples/frameworks/framework-react-vscode.png) | ![Vue rendered with VS Code Light styling](examples/frameworks/framework-vue-vscode-light.png) |

| Complex React / VS Code |
| --- |
| ![Complex React rendered with VS Code styling](examples/frameworks/framework-react-complex-vscode.png) |

| FastAPI / IntelliJ IDEA | Django / IntelliJ IDEA Light |
| --- | --- |
| ![FastAPI rendered with IntelliJ IDEA styling](examples/frameworks/framework-fastapi-idea.png) | ![Django rendered with IntelliJ IDEA Light styling](examples/frameworks/framework-django-idea-light.png) |

| Spring Boot / IntelliJ IDEA Light |
| --- |
| ![Spring Boot rendered with IntelliJ IDEA Light styling](examples/frameworks/framework-spring-idea-light.png) |

Long output:

![Long Ubuntu console output](examples/frames/sample-long-ubuntu.png)

Code input examples:

```text
examples/inputs/example.py
examples/inputs/Vagrantfile
examples/inputs/ansible-playbook.yml
examples/inputs/app.ts
examples/inputs/server.go
examples/inputs/query.sql
examples/inputs/settings.toml
examples/inputs/react-dashboard.tsx
examples/inputs/complex-dashboard.tsx
examples/inputs/vue-profile.vue
examples/inputs/fastapi_app.py
examples/inputs/django_models.py
examples/inputs/SpringApplication.java
examples/inputs/code-render.json
```

Example directories:

```text
examples/frames      Terminal frames and tight terminal blocks
examples/syntax      Syntax theme gallery and editor line-number styles
examples/languages   Multi-language code previews
examples/frameworks  Framework-oriented React, Vue, FastAPI, Django, and Spring previews
examples/themes      Terminal theme gallery
examples/inputs      Source files and logs used to generate the examples
```

## Installation

Install from a local checkout:

```powershell
pip install --user -e .
```

For development with tests:

```powershell
pip install --user -e .[dev]
```

After installation the command is available as:

```powershell
screenshot-compose --help
```

## Usage

```powershell
screenshot-compose render -i lab.log -o build/lab-console.png
```

Common options:

```powershell
screenshot-compose render -i lab.log -o build/windows.png --frame windows
screenshot-compose render -i lab.log -o build/macos.png --frame mac
screenshot-compose render -i lab.log -o build/ubuntu.png --frame ubuntu
screenshot-compose render -i lab.log -o build/block.png --frame frameless
screenshot-compose render -i lab.log -o build/large.png --width 110 --font-size 16
screenshot-compose render -i lab.log -o build/wrapped.png --width 110 --wrap-lines
screenshot-compose render -i lab.log -o build/tight.png --frame frameless --margin 0 --padding-x 0 --padding-y 0
screenshot-compose render -i lab.log -o build/rounded.png --rounded-corners --radius 12
```

Render syntax-highlighted code:

```powershell
screenshot-compose render -i examples/inputs/example.py -o build/python-code.png --content-type code --language python --syntax-theme vscode-dark
screenshot-compose render -i examples/inputs/Vagrantfile -o build/vagrantfile.png --content-type code --language ruby --syntax-theme intellij-dark
screenshot-compose render -i examples/inputs/ansible-playbook.yml -o build/ansible.png --content-type code --language yaml --syntax-theme vscode-light
screenshot-compose render -i examples/inputs/example.py -o build/python-lines.png --content-type code --line-numbers --line-number-style vscode --line-number-start 100
screenshot-compose render -i examples/inputs/example.py -o build/python-idea-lines.png --content-type code --syntax-theme intellij-dark --line-numbers --line-number-style idea
screenshot-compose render -i examples/inputs/example.py -o build/python-no-guides.png --content-type code --line-numbers --line-number-style vscode --no-indent-guides
```

Render framework examples:

```powershell
screenshot-compose render -i examples/inputs/react-dashboard.tsx -o build/react.png --content-type code --language tsx --syntax-theme vscode-dark --line-numbers --line-number-style vscode
screenshot-compose render -i examples/inputs/complex-dashboard.tsx -o build/react-complex.png --content-type code --language tsx --syntax-theme vscode-dark --line-numbers --line-number-style vscode
screenshot-compose render -i examples/inputs/SpringApplication.java -o build/spring.png --content-type code --language java --syntax-theme intellij-light --line-numbers --line-number-style idea
```

Language detection is enabled by default for code mode, using the input filename and content:

```powershell
screenshot-compose render -i examples/inputs/ansible-playbook.yml -o build/ansible-auto.png --content-type code
```

List available built-in themes:

```powershell
screenshot-compose themes
```

For repeatable output, use a JSON config:

```powershell
screenshot-compose render -i examples/inputs/example.py -o build/python-config.png --config examples/inputs/code-render.json --language python
```

Config keys map to `RenderOptions` fields. Short aliases `width` and `theme` are also accepted:

```json
{
  "content_type": "code",
  "syntax_theme": "vscode-dark",
  "frame": "mac",
  "title": "Source Preview",
  "width_chars": 88,
  "wrap_lines": false,
  "font_size": 15,
  "line_spacing": 6,
  "padding_x": 24,
  "padding_y": 20,
  "margin": 14,
  "radius": 12,
  "rounded_corners": false,
  "line_numbers": true,
  "line_number_start": 1,
  "line_number_style": "vscode",
  "indent_guides": true,
  "indent_size": 4
}
```

For larger sets of screenshots, use a YAML project file:

```powershell
screenshot-compose apply -f examples/screenshot-compose.yml
screenshot-compose apply -f examples/screenshot-compose.yml python ansible
```

## YAML Project Files

YAML project files are the main interface for repeatable screenshot sets. A project file describes named render resources, shared defaults, input files, output files, and per-resource overrides.

By default, `apply` looks for `screenshot-compose.yml` in the current directory:

```powershell
screenshot-compose apply
```

Use `-f` to point at another file, and pass resource names to render only part of the project:

```powershell
screenshot-compose apply -f docs/screenshots.yml
screenshot-compose apply -f docs/screenshots.yml api-log python-example
```

Minimal project:

```yaml
version: 1

renders:
  api-log:
    input: logs/api.log
    output: build/api-log.png
```

Project with shared defaults:

```yaml
version: 1

defaults:
  render:
    width: 88
    font_size: 15
    frame: mac
    content_type: code
    syntax_theme: vscode-dark
    line_numbers: true
    line_number_style: vscode

renders:
  python:
    input: inputs/example.py
    output: ../build/project-python.png
    language: python

  terminal:
    input: inputs/sample.log
    output: ../build/project-terminal.png
    content_type: log
    frame: windows
    theme: powershell
    line_numbers: false
```

Paths in project files are resolved relative to the project file location. Resource-level values override `defaults.render`.

Full project-file shape:

```yaml
version: 1

defaults:
  render:
    # Any render option from the table below.
    width: 100
    frame: windows
    content_type: log

renders:
  resource-name:
    input: path/to/input.log
    output: path/to/output.png

    # Options can be written directly on the resource.
    title: Terminal
    theme: auto

  nested-options-example:
    input: path/to/source.py
    output: path/to/source.png

    # Or under options. Direct resource keys and options are merged.
    options:
      content_type: code
      language: python
      syntax_theme: vscode-dark
```

Rules:

- `version` is optional; when omitted it behaves as `1`. Only version `1` is supported.
- `renders` is required and must contain at least one named resource.
- Each resource must define `input` and `output`.
- `defaults.render` is optional. It can contain any render option.
- Resource options override `defaults.render`.
- Options can be placed directly on a resource or inside `options`.
- If the same option exists both directly on a resource and inside `options`, the value inside `options` wins.
- Relative `input`, `output`, and `theme_file` paths are resolved from the YAML file directory.
- Unknown option names fail fast with an error.
- Resources are rendered in the order they appear in the YAML file.

Aliases:

```yaml
width: 88     # same as width_chars: 88
theme: nord   # same as theme_name: nord
```

Render options:

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `width_chars` | integer | `100` | Minimum content width in monospace characters. Long lines expand the image unless `wrap_lines` is enabled. |
| `width` | integer | alias | Short alias for `width_chars`. |
| `wrap_lines` | boolean | `false` | Wrap long lines to `width_chars` instead of expanding the image width. |
| `font_size` | integer | `16` | Font size in pixels. |
| `line_spacing` | integer or null | `null` | Extra pixels between text lines. When omitted, defaults depend on line-number style. |
| `padding_x` | integer | `22` | Horizontal padding inside the terminal window. |
| `padding_y` | integer | `18` | Vertical padding inside the terminal window. |
| `margin` | integer or null | `null` | Transparent outer margin. When omitted, frameless renders use `14`, framed renders use `24`. |
| `titlebar_height` | integer | `38` | Titlebar height for framed windows. Ignored by `frameless`. |
| `radius` | integer | `10` | Window corner radius used when `rounded_corners` is enabled. |
| `rounded_corners` | boolean | `false` | Enable rounded window corners. |
| `title` | string | `Terminal` | Window title text. Long titles are shortened. |
| `theme_name` | string | `auto` | Terminal theme name. |
| `theme` | string | alias | Short alias for `theme_name`. |
| `frame` | string | `windows` | Window frame style: `windows`, `mac`, `ubuntu`, or `frameless`. |
| `content_type` | string | `log` | Render mode: `log` preserves ANSI styling; `code` uses syntax highlighting. |
| `language` | string or null | `null` | Pygments lexer alias, such as `python`, `yaml`, `tsx`, `java`, `go`, or `sql`. |
| `syntax_theme` | string | `vscode-dark` | Syntax theme used when `content_type: code`. |
| `guess_language` | boolean | `true` | Try to infer the lexer from filename/content when `language` is not set. |
| `theme_file` | string or null | `null` | JSON file with custom terminal and syntax themes. Relative paths resolve from the YAML file directory. |
| `line_numbers` | boolean | `false` | Render editor-style line numbers in a left gutter. |
| `line_number_start` | integer | `1` | First rendered line number. Wrapped continuation lines do not receive numbers. |
| `line_number_style` | string | `plain` | Gutter style: `plain`, `vscode`, or `idea`. |
| `indent_guides` | boolean or null | `null` | Render vertical indentation guides. When omitted, enabled for code with `line_number_style: vscode`. |
| `indent_size` | integer | `4` | Number of spaces between indentation guide columns. |

Example: terminal logs with several frames:

```yaml
version: 1

defaults:
  render:
    content_type: log
    width: 100
    font_size: 16
    theme: auto

renders:
  windows-build:
    input: logs/build.log
    output: build/windows-build.png
    frame: windows
    title: Build

  ubuntu-tests:
    input: logs/tests.log
    output: build/ubuntu-tests.png
    frame: ubuntu
    title: pytest

  frameless-snippet:
    input: logs/snippet.log
    output: build/snippet.png
    frame: frameless
    margin: 0
    padding_x: 0
    padding_y: 0
```

Example: source-code screenshots:

```yaml
version: 1

defaults:
  render:
    content_type: code
    frame: mac
    width: 88
    font_size: 15
    line_numbers: true
    line_number_style: vscode
    syntax_theme: vscode-dark

renders:
  python:
    input: src/app.py
    output: build/app-python.png
    language: python
    title: app.py

  react:
    input: src/App.tsx
    output: build/react-component.png
    language: tsx
    title: App.tsx

  idea-java:
    input: src/Main.java
    output: build/main-java.png
    language: java
    syntax_theme: intellij-light
    line_number_style: idea
```

Example: custom theme file:

```yaml
version: 1

defaults:
  render:
    theme_file: themes.json
    theme: lab

renders:
  custom-log:
    input: logs/lab.log
    output: build/lab-log.png

  custom-code:
    input: app.py
    output: build/app.png
    content_type: code
    language: python
    syntax_theme: lab-code
```

Available line number styles:

```text
plain, vscode, idea
```

If `line_spacing` is omitted, `idea` line number style uses a larger default spacing than `plain` and `vscode`. Set `line_spacing` explicitly to override the style default.

When rendering code, `line_number_style: "vscode"` enables vertical indentation guides by default. Use `indent_guides: false` or `--no-indent-guides` to disable them, and `indent_size` or `--indent-size` to change the spacing.

`width_chars` is a minimum width. Long lines expand the image width unless `wrap_lines: true` or `--wrap-lines` is used.

Available frames:

```text
windows, mac, ubuntu, frameless
```

Available themes:

```text
auto, catppuccin-latte, catppuccin-mocha, dark, dracula, github-dark,
github-light, gruvbox-dark, gruvbox-light, light, macos, monokai, nord,
one-dark, powershell, rose-pine, solarized-dark, solarized-light,
tokyo-night, ubuntu
```

Available syntax themes:

```text
catppuccin-latte, catppuccin-mocha, dracula, github-dark, github-light,
gruvbox-dark, gruvbox-light, intellij-dark, intellij-light, monokai, nord,
one-dark, rose-pine, solarized-dark, solarized-light, tokyo-night,
vscode-dark, vscode-light
```

By default, `--theme auto` chooses colors from the selected frame. ANSI colors in the input log are preserved; plain text is not automatically highlighted.

## Built-in Theme Gallery

Terminal theme presets:

| Dark | Light | PowerShell |
| --- | --- | --- |
| ![Dark terminal theme](examples/themes/theme-dark.png) | ![Light terminal theme](examples/themes/theme-light.png) | ![PowerShell terminal theme](examples/themes/theme-powershell.png) |

| Ubuntu | macOS | Dracula |
| --- | --- | --- |
| ![Ubuntu terminal theme](examples/themes/theme-ubuntu.png) | ![macOS terminal theme](examples/themes/theme-macos.png) | ![Dracula terminal theme](examples/themes/theme-dracula.png) |

| Gruvbox Dark | Gruvbox Light | Nord |
| --- | --- | --- |
| ![Gruvbox Dark terminal theme](examples/themes/theme-gruvbox-dark.png) | ![Gruvbox Light terminal theme](examples/themes/theme-gruvbox-light.png) | ![Nord terminal theme](examples/themes/theme-nord.png) |

| Solarized Dark | Solarized Light | Monokai |
| --- | --- | --- |
| ![Solarized Dark terminal theme](examples/themes/theme-solarized-dark.png) | ![Solarized Light terminal theme](examples/themes/theme-solarized-light.png) | ![Monokai terminal theme](examples/themes/theme-monokai.png) |

| One Dark | Catppuccin Mocha | Catppuccin Latte |
| --- | --- | --- |
| ![One Dark terminal theme](examples/themes/theme-one-dark.png) | ![Catppuccin Mocha terminal theme](examples/themes/theme-catppuccin-mocha.png) | ![Catppuccin Latte terminal theme](examples/themes/theme-catppuccin-latte.png) |

| Tokyo Night | Rose Pine | GitHub Dark |
| --- | --- | --- |
| ![Tokyo Night terminal theme](examples/themes/theme-tokyo-night.png) | ![Rose Pine terminal theme](examples/themes/theme-rose-pine.png) | ![GitHub Dark terminal theme](examples/themes/theme-github-dark.png) |

| GitHub Light |
| --- |
| ![GitHub Light terminal theme](examples/themes/theme-github-light.png) |

Syntax theme presets:

| VS Code Dark | VS Code Light | IntelliJ Dark |
| --- | --- | --- |
| ![VS Code Dark syntax theme](examples/syntax/syntax-vscode-dark.png) | ![VS Code Light syntax theme](examples/syntax/syntax-vscode-light.png) | ![IntelliJ Dark syntax theme](examples/syntax/syntax-intellij-dark.png) |

| IntelliJ Light | Dracula | Gruvbox Dark |
| --- | --- | --- |
| ![IntelliJ Light syntax theme](examples/syntax/syntax-intellij-light.png) | ![Dracula syntax theme](examples/syntax/syntax-dracula.png) | ![Gruvbox Dark syntax theme](examples/syntax/syntax-gruvbox-dark.png) |

| Gruvbox Light | Nord | Solarized Dark |
| --- | --- | --- |
| ![Gruvbox Light syntax theme](examples/syntax/syntax-gruvbox-light.png) | ![Nord syntax theme](examples/syntax/syntax-nord.png) | ![Solarized Dark syntax theme](examples/syntax/syntax-solarized-dark.png) |

| Solarized Light | Monokai | One Dark |
| --- | --- | --- |
| ![Solarized Light syntax theme](examples/syntax/syntax-solarized-light.png) | ![Monokai syntax theme](examples/syntax/syntax-monokai.png) | ![One Dark syntax theme](examples/syntax/syntax-one-dark.png) |

| Catppuccin Mocha | Catppuccin Latte | Tokyo Night |
| --- | --- | --- |
| ![Catppuccin Mocha syntax theme](examples/syntax/syntax-catppuccin-mocha.png) | ![Catppuccin Latte syntax theme](examples/syntax/syntax-catppuccin-latte.png) | ![Tokyo Night syntax theme](examples/syntax/syntax-tokyo-night.png) |

| Rose Pine | GitHub Dark | GitHub Light |
| --- | --- | --- |
| ![Rose Pine syntax theme](examples/syntax/syntax-rose-pine.png) | ![GitHub Dark syntax theme](examples/syntax/syntax-github-dark.png) | ![GitHub Light syntax theme](examples/syntax/syntax-github-light.png) |

## Custom Themes

Custom theme files use the same JSON shape as the built-in theme resource. They are merged with built-in themes, so a file can add only the themes it needs:

```json
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
```

Use it from the CLI:

```powershell
screenshot-compose themes --theme-file themes.json
screenshot-compose render -i lab.log -o build/lab.png --theme-file themes.json --theme lab
screenshot-compose render -i app.py -o build/app.png --content-type code --theme-file themes.json --theme lab --syntax-theme lab-code
```

The same `theme_file`, `theme`, and `syntax_theme` keys can be placed in a render config. Relative `theme_file` paths are resolved from the config file directory.

## Saving ANSI Logs

Many CLI tools disable colors when output is redirected to a file. Force colors and save with `tee` or `Tee-Object`.

Linux/macOS:

```bash
pytest --color=yes | tee lab.log
ansible-playbook site.yml --force-color | tee lab.log
docker compose logs --ansi always | tee lab.log
```

PowerShell:

```powershell
pytest --color=yes 2>&1 | Tee-Object lab.log
$env:FORCE_COLOR = "1"
some-command 2>&1 | Tee-Object lab.log
```

Check that ANSI codes were saved:

```powershell
python -c "print(repr(open('lab.log', encoding='utf-8').read()[:300]))"
```

Look for sequences such as `\x1b[32m` and `\x1b[0m`.

## Development

```powershell
pytest
```

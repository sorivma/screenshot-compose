# screenshot-compose

`screenshot-compose` renders terminal logs and source code into polished PNG screenshots. It can be used as a regular CLI for one-off images, but its primary workflow is a compose-style YAML file that declares many screenshot resources with shared defaults.

Use it for documentation, coursework, reports, tutorials, changelogs, and repeatable screenshot pipelines where pasted plain text is not enough.

## What It Does

- Renders terminal logs and source code to PNG.
- Preserves ANSI SGR colors from captured command output.
- Can syntax-highlight entered PowerShell, cmd, WSL, and Ubuntu commands in terminal logs.
- Syntax-highlights source code through Pygments.
- Supports Windows Terminal, macOS Terminal, Ubuntu Terminal, and frameless blocks.
- Provides built-in terminal and syntax themes.
- Adds optional editor-style line numbers and indentation guides.
- Uses YAML project files to render multiple named screenshots consistently.
- Keeps a direct CLI path for quick one-off renders.

## Installation

Install from a local checkout:

```powershell
pip install --user -e .
```

For development with tests:

```powershell
pip install --user -e .[dev]
```

After installation:

```powershell
screenshot-compose --help
```

The legacy command name `console-gen` is still installed as an alias for compatibility.

## Quick Start

Create `screenshot-compose.yml`:

```yaml
version: 1

defaults:
  render:
    width: 88
    font_size: 15
    frame: mac

renders:
  api-log:
    input: logs/api.log
    output: build/api-log.png
    title: API Server

  app-code:
    input: src/app.py
    output: build/app-code.png
    content_type: code
    language: python
    syntax_theme: vscode-dark
    line_numbers: true
    line_number_style: vscode
```

Render all resources:

```powershell
screenshot-compose apply
```

Render only selected resources:

```powershell
screenshot-compose apply api-log
```

Use a project file from another location:

```powershell
screenshot-compose apply -f docs/screenshots.yml
```

Validate a project and all selected input files without rendering:

```powershell
screenshot-compose validate -f docs/screenshots.yml
screenshot-compose validate -f docs/screenshots.yml api-log
```

## Machine-Readable Output

Commands `render`, `themes`, `apply`, and `validate` support `--json`. Successful
responses are written to `stdout`; errors are written to `stderr`. Invalid input
returns exit code `2`, while unexpected internal failures return `1`.

```powershell
screenshot-compose validate -f screenshot-compose.yml --json
screenshot-compose apply -f screenshot-compose.yml --json
screenshot-compose themes --json
screenshot-compose inspect -f screenshot-compose.yml --json
screenshot-compose schema --json
```

The stable response shape contains `status`, `command`, `outputs`, `warnings`,
`errors`, and `data`.

`inspect` reports supported options, themes, and optionally all resources in a
project. `schema` returns the versioned JSON Schema that is also enforced when
project files are loaded.

## Safe Writes

The CLI does not overwrite existing PNG files unless `--force` is supplied.
Use `--dry-run` to validate inputs and plan outputs, and `--output-root` to
prevent writes outside an allowed directory.

```powershell
screenshot-compose apply -f screenshot-compose.yml --dry-run --json
screenshot-compose apply -f screenshot-compose.yml --output-root build --force --json
screenshot-compose apply -f screenshot-compose.yml --manifest build/screenshots.manifest.json --json
```

PNG outputs are written atomically.
Optional manifests contain absolute paths, sizes, and SHA-256 hashes for inputs and outputs.

## YAML Project Files

YAML project files are the main interface for repeatable screenshot sets. They describe named render resources, common defaults, input files, output files, and per-resource overrides.

Minimal project:

```yaml
version: 1

renders:
  build-log:
    input: logs/build.log
    output: build/build-log.png
```

Project with shared defaults:

```yaml
version: 1

defaults:
  render:
    width: 100
    font_size: 16
    frame: windows
    theme: auto

renders:
  tests:
    input: logs/tests.log
    output: build/tests.png
    title: pytest

  deploy:
    input: logs/deploy.log
    output: build/deploy.png
    frame: ubuntu
    title: Deploy
```

Code rendering:

```yaml
version: 1

defaults:
  render:
    content_type: code
    frame: mac
    width: 88
    font_size: 15
    syntax_theme: vscode-dark
    line_numbers: true
    line_number_style: vscode

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

  java-idea:
    input: src/Main.java
    output: build/main-java.png
    language: java
    syntax_theme: intellij-light
    line_number_style: idea
```

Tight frameless snippets:

```yaml
version: 1

defaults:
  render:
    frame: frameless
    margin: 0
    padding_x: 0
    padding_y: 0
    width: 72

renders:
  command-output:
    input: logs/snippet.log
    output: build/snippet.png
```

Custom themes:

```yaml
version: 1

defaults:
  render:
    theme_file: themes.json
    theme: lab

renders:
  lab-log:
    input: logs/lab.log
    output: build/lab-log.png

  lab-code:
    input: app.py
    output: build/app.png
    content_type: code
    language: python
    syntax_theme: lab-code
```

Full project-file shape:

```yaml
version: 1

defaults:
  render:
    # Any render option from the option reference.
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
- `defaults.render` is optional and can contain any render option.
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

## CLI Usage

Render a single terminal log:

```powershell
screenshot-compose render -i lab.log -o build/lab-console.png
```

Common terminal variants:

```powershell
screenshot-compose render -i lab.log -o build/windows.png --frame windows
screenshot-compose render -i lab.log -o build/macos.png --frame mac
screenshot-compose render -i lab.log -o build/ubuntu.png --frame ubuntu
screenshot-compose render -i lab.log -o build/block.png --frame frameless
screenshot-compose render -i lab.log -o build/wrapped.png --width 110 --wrap-lines
screenshot-compose render -i lab.log -o build/tight.png --frame frameless --margin 0 --padding-x 0 --padding-y 0
screenshot-compose render -i lab.log -o build/rounded.png --rounded-corners --radius 12
```

Highlight entered commands in terminal logs:

```powershell
screenshot-compose render -i powershell.log -o build/powershell.png --command-highlight powershell
screenshot-compose render -i cmd.log -o build/cmd.png --command-highlight cmd
screenshot-compose render -i wsl.log -o build/wsl.png --command-highlight wsl
screenshot-compose render -i ubuntu.log -o build/ubuntu.png --command-highlight ubuntu
```

Render source code:

```powershell
screenshot-compose render -i examples/inputs/example.py -o build/python-code.png --content-type code --language python --syntax-theme vscode-dark
screenshot-compose render -i examples/inputs/ansible-playbook.yml -o build/ansible.png --content-type code --language yaml --syntax-theme vscode-light
screenshot-compose render -i examples/inputs/example.py -o build/python-lines.png --content-type code --line-numbers --line-number-style vscode
screenshot-compose render -i examples/inputs/example.py -o build/python-idea-lines.png --content-type code --syntax-theme intellij-dark --line-numbers --line-number-style idea
```

Language detection is enabled by default for code mode:

```powershell
screenshot-compose render -i examples/inputs/ansible-playbook.yml -o build/ansible-auto.png --content-type code
```

Code highlighting uses isolated language providers. Go, Python, Java, JavaScript, TypeScript, JSX, TSX, and Vue
have enriched providers that distinguish declarations, types, functions, methods, parameters, properties, and
namespaces where the language allows it. Other languages use the Pygments fallback provider. A provider failure
or change for one language does not change another language's implementation.

List available themes:

```powershell
screenshot-compose themes
```

Use a JSON or YAML config for one-off `render` commands:

```powershell
screenshot-compose render -i examples/inputs/example.py -o build/python-config.png --config examples/inputs/code-render.json --language python
```

Config keys map to the render options below. `width` and `theme` aliases are accepted.

## Render Option Reference

These keys can be used in `defaults.render`, directly on a YAML resource, inside a resource `options` block, or in a JSON/YAML file passed to `render --config`.

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
| `language` | string or null | `null` | Language alias, such as `python`, `yaml`, `tsx`, `java`, `go`, or `sql`. |
| `syntax_theme` | string | `vscode-dark` | Syntax theme used when `content_type: code`. |
| `guess_language` | boolean | `true` | Try to infer the lexer from filename/content when `language` is not set. |
| `theme_file` | string or null | `null` | JSON file with custom terminal and syntax themes. Relative paths resolve from the config/project file directory. |
| `line_numbers` | boolean | `false` | Render editor-style line numbers in a left gutter. |
| `line_number_start` | integer | `1` | First rendered line number. Wrapped continuation lines do not receive numbers. |
| `line_number_style` | string | `plain` | Gutter style: `plain`, `vscode`, or `idea`. |
| `indent_guides` | boolean or null | `null` | Render vertical indentation guides. When omitted, enabled for code with `line_number_style: vscode`. |
| `indent_size` | integer | `4` | Number of spaces between indentation guide columns. |
| `command_highlight` | string or null | `null` | Highlight recognized shell prompts, entered commands, and common option forms in log mode. Supported values: `powershell`, `cmd`, `wsl`, or `ubuntu`. |

Important behavior:

- `width_chars` is a minimum width. Long lines expand the image width unless `wrap_lines: true` is used.
- `line_number_style: idea` uses a larger default line spacing than `plain` and `vscode`.
- `line_number_style: vscode` enables indentation guides by default for code rendering.
- `theme: auto` chooses terminal colors from the selected frame.
- ANSI colors in log input are preserved; plain log text is not automatically highlighted unless `command_highlight` matches a recognized shell prompt.

Available frames:

```text
windows, mac, ubuntu, frameless
```

Available line number styles:

```text
plain, vscode, idea
```

Available terminal themes:

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

## Examples Gallery

All images in this gallery are generated from one project file:

```powershell
screenshot-compose apply -f examples/screenshot-compose.yml
```

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

Tight output with `margin: 0`, `padding_x: 0`, and `padding_y: 0`:

| Frameless | VS Code Lines | IntelliJ IDEA Lines |
| --- | --- | --- |
| ![Tight frameless terminal block](examples/frames/sample-frameless-tight.png) | ![Tight VS Code line numbers](examples/syntax/syntax-vscode-line-numbers-tight.png) | ![Tight IntelliJ IDEA line numbers](examples/syntax/syntax-idea-line-numbers-tight.png) |

Supported language provider matrix:

Each provider is rendered with VS Code Dark, VS Code Light, IntelliJ Dark, and IntelliJ Light. Images are organized
under `examples/languages/`, with one language directory containing the four theme PNG files.

### Go

| VS Code Dark | VS Code Light | IntelliJ Dark | IntelliJ Light |
| --- | --- | --- | --- |
| ![Go / VS Code Dark](examples/languages/go/vscode-dark.png) | ![Go / VS Code Light](examples/languages/go/vscode-light.png) | ![Go / IntelliJ Dark](examples/languages/go/intellij-dark.png) | ![Go / IntelliJ Light](examples/languages/go/intellij-light.png) |

### Python

| VS Code Dark | VS Code Light | IntelliJ Dark | IntelliJ Light |
| --- | --- | --- | --- |
| ![Python / VS Code Dark](examples/languages/python/vscode-dark.png) | ![Python / VS Code Light](examples/languages/python/vscode-light.png) | ![Python / IntelliJ Dark](examples/languages/python/intellij-dark.png) | ![Python / IntelliJ Light](examples/languages/python/intellij-light.png) |

### Java

| VS Code Dark | VS Code Light | IntelliJ Dark | IntelliJ Light |
| --- | --- | --- | --- |
| ![Java / VS Code Dark](examples/languages/java/vscode-dark.png) | ![Java / VS Code Light](examples/languages/java/vscode-light.png) | ![Java / IntelliJ Dark](examples/languages/java/intellij-dark.png) | ![Java / IntelliJ Light](examples/languages/java/intellij-light.png) |

### JavaScript

| VS Code Dark | VS Code Light | IntelliJ Dark | IntelliJ Light |
| --- | --- | --- | --- |
| ![JavaScript / VS Code Dark](examples/languages/javascript/vscode-dark.png) | ![JavaScript / VS Code Light](examples/languages/javascript/vscode-light.png) | ![JavaScript / IntelliJ Dark](examples/languages/javascript/intellij-dark.png) | ![JavaScript / IntelliJ Light](examples/languages/javascript/intellij-light.png) |

### JSX

| VS Code Dark | VS Code Light | IntelliJ Dark | IntelliJ Light |
| --- | --- | --- | --- |
| ![JSX / VS Code Dark](examples/languages/jsx/vscode-dark.png) | ![JSX / VS Code Light](examples/languages/jsx/vscode-light.png) | ![JSX / IntelliJ Dark](examples/languages/jsx/intellij-dark.png) | ![JSX / IntelliJ Light](examples/languages/jsx/intellij-light.png) |

### TypeScript

| VS Code Dark | VS Code Light | IntelliJ Dark | IntelliJ Light |
| --- | --- | --- | --- |
| ![TypeScript / VS Code Dark](examples/languages/typescript/vscode-dark.png) | ![TypeScript / VS Code Light](examples/languages/typescript/vscode-light.png) | ![TypeScript / IntelliJ Dark](examples/languages/typescript/intellij-dark.png) | ![TypeScript / IntelliJ Light](examples/languages/typescript/intellij-light.png) |

### TSX

| VS Code Dark | VS Code Light | IntelliJ Dark | IntelliJ Light |
| --- | --- | --- | --- |
| ![TSX / VS Code Dark](examples/languages/tsx/vscode-dark.png) | ![TSX / VS Code Light](examples/languages/tsx/vscode-light.png) | ![TSX / IntelliJ Dark](examples/languages/tsx/intellij-dark.png) | ![TSX / IntelliJ Light](examples/languages/tsx/intellij-light.png) |

### Vue

| VS Code Dark | VS Code Light | IntelliJ Dark | IntelliJ Light |
| --- | --- | --- | --- |
| ![Vue / VS Code Dark](examples/languages/vue/vscode-dark.png) | ![Vue / VS Code Light](examples/languages/vue/vscode-light.png) | ![Vue / IntelliJ Dark](examples/languages/vue/intellij-dark.png) | ![Vue / IntelliJ Light](examples/languages/vue/intellij-light.png) |

Framework examples:

| React / VS Code | Vue / VS Code Light |
| --- | --- |
| ![React rendered with VS Code styling](examples/frameworks/framework-react-vscode.png) | ![Vue rendered with VS Code Light styling](examples/frameworks/framework-vue-vscode-light.png) |

| FastAPI / IntelliJ IDEA | Django / IntelliJ IDEA Light |
| --- | --- |
| ![FastAPI rendered with IntelliJ IDEA styling](examples/frameworks/framework-fastapi-idea.png) | ![Django rendered with IntelliJ IDEA Light styling](examples/frameworks/framework-django-idea-light.png) |

| Spring Boot / IntelliJ IDEA Light |
| --- |
| ![Spring Boot rendered with IntelliJ IDEA Light styling](examples/frameworks/framework-spring-idea-light.png) |

Long output:

![Long Ubuntu console output](examples/frames/sample-long-ubuntu.png)

Gallery project and input files:

```text
examples/screenshot-compose.yml
examples/inputs/example.py
examples/inputs/Vagrantfile
examples/inputs/ansible-playbook.yml
examples/inputs/windows.log
examples/inputs/macos.log
examples/inputs/ubuntu.log
examples/inputs/sample.log
examples/inputs/long-ubuntu.log
examples/inputs/app.ts
examples/inputs/app.js
examples/inputs/profile.jsx
examples/inputs/server.go
examples/inputs/query.sql
examples/inputs/settings.toml
examples/inputs/react-dashboard.tsx
examples/inputs/complex-dashboard.tsx
examples/inputs/vue-profile.vue
examples/inputs/fastapi_app.py
examples/inputs/django_models.py
examples/inputs/SpringApplication.java
```

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

## Custom Theme Files

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
        {"token": "keyword", "color": "#f2aa4c", "bold": true},
        {"token": "function", "color": "#ffd166"},
        {"token": "method", "color": "#ffd166"},
        {"token": "type", "color": "#4ec9b0"},
        {"token": "string", "color": "#99ddff"}
      ]
    }
  }
}
```

Syntax themes use language-independent semantic token names:

```text
text, comment, keyword, namespace, type, function, method, parameter,
variable, property, builtin, decorator, tag, attribute, string, number,
operator, punctuation, heading, subheading, deleted, inserted, error
```

Existing Pygments-style names such as `Keyword`, `Name.Function`, and `String` remain supported for compatibility.

Use it from YAML:

```yaml
version: 1

defaults:
  render:
    theme_file: themes.json
    theme: lab

renders:
  app:
    input: app.py
    output: build/app.png
    content_type: code
    language: python
    syntax_theme: lab-code
```

Use it from the CLI:

```powershell
screenshot-compose themes --theme-file themes.json
screenshot-compose render -i lab.log -o build/lab.png --theme-file themes.json --theme lab
screenshot-compose render -i app.py -o build/app.png --content-type code --theme-file themes.json --theme lab --syntax-theme lab-code
```

## Capturing ANSI Logs

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

Run tests:

```powershell
pytest
```

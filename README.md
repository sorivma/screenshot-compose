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

Project files describe named render resources with shared defaults:

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

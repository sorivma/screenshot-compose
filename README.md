# console-gen

`console-gen` turns console logs into PNG screenshots that look like real terminal windows. It is designed for laboratory reports, coursework, and technical documentation where pasted plain text looks too artificial.

## Features

- PNG output with transparent outer margins.
- Window frames for Windows Terminal, macOS Terminal, Ubuntu Terminal, and frameless terminal blocks.
- Automatic terminal theme selection with `--theme auto`.
- ANSI SGR support: real colorized command output is preserved when the input log contains escape codes.
- Logs without ANSI escape codes are rendered with the selected theme text color.
- Long logs are rendered as tall screenshots with automatic line wrapping.

## Examples

| Platform | Input | Output |
| --- | --- | --- |
| Windows | `examples/windows.log` | `examples/sample-windows.png` |
| macOS | `examples/macos.log` | `examples/sample-macos.png` |
| Ubuntu | `examples/ubuntu.log` | `examples/sample-ubuntu.png` |
| Frameless | `examples/ubuntu.log` | `examples/sample-frameless.png` |
| Long Ubuntu log | `examples/long-ubuntu.log` | `examples/sample-long-ubuntu.png` |

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
console-gen --help
```

## Usage

```powershell
console-gen render -i lab.log -o build/lab-console.png
```

Common options:

```powershell
console-gen render -i lab.log -o build/windows.png --frame windows
console-gen render -i lab.log -o build/macos.png --frame mac
console-gen render -i lab.log -o build/ubuntu.png --frame ubuntu
console-gen render -i lab.log -o build/block.png --frame frameless
console-gen render -i lab.log -o build/large.png --width 110 --font-size 16
```

Available frames:

```text
windows, mac, ubuntu, frameless
```

Available themes:

```text
auto, dark, light, macos, powershell, ubuntu
```

By default, `--theme auto` chooses colors from the selected frame. ANSI colors in the input log are preserved; plain text is not automatically highlighted.

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

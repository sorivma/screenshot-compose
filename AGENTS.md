# Agent Guide

## Purpose

`screenshot-compose` renders terminal logs and source code into repeatable PNG artifacts.

## Reliable Workflow

1. Discover capabilities with `screenshot-compose inspect --json`.
2. Obtain the current contract with `screenshot-compose schema --json`.
3. Validate with `screenshot-compose validate -f <project> --json`.
4. Preview writes with `screenshot-compose apply -f <project> --dry-run --output-root <root> --json`.
5. Render with `--force` only when replacing existing artifacts is intended.
6. Use `--manifest <path>` when downstream automation must verify exact inputs and outputs.

Successful JSON is written to stdout. Errors are written to stderr. Exit code `2`
means invalid input or arguments; exit code `1` means an unexpected internal error.

## Development

```powershell
python -m pip install -e ".[dev]"
ruff check src tests
python -m pytest -q
```

Keep `src/console_gen/schemas/v1.json`, examples, README, and CLI behavior aligned.

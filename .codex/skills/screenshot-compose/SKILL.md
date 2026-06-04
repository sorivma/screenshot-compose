---
name: screenshot-compose
description: Validate and render repeatable terminal and source-code PNG screenshots from YAML.
---

# Screenshot Compose

1. Discover capabilities with `screenshot-compose inspect --json`.
2. Read the exact contract with `screenshot-compose schema --json`.
3. Validate with `screenshot-compose validate -f <project> --json`.
4. Preview with `screenshot-compose apply -f <project> --dry-run --output-root <root> --json`.
5. Render with an explicit output root. Add `--force` only for intentional replacement.
6. Add `--manifest <path>` when exact input/output hashes are required.

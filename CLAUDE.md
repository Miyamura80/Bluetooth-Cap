# CLAUDE.md

## Project Overview

CLI for interfacing with a BLE LED matrix cap (`LED_BLE_62F7C880`). Uses `bleak` for BLE communication. Python >= 3.12, `uv` for deps.
**Before any other work in this repo, enable prek:** `uv tool install prek && prek install`. Hooks are defined in `prek.toml`.

## BLE Device

- **Device name**: `LED_BLE_62F7C880` (configurable in `common/global_config.yaml` under `ble.device_name`)
- **Service 0x00FA**: char `fa02` (write), char `fa03` (notify) - primary data channel
- **Service 0xAE00**: char `ae01` (write), char `ae02` (notify) - secondary channel
- Protocol is not yet reverse-engineered; commands under `commands/` currently do scanning and service enumeration only.

## Common Commands

```bash
make ci             # Run all CI checks before committing
make test           # Run pytest
make fmt            # Format with ruff + jq
uv sync             # Install deps
uv run bluecap scan           # Scan for LED_BLE devices
uv run bluecap device info    # Connect and show services
```

## Architecture

- **commands/** - Auto-discovered CLI commands (`scan.py`, `device.py`, `config.py`, `doctor.py`)
- **common/** - Pydantic-settings config (`global_config.yaml`, `.env`)
- **src/cli/** - CLI framework (state, telemetry, scaffold, security, completions)
- **src/utils/** - Shared utilities (output, errors, theme, progress)
- **cli.py:176** - Entry point (`main_cli`)

## Code Style

Enforced by ruff (config in `pyproject.toml`). snake_case functions, CamelCase classes, 4-space indent, double quotes, built-in generic types.

## Configuration Pattern

```python
from common import global_config
global_config.ble.device_name  # "LED_BLE_62F7C880"
```

## Logging

```python
from loguru import logger as log
from src.utils.logging_config import setup_logging

setup_logging()
log.debug("detailed diagnostic information")
log.info("general informational message")
log.warning("warning message for potentially harmful situations")
log.error("error message for error events")
```

## Commit Message Convention

Emoji prefixes (multiple = 5+ files): 🏗️ initial, 🔨 feature, 🐛 bugfix, ✨ formatting, ✅ feature+tests, ⚙️ config.

## Long-Running Code Pattern

Structure as: `init()` -> `continue(id)` -> `cleanup(id)`
- Keep state serializable
- Use descriptive IDs (runId, taskId)
- Handle rate limits, timeouts, retries at system boundaries

## Subagents

- Folder-size CI failure -> spawn subagent `.claude/agents/folder-refactor-advisor.md`.

## Git Workflow

- **Protected Branch**: `main` - use PRs, squash merge.
- **Never force push**.
- **Pre-commit CI gate**: `make ci` must pass before committing.

## Deprecated

- Don't use `datetime.utcnow()` - use `datetime.now(timezone.utc)`

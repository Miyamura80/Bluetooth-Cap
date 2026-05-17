# Contributing

## Getting Started

1.  **Prerequisites**:
    *   Python >= 3.12
    *   `uv` (for dependency management)
    *   A BLE-capable machine (macOS, Linux with BlueZ, Windows)
    *   The LED cap powered on and nearby for integration testing

2.  **Setup**:
    ```bash
    uv sync
    uv run bluecap doctor --fix
    ```

3.  **Run Tests**:
    ```bash
    make test
    ```

## Development Workflow

1.  Create a new branch for your feature/fix.
2.  Make your changes.
3.  Ensure code quality commands pass:
    ```bash
    make ci
    ```

## Protocol Extension

The iPIXEL Color protocol is implemented in `src/protocol/`. To add new commands:

1. Use `bluecap send` to send raw bytes and `bluecap notify` to observe responses.
2. Add the command encoder to `src/protocol/commands.py` and a CLI command in `commands/`.
3. Use nRF Connect (mobile) or Wireshark with an nRF52840 dongle to capture packets from the official app for undocumented commands.

## Code Style

*   Follow the existing conventions (snake_case for functions, CamelCase for classes).
*   Use `ruff` for linting and formatting (handled by `make fmt` and `make ruff`).
*   Add tests for new features.

## Pull Requests

*   Keep PRs focused on a single change.
*   Update documentation if necessary.

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

## Protocol Research

If you're contributing to the BLE protocol reverse engineering:

1. Use nRF Connect (mobile) or Wireshark with an nRF52840 dongle to capture packets.
2. Document findings in `docs/` with hex dumps and annotated field breakdowns.
3. Add corresponding CLI commands in `commands/` once the protocol is understood.

## Code Style

*   Follow the existing conventions (snake_case for functions, CamelCase for classes).
*   Use `ruff` for linting and formatting (handled by `make fmt` and `make ruff`).
*   Add tests for new features.

## Pull Requests

*   Keep PRs focused on a single change.
*   Update documentation if necessary.

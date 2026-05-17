---
name: usage
description: How to use the CLI interface. Use this skill when interacting with the tool as an end user.
---
# Usage Guide

This skill teaches you how to use the CLI interface provided by this project.

## CLI

### Installation

```bash
pip install bluetooth-cap
```

Or install from source:

```bash
git clone https://github.com/Miyamura80/CLI-Template.git
cd CLI-Template
uv sync
```

### Basic Usage

```bash
# Show help and all available commands
uv run bluecap --help

# Run a command
uv run bluecap greet Alice

# Scaffold a new command
uv run bluecap init my_command --desc "Does something"
```

### Global Flags

Global flags go **before** the subcommand:

| Flag | Short | Description |
|---|---|---|
| `--verbose` | `-v` | Increase output verbosity |
| `--quiet` | `-q` | Suppress non-essential output |
| `--debug` | | Show full tracebacks on error |
| `--format` | `-f` | Output format: `table`, `json`, `plain` |
| `--dry-run` | | Preview actions without executing |
| `--version` | `-V` | Print version and exit |

### Examples

```bash
# JSON output
uv run bluecap --format json config show

# Preview without executing
uv run bluecap --dry-run greet Bob

# Detailed output
uv run bluecap --verbose greet Alice

# Manage configuration
uv run bluecap config show
uv run bluecap config get llm_config.cache_enabled
uv run bluecap config set logging.verbose false
```

### Shell Completions

```bash
# Install completions for your shell
uv run bluecap --install-completion

# Show completion script
uv run bluecap --show-completion
```

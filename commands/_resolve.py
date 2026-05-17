"""Shared device name resolution for CLI commands."""

import typer
from rich.console import Console


def resolve_device_name(name: str | None, console: Console) -> str:
    """Resolve BLE device name from --name flag or global config."""
    if name:
        return name
    try:
        from common import global_config

        ble_cfg = getattr(global_config, "ble", None)
        if isinstance(ble_cfg, dict) and ble_cfg.get("device_name"):
            return ble_cfg["device_name"]
    except (ImportError, AttributeError, KeyError, TypeError):
        pass
    console.print("[red]No device name specified.[/red]")
    console.print("[dim]Use --name or set ble.device_name in global_config.yaml[/dim]")
    raise typer.Exit(code=1)

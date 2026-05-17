# bluetooth-cap

<p align="center">
  <img src="media/banner.png" alt="2" width="400">
</p>

<p align="center">
<b>🧢 CLI for interfacing with BLE LED matrix cap</b>
</p>

<p align="center">
  <a href="#quick-start">Quick Start</a> •
  <a href="#commands">Commands</a> •
  <a href="#device-info">Device Info</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#roadmap">Roadmap</a>
</p>

<p align="center">
  <img alt="Project Version" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fraw.githubusercontent.com%2FMiyamura80%2FBluetooth-Cap%2Fmain%2Fpyproject.toml&query=%24.project.version&label=version&color=blue">
  <img alt="Python Version" src="https://img.shields.io/badge/dynamic/toml?url=https%3A%2F%2Fraw.githubusercontent.com%2FMiyamura80%2FBluetooth-Cap%2Fmain%2Fpyproject.toml&query=%24.project['requires-python']&label=python&logo=python&color=blue">
  <img alt="GitHub repo size" src="https://img.shields.io/github/repo-size/Miyamura80/Bluetooth-Cap">
</p>

---

A Python CLI for scanning, connecting to, and (eventually) controlling a [BLE LED matrix cap](https://www.amazon.co.uk/LIOVODE-Christmas-Birthday-Advertising-Campaign/dp/B0G2S4H849?th=1). The cap advertises as `LED_BLE_*` over Bluetooth Low Energy.

Currently in scaffolding phase - protocol reverse engineering is planned but not yet implemented.

## Agent Prompt

> Copy and paste this into your AI coding agent (Claude Code, Cursor, Copilot, etc.) to install:

```text
Install the CLI and download the usage skill:

uv pip install bluetooth-cap

curl -fsSL https://raw.githubusercontent.com/Miyamura80/Bluetooth-Cap/main/scripts/install-skills.sh -o install-skills.sh
bash install-skills.sh && rm install-skills.sh
```

## Quick Start

```bash
uv sync                                              # install deps (includes bleak for BLE)
uv run bluecap scan                                  # find nearby LED_BLE devices
uv run bluecap info --name LED_BLE_62F7C880          # connect and inspect BLE services
uv run bluecap probe                                 # detect device type and LED dimensions
uv run bluecap power on                              # power on the cap
uv run bluecap brightness 50                         # set brightness to 50%
```

## Commands

| Command | Description |
|---------|-------------|
| `bluecap scan` | Scan for nearby BLE LED cap devices |
| `bluecap info` | Connect to cap and display service/characteristic tree |
| `bluecap probe` | Query device type and LED matrix dimensions |
| `bluecap send <hex>` | Send raw bytes to cap (reverse engineering tool) |
| `bluecap power on\|off` | Turn the LED cap on or off |
| `bluecap brightness <1-100>` | Set LED brightness |
| `bluecap notify <uuid>` | Subscribe to notifications from a characteristic |
| `bluecap doctor` | Check project environment health |
| `bluecap config show` | Show current configuration |

### Scan

```bash
uv run bluecap scan                    # find LED_BLE_* devices (10s scan)
uv run bluecap scan --timeout 20       # longer scan
uv run bluecap scan --all              # show all BLE devices
uv run bluecap scan --prefix "LED"     # custom name prefix filter
```

### Device Control

```bash
uv run bluecap info                    # connect and show BLE service tree
uv run bluecap probe                   # detect device type and matrix size
uv run bluecap power on                # turn on
uv run bluecap power off               # turn off
uv run bluecap brightness 75           # set brightness to 75%
```

### Reverse Engineering

```bash
uv run bluecap send 05 00 07 01 01     # send raw bytes (power on command)
uv run bluecap send 05 00 04 80 32     # send raw bytes (brightness 50%)
uv run bluecap send --no-listen AA BB  # send without listening for response
uv run bluecap notify 0000fa03-0000-1000-8000-00805f9b34fb  # listen for notifications
```

## Protocol

Uses the **iPIXEL Color** protocol. All commands are written to characteristic `fa02`, responses come back on `fa03`.

Command format: `[LEN_LO][LEN_HI][CMD_LO][CMD_HI][DATA...]` (little-endian).

| Service UUID | Characteristics | Description |
|---|---|---|
| `000000fa-0000-1000-8000-00805f9b34fb` | `fa02` (write), `fa03` (notify) | Primary data channel (iPIXEL protocol) |
| `0000ae00-0000-1000-8000-00805f9b34fb` | `ae01` (write), `ae02` (notify) | Jieli RCSP channel (auth/OTA) |

| Command | Bytes | Description |
|---|---|---|
| Power on | `05 00 07 01 01` | Turn display on |
| Power off | `05 00 07 01 00` | Turn display off |
| Brightness 50% | `05 00 04 80 32` | Set brightness (1-100) |
| Device info | `08 00 01 80 HH MM SS 00` | Query device type (also syncs clock) |
| Default mode | `04 00 03 80` | Return to default display |
| Flip display | `05 00 06 80 01` | Flip display upside down |

## Configuration

BLE settings in `common/global_config.yaml`:

```yaml
ble:
  device_name: "LED_BLE_62F7C880"
  scan_timeout: 10.0
  device_prefix: "LED_BLE"
```

## Roadmap

- [x] BLE device scanning
- [x] Service/characteristic enumeration
- [x] Notification subscription
- [x] iPIXEL protocol implementation (power, brightness, device info)
- [x] Raw byte sending for reverse engineering
- [x] Device type detection and matrix dimension query
- [ ] Display text on LED matrix
- [ ] Display images (PNG/GIF) on LED matrix
- [ ] Animation and clock mode support
- [ ] DIY pixel drawing mode

## Credits

- [Bleak](https://bleak.readthedocs.io/) - Cross-platform BLE library
- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [uv](https://docs.astral.sh/uv/) - Python package manager
- [prek](https://github.com/j178/prek) - Rust-based pre-commit framework

## About the Core Contributors

<a href="https://github.com/Miyamura80/Bluetooth-Cap/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Miyamura80/Bluetooth-Cap" />
</a>

Made with [contrib.rocks](https://contrib.rocks).

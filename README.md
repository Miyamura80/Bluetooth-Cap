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

<img width="512" height="501" alt="Screenshot 2026-05-17 at 17 37 27" src="https://github.com/user-attachments/assets/b1e27c64-e893-44d3-af75-aa11e932a1a3" />


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
uv run bluecap device info --name LED_BLE_62F7C880   # connect and inspect BLE services
```

## Commands

| Command | Description |
|---------|-------------|
| `bluecap scan` | Scan for nearby BLE LED cap devices |
| `bluecap device info` | Connect to cap and display service/characteristic tree |
| `bluecap device notify <uuid>` | Subscribe to notifications from a characteristic |
| `bluecap doctor` | Check project environment health |
| `bluecap config show` | Show current configuration |

### Scan

```bash
uv run bluecap scan                    # find LED_BLE_* devices (10s scan)
uv run bluecap scan --timeout 20       # longer scan
uv run bluecap scan --all              # show all BLE devices
uv run bluecap scan --prefix "LED"     # custom name prefix filter
```

### Device

```bash
uv run bluecap device info --name LED_BLE_62F7C880   # connect to a specific device
uv run bluecap device notify 0000fa03-0000-1000-8000-00805f9b34fb  # listen for notifications
```

## Device Info

Devices advertise as `LED_BLE_<ID>` (e.g. `LED_BLE_62F7C880`).

| Service UUID | Characteristics | Description |
|---|---|---|
| `000000fa-0000-1000-8000-00805f9b34fb` | `fa02` (write), `fa03` (notify) | Primary data channel |
| `0000ae00-0000-1000-8000-00805f9b34fb` | `ae01` (write), `ae02` (notify) | Secondary channel |

Protocol details TBD - reverse engineering not yet started.

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
- [ ] Protocol reverse engineering (packet capture & analysis)
- [ ] Display text/images on LED matrix
- [ ] Animation support
- [ ] Brightness/speed control

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

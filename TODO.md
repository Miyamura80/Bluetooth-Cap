# TODO

## Protocol Reverse Engineering

- [ ] Capture BLE packets while using the official phone app (use Wireshark + nRF Connect)
- [ ] Document the packet format for service `0x00FA` (primary data channel)
- [ ] Document the packet format for service `0xAE00` (secondary channel)
- [ ] Identify command structure: header, payload, checksum
- [ ] Map commands: set text, set animation, set brightness, set speed

## CLI Features

- [ ] `bluecap send` command - send raw bytes to a characteristic
- [ ] `bluecap text` command - display text on the LED matrix (after protocol is known)
- [ ] `bluecap image` command - display bitmap on the LED matrix
- [ ] `bluecap animate` command - play animations
- [ ] Device auto-reconnection with retry logic
- [ ] Save device address to config for faster connections (skip scan)

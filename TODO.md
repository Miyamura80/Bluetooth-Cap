# TODO

## Protocol Verification

- [ ] Run `bluecap probe` against the physical device to confirm iPIXEL protocol and detect matrix dimensions
- [ ] Verify `bluecap power on/off` commands work
- [ ] Verify `bluecap brightness` works (try 1, 50, 100)
- [ ] Capture and document any unknown response bytes from `probe`

## CLI Features

- [ ] `bluecap text` command - render text client-side and send as bitmap (TYPE_TEXT)
- [ ] `bluecap image` command - send PNG/GIF with chunked 12KB windows + CRC32 + ACK
- [ ] `bluecap clock` command - configure clock display mode
- [ ] `bluecap flip` command - flip display orientation
- [ ] `bluecap screen` command - select display buffer (1-9)
- [ ] `bluecap diy` command - enter DIY pixel drawing mode
- [ ] `bluecap erase` command - erase display buffers
- [ ] Device auto-reconnection with retry logic
- [ ] Save device address to config for faster connections (skip scan)

## Protocol

- [ ] Implement chunked image transfer with 12KB windows and ACK handling
- [ ] Implement CRC32 verification for image data
- [ ] Implement text-to-bitmap rendering (font rasterization)
- [ ] Investigate AE00 service (Jieli RCSP) for firmware version query
- [ ] Document any protocol differences specific to this device variant

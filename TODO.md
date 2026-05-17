# TODO

## Done

- [x] Run `bluecap probe` against the physical device to confirm iPIXEL protocol and detect matrix dimensions
- [x] Verify `bluecap power on/off` commands work
- [x] Verify `bluecap brightness` works (try 1, 50, 100)
- [x] `bluecap text` command - static text (PNG) and scrolling text (GIF-based)
- [x] `bluecap image` command - send PNG/GIF with chunked 12KB windows + CRC32 + ACK
- [x] `bluecap clock` command - configure clock display mode (8 styles, 12h/24h, date)
- [x] `bluecap flip` command - flip display orientation
- [x] `bluecap screen` command - select display buffer (1-9)
- [x] `bluecap pixel` command - DIY pixel drawing mode
- [x] `bluecap erase` command - erase display buffers
- [x] Implement chunked image transfer with 12KB windows and ACK handling
- [x] Implement CRC32 verification for image data
- [x] Implement text-to-bitmap rendering (font rasterization)

## Remaining

- [ ] Device auto-reconnection with retry logic
- [ ] Save device address to config for faster connections (skip scan)
- [ ] Investigate AE00 service (Jieli RCSP) for firmware version query
- [ ] Document any protocol differences specific to this device variant

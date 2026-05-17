---
name: gif-protocol
description: Sharp bits and gotchas for sending GIFs and scrolling text to the iPIXEL LED cap
user_invocable: true
triggers:
  - /gif-protocol
---

<!-- claude-only -->

# GIF Protocol - Sharp Bits

Reference for sending GIF animations (including scrolling text) to the iPIXEL LED cap. These are non-obvious constraints discovered through hardware testing.

## GIF Encoding Requirements

The device's GIF decoder is simple. Two Pillow settings are **mandatory** for smooth playback:

```python
frames[0].save(
    buf,
    format="GIF",
    save_all=True,
    append_images=frames[1:],
    duration=frame_duration,
    loop=0,
    disposal=2,       # REQUIRED: restore to background between frames
    optimize=False,    # REQUIRED: full frames, no inter-frame diffs
)
```

- **`disposal=2`**: Without this, the device stacks frames on top of each other, causing visual corruption and discontinuous jumps.
- **`optimize=False`**: Pillow's default inter-frame optimization produces diffs the device can't decode properly. Each frame must be a complete image.
- **`convert("RGBA")`**: Frames should be converted to RGBA before saving (matches the format that worked with pre-made GIFs).

## Scrolling Text as GIF

The native text protocol (`CMD_TEXT = 0x0100`) causes an immediate device disconnect on this hardware variant. Scrolling text is implemented by rendering text frames as a GIF animation instead.

Key design decisions:
- **Text starts at x=0** (visible from frame 1). Do NOT pad with blank frames before/after the text - the device plays through them and the user sees flicker/blank.
- **Step size = 2px** per frame for smooth scrolling. Larger steps (5-10px) produce visible jumps.
- **Canvas layout**: `total_width = text_width + display_width`. Text at position 0, one display-width of blank padding at the end for the loop gap.
- **Frame duration**: `max(30, 250 - speed * 3)` ms, where speed is 0-100.

## Windowed Transfer (>12KB)

Payloads exceeding 12,288 bytes (WINDOW_SIZE) are split into windows by `src/protocol/transport.py`:

- Each window gets a header: `[option][total_size:4LE][crc32:4LE][0x00][slot]`
- First window: `option=0x00`, subsequent: `option=0x02`
- Device ACKs each window before the next is sent
- Final ACK byte `0x03` = all data received; `0x01` = more windows expected
- Chunks within each window are MTU-sized (MTU - 3, capped at 512 bytes)

## Static Text as PNG

For non-scrolling text, render to a 32x16 PNG and send via `CMD_GIF_DATA` (0x0003). The PNG must be exactly the display dimensions (32x16) - oversized PNGs are accepted (ACK) but not displayed.

## Common Pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| Frames flash/jump discontinuously | Missing `disposal=2` or `optimize=False` | Add both to GIF save |
| Text not visible, blank display | PNG wider than 32px | Render to exact display dimensions |
| Device disconnects on send | Using native text protocol (0x0100) | Use GIF-based scrolling instead |
| Only see flicker of text edges | Too many blank padding frames | Start text at x=0, not x=width |
| Scrolling looks janky | Step size too large | Use step=2px for smooth movement |
| Send hangs/times out | Payload >12KB without windowing | Use `send_data()` from transport.py |

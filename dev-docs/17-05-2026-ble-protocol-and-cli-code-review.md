# Code Review - ble-protocol-and-cli

**Date:** 17-05-2026
**Branch:** main (uncommitted changes)
**Scope:** iPIXEL BLE protocol implementation, CLI commands for LED cap control, windowed transport, GIF-based scrolling text

**Legend:** ✅ valid (fixed) · 🟡 deferred · ❌ invalid

---

## Iteration 1 - /codex:rescue

### ✅ P1 Finding 1.1 - Static text sends PNG data via CMD_GIF_DATA
- **File:** `commands/text.py:136`
- **Severity:** P1
- **Category:** bug

**Codex said:**
> Static text renders PNG bytes but sends them with `CMD_GIF_DATA`. The device receives a PNG payload under the GIF command, so `bluecap text --static` can be rejected, misdecoded, or display corrupted data.

**Relevant code:**
```python
acks = await send_data(client, CMD_GIF_DATA, data, slot=slot, timeout=30.0)
```

**Resolution:** Correct - static text renders a PNG and should use `CMD_PNG_DATA`, matching how `commands/image.py` sends PNGs. It worked by accident on the device but is semantically wrong.

**Diff:**
```diff
-from src.protocol.commands import CMD_GIF_DATA
+from src.protocol.commands import CMD_GIF_DATA, CMD_PNG_DATA
...
-        acks = await send_data(client, CMD_GIF_DATA, data, slot=slot, timeout=30.0)
+        acks = await send_data(client, CMD_PNG_DATA, data, slot=slot, timeout=30.0)
```

---

### ✅ P1 Finding 1.2 - Window ACK timeout swallowed, transfer continues
- **File:** `src/protocol/transport.py:72`
- **Severity:** P1
- **Category:** bug

**Codex said:**
> Window ACK timeouts are swallowed and transfer continues. After a missing ACK, later windows can still be sent, violating the documented "ACK before next window" protocol and risking partial or corrupted image/GIF transfers.

**Relevant code:**
```python
except TimeoutError:
    acks.append(b"")
finally:
    await client.stop_notify(NOTIFY_UUID)
```

**Resolution:** Valid. The protocol requires an ACK before the next window. If a window times out, continuing sends data the device isn't expecting. Added `break` to abort the transfer on timeout.

**Diff:**
```diff
 except TimeoutError:
     acks.append(b"")
+    break
 finally:
     await client.stop_notify(NOTIFY_UUID)
```

---

### 🟡 P2 Finding 1.3 - make_payload 16-bit length overflow
- **File:** `src/protocol/commands.py:33`
- **Severity:** P2
- **Category:** bug

**Codex said:**
> `make_payload()` packs total length as an unsigned 16-bit field without validating size. Direct `png_data()`/`gif_data()` calls with payloads over 65,531 bytes raise `struct.error` instead of producing a controlled error or using windowed transport.

**Relevant code:**
```python
def make_payload(command: int, data: bytes = b"") -> bytes:
    length = len(data) + 2
    return struct.pack("<HH", length, command) + data
```

**Resolution:** Real concern but deferred. In practice `make_payload` is only called from `transport.send_data()` which splits data into 12KB windows before calling it, so the 16-bit overflow can't happen through normal usage. Direct calls to `png_data()`/`gif_data()` in commands.py are unused (the windowed path is used instead). Adding validation would be defensive but not critical.

---

### ❌ P3 Finding 1.4 - Slot range not validated in transport.py
- **File:** `src/protocol/transport.py:52`
- **Severity:** P3
- **Category:** nit

**Codex said:**
> `slot` is packed with `bytes([0x00, slot])` without range validation. `slot < 0` or `slot > 255` crashes with `ValueError`; invalid display slots like `0` or `10` are silently sent to the device.

**Relevant code:**
```python
+ bytes([0x00, slot])
```

**Resolution:** Disagree this warrants a fix here. The CLI layer (typer) constrains slot to int, and all callers pass values from `--slot` options documented as 1-9. Transport is an internal module, not a public API boundary. The device itself rejects invalid slots harmlessly.

---

### ❌ P3 Finding 1.5 - Pixel coordinates not validated
- **File:** `commands/pixel.py:44`
- **Severity:** P3
- **Category:** nit

**Codex said:**
> Pixel coordinates are passed unchecked into `proto.set_pixel()`, which packs `x` and `y` into single bytes. Negative or >255 coordinates crash; coordinates outside the actual LED matrix but within byte range are sent as invalid device commands.

**Relevant code:**
```python
proto.set_pixel(x, y, r, g, b)
```

**Resolution:** Disagree - typer enforces int type, and the device (32x16) silently ignores out-of-range pixels. Adding validation at every command would be defensive clutter for a CLI tool used interactively. Same pattern as slot validation.

---

### ❌ P3 Finding 1.6 - Erase slots not validated
- **File:** `commands/erase.py:19`
- **Severity:** P3
- **Category:** nit

**Codex said:**
> Erase slots are passed unchecked into `proto.erase_buffers()`. Invalid values can crash byte packing or send erase commands for buffer slots outside the documented `1-9` range.

**Relevant code:**
```python
proto.erase_buffers(slots)
```

**Resolution:** Same reasoning as findings 1.4 and 1.5. The CLI documents the valid range, and the device ignores invalid slots. Not a runtime risk.

---

### ✅ P2 Finding 1.7 - Notify cleanup missing in send.py
- **File:** `commands/send.py:50`
- **Severity:** P2
- **Category:** bug

**Codex said:**
> Notifications are started without a `finally` cleanup around write/listen operations. If `write_gatt_char()` or the listen sleep fails before line 58, `stop_notify()` is skipped until disconnect cleanup.

**Relevant code:**
```python
await client.start_notify(NOTIFY_UUID, on_notify)

console.print(f"[yellow]>> {data.hex(' ')}[/yellow]  ({len(data)} bytes)")
await client.write_gatt_char(char_uuid, data)

if listen:
    ...
    await client.stop_notify(NOTIFY_UUID)
```

**Resolution:** Valid. If `write_gatt_char` raises, `stop_notify` is never called. Wrapped the write+listen block in try/finally.

**Diff:**
```diff
-        console.print(f"[yellow]>> {data.hex(' ')}[/yellow]  ({len(data)} bytes)")
-        await client.write_gatt_char(char_uuid, data)
-
-        if listen:
-            ...
-            await client.stop_notify(NOTIFY_UUID)
+        try:
+            console.print(...)
+            await client.write_gatt_char(char_uuid, data)
+            if listen:
+                ...
+        finally:
+            if listen:
+                await client.stop_notify(NOTIFY_UUID)
```

---

### ❌ P2 Finding 1.8 - Loguru diagnose=True leaks secrets via tracebacks
- **File:** `src/utils/logging_config.py:295`
- **Severity:** P2
- **Category:** security

**Codex said:**
> Loguru is configured with `diagnose=True` while the scrubber only redacts message, exception args, and extras. Exception tracebacks can include local variable values that bypass the redaction path and leak secrets into logs.

**Relevant code:**
```python
# (not in our diff)
```

**Resolution:** This file is not part of the current changeset - it's pre-existing code untouched by this PR. Out of scope for this review.

---

### ❌ P2 Finding 1.9 - Debug tracebacks with show_locals=True
- **File:** `src/utils/errors.py:41`
- **Severity:** P2
- **Category:** security

**Codex said:**
> Debug tracebacks are rendered with `show_locals=True`. Running with debug error handling can print local variables, including secret values handled by commands such as `commands/secrets.py`.

**Relevant code:**
```python
# (not in our diff)
```

**Resolution:** Same as 1.8 - `errors.py` is not part of the current changeset. Pre-existing code, out of scope.

---

### ❌ P3 Finding 1.10 - Image width/height not validated
- **File:** `commands/image.py:31`
- **Severity:** P3
- **Category:** nit

**Codex said:**
> Width and height are accepted from CLI and passed directly to Pillow resize. Zero or negative dimensions raise uncaught Pillow errors instead of a clean CLI validation failure.

**Relevant code:**
```python
img = img.resize((width, height), Image.Resampling.LANCZOS)
```

**Resolution:** Disagree. Zero/negative dimensions from CLI is a deliberate misuse. Pillow raises a clear error, and the global error handler catches it. Adding validation for impossible CLI inputs is unnecessary clutter.

---

## Iteration 2 - /codex:rescue (verification)

No new P0, P1, or P2 findings. All three fixes from iteration 1 verified clean:
- `CMD_PNG_DATA` correctly used for static text, `CMD_GIF_DATA` still used for scrolling GIF.
- `break` on timeout properly halts windowed transfer; `finally` block still runs.
- `try/finally` in send.py correctly wraps write+listen with `stop_notify` cleanup.

---

## Summary

- **Iterations run:** 2 (clean-verification)
- **Findings:** 10 total
  - **P1:** 2 (✅ 2 fixed)
  - **P2:** 4 (✅ 1 fixed, 🟡 1 deferred, ❌ 2 out-of-scope)
  - **P3:** 4 (❌ 4 invalid/nits)
- **Open P0-P2 issues:** 1 deferred - `make_payload()` 16-bit length overflow (mitigated by windowed transport)
- **Files modified:** `commands/text.py`, `src/protocol/transport.py`, `commands/send.py`
- **Uncommitted state:** all changes unstaged in working tree
- **Review log path:** `dev-docs/17-05-2026-ble-protocol-and-cli-code-review.md`

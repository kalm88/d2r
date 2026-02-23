# D2R Overlay Prototype

This repository now includes a **Windows Python desktop overlay** that auto-attaches to `d2r.exe`, plus the original browser prototype files.

## Desktop Overlay (Auto-attach to `d2r.exe`)

### Features
- Automatically detects and attaches to the `d2r.exe` window
- Transparent always-on-top overlay that tracks the game window bounds
- Live transparency slider (25% to 100%)
- Notes, timer, and quick controls
- F10 hide/show hotkey

### Requirements (Windows)

```bash
pip install -r requirements.txt
```

### Run

```bash
python overlay_app.py
```

## Browser Prototype (legacy)

You can still run the previous static prototype:

```bash
python3 -m http.server 4173
```

Then open `http://localhost:4173`.

## Notes

- The desktop overlay process attachment is Windows-only because it relies on Win32 APIs (`pywin32`).
- Some game anti-cheat / rendering modes can affect overlay visibility in borderless/fullscreen modes.

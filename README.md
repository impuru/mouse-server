# Remote Mouse — control your laptop's mouse from your phone

A tiny local server (Python) + a touchpad web app for your phone. No app
store needed — your phone just opens a webpage served by your laptop over
your home Wi-Fi.

```
mouse-server/
├── server.py            ← the mouse server (controls the cursor)
├── gui.py                ← desktop Start/Stop control panel
├── requirements.txt
└── templates/
    └── index.html       ← the touchpad page your phone opens
```

## 1. Setup (on your laptop)

Requires Python 3.8+ (Tkinter is included with the standard Mac/Windows
installers; on Linux you may need `sudo apt install python3-tk`).

```bash
cd mouse-server
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Option A — desktop control panel (recommended)

```bash
python gui.py
```

A small window opens with a **Start Server** / **Stop Server** button. When
running, it shows the address to open on your phone and a QR code you can
scan to jump straight there (QR code needs `pip install qrcode[pil]`).
Closing the window automatically stops the server.

### Option B — run from the terminal directly

```bash
python server.py
```

You'll see something like:

```
==================================================
 Phone Mouse Server is running
 On your phone's browser (same Wi-Fi), open:
   http://192.168.1.23:5000
==================================================
```

Press `Ctrl+C` to stop it.

## 2. Connect (on your phone)

1. Make sure your phone is on the **same Wi-Fi network** as your laptop.
2. Open that `http://192.168.x.x:5000` address in your phone's browser
   (Safari/Chrome — no install needed).
3. Optional: tap **Share → Add to Home Screen** so it behaves like an app icon.

## 3. Using it

**Mouse tab**
- **Drag with one finger** — move the cursor
- **Tap** — left click
- **Two-finger tap** — right click
- **Two-finger drag** — scroll
- **Press and hold, then drag** — click-and-drag / text selection
- Bottom buttons — explicit Left / Right click

**Media tab**
- ▶❚❚ — Space (play/pause)
- ◀◀ / ▶▶ — Left / Right arrow (seek, previous/next track)
- ▲ / ▼ — Up / Down arrow (volume)

These send the literal keypress, so they work in whatever app/window is
currently focused on your laptop — YouTube, Netflix, Spotify Web, VLC,
PowerPoint, etc. Make sure the player is the focused/active window.

**Files tab**
- Browse your laptop's folders and tap a folder to open it
- Tap a file to download it to your phone
- ⬆ up a level · ⌂ home folder · ▦ drives (Windows) / root (Mac/Linux)

⚙ settings (top right) — change server address manually, adjust sensitivity

## Security note

This server has **no login or password** — anyone on the same Wi-Fi network
who knows (or guesses) the address can control your mouse/keyboard and
browse/download your files. That's fine on a private home network, but:
- Don't run this on public or shared Wi-Fi (coffee shops, offices, etc.)
- Stop the server when you're not using it (the `gui.py` control panel makes
  this one click)

## Platform notes

- **macOS**: the first time you run `server.py`, macOS will ask you to grant
  **Accessibility** permission to your terminal (or Python) under
  *System Settings → Privacy & Security → Accessibility*. Without this the
  mouse won't move. After granting it, restart the server.
- **Windows**: Windows Firewall may prompt to allow Python on private
  networks the first time — click **Allow**.
- **Linux**: works on X11. If you're on Wayland, `pynput` may not be able to
  move the cursor depending on your compositor.

## Troubleshooting

- **Phone shows "cannot reach server"** — double check both devices are on
  the same Wi-Fi (not phone on mobile data, and not a "guest" network that
  isolates devices), and that the IP/port match what `server.py` printed.
- **Firewall blocks the connection** — allow inbound connections on port
  `5000` for Python in your laptop's firewall settings.
- **IP address changed** — your laptop's local IP can change between
  sessions; just re-run `server.py` and use the new address it prints, or
  edit it in the phone app's ⚙ settings.
- Want a different port? Edit `port = 5000` near the bottom of `server.py`.

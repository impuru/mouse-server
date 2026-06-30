# Remote Mouse — control your laptop's mouse from your phone

A tiny local server (Python) + a touchpad web app for your phone. No app
store needed — your phone just opens a webpage served by your laptop over
your home Wi-Fi.

```
mouse-server/
├── server.py            ← run this on your laptop
├── requirements.txt
└── templates/
    └── index.html       ← the touchpad page your phone opens
```

## 1. Setup (on your laptop)

Requires Python 3.8+.

```bash
cd mouse-server
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
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

## 2. Connect (on your phone)

1. Make sure your phone is on the **same Wi-Fi network** as your laptop.
2. Open that `http://192.168.x.x:5000` address in your phone's browser
   (Safari/Chrome — no install needed).
3. Optional: tap **Share → Add to Home Screen** so it behaves like an app icon.

## 3. Using it

- **Drag with one finger** — move the cursor
- **Tap** — left click
- **Two-finger tap** — right click
- **Two-finger drag** — scroll
- **Press and hold, then drag** — click-and-drag / text selection
- Bottom buttons — explicit Left / Right click
- ⚙ settings (top right) — change server address manually, adjust sensitivity

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

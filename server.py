#!/usr/bin/env python3
"""
Phone Mouse Server
-------------------
Run this on your laptop. It serves a touchpad webpage that your phone
opens in a browser (same Wi-Fi network), and translates touch gestures
into real mouse movements/clicks on the laptop.

Usage:
    pip install -r requirements.txt
    python server.py

Then open the printed http://<laptop-ip>:5000 address on your phone's browser.
"""

# IMPORTANT: eventlet's monkey patch must run before any other imports
# (including stdlib socket/os) or the server's async loop won't be truly
# cooperative - this is what was causing the ~1-2 minute disconnects, since
# a blocked event loop misses the WebSocket ping/pong heartbeat.
import eventlet
eventlet.monkey_patch()

import os
import platform
import socket

from flask import Flask, abort, jsonify, render_template, request, send_file
from flask_socketio import SocketIO
from pynput.mouse import Button, Controller
from pynput.keyboard import Controller as KeyboardController
from pynput.keyboard import Key

app = Flask(__name__)
app.config["SECRET_KEY"] = "phone-mouse-server"
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="eventlet",
    ping_interval=25,   # how often the server pings the client (seconds)
    ping_timeout=60,    # how long to wait for a pong before dropping (seconds)
)
mouse = Controller()
keyboard = KeyboardController()

BUTTONS = {"left": Button.left, "right": Button.right, "middle": Button.middle}

KEYS = {
    "left": Key.left,
    "right": Key.right,
    "up": Key.up,
    "down": Key.down,
    "space": Key.space,
    # Real OS media keys, used by the Media tab's play/pause, prev, next.
    # Most desktop apps (Spotify, browsers, VLC) respond to these directly.
    "media_play_pause": Key.media_play_pause,
    "media_previous": Key.media_previous,
    "media_next": Key.media_next,
    "media_volume_up": Key.media_volume_up,
    "media_volume_down": Key.media_volume_down,
    "media_volume_mute": Key.media_volume_mute,
}


def get_local_ip() -> str:
    """Best-effort detection of the LAN IP address (no internet traffic sent)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


DRIVES_TOKEN = "__drives__"


def list_drives():
    """Windows drive letters (C:\\, D:\\, ...). Just '/' on macOS/Linux."""
    if platform.system() == "Windows":
        import string
        from ctypes import windll

        drives = []
        bitmask = windll.kernel32.GetLogicalDrives()
        for letter in string.ascii_uppercase:
            if bitmask & 1:
                drives.append(f"{letter}:\\")
            bitmask >>= 1
        return drives
    return ["/"]


def compute_parent(path: str):
    """Parent dir for `path`, or DRIVES_TOKEN/None once at a filesystem root."""
    parent = os.path.dirname(path)
    if parent == path:
        return DRIVES_TOKEN if platform.system() == "Windows" else None
    return parent


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/browse")
def api_browse():
    raw_path = request.args.get("path")

    if raw_path == DRIVES_TOKEN:
        entries = [
            {"name": d, "path": d, "is_dir": True, "size": None}
            for d in list_drives()
        ]
        return jsonify({"path": DRIVES_TOKEN, "parent": None, "entries": entries})

    path = os.path.realpath(raw_path) if raw_path else os.path.expanduser("~")

    if not os.path.isdir(path):
        return jsonify({"error": "That folder doesn't exist or isn't accessible."}), 400

    entries = []
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.name.startswith('.') and entry.is_dir(follow_symlinks=False):
                        continue

                    is_dir = entry.is_dir(follow_symlinks=False)
                    size = None if is_dir else entry.stat(follow_symlinks=False).st_size
                    entries.append(
                        {"name": entry.name, "path": entry.path, "is_dir": is_dir, "size": size}
                    )
                except OSError:
                    continue
    except PermissionError:
        return jsonify({"error": "Permission denied for this folder."}), 403

    entries.sort(key=lambda e: (not e["is_dir"], e["name"].lower()))
    return jsonify({"path": path, "parent": compute_parent(path), "entries": entries})


@app.route("/api/preview")
def api_preview():
    raw_path = request.args.get("path")
    if not raw_path:
        abort(400)
    path = os.path.realpath(raw_path)
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, as_attachment=False)


@app.route("/api/download")
def api_download():
    raw_path = request.args.get("path")
    if not raw_path:
        abort(400)
    path = os.path.realpath(raw_path)
    if not os.path.isfile(path):
        abort(404)
    return send_file(path, as_attachment=True)


@socketio.on("move")
def on_move(data):
    dx = float(data.get("dx", 0))
    dy = float(data.get("dy", 0))
    mouse.move(dx, dy)


@socketio.on("scroll")
def on_scroll(data):
    dx = float(data.get("dx", 0))
    dy = float(data.get("dy", 0))
    mouse.scroll(dx, dy)


@socketio.on("click")
def on_click(data):
    btn = BUTTONS.get(data.get("button", "left"), Button.left)
    mouse.click(btn, 1)


@socketio.on("double_click")
def on_double_click(data):
    mouse.click(Button.left, 2)


@socketio.on("mouse_down")
def on_mouse_down(data):
    btn = BUTTONS.get(data.get("button", "left"), Button.left)
    mouse.press(btn)


@socketio.on("mouse_up")
def on_mouse_up(data):
    btn = BUTTONS.get(data.get("button", "left"), Button.left)
    mouse.release(btn)


@socketio.on("key")
def on_key(data):
    key = KEYS.get(data.get("key"))
    if key is None:
        return
    keyboard.press(key)
    keyboard.release(key)


if __name__ == "__main__":
    ip = get_local_ip()
    port = 5000
    # NOTE: the "SERVER_URL:" line below is parsed by gui.py - keep it intact.
    print("=" * 50, flush=True)
    print(" Phone Mouse Server is running", flush=True)
    print(" On your phone's browser (same Wi-Fi), open:", flush=True)
    print(f"   http://{ip}:{port}", flush=True)
    print(f"SERVER_URL:http://{ip}:{port}", flush=True)
    print("=" * 50, flush=True)
    socketio.run(app, host="0.0.0.0", port=port, debug=False)

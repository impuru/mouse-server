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

import socket

from flask import Flask, render_template
from flask_socketio import SocketIO
from pynput.mouse import Button, Controller
from pynput.keyboard import Controller as KeyboardController
from pynput.keyboard import Key

app = Flask(__name__)
app.config["SECRET_KEY"] = "phone-mouse-server"
socketio = SocketIO(app, cors_allowed_origins="*")
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


@app.route("/")
def index():
    return render_template("index.html")


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
    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)

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
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Key, Controller as KeyboardController

app = Flask(__name__)
app.config["SECRET_KEY"] = "phone-mouse-server"
socketio = SocketIO(app, cors_allowed_origins="*")
mouse = MouseController()
keyboard = KeyboardController()

BUTTONS = {"left": Button.left, "right": Button.right, "middle": Button.middle}


def press_key(key):
    try:
        keyboard.press(key)
        keyboard.release(key)
    except Exception:
        pass


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


@socketio.on("player_play")
def on_player_play(data):
    press_key(Key.space)


@socketio.on("player_pause")
def on_player_pause(data):
    press_key('p')


@socketio.on("player_prev")
def on_player_prev(data):
    press_key(Key.left)


@socketio.on("player_next")
def on_player_next(data):
    press_key(Key.right)


@socketio.on("player_volume")
def on_player_volume(data):
    direction = data.get("direction", "up")
    amount = int(data.get("amount", 1))
    key = Key.up if direction == "up" else Key.down
    for _ in range(max(1, amount)):
        press_key(key)


if __name__ == "__main__":
    ip = get_local_ip()
    port = 5000
    print("=" * 50)
    print(" Phone Mouse Server is running")
    print(f" On your phone's browser (same Wi-Fi), open:")
    print(f"   http://{ip}:{port}")
    print("=" * 50)
    socketio.run(app, host="0.0.0.0", port=port, debug=False, allow_unsafe_werkzeug=True)

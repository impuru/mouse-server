#!/usr/bin/env python3
"""
Remote Mouse — control panel
-----------------------------
A small desktop window with a Start/Stop button for the phone-mouse server.
Launches server.py as a subprocess so Stop can cleanly kill it.

Usage:
    python gui.py
"""

import os
import queue
import re
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import font as tkfont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SERVER_SCRIPT = os.path.join(BASE_DIR, "server.py")

# Optional QR code support (pip install qrcode[pil]) - falls back gracefully.
try:
    import qrcode
    from PIL import ImageTk
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False

BG = "#14161a"
PANEL = "#1d2026"
PANEL_2 = "#23262e"
TEXT = "#e8eaf0"
TEXT_DIM = "#8a8f9c"
ACCENT = "#5b8cff"
OK = "#3ddc84"
BAD = "#ff5d5d"
BORDER = "#2c303a"


class MouseServerGUI:
    def __init__(self, root):
        self.root = root
        self.process = None
        self.log_queue = queue.Queue()
        self.server_url = None
        self.qr_imgtk = None

        root.title("Remote Mouse — Server")
        root.configure(bg=BG)
        root.geometry("380x500")
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self.on_close)

        title_font = tkfont.Font(family="Helvetica", size=16, weight="bold")
        sub_font = tkfont.Font(family="Helvetica", size=11)
        mono_font = tkfont.Font(family="Courier", size=13, weight="bold")
        small_font = tkfont.Font(family="Helvetica", size=10)

        # Header
        header = tk.Frame(root, bg=BG)
        header.pack(fill="x", padx=20, pady=(20, 10))

        dot_row = tk.Frame(header, bg=BG)
        dot_row.pack(fill="x")
        self.dot = tk.Canvas(dot_row, width=10, height=10, bg=BG, highlightthickness=0)
        self.dot_id = self.dot.create_oval(1, 1, 9, 9, fill=BAD, outline="")
        self.dot.pack(side="left", pady=4)
        tk.Label(dot_row, text="  Remote Mouse Server", font=title_font, bg=BG, fg=TEXT).pack(side="left")

        self.status_label = tk.Label(header, text="Stopped", font=sub_font, bg=BG, fg=TEXT_DIM, anchor="w")
        self.status_label.pack(fill="x", pady=(4, 0))

        # Address panel
        self.addr_panel = tk.Frame(root, bg=PANEL, highlightbackground=BORDER, highlightthickness=1)
        self.addr_panel.pack(fill="x", padx=20, pady=10)
        tk.Label(self.addr_panel, text="OPEN ON YOUR PHONE", font=small_font, bg=PANEL, fg=TEXT_DIM).pack(
            anchor="w", padx=14, pady=(12, 0)
        )
        self.addr_label = tk.Label(
            self.addr_panel, text="Not running", font=mono_font, bg=PANEL, fg=TEXT, anchor="w"
        )
        self.addr_label.pack(anchor="w", padx=14, pady=(2, 14))

        # QR code area
        self.qr_frame = tk.Frame(root, bg=BG, width=180, height=180)
        self.qr_frame.pack(pady=(0, 10))
        self.qr_frame.pack_propagate(False)
        self.qr_label = tk.Label(self.qr_frame, bg=PANEL_2, fg=TEXT_DIM, font=small_font, justify="center")
        self.qr_label.pack(fill="both", expand=True)
        self._set_qr_placeholder()

        # Start/Stop button
        self.toggle_btn = tk.Button(
            root,
            text="Start Server",
            font=tkfont.Font(family="Helvetica", size=13, weight="bold"),
            bg=ACCENT,
            fg="white",
            activebackground="#4a78e0",
            activeforeground="white",
            relief="flat",
            bd=0,
            height=2,
            command=self.toggle_server,
        )
        self.toggle_btn.pack(fill="x", padx=20, pady=(6, 10))

        # Log box
        log_frame = tk.Frame(root, bg=PANEL_2, highlightbackground=BORDER, highlightthickness=1)
        log_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        self.log_text = tk.Text(
            log_frame, bg=PANEL_2, fg=TEXT_DIM, font=("Courier", 9), bd=0,
            wrap="word", state="disabled", padx=10, pady=8,
        )
        self.log_text.pack(fill="both", expand=True)

        self.root.after(150, self._poll_log_queue)

    # ---------- UI helpers ----------
    def _set_qr_placeholder(self):
        if QR_AVAILABLE:
            self.qr_label.config(image="", text="QR appears here\nonce running", compound="center")
        else:
            self.qr_label.config(
                image="", text="(install 'qrcode[pil]'\nfor a QR code)", compound="center"
            )

    def _set_status(self, running, text):
        self.dot.itemconfig(self.dot_id, fill=OK if running else BAD)
        self.status_label.config(text=text)

    def _append_log(self, line):
        self.log_text.config(state="normal")
        self.log_text.insert("end", line + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _render_qr(self, url):
        if not QR_AVAILABLE:
            return
        img = qrcode.make(url)
        img = img.resize((164, 164))
        self.qr_imgtk = ImageTk.PhotoImage(img)
        self.qr_label.config(image=self.qr_imgtk, text="")

    # ---------- Server process control ----------
    def toggle_server(self):
        if self.process is None:
            self.start_server()
        else:
            self.stop_server()

    def start_server(self):
        if not os.path.exists(SERVER_SCRIPT):
            self._append_log(f"ERROR: server.py not found at {SERVER_SCRIPT}")
            return

        self.toggle_btn.config(state="disabled", text="Starting…")
        self._set_status(False, "Starting…")
        self._append_log("Starting server…")

        creationflags = 0
        if sys.platform == "win32":
            creationflags = subprocess.CREATE_NO_WINDOW

        try:
            self.process = subprocess.Popen(
                [sys.executable, SERVER_SCRIPT],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                cwd=BASE_DIR,
                creationflags=creationflags,
            )
        except Exception as e:
            self._append_log(f"ERROR: failed to launch server: {e}")
            self.toggle_btn.config(state="normal", text="Start Server")
            self._set_status(False, "Stopped")
            self.process = None
            return

        threading.Thread(target=self._read_process_output, daemon=True).start()

    def _read_process_output(self):
        url_pattern = re.compile(r"^SERVER_URL:(\S+)")
        for line in self.process.stdout:
            line = line.rstrip()
            if not line:
                continue
            match = url_pattern.match(line)
            if match:
                self.log_queue.put(("url", match.group(1)))
            else:
                self.log_queue.put(("log", line))
        # process ended (either stopped, or crashed)
        self.log_queue.put(("exited", None))

    def _poll_log_queue(self):
        try:
            while True:
                kind, payload = self.log_queue.get_nowait()
                if kind == "log":
                    self._append_log(payload)
                elif kind == "url":
                    self.server_url = payload
                    self.addr_label.config(text=payload.replace("http://", ""))
                    self._set_status(True, "Running — waiting for phone to connect")
                    self.toggle_btn.config(state="normal", text="Stop Server", bg=BAD, activebackground="#d94e4e")
                    self._render_qr(payload)
                elif kind == "exited":
                    was_running = self.process is not None
                    self.process = None
                    self.addr_label.config(text="Not running")
                    self._set_qr_placeholder()
                    self._set_status(False, "Stopped")
                    self.toggle_btn.config(state="normal", text="Start Server", bg=ACCENT, activebackground="#4a78e0")
                    if was_running:
                        self._append_log("Server stopped.")
        except queue.Empty:
            pass
        self.root.after(150, self._poll_log_queue)

    def stop_server(self):
        if self.process is None:
            return
        self._append_log("Stopping server…")
        self.toggle_btn.config(state="disabled", text="Stopping…")
        try:
            self.process.terminate()
            try:
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()
        except Exception as e:
            self._append_log(f"Error stopping server: {e}")

    def on_close(self):
        if self.process is not None:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass
        self.root.destroy()


def main():
    root = tk.Tk()
    MouseServerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()

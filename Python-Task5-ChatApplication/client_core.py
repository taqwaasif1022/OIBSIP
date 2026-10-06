"""client_core.py - networking + small pure helpers for the GUI client.

Nothing here imports Tkinter, so it can be unit-tested without a display.
ChatConnection runs socket I/O in background threads and hands events to the
GUI through a thread-safe queue, so the GUI never blocks on the network.
"""
import json
import queue
import socket
import threading
from datetime import datetime


class ChatConnection:
    def __init__(self):
        self.events = queue.Queue()     # dicts from the server + local events
        self._outbox = queue.Queue()
        self._sock = None
        self.connected = False
        self._closing = False
        self.target = None              # (host, port)

    def connect_async(self, host, port, timeout=5.0):
        """Connect in the background. Emits 'connected' or 'connect_failed'."""
        self.target = (host, port)
        threading.Thread(target=self._connect, args=(host, port, timeout), daemon=True).start()

    def _connect(self, host, port, timeout):
        try:
            sock = socket.create_connection((host, port), timeout=timeout)
            sock.settimeout(None)
        except (OSError, ValueError, OverflowError) as exc:
            self.events.put({"type": "connect_failed", "error": str(exc)})
            return
        self._sock, self.connected = sock, True
        threading.Thread(target=self._write_loop, daemon=True).start()
        self.events.put({"type": "connected"})
        self._read_loop()

    def _read_loop(self):
        try:
            reader = self._sock.makefile("rb")
            for line in iter(reader.readline, b""):
                try:
                    event = json.loads(line.decode("utf-8"))
                except (UnicodeDecodeError, ValueError):
                    continue                       # ignore malformed server data
                if isinstance(event, dict) and isinstance(event.get("type"), str):
                    self.events.put(event)
        except (OSError, ValueError):
            pass
        finally:
            was_open = self.connected and not self._closing
            self.connected = False
            self._outbox.put(None)
            if was_open:
                self.events.put({"type": "connection_lost"})

    def _write_loop(self):
        while True:
            data = self._outbox.get()
            if data is None:
                break
            try:
                self._sock.sendall(data)
            except OSError:
                break

    def send(self, type_, **fields):
        """Queue a message for sending. Returns False if not connected."""
        if not self.connected:
            return False
        self._outbox.put((json.dumps({"type": type_, **fields}) + "\n").encode("utf-8"))
        return True

    def close(self):
        self._closing = True
        self.connected = False
        self._outbox.put(None)
        if self._sock:
            try:
                self._sock.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self._sock.close()
            except OSError:
                pass


def format_timestamp(ts, today=None):
    """'2026-09-28 14:35:10' -> '14:35' (today) or '09-27 14:35' (older)."""
    try:
        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
    except (TypeError, ValueError):
        return "--:--"
    today = today or datetime.now().date()
    return dt.strftime("%H:%M") if dt.date() == today else dt.strftime("%m-%d %H:%M")


def should_notify(window_focused, sender, me):
    """Notify only for messages from other people while the window is not focused."""
    return (not window_focused) and sender != me

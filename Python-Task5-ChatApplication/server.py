"""server.py - the chat server.

Protocol: TCP, one JSON object per line ("\n" terminated), UTF-8.
Each client gets its own thread. The server keeps track of who is logged in
and which room each user is currently in, stores messages in SQLite, and
broadcasts every message only to the users in the same room.

Run:  python server.py [--host 127.0.0.1] [--port 5555] [--db chat.db]
"""
import argparse
import json
import logging
import socket
import threading
import time
from datetime import datetime

import auth
from auth import AuthError
from database import Database, DatabaseError, DuplicateError, DEFAULT_DB_PATH
from emoji_map import convert_shortcodes

HOST, PORT = "127.0.0.1", 5555
MAX_LINE = 16 * 1024          # largest accepted request (bytes)
MAX_MESSAGE_LEN = 1000        # largest chat message (characters)
HISTORY_LIMIT = 100           # messages loaded when entering a room
MAX_FAILED_LOGINS = 5         # per connection

log = logging.getLogger("chat.server")


def now_string():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class ClientSession:
    """State for one connected client."""

    def __init__(self, conn, addr):
        self.conn, self.addr = conn, addr
        self.user = None            # {"id", "username"} once logged in
        self.room = None            # {"id", "room_name"} once in a room
        self.failed_logins = 0
        self._send_lock = threading.Lock()

    def send(self, payload):
        """Send one JSON message. Returns False if the client is gone."""
        data = (json.dumps(payload) + "\n").encode("utf-8")
        try:
            with self._send_lock:
                self.conn.sendall(data)
            return True
        except OSError:
            return False

    def error(self, text):
        self.send({"type": "error", "text": text})

    def close(self):
        try:
            self.conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            self.conn.close()
        except OSError:
            pass


class ChatServer:
    def __init__(self, host=HOST, port=PORT, db_path=DEFAULT_DB_PATH):
        self.host, self.port = host, port
        self.db = Database(db_path)
        self.db.ensure_default_rooms()
        self.lock = threading.RLock()   # protects the three structures below
        self.sessions = set()           # every connected client
        self.online = {}                # username.lower() -> session (logged in)
        self.members = {}               # room_id -> set of sessions in that room
        self._sock = None
        self._running = False
        self._handlers = {
            "register": self._on_register, "login": self._on_login,
            "logout": self._on_logout, "list_rooms": self._on_list_rooms,
            "create_room": self._on_create_room, "join_room": self._on_join_room,
            "message": self._on_message,
        }

    # ---- start / stop ------------------------------------------------------
    def start(self):
        """Bind the port and accept clients in a background thread."""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind((self.host, self.port))
        self._sock.listen()
        self.port = self._sock.getsockname()[1]   # useful when port 0 was requested
        self._running = True
        threading.Thread(target=self._accept_loop, daemon=True).start()
        log.info("Server listening on %s:%s", self.host, self.port)

    def serve_forever(self):
        self.start()
        try:
            while self._running:
                time.sleep(0.5)
        except KeyboardInterrupt:
            log.info("Shutting down...")
        finally:
            self.stop()

    def stop(self):
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
        with self.lock:
            sessions = list(self.sessions)
        for s in sessions:
            s.close()

    def _accept_loop(self):
        while self._running:
            try:
                conn, addr = self._sock.accept()
            except OSError:
                break
            session = ClientSession(conn, addr)
            with self.lock:
                self.sessions.add(session)
            threading.Thread(target=self._handle_client, args=(session,), daemon=True).start()

    # ---- per-client loop ---------------------------------------------------
    def _handle_client(self, session):
        log.info("Client connected: %s", session.addr)
        try:
            reader = session.conn.makefile("rb")
            while self._running:
                line = reader.readline(MAX_LINE + 1)
                if not line:
                    break                                  # client closed the connection
                if len(line) > MAX_LINE and not line.endswith(b"\n"):
                    session.error("Message too large.")
                    break
                self._process_line(session, line)
        except (OSError, ValueError):
            pass                                           # connection dropped
        finally:
            self._cleanup(session, "disconnected")

    def _process_line(self, session, line):
        try:
            data = json.loads(line.decode("utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("type"), str):
                raise ValueError("bad shape")
        except (UnicodeDecodeError, ValueError):
            session.error("Invalid message format.")
            return
        handler = self._handlers.get(data["type"])
        if handler is None:
            session.error("Unknown request type.")
            return
        try:
            handler(session, data)
        except AuthError as exc:
            session.error(str(exc))
        except DatabaseError as exc:
            log.error("Database error: %s", exc)
            session.error("Database error. Please try again.")
        except Exception:                                   # never let one client kill the server
            log.exception("Unexpected error")
            session.error("Internal server error.")

    def _cleanup(self, session, reason):
        with self.lock:
            self.sessions.discard(session)
        if session.user:
            self._log_out(session, f"{session.user['username']} {reason}.")
        session.close()
        log.info("Client gone: %s", session.addr)

    # ---- helpers -----------------------------------------------------------
    def _require_login(self, session):
        if not session.user:
            raise AuthError("Please log in first.")

    def _rooms_payload(self):
        with self.lock:
            counts = {rid: len(m) for rid, m in self.members.items()}
        return [{"name": r["room_name"], "online": counts.get(r["id"], 0)}
                for r in self.db.list_rooms()]

    def _broadcast_rooms(self):
        try:
            payload = {"type": "rooms", "rooms": self._rooms_payload()}
        except DatabaseError as exc:
            log.error("Database error: %s", exc)
            return
        with self.lock:
            targets = list(self.online.values())
        for s in targets:
            s.send(payload)

    def _broadcast(self, room_id, payload, exclude=None):
        with self.lock:
            targets = list(self.members.get(room_id, ()))
        for s in targets:
            if s is not exclude:
                s.send(payload)

    def _system_message(self, room_id, text, exclude=None):
        self._broadcast(room_id, {"type": "system", "text": text, "timestamp": now_string()},
                        exclude)

    def _leave_room(self, session):
        """Remove the session from its room. Returns the room it left (or None)."""
        with self.lock:
            room, session.room = session.room, None
            if room:
                self.members.get(room["id"], set()).discard(session)
        return room

    def _log_out(self, session, room_text):
        """Shared by logout and disconnect: leave room, tell others, forget user."""
        room = self._leave_room(session)
        with self.lock:
            self.online.pop(session.user["username"].lower(), None)
        session.user = None
        if room:
            self._system_message(room["id"], room_text)
        self._broadcast_rooms()

    # ---- request handlers --------------------------------------------------
    def _on_register(self, session, data):
        try:
            auth.register_user(self.db, data.get("username"), data.get("password"))
        except AuthError as exc:
            session.send({"type": "auth_result", "action": "register", "ok": False,
                          "error": str(exc)})
            return
        session.send({"type": "auth_result", "action": "register", "ok": True})

    def _on_login(self, session, data):
        if session.user:
            session.send({"type": "auth_result", "action": "login", "ok": False,
                          "error": "You are already logged in."})
            return
        try:
            user = auth.authenticate(self.db, data.get("username"), data.get("password"))
            with self.lock:
                if user["username"].lower() in self.online:
                    raise AuthError("This account is already logged in elsewhere.")
                session.user = {"id": user["id"], "username": user["username"]}
                self.online[user["username"].lower()] = session
        except AuthError as exc:
            session.failed_logins += 1
            session.send({"type": "auth_result", "action": "login", "ok": False,
                          "error": str(exc)})
            if session.failed_logins >= MAX_FAILED_LOGINS:
                session.error("Too many failed login attempts. Disconnecting.")
                session.close()
            return
        session.send({"type": "auth_result", "action": "login", "ok": True,
                      "username": session.user["username"]})
        session.send({"type": "rooms", "rooms": self._rooms_payload()})

    def _on_logout(self, session, data):
        if session.user:
            self._log_out(session, f"{session.user['username']} logged out.")
        session.send({"type": "logout_ok"})

    def _on_list_rooms(self, session, data):
        self._require_login(session)
        session.send({"type": "rooms", "rooms": self._rooms_payload()})

    def _on_create_room(self, session, data):
        self._require_login(session)
        name = auth.validate_room_name(data.get("room"))
        try:
            self.db.create_room(name)
        except DuplicateError:
            raise AuthError("A room with that name already exists.")
        session.send({"type": "room_created", "room": name})
        self._broadcast_rooms()

    def _on_join_room(self, session, data):
        self._require_login(session)
        name = data.get("room")
        room = self.db.get_room(name) if isinstance(name, str) else None
        if room is None:
            raise AuthError("That room does not exist.")
        username = session.user["username"]
        # Hold the lock while loading history AND registering as a member, so a
        # message can't be both in the history and delivered live (or be missed).
        with self.lock:
            already_here = session.room is not None and session.room["id"] == room["id"]
            if not already_here:
                old = self._leave_room(session)
                if old:
                    self._system_message(old["id"], f"{username} left the room.")
                session.room = room
                self.members.setdefault(room["id"], set()).add(session)
            history = self.db.get_history(room["id"], HISTORY_LIMIT)
            session.send({"type": "joined", "room": room["room_name"], "history": history})
        if not already_here:
            self._system_message(room["id"], f"{username} joined the room.", exclude=session)
        self._broadcast_rooms()

    def _on_message(self, session, data):
        self._require_login(session)
        if session.room is None:
            raise AuthError("Join a room before sending messages.")
        text = data.get("text")
        if not isinstance(text, str) or not text.strip():
            raise AuthError("Cannot send an empty message.")
        text = text.strip()
        if len(text) > MAX_MESSAGE_LEN:
            raise AuthError(f"Message too long (max {MAX_MESSAGE_LEN} characters).")
        text = convert_shortcodes(text)
        timestamp = now_string()
        room = session.room
        payload = {"type": "message", "room": room["room_name"],
                   "user": session.user["username"], "text": text, "timestamp": timestamp}
        with self.lock:   # store + fan-out atomically w.r.t. room joins
            self.db.add_message(room["id"], session.user["id"], text, timestamp)
            targets = list(self.members.get(room["id"], ()))
        for s in targets:
            s.send(payload)


def main():
    parser = argparse.ArgumentParser(description="Advanced Chat Application - server")
    parser.add_argument("--host", default=HOST, help="interface to bind (default 127.0.0.1)")
    parser.add_argument("--port", type=int, default=PORT, help="TCP port (default 5555)")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="SQLite file (default chat.db)")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        ChatServer(args.host, args.port, args.db).serve_forever()
    except OSError as exc:
        log.error("Could not start server on %s:%s - %s", args.host, args.port, exc)
        raise SystemExit(1)
    except DatabaseError as exc:
        log.error("Could not open database: %s", exc)
        raise SystemExit(1)


if __name__ == "__main__":
    main()

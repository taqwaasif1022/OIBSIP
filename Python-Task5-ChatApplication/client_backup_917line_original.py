"""Modern Tkinter GUI for the Advanced Chat Application (Nexora Chat).

Compatible with the existing client_core.py and server.py protocol - no
server-side changes were needed for this round of visual/UX work.
"""
import argparse
import queue
import re
import sys
import tkinter as tk
from tkinter import messagebox, simpledialog

from client_core import ChatConnection, format_timestamp, should_notify

APP_TITLE = "Nexora Chat"
DEFAULT_HOST, DEFAULT_PORT = "127.0.0.1", 5555
FONT = "Segoe UI" if sys.platform.startswith("win") else ("Helvetica Neue" if sys.platform == "darwin" else "DejaVu Sans")

EMOJI_CATEGORIES = [
    ("Smileys", ["😀", "😄", "😁", "😆", "😊", "😉", "😍", "🤩", "😘", "😜", "🤔", "😴",
                 "😎", "🙃", "🥳", "😭", "😢", "😡", "😱", "🥺", "😇", "🤗", "🙄", "😏"]),
    ("Hearts", ["❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "💔", "💕", "💞", "💗"]),
    ("Gestures", ["👍", "👎", "👏", "🙌", "🙏", "👋", "✌️", "🤝", "💪", "🤞", "👌", "🫶"]),
    ("Animals", ["🐶", "🐱", "🦊", "🐼", "🐸", "🐵", "🦁", "🐰", "🐧", "🐢", "🐝", "🦄"]),
    ("Food", ["🍕", "🍔", "🍟", "🍩", "🍰", "🍓", "☕", "🍺", "🍎", "🍫", "🍪", "🥑"]),
    ("Activities", ["⚽", "🏀", "🎮", "🎧", "🎨", "🎬", "🏆", "🎯", "🎸", "📚", "✈️", "🎉"]),
    ("Objects", ["💡", "🔥", "🚀", "⭐", "✨", "💯", "✅", "❌", "⚠️", "📌", "🔔", "💬"]),
]

# --- lightweight rich-text markup: **bold**  *italic*  ~~strike~~  `code` ---
_RICH_RE = re.compile(r"(\*\*(?P<bold>.+?)\*\*)|(~~(?P<strike>.+?)~~)|(`(?P<code>.+?)`)|(\*(?P<italic>.+?)\*)")


def parse_rich(text):
    """Split `text` into (segment, tag) pairs. tag is one of None/'b'/'i'/'s'/'code'."""
    segments, pos = [], 0
    for m in _RICH_RE.finditer(text):
        if m.start() > pos:
            segments.append((text[pos:m.start()], None))
        if m.group("bold") is not None:
            segments.append((m.group("bold"), "b"))
        elif m.group("strike") is not None:
            segments.append((m.group("strike"), "s"))
        elif m.group("code") is not None:
            segments.append((m.group("code"), "code"))
        elif m.group("italic") is not None:
            segments.append((m.group("italic"), "i"))
        pos = m.end()
    if pos < len(text):
        segments.append((text[pos:], None))
    return segments or [(text, None)]


class Tooltip:
    """Small delayed hover tooltip for icon-only buttons."""

    def __init__(self, widget, text, bg, fg):
        self.widget, self.text, self.bg, self.fg, self.tip = widget, text, bg, fg, None
        widget.bind("<Enter>", self.show, add="+")
        widget.bind("<Leave>", self.hide, add="+")

    def show(self, _e=None):
        if self.tip or not self.text:
            return
        x = self.widget.winfo_rootx()
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tip = tk.Toplevel(self.widget)
        self.tip.overrideredirect(True)
        self.tip.attributes("-topmost", True)
        tk.Label(self.tip, text=self.text, bg=self.bg, fg=self.fg, font=(FONT, 8),
                 padx=8, pady=4).pack()
        self.tip.geometry(f"+{x}+{y}")

    def hide(self, _e=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None


class ChatApp:
    def __init__(self, root, host=DEFAULT_HOST, port=DEFAULT_PORT):
        self.root = root
        self.host, self.port = host, port
        self.conn = ChatConnection()
        self.username = None
        self.current_room = None
        self.last_room = "General"
        self.rooms = []
        self.room_cache = []
        self.room_rows = []           # parallel to room_list rows: ("header", None) or ("room", room_dict)
        self.current_room_is_private = False
        self.pending_auth = None
        self.pending_create = False
        self.pending_create_private = False
        self.pending_private_join = False
        self.dialog_error_sink = None  # when a dialog is open, server errors go here instead of the banner
        self._create_dialog = None
        self._join_dialog = None
        self.mode = "login"
        self.dark_mode = True
        self.theme_name = "Violet"
        self.unread = 0
        self._toast = None
        self._emoji_popup = None
        self._theme_popup = None
        self.window_is_focused = True
        self.search_var = tk.StringVar()
        self.chat_search_var = tk.StringVar()
        self.sidebar_compact = False
        self.message_status = {}
        self._search_after = None
        # current_log: the message/system entries of the room on screen, kept
        # independently of the widgets so a theme rebuild can replay them
        # instead of losing them (this is the fix for the theme-switch bug).
        self.current_log = []
        self.user_var = tk.StringVar()
        self.pass_var = tk.StringVar()
        self.confirm_var = tk.StringVar()
        self.msg_var = tk.StringVar()
        self.root.title(APP_TITLE)
        self.root.geometry("1180x720")
        self.root.minsize(560, 560)
        self._theme()
        self._build_login()
        self._build_chat()
        self.show_login()
        self.root.bind("<FocusIn>", self.on_focus_in)
        self.root.bind("<FocusOut>", self.on_focus_out)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.after(100, self.poll_events)

    # ------------------------------------------------------------ theme data
    def _theme(self):
        palettes = {
            "Violet": {
                "dark": dict(bg="#09070F", surface="#12101B", surface2="#1B1727", surface3="#29203A", border="#3A2E50",
                              text="#F8F4FF", muted="#AAA0BC", accent="#A855F7", accent2="#7C3AED", accent3="#D946EF",
                              other="#211A2E", mine="#6D3BB5", input="#17131F", danger="#F05A78", success="#55D99A", online="#55D99A"),
                "light": dict(bg="#F7F4FB", surface="#FFFFFF", surface2="#F1EAF8", surface3="#E7D9F3", border="#E1D5EB",
                               text="#292232", muted="#766A82", accent="#8B5CF6", accent2="#7C3AED", accent3="#A855F7",
                               other="#F0E8F7", mine="#DCC7F7", input="#FFFFFF", danger="#D94C6A", success="#25A66A", online="#25A66A")
            },
            "Rose": {
                "dark": dict(bg="#10080D", surface="#191017", surface2="#27151F", surface3="#3B1D2D", border="#563044",
                              text="#FFF5F8", muted="#C0A3AE", accent="#F43F8E", accent2="#E11D48", accent3="#FB7185",
                              other="#2A1721", mine="#8F315B", input="#201119", danger="#FF718A", success="#54D6A0", online="#54D6A0"),
                "light": dict(bg="#FFF6F8", surface="#FFFFFF", surface2="#FCE7EF", surface3="#F9D4E2", border="#EED6DF",
                               text="#32212A", muted="#826D76", accent="#E83E8C", accent2="#D92668", accent3="#F05B86",
                               other="#FBEAF0", mine="#F6C9DC", input="#FFFFFF", danger="#D94C6A", success="#25A66A", online="#25A66A")
            },
            "Mint": {
                "dark": dict(bg="#06100F", surface="#0D1917", surface2="#132521", surface3="#1B3831", border="#285247",
                              text="#F1FFFB", muted="#9BB9B2", accent="#19B995", accent2="#0F8F78", accent3="#42D3B0",
                              other="#11241F", mine="#176A5A", input="#101E1B", danger="#F06A7C", success="#55D99A", online="#55D99A"),
                "light": dict(bg="#F0FAF7", surface="#FFFFFF", surface2="#E2F4EE", surface3="#CFEDE4", border="#D0E8E0",
                               text="#19302A", muted="#668078", accent="#16A889", accent2="#0D8D74", accent3="#25B79A",
                               other="#E7F6F1", mine="#BDE8DA", input="#FFFFFF", danger="#D94C6A", success="#1F9B69", online="#1F9B69")
            },
            "Ocean": {
                "dark": dict(bg="#060B14", surface="#0D1420", surface2="#131E2E", surface3="#1A3047", border="#28445F",
                              text="#F3F9FF", muted="#9AAFC4", accent="#3B9CFF", accent2="#2563EB", accent3="#38BDF8",
                              other="#122238", mine="#245B91", input="#101A29", danger="#F06A7C", success="#55D99A", online="#55D99A"),
                "light": dict(bg="#F2F8FF", surface="#FFFFFF", surface2="#E6F1FC", surface3="#D4E8F9", border="#D2E2F0",
                               text="#1B2C3D", muted="#657A8C", accent="#318CEB", accent2="#2563D6", accent3="#24A8E8",
                               other="#E9F4FD", mine="#C8E3FA", input="#FFFFFF", danger="#D94C6A", success="#1F9B69", online="#1F9B69")
            },
            "Sunset": {
                "dark": dict(bg="#100A07", surface="#1A110D", surface2="#2A1B14", surface3="#42261A", border="#5B3A27",
                              text="#FFF8F1", muted="#C0AA98", accent="#FF8A3D", accent2="#F05A28", accent3="#FFC857",
                              other="#2B1B13", mine="#9A4C25", input="#21150F", danger="#F06A7C", success="#55D99A", online="#55D99A"),
                "light": dict(bg="#FFF8F2", surface="#FFFFFF", surface2="#FFF0E4", surface3="#FFE1CB", border="#F1D9C5",
                               text="#3A2920", muted="#816C5D", accent="#F47B32", accent2="#E85B24", accent3="#F2A83B",
                               other="#FFF0E5", mine="#FFD7B7", input="#FFFFFF", danger="#D94C6A", success="#249A68", online="#249A68")
            },
            "Indigo": {
                "dark": dict(bg="#080812", surface="#111122", surface2="#181833", surface3="#242451", border="#34346C",
                              text="#F5F5FF", muted="#A8A8C8", accent="#6366F1", accent2="#4F46E5", accent3="#818CF8",
                              other="#1B1B38", mine="#4646A5", input="#14142A", danger="#F06A7C", success="#55D99A", online="#55D99A"),
                "light": dict(bg="#F5F5FF", surface="#FFFFFF", surface2="#EBEBFC", surface3="#DCDDF9", border="#D7D8EF",
                               text="#272743", muted="#70708A", accent="#5B5FEF", accent2="#4F46E5", accent3="#7277F4",
                               other="#EDEDFB", mine="#D4D5F8", input="#FFFFFF", danger="#D94C6A", success="#249A68", online="#249A68")
            },
        }
        self.c = palettes[self.theme_name]["dark" if self.dark_mode else "light"]
        self.root.configure(bg=self.c["bg"])

    # ------------------------------------------------------------ rebuild (theme switch)
    def _rebuild(self):
        """Re-skin the whole UI without losing the current room, its messages,
        scroll position or an in-progress (unsent) draft."""
        logged = bool(self.username)
        current = self.current_room
        saved_rooms = list(self.room_cache or self.rooms)
        was_at_bottom = True
        if logged and hasattr(self, "chat_canvas"):
            try:
                top, bottom = self.chat_canvas.yview()
                was_at_bottom = bottom > 0.98
                scroll_top = top
            except tk.TclError:
                scroll_top = 0.0
        else:
            scroll_top = 0.0
        self._close_popups()
        if getattr(self, "_chat_search_bar", None) is not None:
            try:
                self._chat_search_bar.destroy()
            except tk.TclError:
                pass
            self._chat_search_bar = None
        self._theme()
        self._build_login()
        self._build_chat()
        if logged:
            self.current_room = current
            self.show_chat(keep_state=True)
            self.rooms = saved_rooms
            self.update_rooms(saved_rooms)
            if current:
                self.room_header.config(text=f"# {current}")
            # Replay the preserved log into the freshly built (re-themed) widgets.
            for entry in self.current_log:
                if entry["kind"] == "message":
                    self._render_message(entry["timestamp"], entry["user"], entry["text"])
                else:
                    self._render_system(entry["text"])
            self.root.after(30, lambda: self.chat_canvas.yview_moveto(1.0 if was_at_bottom else scroll_top))
        else:
            self.show_login()

    def _close_popups(self):
        for popup in (self._emoji_popup, self._theme_popup, self._toast):
            try:
                if popup is not None:
                    popup.destroy()
            except tk.TclError:
                pass
        self._emoji_popup = self._theme_popup = self._toast = None

    # ------------------------------------------------------------ small widget helpers
    def _hover(self, widget, normal, hover):
        widget.bind("<Enter>", lambda _e: widget.configure(bg=hover))
        widget.bind("<Leave>", lambda _e: widget.configure(bg=normal))

    def _tip(self, widget, text):
        Tooltip(widget, text, self.c["surface3"], self.c["text"])

    def _icon_button(self, parent, text, command, tooltip=None, size=11, fg=None):
        btn = tk.Button(parent, text=text, command=command, bg=self.c["surface2"],
                        fg=fg or self.c["accent"], activebackground=self.c["surface3"],
                        activeforeground=fg or self.c["accent"], relief="flat", bd=0,
                        cursor="hand2", font=(FONT, size, "bold"), padx=8, pady=5)
        self._hover(btn, self.c["surface2"], self.c["surface3"])
        if tooltip:
            self._tip(btn, tooltip)
        return btn

    def _button(self, parent, text, command, tooltip=None):
        btn = tk.Button(parent, text=text, command=command, bg=self.c["accent"], fg="#FFFFFF",
                        activebackground=self.c["accent2"], activeforeground="#FFFFFF",
                        disabledforeground="#C8BDD2", relief="flat", bd=0, highlightthickness=0,
                        cursor="hand2", font=(FONT, 10, "bold"), padx=12, pady=9)
        self._hover(btn, self.c["accent"], self.c["accent2"])
        if tooltip:
            self._tip(btn, tooltip)
        return btn

    def _entry(self, parent, label, var, show=None):
        box = tk.Frame(parent, bg=self.c["surface"])
        tk.Label(box, text=label, bg=self.c["surface"], fg=self.c["muted"], font=(FONT, 9, "bold"),
                 anchor="w").pack(fill="x", pady=(0, 5))
        ent = tk.Entry(box, textvariable=var, show=show or "", bg=self.c["input"], fg=self.c["text"],
                       insertbackground=self.c["text"], relief="flat", bd=0, font=(FONT, 11))
        ent.pack(fill="x", ipady=10)
        return box, ent

    # ------------------------------------------------------------ login / register screen
    def _build_login(self):
        if hasattr(self, "login_frame"):
            self.login_frame.destroy()
        self.login_frame = tk.Frame(self.root, bg=self.c["bg"])
        card = tk.Frame(self.login_frame, bg=self.c["surface"], padx=42, pady=34,
                        highlightthickness=1, highlightbackground=self.c["border"])
        card.place(relx=.5, rely=.5, anchor="center", width=460)
        tk.Label(card, text="🤖", bg=self.c["surface"], font=(FONT, 30)).pack()
        self.auth_title = tk.Label(card, bg=self.c["surface"], fg=self.c["text"], font=(FONT, 24, "bold"))
        self.auth_title.pack()
        self.auth_subtitle = tk.Label(card, bg=self.c["surface"], fg=self.c["muted"], font=(FONT, 10))
        self.auth_subtitle.pack(pady=(5, 20))
        ub, self.user_entry = self._entry(card, "Username", self.user_var)
        ub.pack(fill="x", pady=6)
        pb, self.pass_entry = self._entry(card, "Password", self.pass_var, "•")
        pb.pack(fill="x", pady=6)
        self.confirm_box, self.confirm_entry = self._entry(card, "Confirm Password", self.confirm_var, "•")
        self.show_pw = tk.BooleanVar(value=False)
        tk.Checkbutton(card, text="Show password", variable=self.show_pw, command=self.toggle_password,
                       bg=self.c["surface"], fg=self.c["muted"], selectcolor=self.c["surface"],
                       activebackground=self.c["surface"], activeforeground=self.c["text"],
                       font=(FONT, 9)).pack(anchor="w", pady=4)
        self.auth_button = self._button(card, "Sign In", self.submit_auth)
        self.auth_button.pack(pady=(10, 8))
        self.switch_btn = tk.Button(card, command=self.toggle_mode, bg=self.c["surface"], fg=self.c["accent3"],
                                    activebackground=self.c["surface"], activeforeground=self.c["accent"],
                                    relief="flat", bd=0, cursor="hand2", font=(FONT, 9, "bold"))
        self.switch_btn.pack()
        self.auth_status = tk.Label(card, bg=self.c["surface"], fg=self.c["danger"], wraplength=330, font=(FONT, 9))
        self.auth_status.pack(pady=(12, 0))
        self.theme_btn = self._icon_button(self.login_frame, f"🎨 {self.theme_name}", self.open_theme_panel,
                                           "Choose a theme", size=9)
        self.theme_btn.place(relx=.97, rely=.045, anchor="ne")
        for e in (self.user_entry, self.pass_entry, self.confirm_entry):
            e.bind("<Return>", lambda _e: self.submit_auth())
        self.set_mode(self.mode)

    def set_mode(self, mode):
        self.mode = mode
        if mode == "login":
            self.auth_title.config(text="Welcome Back")
            self.auth_subtitle.config(text="Sign in to continue your conversations")
            self.confirm_box.pack_forget()
            self.switch_btn.config(text="Don't have an account?  Create Account")
        else:
            self.auth_title.config(text="Create Account")
            self.auth_subtitle.config(text="Join Nexora Chat and start messaging")
            self.confirm_box.pack(fill="x", pady=6, before=self.auth_button)
            self.switch_btn.config(text="Already have an account?  Sign In")
        self.set_auth_status("")

    def toggle_mode(self):
        self.set_mode("register" if self.mode == "login" else "login")

    # ------------------------------------------------------------ theme popover (real panel, not a plain menu)
    def open_theme_panel(self):
        if self._theme_popup is not None:
            self._close_popups()
            return
        anchor = self.theme_btn if self.username is None else self.chat_theme_btn
        c = self.c
        popup = tk.Toplevel(self.root)
        self._theme_popup = popup
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        frame = tk.Frame(popup, bg=c["surface"], padx=16, pady=14, highlightthickness=1,
                         highlightbackground=c["border"])
        frame.pack()
        tk.Label(frame, text="Theme", bg=c["surface"], fg=c["text"], font=(FONT, 10, "bold"),
                 anchor="w").grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 8))
        names = ["Violet", "Rose", "Mint", "Ocean", "Sunset", "Indigo"]
        swatch_colors = {"Violet": "#A855F7", "Rose": "#F43F8E", "Mint": "#19B995",
                         "Ocean": "#3B9CFF", "Sunset": "#FF8A3D", "Indigo": "#6366F1"}
        for i, name in enumerate(names):
            col_frame = tk.Frame(frame, bg=c["surface"])
            col_frame.grid(row=1, column=i, padx=6)
            cv = tk.Canvas(col_frame, width=34, height=34, bg=c["surface"], highlightthickness=0, cursor="hand2")
            cv.pack()
            outline = c["text"] if name == self.theme_name else ""
            cv.create_oval(3, 3, 31, 31, fill=swatch_colors[name], outline=outline, width=2)
            cv.bind("<Button-1>", lambda _e, n=name: self.set_theme(n))
            tk.Label(col_frame, text=name, bg=c["surface"], fg=c["muted"], font=(FONT, 7)).pack()
        sep = tk.Frame(frame, bg=c["border"], height=1)
        sep.grid(row=2, column=0, columnspan=6, sticky="ew", pady=12)
        mode_row = tk.Frame(frame, bg=c["surface"])
        mode_row.grid(row=3, column=0, columnspan=6, sticky="ew")
        light_btn = tk.Button(mode_row, text="☀  Light", command=lambda: self.set_mode_theme(False),
                              bg=c["surface2"] if self.dark_mode else c["accent"],
                              fg=c["text"] if self.dark_mode else "white", relief="flat", bd=0,
                              cursor="hand2", font=(FONT, 9, "bold"), padx=10, pady=6)
        light_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))
        dark_btn = tk.Button(mode_row, text="☾  Dark", command=lambda: self.set_mode_theme(True),
                             bg=c["accent"] if self.dark_mode else c["surface2"],
                             fg="white" if self.dark_mode else c["text"], relief="flat", bd=0,
                             cursor="hand2", font=(FONT, 9, "bold"), padx=10, pady=6)
        dark_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))
        popup.update_idletasks()
        x = anchor.winfo_rootx()
        y = anchor.winfo_rooty() + anchor.winfo_height() + 6
        popup.geometry(f"+{x}+{y}")
        popup.bind("<FocusOut>", lambda _e: self._close_popups())
        popup.focus_set()

    def set_theme(self, name):
        self.theme_name = name
        self._close_popups()
        self._rebuild()

    def set_mode_theme(self, dark):
        self.dark_mode = dark
        self._close_popups()
        self._rebuild()

    def toggle_password(self):
        show = "" if self.show_pw.get() else "•"
        self.pass_entry.config(show=show)
        self.confirm_entry.config(show=show)

    def set_auth_status(self, text, color=None):
        self.auth_status.config(text=text, fg=color or self.c["danger"])

    def set_auth_buttons(self, enabled):
        self.auth_button.configure(state="normal" if enabled else "disabled")

    def submit_auth(self):
        username, password = self.user_var.get().strip(), self.pass_var.get()
        if not username or not password:
            self.set_auth_status("Please enter your username and password.")
            return
        if self.mode == "register" and password != self.confirm_var.get():
            self.set_auth_status("Passwords do not match.")
            return
        self.pending_auth = (self.mode, username, password)
        self.set_auth_buttons(False)
        self.set_auth_status("Connecting...", self.c["muted"])
        if self.conn.connected and self.conn.target == (self.host, self.port):
            self.send_pending_auth()
        else:
            self.conn.close()
            self.conn = ChatConnection()
            self.conn.connect_async(self.host, self.port)

    def send_pending_auth(self):
        if self.pending_auth:
            mode, username, password = self.pending_auth
            self.conn.send(mode, username=username, password=password)

    # ------------------------------------------------------------ chat screen
    def _build_chat(self):
        if hasattr(self, "chat_frame"):
            self.chat_frame.destroy()
        c = self.c
        self.chat_frame = tk.Frame(self.root, bg=c["bg"])
        head = tk.Frame(self.chat_frame, bg=c["surface"], highlightthickness=1, highlightbackground=c["border"])
        head.pack(fill="x")
        tk.Label(head, text="🤖  NEXORA CHAT", bg=c["surface"], fg=c["text"], font=(FONT, 14, "bold")
                 ).pack(side="left", padx=12, pady=14)
        self.chat_theme_btn = self._icon_button(head, f"🎨 {self.theme_name}", self.open_theme_panel,
                                                "Choose a theme", size=9)
        self.chat_theme_btn.pack(side="right", padx=(4, 12), pady=8)
        logout_btn = tk.Button(head, text="Logout", command=self.logout, bg=c["surface2"], fg=c["text"],
                              activebackground=c["surface3"], activeforeground=c["text"], relief="flat", bd=0,
                              padx=12, pady=6, cursor="hand2", font=(FONT, 9, "bold"))
        logout_btn.pack(side="right", padx=4)
        self._hover(logout_btn, c["surface2"], c["surface3"])
        call_btn = self._icon_button(head, "📞", self.media_not_ready, "Voice call (coming soon)")
        call_btn.pack(side="right", padx=4)
        self.user_label = tk.Label(head, text="", bg=c["surface"], fg=c["muted"], font=(FONT, 9))
        self.user_label.pack(side="right", padx=12)
        body = tk.Frame(self.chat_frame, bg=c["bg"])
        body.pack(fill="both", expand=True)
        side = tk.Frame(body, bg=c["surface"], width=250, highlightthickness=1, highlightbackground=c["border"])
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        # WhatsApp-style profile/header strip
        profile = tk.Frame(side, bg=c["surface2"], padx=12, pady=10)
        profile.pack(fill="x", padx=10, pady=(10, 6))
        self._avatar(profile, self.username or "?")
        profile_avatar = profile.winfo_children()[-1]
        profile_avatar.pack(side="left", padx=(0, 9))
        ptxt = tk.Frame(profile, bg=c["surface2"])
        ptxt.pack(side="left", fill="x", expand=True)
        tk.Label(ptxt, text=self.username or "Guest", bg=c["surface2"], fg=c["text"],
                 font=(FONT, 10, "bold"), anchor="w").pack(fill="x")
        tk.Label(ptxt, text="● online", bg=c["surface2"], fg=c["online"],
                 font=(FONT, 8)).pack(fill="x", pady=(2, 0))
        menu_btn = self._icon_button(profile, "⋮", self.open_profile_menu, "Profile options", size=14)
        menu_btn.pack(side="right")

        tk.Label(side, text="MESSAGES", bg=c["surface"], fg=c["muted"], font=(FONT, 9, "bold"),
                 anchor="w").pack(fill="x", padx=18, pady=(12, 5))
        search_box = tk.Frame(side, bg=c["input"], highlightthickness=1, highlightbackground=c["border"])
        search_box.pack(fill="x", padx=10, pady=(0, 8))
        tk.Label(search_box, text="⌕", bg=c["input"], fg=c["muted"], font=(FONT, 14)).pack(side="left", padx=(8, 3))
        self.room_search_entry = tk.Entry(search_box, textvariable=self.search_var, bg=c["input"], fg=c["text"],
                                          insertbackground=c["text"], relief="flat", bd=0,
                                          font=(FONT, 9))
        self.room_search_entry.pack(side="left", fill="x", expand=True, ipady=7, padx=(0, 7))
        self.room_search_entry.bind("<KeyRelease>", lambda _e: self.filter_rooms())

        tk.Label(side, text="Rooms", bg=c["surface"], fg=c["text"], font=(FONT, 13, "bold"),
                 anchor="w").pack(fill="x", padx=18, pady=(0, 7))
        self.room_list = tk.Listbox(side, bg=c["surface"], fg=c["text"], selectbackground=c["accent"],
                                    selectforeground="#FFFFFF", font=(FONT, 10, "bold"), borderwidth=0,
                                    highlightthickness=0, activestyle="none", exportselection=False, height=12)
        self.room_list.pack(fill="both", expand=True, padx=10, pady=(2, 0))
        self.room_list.bind("<<ListboxSelect>>", self.on_room_click)
        btn_box = tk.Frame(side, bg=c["surface"])
        btn_box.pack(fill="x", padx=16, pady=(16, 16))
        new_room_btn = tk.Button(btn_box, text="＋  New Room", command=self.create_room,
                                 bg=c["accent"], fg="white", activebackground=c["accent2"],
                                 activeforeground="white", relief="flat", bd=0, cursor="hand2",
                                 font=(FONT, 10, "bold"), pady=9)
        new_room_btn.pack(fill="x")
        self._hover(new_room_btn, c["accent"], c["accent2"])
        join_private_btn = tk.Button(btn_box, text="🔒  Join Private Room", command=self.open_join_private_dialog,
                                     bg=c["surface2"], fg=c["text"], activebackground=c["surface3"],
                                     activeforeground=c["text"], relief="flat", bd=0, cursor="hand2",
                                     font=(FONT, 9, "bold"), pady=8)
        join_private_btn.pack(fill="x", pady=(8, 0))
        self._hover(join_private_btn, c["surface2"], c["surface3"])
        main = tk.Frame(body, bg=c["bg"])
        main.pack(side="left", fill="both", expand=True)
        bar = tk.Frame(main, bg=c["surface"], highlightthickness=1, highlightbackground=c["border"])
        bar.pack(fill="x")
        self.room_header = tk.Label(bar, text="Select a room", bg=c["surface"], fg=c["text"],
                                    font=(FONT, 13, "bold"), anchor="w")
        self.room_header.pack(side="left", padx=18, pady=14)
        self.online_label = tk.Label(bar, text="", bg=c["surface"], fg=c["online"], font=(FONT, 9, "bold"))
        self.online_label.pack(side="left", padx=8)
        self.chat_search_btn = self._icon_button(bar, "⌕", self.toggle_chat_search, "Search messages", size=14)
        self.chat_search_btn.pack(side="right", padx=(3, 10), pady=8)
        area = tk.Frame(main, bg=c["bg"])
        area.pack(fill="both", expand=True, padx=14, pady=12)
        self.chat_canvas = tk.Canvas(area, bg=c["bg"], highlightthickness=0, bd=0)
        sb = tk.Scrollbar(area, orient="vertical", command=self.chat_canvas.yview)
        sb.pack(side="right", fill="y")
        self.chat_canvas.pack(side="left", fill="both", expand=True)
        self.chat_canvas.configure(yscrollcommand=sb.set)
        self.message_frame = tk.Frame(self.chat_canvas, bg=c["bg"])
        self.canvas_window = self.chat_canvas.create_window((0, 0), window=self.message_frame, anchor="nw")
        self.message_frame.bind("<Configure>", lambda _e: self.chat_canvas.configure(scrollregion=self.chat_canvas.bbox("all")))
        self.chat_canvas.bind("<Configure>", lambda e: self.chat_canvas.itemconfigure(self.canvas_window, width=e.width))
        comp = tk.Frame(main, bg=c["surface"], highlightthickness=1, highlightbackground=c["border"])
        comp.pack(fill="x", padx=14, pady=(0, 14))
        self.emoji_btn = self._icon_button(comp, "😊", self.open_emoji_picker, "Emoji picker", size=13)
        self.emoji_btn.pack(side="left", padx=(8, 3), pady=8)
        self.attach_btn = self._icon_button(comp, "📎", self.media_not_ready, "Attach file/image (coming soon)", size=12)
        self.attach_btn.pack(side="left", padx=2)
        bold_btn = self._icon_button(comp, "B", lambda: self.wrap_selection("**", "**"), "Bold")
        bold_btn.pack(side="left", padx=2)
        italic_btn = self._icon_button(comp, "I", lambda: self.wrap_selection("*", "*"), "Italic")
        italic_btn.pack(side="left", padx=2)
        strike_btn = self._icon_button(comp, "S", lambda: self.wrap_selection("~~", "~~"), "Strikethrough")
        strike_btn.pack(side="left", padx=(2, 6))
        self.msg_entry = tk.Entry(comp, textvariable=self.msg_var, bg=c["input"], fg=c["text"],
                                  insertbackground=c["text"], relief="flat", bd=0, font=(FONT, 11))
        self.msg_entry.pack(side="left", fill="x", expand=True, ipady=10, padx=5)
        self.msg_entry.bind("<Return>", lambda _e: self.send_message())
        self.msg_entry.bind("<FocusIn>", lambda _e: self.msg_entry.configure(highlightthickness=1, highlightbackground=c["accent"]))
        self.msg_entry.bind("<FocusOut>", lambda _e: self.msg_entry.configure(highlightthickness=0))
        image_btn = self._icon_button(comp, "🖼", self.media_not_ready, "Send an image (coming soon)", size=12)
        image_btn.pack(side="left", padx=3)
        mic_btn = self._icon_button(comp, "🎤", self.media_not_ready, "Voice message (coming soon)")
        mic_btn.pack(side="left", padx=3)
        send_btn = self._button(comp, "Send  ➤", self.send_message, "Send message (Enter)")
        send_btn.pack(side="right", padx=8, pady=7)
        status = tk.Frame(self.chat_frame, bg=c["surface"], highlightthickness=1, highlightbackground=c["border"])
        status.pack(side="bottom", fill="x")
        self.conn_label = tk.Label(status, text="● Connected", bg=c["surface"], fg=c["online"], font=(FONT, 8, "bold"))
        self.conn_label.pack(side="right", padx=14, pady=5)
        self.status_user = tk.Label(status, text="", bg=c["surface"], fg=c["muted"], font=(FONT, 8))
        self.status_user.pack(side="left", padx=14, pady=5)

    # ------------------------------------------------------------ emoji picker (real, no shortcodes needed)
    def open_emoji_picker(self):
        if self._emoji_popup is not None:
            self._close_popups()
            return
        c = self.c
        popup = tk.Toplevel(self.root)
        self._emoji_popup = popup
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        outer = tk.Frame(popup, bg=c["surface"], highlightthickness=1, highlightbackground=c["border"])
        outer.pack()
        tabs = tk.Frame(outer, bg=c["surface"])
        tabs.pack(fill="x", padx=8, pady=(8, 0))
        grid_holder = tk.Frame(outer, bg=c["surface"], padx=10, pady=8)
        grid_holder.pack()

        def show_category(idx):
            for w in grid_holder.winfo_children():
                w.destroy()
            _, emojis = EMOJI_CATEGORIES[idx]
            for i, glyph in enumerate(emojis):
                b = tk.Button(grid_holder, text=glyph, bg=c["surface"], activebackground=c["surface3"],
                             relief="flat", bd=0, font=(FONT, 14), cursor="hand2",
                             command=lambda g=glyph: self.insert_emoji(g))
                b.grid(row=i // 6, column=i % 6, padx=2, pady=2)

        for idx, (label, _) in enumerate(EMOJI_CATEGORIES):
            t = tk.Button(tabs, text=label, bg=c["surface"], fg=c["muted"], activebackground=c["surface2"],
                         relief="flat", bd=0, font=(FONT, 8, "bold"), cursor="hand2",
                         command=lambda i=idx: show_category(i))
            t.pack(side="left", padx=2)
        show_category(0)
        popup.update_idletasks()
        x = self.emoji_btn.winfo_rootx()
        y = self.emoji_btn.winfo_rooty() - popup.winfo_height() - 8
        popup.geometry(f"+{x}+{max(y, 10)}")
        popup.bind("<FocusOut>", lambda _e: self._close_popups())
        popup.focus_set()

    def insert_emoji(self, glyph):
        self.msg_entry.insert("insert", glyph)
        self.msg_entry.focus_set()
        self._close_popups()

    # ------------------------------------------------------------ bold/italic/strike helper
    def wrap_selection(self, left, right):
        entry = self.msg_entry
        try:
            if entry.selection_present():
                start, end = entry.index("sel.first"), entry.index("sel.last")
                selected = entry.get()[start:end]
                entry.delete(start, end)
                entry.insert(start, f"{left}{selected}{right}")
                entry.icursor(start + len(left) + len(selected) + len(right))
                return
        except tk.TclError:
            pass
        pos = entry.index("insert")
        entry.insert(pos, f"{left}{right}")
        entry.icursor(pos + len(left))
        entry.focus_set()

    # ------------------------------------------------------------ message rendering (data + widgets kept separate)
    def clear_chat(self):
        self.current_log = []
        if hasattr(self, "message_frame"):
            for w in self.message_frame.winfo_children():
                w.destroy()

    def _avatar(self, parent, user):
        size = 34
        cv = tk.Canvas(parent, width=size, height=size, bg=self.c["bg"], highlightthickness=0)
        cv.pack()
        accents = [self.c["accent"], self.c["accent2"], self.c["accent3"], self.c["success"]]
        color = accents[sum(ord(ch) for ch in user) % len(accents)]
        cv.create_oval(2, 2, size - 2, size - 2, fill=color, outline="")
        initials = "".join(part[0] for part in user.replace("_", " ").split()[:2]).upper() or "?"
        cv.create_text(size / 2, size / 2, text=initials, fill="#FFFFFF", font=(FONT, 9, "bold"))
        return cv

    # Bubble width is snug to content (in characters), never wider than this,
    # so long messages wrap instead of stretching the bubble across the chat.
    BUBBLE_MAX_CHARS = 42
    BUBBLE_MIN_CHARS = 2

    def _rich_text_widget(self, parent, text, bg, fg, max_chars):
        """A read-only Text widget that renders **bold** / *italic* / ~~strike~~ / `code`
        and auto-sizes tightly to its wrapped content (used inside bubbles).

        IMPORTANT: the widget must be packed into its parent *before* we ask
        Tk how many display lines it wrapped to. Measuring before packing
        leaves the widget with no real pixel width to wrap against, so Tk
        guesses (badly) and can report many more lines than the text
        actually needs - that was the cause of short messages rendering as
        tall bubbles.
        """
        segments = parse_rich(text)
        visible_len = sum(len(segment) for segment, _tag in segments) or 1
        width_chars = max(self.BUBBLE_MIN_CHARS, min(max_chars, visible_len))
        widget = tk.Text(parent, bg=bg, fg=fg, relief="flat", bd=0, wrap="word", padx=0, pady=0,
                         font=(FONT, 10), highlightthickness=0, width=width_chars, height=1,
                         cursor="arrow", takefocus=0)
        widget.tag_config("b", font=(FONT, 10, "bold"))
        widget.tag_config("i", font=(FONT, 10, "italic"))
        widget.tag_config("s", font=(FONT, 10, "overstrike"))
        widget.tag_config("code", font=("Courier New", 9), background=self.c["surface3"])
        for segment, tag in segments:
            if tag:
                widget.insert("end", segment, tag)
            else:
                widget.insert("end", segment)
        widget.configure(state="disabled")
        widget.pack()                  # realize it first...
        widget.update_idletasks()      # ...then let Tk finish laying it out...
        lines = max(1, int(widget.count("1.0", "end", "displaylines")[0]))
        widget.configure(height=lines)  # ...only then is the line count trustworthy.
        return widget

    def _render_message(self, timestamp, user, text):
        mine = user == self.username
        c = self.c
        row = tk.Frame(self.message_frame, bg=c["bg"])
        row.pack(fill="x", pady=3, padx=8)
        wrap = tk.Frame(row, bg=c["bg"])
        wrap.pack(side="right" if mine else "left", anchor="e" if mine else "w")
        if not mine:
            avatar_col = tk.Frame(wrap, bg=c["bg"])
            avatar_col.pack(side="left", padx=(0, 7), anchor="s")
            self._avatar(avatar_col, user)
        holder = tk.Frame(wrap, bg=c["bg"])
        holder.pack(side="left" if not mine else "right")
        top = tk.Frame(holder, bg=c["bg"])
        top.pack(fill="x")
        tk.Label(top, text="You" if mine else user, bg=c["bg"], fg=c["accent"] if mine else c["muted"],
                 font=(FONT, 8, "bold")).pack(side="right" if mine else "left", padx=7)
        bubble_bg = c["mine"] if mine else c["other"]
        # Small, tight padding so the bubble hugs its content instead of
        # ballooning - this is the "compact for short messages" requirement.
        bubble = tk.Frame(holder, bg=bubble_bg, padx=10, pady=6)
        bubble.pack(anchor="e" if mine else "w")
        self._rich_text_widget(bubble, text, bubble_bg, c["text"], self.BUBBLE_MAX_CHARS)
        # Timestamp lives inside the bubble, right-aligned under the text,
        # instead of as a separate label outside it.
        stamp = format_timestamp(timestamp)
        status_text = "  ✓✓" if mine else ""
        tk.Label(bubble, text=f"{stamp}{status_text}", bg=bubble_bg, fg=c["muted"],
                 font=(FONT, 7)).pack(anchor="e", pady=(1, 0))
        self.root.after(20, lambda: self.chat_canvas.yview_moveto(1.0))

    def _render_system(self, text):
        tk.Label(self.message_frame, text=text, bg=self.c["bg"], fg=self.c["muted"],
                 font=(FONT, 8, "italic")).pack(pady=8)

    def append_message(self, timestamp, user, text):
        self.current_log.append({"kind": "message", "timestamp": timestamp, "user": user, "text": text})
        self._render_message(timestamp, user, text)

    def append_system(self, text):
        self.current_log.append({"kind": "system", "text": text})
        self._render_system(text)

    # ------------------------------------------------------------ screens
    def show_login(self, message="", color=None):
        self.chat_frame.pack_forget()
        self.login_frame.pack(fill="both", expand=True)
        self.username = None
        self.current_room = None
        self.pending_auth = None
        self.clear_unread()
        self.user_var.set("")
        self.pass_var.set("")
        self.confirm_var.set("")
        self.set_auth_buttons(True)
        self.set_auth_status(message, color or self.c["danger"])

    def show_chat(self, keep_state=False):
        self.login_frame.pack_forget()
        self.chat_frame.pack(fill="both", expand=True)
        self.user_label.config(text=f"@{self.username}")
        self.status_user.config(text=f"Signed in as {self.username}")
        self.conn_label.config(text="● Connected", fg=self.c["online"])
        if not keep_state:
            self.clear_chat()
            self.room_list.delete(0, "end")
            self.join_room(self.last_room)

    # ------------------------------------------------------------ WhatsApp-style utilities
    def toggle_chat_search(self):
        if getattr(self, "_chat_search_bar", None) is not None:
            self._chat_search_bar.destroy()
            self._chat_search_bar = None
            return
        bar = tk.Frame(self.chat_frame, bg=self.c["surface2"], highlightthickness=1,
                       highlightbackground=self.c["border"])
        bar.place(relx=1.0, rely=0.0, anchor="ne", relwidth=.42)
        self._chat_search_bar = bar
        tk.Label(bar, text="⌕", bg=self.c["surface2"], fg=self.c["muted"],
                 font=(FONT, 14)).pack(side="left", padx=(8, 3))
        ent = tk.Entry(bar, textvariable=self.chat_search_var, bg=self.c["input"], fg=self.c["text"],
                       insertbackground=self.c["text"], relief="flat", bd=0, font=(FONT, 9))
        ent.pack(side="left", fill="x", expand=True, ipady=7)
        ent.focus_set()
        tk.Button(bar, text="×", command=self.toggle_chat_search, bg=self.c["surface2"],
                  fg=self.c["muted"], relief="flat", bd=0, font=(FONT, 13),
                  cursor="hand2").pack(side="right", padx=6)
        ent.bind("<KeyRelease>", self.highlight_chat_search)

    def highlight_chat_search(self, _event=None):
        query = self.chat_search_var.get().strip().lower()
        for child in self.message_frame.winfo_children():
            # Keep existing rendered widgets intact; simply lower opacity is not
            # available in Tkinter, so matching messages are given a subtle
            # border where possible.
            if not query:
                try:
                    child.configure(highlightthickness=0)
                except tk.TclError:
                    pass
                continue
            text_blob = child.winfo_children()
            matched = query in str(text_blob).lower()
            try:
                child.configure(highlightthickness=1 if matched else 0,
                                highlightbackground=self.c["accent"])
            except tk.TclError:
                pass

    def open_profile_menu(self):
        popup = tk.Toplevel(self.root)
        popup.title("Profile")
        popup.configure(bg=self.c["surface"])
        popup.resizable(False, False)
        frame = tk.Frame(popup, bg=self.c["surface"], padx=20, pady=18)
        frame.pack()
        self._avatar(frame, self.username or "?")
        tk.Label(frame, text=self.username or "Guest", bg=self.c["surface"], fg=self.c["text"],
                 font=(FONT, 13, "bold")).pack(pady=(8, 2))
        tk.Label(frame, text="● Online", bg=self.c["surface"], fg=self.c["online"],
                 font=(FONT, 9)).pack()
        tk.Button(frame, text="Close", command=popup.destroy, bg=self.c["accent"], fg="white",
                  relief="flat", bd=0, cursor="hand2", padx=18, pady=7,
                  font=(FONT, 9, "bold")).pack(pady=(14, 0))

    def open_join_private_dialog(self):
        messagebox.showinfo(
            "Private rooms",
            "Private-room access requires the matching server/database room-membership "
            "protocol. This client will not pretend that a code works until the backend "
            "supports it.",
            parent=self.root,
        )

    # ------------------------------------------------------------ actions
    def logout(self):
        if self.conn.connected:
            self.conn.send("logout")
        self.current_room = None
        self.show_login("You have been logged out.", self.c["muted"])

    def create_room(self):
        name = simpledialog.askstring(
            "＋ New Room",
            "Room name (2–30 letters, digits, spaces, - or _):",
            parent=self.root,
        )
        if name is None:
            return
        name = name.strip()
        if not (2 <= len(name) <= 30):
            messagebox.showerror("Invalid room name", "Room name must be 2–30 characters.", parent=self.root)
            return
        if not re.fullmatch(r"[A-Za-z0-9 _-]+", name):
            messagebox.showerror(
                "Invalid room name",
                "Use only letters, numbers, spaces, hyphens or underscores.",
                parent=self.root,
            )
            return
        self.pending_create = True
        if not self.conn.send("create_room", room=name):
            self.pending_create = False
            self.flash_banner("Not connected to the server.")

    def join_room(self, name):
        if not self.conn.send("join_room", room=name):
            self.flash_banner("Not connected to the server.")

    def on_room_click(self, _event):
        s = self.room_list.curselection()
        if not s:
            return
        shown = [r for r in self.room_cache
                 if self.search_var.get().strip().lower() in r.get("name", "").lower()]
        if s[0] < len(shown):
            name = shown[s[0]]["name"]
            if name != self.current_room:
                self.join_room(name)

    def send_message(self):
        text = self.msg_var.get().strip()
        if not text:
            self.flash_banner("Type a message first.", self.c["muted"], 1800)
            return
        if not self.current_room:
            self.flash_banner("Join a room first.", self.c["muted"], 1800)
            return
        if not self.conn.send("message", text=text):
            self.flash_banner("Not connected to the server.")
            return
        self.msg_var.set("")

    def media_not_ready(self):
        messagebox.showinfo(
            "Coming soon",
            "Image sharing, voice messages and live voice calls need extra work on the "
            "server side (a new binary/streaming protocol, storage limits, call signalling) "
            "before they can be turned on safely. They are intentionally left as clearly "
            "labelled placeholders here rather than faked.\n\n"
            "A true phone app also needs its own mobile client - this Tkinter window is a "
            "desktop app.")

    # ------------------------------------------------------------ notifications
    def on_focus_in(self, _e=None):
        self.window_is_focused = True
        self.search_var = tk.StringVar()
        self.chat_search_var = tk.StringVar()
        self.sidebar_compact = False
        self.message_status = {}
        self._search_after = None
        self.clear_unread()

    def on_focus_out(self, _e=None):
        self.window_is_focused = False

    def notify_new_message(self, room, user, text):
        if not should_notify(self.window_is_focused, user, self.username):
            return
        self.unread += 1
        self.root.title(f"({self.unread}) New message • {APP_TITLE}")
        try:
            self.root.bell()
        except tk.TclError:
            pass
        self.show_toast(f"{user} in #{room}", text if len(text) <= 80 else text[:77] + "...")

    def show_toast(self, title, body):
        try:
            if self._toast is not None:
                self._toast.destroy()
            t = tk.Toplevel(self.root)
            self._toast = t
            t.overrideredirect(True)
            t.attributes("-topmost", True)
            f = tk.Frame(t, bg=self.c["surface"], padx=14, pady=10, highlightthickness=1,
                        highlightbackground=self.c["border"])
            f.pack(fill="both", expand=True)
            tk.Label(f, text="🔔  " + title, bg=self.c["surface"], fg=self.c["text"], font=(FONT, 9, "bold"),
                     anchor="w").pack(fill="x")
            tk.Label(f, text=body, bg=self.c["surface"], fg=self.c["muted"], font=(FONT, 9), anchor="w",
                     wraplength=290, justify="left").pack(fill="x", pady=(4, 0))
            w, h = 320, 82
            x = self.root.winfo_screenwidth() - w - 20
            y = self.root.winfo_screenheight() - h - 70
            t.geometry(f"{w}x{h}+{x}+{y}")
            t.after(4500, self._close_toast)
        except tk.TclError:
            pass

    def _close_toast(self):
        try:
            if self._toast is not None:
                self._toast.destroy()
        except tk.TclError:
            pass
        self._toast = None

    def clear_unread(self):
        self.unread = 0
        self.root.title(APP_TITLE)

    def flash_banner(self, text, color=None, ms=4500):
        color = color or self.c["danger"]
        b = tk.Label(self.chat_frame, text=text, bg=color, fg="white", font=(FONT, 9, "bold"), pady=7)
        b.place(relx=.5, rely=.075, anchor="n")
        self.root.after(ms, b.destroy)

    # ------------------------------------------------------------ server events
    def poll_events(self):
        while True:
            try:
                ev = self.conn.events.get_nowait()
            except queue.Empty:
                break
            self.handle_event(ev)
        self.root.after(100, self.poll_events)

    def handle_event(self, ev):
        kind = ev.get("type")
        if kind == "connected":
            self.send_pending_auth()
        elif kind == "connect_failed":
            self.pending_auth = None
            self.set_auth_buttons(True)
            self.set_auth_status("Cannot reach the server. Please try again.")
        elif kind == "connection_lost":
            if self.username:
                self.show_login("Connection to the server was lost. Please log in again.")
            else:
                self.pending_auth = None
                self.set_auth_buttons(True)
                self.set_auth_status("Connection to the server was lost.")
        elif kind == "auth_result":
            self.on_auth_result(ev)
        elif kind == "rooms":
            self.update_rooms(ev.get("rooms", []))
        elif kind == "room_created":
            if self.pending_create:
                self.pending_create = False
                self.join_room(ev.get("room"))
        elif kind == "joined":
            self.on_joined(ev)
        elif kind == "message":
            if ev.get("room") == self.current_room:
                self.append_message(ev.get("timestamp"), ev.get("user", "?"), ev.get("text", ""))
                self.notify_new_message(ev.get("room"), ev.get("user", "?"), ev.get("text", ""))
        elif kind == "system":
            self.append_system(f"[{format_timestamp(ev.get('timestamp'))}] {ev.get('text', '')}")
        elif kind == "error":
            self.on_error(ev.get("text", "Unknown error."))

    def on_auth_result(self, ev):
        self.set_auth_buttons(True)
        self.pending_auth = None
        if not ev.get("ok"):
            self.set_auth_status(ev.get("error", "Authentication failed."))
            return
        if ev.get("action") == "register":
            self.set_mode("login")
            self.pass_var.set("")
            self.confirm_var.set("")
            self.set_auth_status("Account created successfully. You can now sign in.", self.c["success"])
            return
        self.username = ev.get("username")
        self.pass_var.set("")
        self.confirm_var.set("")
        self.show_chat()

    def update_rooms(self, rooms):
        self.rooms = list(rooms)
        self.room_cache = list(rooms)
        self._draw_room_list(self.room_cache)

    def _draw_room_list(self, rooms):
        self.room_list.delete(0, "end")
        for r in rooms:
            lock = "🔒" if r.get("private") else "●"
            online = r.get("online", 0)
            self.room_list.insert("end", f"  {lock}  #{r['name']}    {online} online")
        for i, r in enumerate(rooms):
            if r["name"] == self.current_room:
                self.room_list.selection_set(i)
                self.room_header.config(text=f"# {r['name']}")
                self.online_label.config(text=f"● {r.get('online', 0)} online")

    def filter_rooms(self):
        query = self.search_var.get().strip().lower()
        if not query:
            self._draw_room_list(self.room_cache)
            return
        filtered = [r for r in self.room_cache if query in r.get("name", "").lower()]
        self._draw_room_list(filtered)

    def on_joined(self, ev):
        self.current_room = self.last_room = ev.get("room")
        self.clear_chat()
        for m in ev.get("history", []):
            self.append_message(m.get("timestamp"), m.get("user", "?"), m.get("text", ""))
        self.append_system(f"— You joined #{self.current_room} —")
        self.room_header.config(text=f"# {self.current_room}")
        self.update_rooms(self.rooms)
        self.msg_entry.focus_set()

    def on_error(self, text):
        if self.username is None:
            self.set_auth_buttons(True)
            self.set_auth_status(text)
            return
        self.flash_banner(text)
        if self.pending_create:
            self.pending_create = False
            messagebox.showerror("Could not create room", text, parent=self.root)

    def on_close(self):
        self.conn.close()
        self.root.destroy()


def main():
    p = argparse.ArgumentParser(description="Nexora Chat - GUI client")
    p.add_argument("--host", default=DEFAULT_HOST)
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    a = p.parse_args()
    root = tk.Tk()
    ChatApp(root, a.host, a.port)
    root.mainloop()


if __name__ == "__main__":
    main()

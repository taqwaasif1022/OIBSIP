"""
Oasis Infobyte - Python Programming Internship
Task 2: Advanced BMI Calculator

Professional BMI tracking desktop application.
Tech: Python, Tkinter, SQLite, Matplotlib
"""

import tkinter as tk
from tkinter import ttk, messagebox

from datetime import datetime

from database import BMIDatabase, DatabaseError

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


# ============================================================
# APPLICATION COLORS
# ============================================================

BG = "#0f172a"
CARD = "#1e293b"
CARD_LIGHT = "#263449"
TEXT = "#f8fafc"
MUTED = "#94a3b8"
ACCENT = "#38bdf8"
ACCENT_DARK = "#0284c7"

GREEN = "#22c55e"
YELLOW = "#f59e0b"
ORANGE = "#f97316"
RED = "#ef4444"

BORDER = "#334155"


# ============================================================
# BMI CALCULATION
# ============================================================

def calculate_bmi(weight: float, height: float):
    """Calculate BMI and determine its health category."""

    if weight <= 0:
        raise ValueError("Weight must be greater than 0 kg.")

    if height <= 0:
        raise ValueError("Height must be greater than 0 meters.")

    bmi = weight / (height ** 2)
    bmi = round(bmi, 2)

    if bmi < 18.5:
        category = "Underweight"
    elif bmi < 25:
        category = "Normal"
    elif bmi < 30:
        category = "Overweight"
    else:
        category = "Obese"

    return bmi, category


def category_color(category: str):
    """Return display color for BMI category."""

    colors = {
        "Underweight": ACCENT,
        "Normal": GREEN,
        "Overweight": YELLOW,
        "Obese": RED,
    }

    return colors.get(category, TEXT)


# ============================================================
# MAIN APPLICATION
# ============================================================

class BMIApp:
    """Main BMI Calculator GUI."""

    def __init__(self, root):
        self.root = root

        self.root.title("BMI Tracker • Oasis Infobyte")
        self.root.geometry("1100x720")
        self.root.minsize(950, 650)
        self.root.configure(bg=BG)

        self.db = BMIDatabase()

        self.current_bmi = None
        self.current_category = None

        self.user_var = tk.StringVar()
        self.weight_var = tk.StringVar()
        self.height_var = tk.StringVar()

        self.bmi_value_var = tk.StringVar(value="--")
        self.category_var = tk.StringVar(value="Calculate your BMI")
        self.status_var = tk.StringVar(value="Ready")

        self._configure_styles()
        self._build_interface()
        self._load_users()

    # ========================================================
    # STYLES
    # ========================================================

    def _configure_styles(self):
        """Configure ttk widget styles."""

        style = ttk.Style()

        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure(
            "TCombobox",
            fieldbackground=CARD_LIGHT,
            background=CARD_LIGHT,
            foreground=TEXT,
            arrowcolor=TEXT,
            bordercolor=BORDER,
            lightcolor=BORDER,
            darkcolor=BORDER,
            padding=8,
        )

        style.map(
            "TCombobox",
            fieldbackground=[("readonly", CARD_LIGHT)],
            foreground=[("readonly", TEXT)],
        )

        style.configure(
            "Treeview",
            background=CARD,
            foreground=TEXT,
            fieldbackground=CARD,
            bordercolor=BORDER,
            rowheight=32,
        )

        style.configure(
            "Treeview.Heading",
            background=CARD_LIGHT,
            foreground=TEXT,
            bordercolor=BORDER,
            font=("Segoe UI", 10, "bold"),
        )

        style.map(
            "Treeview",
            background=[("selected", ACCENT_DARK)],
            foreground=[("selected", TEXT)],
        )

    # ========================================================
    # HELPER WIDGETS
    # ========================================================

    def _label(self, parent, text, size=10, bold=False, color=TEXT):
        """Create a consistent label."""

        font = ("Segoe UI", size, "bold" if bold else "normal")

        return tk.Label(
            parent,
            text=text,
            font=font,
            bg=parent.cget("bg"),
            fg=color,
        )

    def _button(self, parent, text, command, primary=False):
        """Create a styled button."""

        bg = ACCENT_DARK if primary else CARD_LIGHT
        active = ACCENT if primary else "#334155"

        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 10, "bold"),
            bg=bg,
            fg=TEXT,
            activebackground=active,
            activeforeground=TEXT,
            relief="flat",
            bd=0,
            padx=18,
            pady=10,
            cursor="hand2",
        )

    # ========================================================
    # INTERFACE
    # ========================================================

    def _build_interface(self):
        """Build complete application interface."""

        # ---------------- HEADER ----------------

        header = tk.Frame(self.root, bg=BG)
        header.pack(fill="x", padx=30, pady=(24, 12))

        title_area = tk.Frame(header, bg=BG)
        title_area.pack(side="left")

        tk.Label(
            title_area,
            text="BMI TRACKER",
            font=("Segoe UI", 24, "bold"),
            bg=BG,
            fg=TEXT,
        ).pack(anchor="w")

        tk.Label(
            title_area,
            text="Personal BMI & Health Tracking",
            font=("Segoe UI", 10),
            bg=BG,
            fg=MUTED,
        ).pack(anchor="w", pady=(2, 0))

        tk.Label(
            header,
            text="OASIS INFOBYTE • PYTHON",
            font=("Segoe UI", 9, "bold"),
            bg=BG,
            fg=ACCENT,
        ).pack(side="right", pady=8)

        # ---------------- MAIN CONTENT ----------------

        content = tk.Frame(self.root, bg=BG)
        content.pack(fill="both", expand=True, padx=30, pady=10)

        content.columnconfigure(0, weight=1)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)

        # LEFT SIDE
        left = tk.Frame(
            content,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        left.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 10),
        )

        self._build_input_panel(left)

        # RIGHT SIDE
        right = tk.Frame(
            content,
            bg=CARD,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        right.grid(
            row=0,
            column=1,
            sticky="nsew",
            padx=(10, 0),
        )

        self._build_result_panel(right)

        # ---------------- STATUS BAR ----------------

        status = tk.Frame(self.root, bg=BG)
        status.pack(fill="x", padx=30, pady=(4, 18))

        tk.Label(
            status,
            textvariable=self.status_var,
            font=("Segoe UI", 9),
            bg=BG,
            fg=MUTED,
        ).pack(side="left")

        tk.Label(
            status,
            text="SQLite • Matplotlib • Tkinter",
            font=("Segoe UI", 9),
            bg=BG,
            fg=MUTED,
        ).pack(side="right")

    # ========================================================
    # INPUT PANEL
    # ========================================================

    def _build_input_panel(self, parent):
        """Build user and measurement input section."""

        tk.Label(
            parent,
            text="BMI Calculator",
            font=("Segoe UI", 17, "bold"),
            bg=CARD,
            fg=TEXT,
        ).pack(anchor="w", padx=25, pady=(25, 4))

        tk.Label(
            parent,
            text="Enter your measurements to calculate BMI.",
            font=("Segoe UI", 9),
            bg=CARD,
            fg=MUTED,
        ).pack(anchor="w", padx=25, pady=(0, 25))

        # USER
        tk.Label(
            parent,
            text="USER",
            font=("Segoe UI", 9, "bold"),
            bg=CARD,
            fg=MUTED,
        ).pack(anchor="w", padx=25)

        user_frame = tk.Frame(parent, bg=CARD)
        user_frame.pack(fill="x", padx=25, pady=(7, 22))

        self.user_combo = ttk.Combobox(
            user_frame,
            textvariable=self.user_var,
            state="normal",
            font=("Segoe UI", 11),
        )
        self.user_combo.pack(
            side="left",
            fill="x",
            expand=True,
        )

        self._button(
            user_frame,
            "+ New User",
            self.new_user,
        ).pack(side="left", padx=(8, 0))

        # WEIGHT
        tk.Label(
            parent,
            text="WEIGHT",
            font=("Segoe UI", 9, "bold"),
            bg=CARD,
            fg=MUTED,
        ).pack(anchor="w", padx=25)

        weight_frame = tk.Frame(
            parent,
            bg=CARD_LIGHT,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        weight_frame.pack(fill="x", padx=25, pady=(7, 18))

        self.weight_entry = tk.Entry(
            weight_frame,
            textvariable=self.weight_var,
            font=("Segoe UI", 12),
            bg=CARD_LIGHT,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            bd=0,
        )
        self.weight_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=12,
            pady=11,
        )

        tk.Label(
            weight_frame,
            text="kg",
            font=("Segoe UI", 10, "bold"),
            bg=CARD_LIGHT,
            fg=MUTED,
        ).pack(side="right", padx=12)

        # HEIGHT
        tk.Label(
            parent,
            text="HEIGHT",
            font=("Segoe UI", 9, "bold"),
            bg=CARD,
            fg=MUTED,
        ).pack(anchor="w", padx=25)

        height_frame = tk.Frame(
            parent,
            bg=CARD_LIGHT,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        height_frame.pack(fill="x", padx=25, pady=(7, 25))

        self.height_entry = tk.Entry(
            height_frame,
            textvariable=self.height_var,
            font=("Segoe UI", 12),
            bg=CARD_LIGHT,
            fg=TEXT,
            insertbackground=TEXT,
            relief="flat",
            bd=0,
        )
        self.height_entry.pack(
            side="left",
            fill="x",
            expand=True,
            padx=12,
            pady=11,
        )

        tk.Label(
            height_frame,
            text="m",
            font=("Segoe UI", 10, "bold"),
            bg=CARD_LIGHT,
            fg=MUTED,
        ).pack(side="right", padx=12)

        # CALCULATE
        self._button(
            parent,
            "Calculate BMI",
            self.calculate,
            primary=True,
        ).pack(
            fill="x",
            padx=25,
            pady=(0, 10),
        )

        # SAVE
        self.save_button = self._button(
            parent,
            "Save BMI Record",
            self.save_record,
        )
        self.save_button.pack(
            fill="x",
            padx=25,
            pady=5,
        )

        # HISTORY / GRAPH
        bottom_buttons = tk.Frame(parent, bg=CARD)
        bottom_buttons.pack(
            fill="x",
            padx=25,
            pady=(8, 20),
        )

        self._button(
            bottom_buttons,
            "View History",
            self.show_history,
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(0, 5),
        )

        self._button(
            bottom_buttons,
            "BMI Trend",
            self.show_trend,
        ).pack(
            side="left",
            fill="x",
            expand=True,
            padx=(5, 0),
        )

    # ========================================================
    # RESULT PANEL
    # ========================================================

    def _build_result_panel(self, parent):
        """Build BMI result card."""

        tk.Label(
            parent,
            text="Your Result",
            font=("Segoe UI", 17, "bold"),
            bg=CARD,
            fg=TEXT,
        ).pack(anchor="w", padx=25, pady=(25, 4))

        tk.Label(
            parent,
            text="Your latest BMI calculation appears here.",
            font=("Segoe UI", 9),
            bg=CARD,
            fg=MUTED,
        ).pack(anchor="w", padx=25, pady=(0, 25))

        self.result_card = tk.Frame(
            parent,
            bg=CARD_LIGHT,
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        self.result_card.pack(
            fill="x",
            padx=25,
        )

        tk.Label(
            self.result_card,
            text="BMI",
            font=("Segoe UI", 10, "bold"),
            bg=CARD_LIGHT,
            fg=MUTED,
        ).pack(pady=(25, 0))

        self.bmi_label = tk.Label(
            self.result_card,
            textvariable=self.bmi_value_var,
            font=("Segoe UI", 48, "bold"),
            bg=CARD_LIGHT,
            fg=ACCENT,
        )
        self.bmi_label.pack(pady=(0, 2))

        self.category_label = tk.Label(
            self.result_card,
            textvariable=self.category_var,
            font=("Segoe UI", 14, "bold"),
            bg=CARD_LIGHT,
            fg=MUTED,
        )
        self.category_label.pack(pady=(0, 25))

        # INFORMATION
        info = tk.Frame(parent, bg=CARD)
        info.pack(fill="x", padx=25, pady=25)

        tk.Label(
            info,
            text="BMI Categories",
            font=("Segoe UI", 11, "bold"),
            bg=CARD,
            fg=TEXT,
        ).pack(anchor="w", pady=(0, 12))

        categories = [
            ("Underweight", "< 18.5", ACCENT),
            ("Normal", "18.5 – 24.9", GREEN),
            ("Overweight", "25 – 29.9", YELLOW),
            ("Obese", "30+", RED),
        ]

        for name, range_text, color in categories:
            row = tk.Frame(info, bg=CARD)
            row.pack(fill="x", pady=4)

            indicator = tk.Frame(
                row,
                bg=color,
                width=8,
                height=8,
            )
            indicator.pack(side="left", padx=(0, 10))
            indicator.pack_propagate(False)

            tk.Label(
                row,
                text=name,
                font=("Segoe UI", 9),
                bg=CARD,
                fg=TEXT,
            ).pack(side="left")

            tk.Label(
                row,
                text=range_text,
                font=("Segoe UI", 9),
                bg=CARD,
                fg=MUTED,
            ).pack(side="right")

        # DEMO NOTE
        note = tk.Frame(
            parent,
            bg="#172033",
            highlightbackground=BORDER,
            highlightthickness=1,
        )
        note.pack(
            fill="x",
            padx=25,
            pady=(0, 25),
        )

        tk.Label(
            note,
            text="Tip",
            font=("Segoe UI", 10, "bold"),
            bg="#172033",
            fg=ACCENT,
        ).pack(anchor="w", padx=15, pady=(12, 2))

        tk.Label(
            note,
            text="Use the same user to build a BMI trend over time.",
            font=("Segoe UI", 9),
            bg="#172033",
            fg=MUTED,
        ).pack(anchor="w", padx=15, pady=(0, 12))

    # ========================================================
    # USER MANAGEMENT
    # ========================================================

    def _load_users(self):
        """Load saved users into the dropdown."""

        try:
            users = self.db.get_users()

            self.user_combo["values"] = users

            if users and not self.user_var.get():
                self.user_var.set(users[0])

        except DatabaseError as exc:
            messagebox.showerror(
                "Database Error",
                str(exc),
            )

    def new_user(self):
        """Clear the user field for a new user."""

        self.user_var.set("")
        self.user_combo.focus_set()

        self.status_var.set(
            "Enter a new user name, then calculate a BMI."
        )

    # ========================================================
    # BMI CALCULATION
    # ========================================================

    def calculate(self):
        """Validate input and calculate BMI."""

        user_name = self.user_var.get().strip()

        if not user_name:
            messagebox.showwarning(
                "User Required",
                "Please enter or select a user name.",
            )
            self.user_combo.focus_set()
            return

        try:
            weight = float(self.weight_var.get().strip())
            height = float(self.height_var.get().strip())

        except ValueError:
            messagebox.showerror(
                "Invalid Input",
                "Weight and height must contain numbers only.\n\n"
                "Example:\n"
                "Weight: 60\n"
                "Height: 1.65",
            )
            return

        try:
            bmi, category = calculate_bmi(
                weight,
                height,
            )

        except ValueError as exc:
            messagebox.showerror(
                "Invalid Measurement",
                str(exc),
            )
            return

        self.current_bmi = bmi
        self.current_category = category

        color = category_color(category)

        self.bmi_value_var.set(f"{bmi:.2f}")
        self.category_var.set(category)

        self.bmi_label.configure(fg=color)
        self.category_label.configure(fg=color)

        self.status_var.set(
            f"BMI calculated for {user_name}."
        )

    # ========================================================
    # SAVE RECORD
    # ========================================================

    def save_record(self):
        """Save current BMI result to SQLite."""

        user_name = self.user_var.get().strip()

        if not user_name:
            messagebox.showwarning(
                "User Required",
                "Please enter or select a user name first.",
            )
            return

        if self.current_bmi is None:
            messagebox.showwarning(
                "Calculate First",
                "Please calculate your BMI before saving.",
            )
            return

        try:
            weight = float(self.weight_var.get().strip())
            height = float(self.height_var.get().strip())

            self.db.save_bmi_record(
                user_name=user_name,
                weight=weight,
                height=height,
                bmi=self.current_bmi,
                category=self.current_category,
            )

            self._load_users()

            self.status_var.set(
                f"BMI record saved for {user_name}."
            )

            messagebox.showinfo(
                "Record Saved",
                f"BMI {self.current_bmi:.2f} was saved successfully.",
            )

        except ValueError:
            messagebox.showerror(
                "Invalid Input",
                "Please enter valid numeric weight and height.",
            )

        except DatabaseError as exc:
            messagebox.showerror(
                "Database Error",
                f"Could not save the BMI record.\n\n{exc}",
            )

    # ========================================================
    # HISTORY WINDOW
    # ========================================================

    def show_history(self):
        """Display BMI history for selected user."""

        user_name = self.user_var.get().strip()

        if not user_name:
            messagebox.showwarning(
                "User Required",
                "Please select or enter a user first.",
            )
            return

        try:
            records = self.db.get_user_history(user_name)

        except DatabaseError as exc:
            messagebox.showerror(
                "Database Error",
                str(exc),
            )
            return

        window = tk.Toplevel(self.root)
        window.title(f"BMI History • {user_name}")
        window.geometry("800x500")
        window.configure(bg=BG)

        tk.Label(
            window,
            text=f"{user_name}'s BMI History",
            font=("Segoe UI", 18, "bold"),
            bg=BG,
            fg=TEXT,
        ).pack(anchor="w", padx=25, pady=(20, 3))

        tk.Label(
            window,
            text=f"{len(records)} saved record(s)",
            font=("Segoe UI", 9),
            bg=BG,
            fg=MUTED,
        ).pack(anchor="w", padx=25, pady=(0, 15))

        table_frame = tk.Frame(window, bg=BG)
        table_frame.pack(
            fill="both",
            expand=True,
            padx=25,
            pady=(0, 20),
        )

        columns = (
            "date",
            "weight",
            "height",
            "bmi",
            "category",
        )

        tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
        )

        tree.heading("date", text="Date")
        tree.heading("weight", text="Weight (kg)")
        tree.heading("height", text="Height (m)")
        tree.heading("bmi", text="BMI")
        tree.heading("category", text="Category")

        tree.column("date", width=190)
        tree.column("weight", width=110, anchor="center")
        tree.column("height", width=110, anchor="center")
        tree.column("bmi", width=90, anchor="center")
        tree.column("category", width=140, anchor="center")

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=tree.yview,
        )

        tree.configure(yscrollcommand=scrollbar.set)

        tree.pack(
            side="left",
            fill="both",
            expand=True,
        )

        scrollbar.pack(
            side="right",
            fill="y",
        )

        for record in records:
            timestamp = record["recorded_at"]

            try:
                date_display = datetime.fromisoformat(
                    timestamp
                ).strftime("%d %b %Y, %I:%M %p")
            except ValueError:
                date_display = timestamp

            tree.insert(
                "",
                "end",
                values=(
                    date_display,
                    f"{record['weight']:.2f}",
                    f"{record['height']:.2f}",
                    f"{record['bmi']:.2f}",
                    record["category"],
                ),
            )

        if not records:
            tk.Label(
                window,
                text="No BMI records found for this user yet.",
                font=("Segoe UI", 10),
                bg=BG,
                fg=MUTED,
            ).pack(pady=(0, 20))

    # ========================================================
    # TREND GRAPH
    # ========================================================

    def show_trend(self):
        """Display BMI trend chart using Matplotlib."""

        user_name = self.user_var.get().strip()

        if not user_name:
            messagebox.showwarning(
                "User Required",
                "Please select or enter a user first.",
            )
            return

        try:
            records = self.db.get_user_trend(user_name)

        except DatabaseError as exc:
            messagebox.showerror(
                "Database Error",
                str(exc),
            )
            return

        if not records:
            messagebox.showinfo(
                "No Trend Data",
                "Save at least one BMI record to view the trend.",
            )
            return

        window = tk.Toplevel(self.root)
        window.title(f"BMI Trend • {user_name}")
        window.geometry("900x600")
        window.configure(bg=BG)

        tk.Label(
            window,
            text=f"{user_name}'s BMI Trend",
            font=("Segoe UI", 18, "bold"),
            bg=BG,
            fg=TEXT,
        ).pack(anchor="w", padx=25, pady=(20, 0))

        tk.Label(
            window,
            text="BMI measurements over time",
            font=("Segoe UI", 9),
            bg=BG,
            fg=MUTED,
        ).pack(anchor="w", padx=25, pady=(2, 10))

        figure = Figure(
            figsize=(8.5, 5),
            dpi=100,
        )

        axis = figure.add_subplot(111)

        dates = []
        bmi_values = []

        for record in records:
            try:
                date = datetime.fromisoformat(
                    record["recorded_at"]
                )
            except ValueError:
                continue

            dates.append(date)
            bmi_values.append(record["bmi"])

        if not bmi_values:
            window.destroy()

            messagebox.showerror(
                "Graph Error",
                "The saved date information could not be read.",
            )
            return

        axis.plot(
            dates,
            bmi_values,
            marker="o",
            linewidth=2.5,
            markersize=7,
        )

        axis.axhspan(
            18.5,
            25,
            alpha=0.08,
        )

        axis.axhline(
            18.5,
            linestyle="--",
            linewidth=1,
        )

        axis.axhline(
            25,
            linestyle="--",
            linewidth=1,
        )

        axis.axhline(
            30,
            linestyle="--",
            linewidth=1,
        )

        axis.set_title(
            "BMI Progress",
            fontsize=14,
            fontweight="bold",
        )

        axis.set_xlabel("Date")
        axis.set_ylabel("BMI")

        axis.grid(
            True,
            alpha=0.2,
        )

        figure.autofmt_xdate()

        canvas = FigureCanvasTkAgg(
            figure,
            master=window,
        )

        canvas.draw()

        canvas.get_tk_widget().pack(
            fill="both",
            expand=True,
            padx=20,
            pady=(0, 20),
        )


# ============================================================
# APPLICATION START
# ============================================================

def main():
    """Start the BMI Tracker application."""

    try:
        root = tk.Tk()
        BMIApp(root)
        root.mainloop()

    except DatabaseError as exc:
        messagebox.showerror(
            "Database Error",
            str(exc),
        )


if __name__ == "__main__":
    main()
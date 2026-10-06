import tkinter as tk
from tkinter import ttk, messagebox
import secrets
import string
import pyperclip

class PasswordGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Password Generator - Task 3")
        self.root.geometry("520x650")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")

        # History list (max 5)
        self.history = []

        # Title
        title = tk.Label(
            root, text="🔐 Advanced Password Generator",
            font=("Segoe UI", 18, "bold"),
            bg="#1e1e2e", fg="#cdd6f4"
        )
        title.pack(pady=15)

        # ===== Length Control =====
        length_frame = tk.Frame(root, bg="#1e1e2e")
        length_frame.pack(pady=5, fill="x", padx=30)

        tk.Label(
            length_frame, text="Password Length:",
            font=("Segoe UI", 11), bg="#1e1e2e", fg="#cdd6f4"
        ).pack(side="left")

        self.length_var = tk.IntVar(value=16)
        self.length_spin = tk.Spinbox(
            length_frame, from_=8, to=64,
            textvariable=self.length_var, width=5,
            font=("Segoe UI", 11),
            command=self.update_strength
        )
        self.length_spin.pack(side="left", padx=10)

        self.length_slider = tk.Scale(
            length_frame, from_=8, to=64, orient="horizontal",
            variable=self.length_var, length=200,
            bg="#1e1e2e", fg="#cdd6f4", highlightthickness=0,
            troughcolor="#313244", activebackground="#89b4fa",
            command=lambda v: self.update_strength()
        )
        self.length_slider.pack(side="left", padx=5)

        # ===== Character Types =====
        types_frame = tk.LabelFrame(
            root, text=" Character Types (select at least 2) ",
            font=("Segoe UI", 10, "bold"),
            bg="#1e1e2e", fg="#89b4fa", padx=15, pady=10
        )
        types_frame.pack(pady=10, fill="x", padx=30)

        self.upper_var = tk.BooleanVar(value=True)
        self.lower_var = tk.BooleanVar(value=True)
        self.digits_var = tk.BooleanVar(value=True)
        self.symbols_var = tk.BooleanVar(value=True)
        self.exclude_ambig_var = tk.BooleanVar(value=False)

        tk.Checkbutton(
            types_frame, text="Uppercase (A-Z)", variable=self.upper_var,
            bg="#1e1e2e", fg="#cdd6f4", selectcolor="#313244",
            activebackground="#1e1e2e", activeforeground="#cdd6f4",
            font=("Segoe UI", 10), command=self.update_strength
        ).grid(row=0, column=0, sticky="w", pady=2)

        tk.Checkbutton(
            types_frame, text="Lowercase (a-z)", variable=self.lower_var,
            bg="#1e1e2e", fg="#cdd6f4", selectcolor="#313244",
            activebackground="#1e1e2e", activeforeground="#cdd6f4",
            font=("Segoe UI", 10), command=self.update_strength
        ).grid(row=0, column=1, sticky="w", pady=2)

        tk.Checkbutton(
            types_frame, text="Numbers (0-9)", variable=self.digits_var,
            bg="#1e1e2e", fg="#cdd6f4", selectcolor="#313244",
            activebackground="#1e1e2e", activeforeground="#cdd6f4",
            font=("Segoe UI", 10), command=self.update_strength
        ).grid(row=1, column=0, sticky="w", pady=2)

        tk.Checkbutton(
            types_frame, text="Symbols (!@#$...)", variable=self.symbols_var,
            bg="#1e1e2e", fg="#cdd6f4", selectcolor="#313244",
            activebackground="#1e1e2e", activeforeground="#cdd6f4",
            font=("Segoe UI", 10), command=self.update_strength
        ).grid(row=1, column=1, sticky="w", pady=2)

        tk.Checkbutton(
            types_frame, text="Exclude Ambiguous (0 O l 1 I)",
            variable=self.exclude_ambig_var,
            bg="#1e1e2e", fg="#f9e2af", selectcolor="#313244",
            activebackground="#1e1e2e", activeforeground="#f9e2af",
            font=("Segoe UI", 10), command=self.update_strength
        ).grid(row=2, column=0, columnspan=2, sticky="w", pady=5)

        # ===== Strength Indicator =====
        strength_frame = tk.Frame(root, bg="#1e1e2e")
        strength_frame.pack(pady=8, fill="x", padx=30)

        tk.Label(
            strength_frame, text="Strength:",
            font=("Segoe UI", 11), bg="#1e1e2e", fg="#cdd6f4"
        ).pack(side="left")

        self.strength_label = tk.Label(
            strength_frame, text="Strong",
            font=("Segoe UI", 11, "bold"),
            bg="#1e1e2e", fg="#a6e3a1"
        )
        self.strength_label.pack(side="left", padx=10)

        self.strength_bar = ttk.Progressbar(
            strength_frame, length=250, mode="determinate"
        )
        self.strength_bar.pack(side="left", padx=5)
        self.strength_bar["value"] = 90

        # ===== Generate Button =====
        self.generate_btn = tk.Button(
            root, text="⚡ Generate Password",
            font=("Segoe UI", 12, "bold"),
            bg="#89b4fa", fg="#1e1e2e",
            activebackground="#74c7ec",
            relief="flat", padx=20, pady=8,
            cursor="hand2",
            command=self.generate_password
        )
        self.generate_btn.pack(pady=12)

        # ===== Password Display =====
        self.password_var = tk.StringVar()
        self.password_entry = tk.Entry(
            root, textvariable=self.password_var,
            font=("Consolas", 14), width=36,
            justify="center", bd=0,
            bg="#313244", fg="#cdd6f4",
            insertbackground="#cdd6f4"
        )
        self.password_entry.pack(pady=5)

        # ===== Copy Button =====
        self.copy_btn = tk.Button(
            root, text="📋 Copy to Clipboard",
            font=("Segoe UI", 10),
            bg="#a6e3a1", fg="#1e1e2e",
            activebackground="#94e2d5",
            relief="flat", padx=15, pady=5,
            cursor="hand2",
            command=self.copy_to_clipboard
        )
        self.copy_btn.pack(pady=5)

        # ===== History =====
        history_frame = tk.LabelFrame(
            root, text=" Last 5 Generated Passwords ",
            font=("Segoe UI", 10, "bold"),
            bg="#1e1e2e", fg="#89b4fa", padx=10, pady=5
        )
        history_frame.pack(pady=10, fill="both", expand=True, padx=30)

        self.history_listbox = tk.Listbox(
            history_frame, height=5,
            font=("Consolas", 10),
            bg="#313244", fg="#cdd6f4",
            selectbackground="#89b4fa",
            bd=0, highlightthickness=0
        )
        self.history_listbox.pack(fill="both", expand=True, pady=5)

        # Initial strength update
        self.update_strength()

    def get_charset(self):
        """Build character set based on selected options"""
        chars = ""
        if self.upper_var.get():
            chars += string.ascii_uppercase
        if self.lower_var.get():
            chars += string.ascii_lowercase
        if self.digits_var.get():
            chars += string.digits
        if self.symbols_var.get():
            chars += "!@#$%^&*()-_=+[]{}|;:,.<>?/"

        if self.exclude_ambig_var.get():
            # Remove ambiguous characters
            ambiguous = "0Ool1I"
            chars = "".join(c for c in chars if c not in ambiguous)

        return chars

    def update_strength(self, *args):
        """Update strength label and progress bar"""
        length = self.length_var.get()
        types_count = sum([
            self.upper_var.get(),
            self.lower_var.get(),
            self.digits_var.get(),
            self.symbols_var.get()
        ])

        score = 0
        if length >= 8:
            score += 20
        if length >= 12:
            score += 20
        if length >= 16:
            score += 20
        if types_count >= 2:
            score += 15
        if types_count >= 3:
            score += 15
        if types_count == 4:
            score += 10

        self.strength_bar["value"] = score

        if score < 40:
            self.strength_label.config(text="Weak", fg="#f38ba8")
        elif score < 70:
            self.strength_label.config(text="Medium", fg="#f9e2af")
        else:
            self.strength_label.config(text="Strong", fg="#a6e3a1")

    def generate_password(self):
        """Generate a secure password that includes at least one of each selected type"""
        length = self.length_var.get()
        if length < 8:
            messagebox.showerror("Error", "Password length must be at least 8 characters!")
            return

        selected_types = []
        if self.upper_var.get():
            selected_types.append(string.ascii_uppercase)
        if self.lower_var.get():
            selected_types.append(string.ascii_lowercase)
        if self.digits_var.get():
            selected_types.append(string.digits)
        if self.symbols_var.get():
            selected_types.append("!@#$%^&*()-_=+[]{}|;:,.<>?/")

        if len(selected_types) < 2:
            messagebox.showerror("Error", "Please select at least 2 character types!")
            return

        charset = self.get_charset()
        if not charset:
            messagebox.showerror("Error", "No characters available after exclusions!")
            return

        # Guarantee at least one character from each selected type
        password_chars = []
        for char_set in selected_types:
            # Apply ambiguous exclusion if needed
            if self.exclude_ambig_var.get():
                char_set = "".join(c for c in char_set if c not in "0Ool1I")
            if char_set:
                password_chars.append(secrets.choice(char_set))

        # Fill the rest randomly
        remaining = length - len(password_chars)
        for _ in range(remaining):
            password_chars.append(secrets.choice(charset))

        # Shuffle securely
        secrets.SystemRandom().shuffle(password_chars)
        password = "".join(password_chars)

        self.password_var.set(password)

        # Auto copy to clipboard
        try:
            pyperclip.copy(password)
        except Exception:
            pass  # clipboard may fail in some environments

        # Add to history (keep last 5)
        self.history.insert(0, password)
        if len(self.history) > 5:
            self.history.pop()

        self.history_listbox.delete(0, tk.END)
        for pwd in self.history:
            self.history_listbox.insert(tk.END, pwd)

        self.update_strength()

    def copy_to_clipboard(self):
        password = self.password_var.get()
        if password:
            try:
                pyperclip.copy(password)
                messagebox.showinfo("Copied", "Password copied to clipboard!")
            except Exception:
                messagebox.showerror("Error", "Could not copy to clipboard.")
        else:
            messagebox.showwarning("Warning", "No password generated yet!")

if __name__ == "__main__":
    root = tk.Tk()
    app = PasswordGeneratorApp(root)
    root.mainloop()
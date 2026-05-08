import tkinter as tk
from tkinter import messagebox
from frontend.theme import *
from services.auth import login


class LoginPage(tk.Frame):
    def __init__(self, master, on_login_success):
        super().__init__(master, bg=BG)
        self.master = master
        self.on_login_success = on_login_success
        self.password_visible = False
        self.build()

    def build(self):
        self.pack(fill="both", expand=True)

        wrapper = tk.Frame(self, bg=BG)
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        shell = tk.Frame(
            wrapper,
            bg=CARD,
            highlightthickness=1,
            highlightbackground=BORDER
        )
        shell.pack()

        brand = tk.Frame(shell, bg=ACCENT, width=280, height=430)
        brand.pack(side="left", fill="both")
        brand.pack_propagate(False)

        logo = tk.Frame(brand, bg="white", width=62, height=62)
        logo.pack(anchor="w", padx=32, pady=(42, 20))
        logo.pack_propagate(False)

        tk.Label(
            logo,
            text="EF",
            bg="white",
            fg=ACCENT,
            font=("Segoe UI", 20, "bold")
        ).pack(expand=True)

        tk.Label(
            brand,
            text="ExpenseFlow",
            bg=ACCENT,
            fg="white",
            font=("Segoe UI", 24, "bold")
        ).pack(anchor="w", padx=32)

        tk.Label(
            brand,
            text="A secure expense approval\nand budget control system.",
            bg=ACCENT,
            fg="white",
            font=FONT_NORMAL,
            justify="left"
        ).pack(anchor="w", padx=32, pady=(12, 24))

        for text in [
            "✓ Submit expense claims",
            "✓ Attach digital receipts",
            "✓ Track approval status",
            "✓ Department budget visibility"
        ]:
            tk.Label(
                brand,
                text=text,
                bg=ACCENT,
                fg="white",
                font=FONT_NORMAL,
                justify="left"
            ).pack(anchor="w", padx=32, pady=4)

        tk.Label(
            brand,
            text="Secure access portal",
            bg=ACCENT,
            fg="white",
            font=FONT_LABEL
        ).pack(anchor="sw", padx=32, pady=(45, 22))

        card = tk.Frame(shell, bg=CARD, padx=42, pady=38, width=390, height=430)
        card.pack(side="left", fill="both")
        card.pack_propagate(False)

        tk.Label(
            card,
            text="Welcome back",
            bg=CARD,
            fg=TEXT,
            font=("Segoe UI", 24, "bold")
        ).pack(anchor="w")

        tk.Label(
            card,
            text="Sign in to your account",
            bg=CARD,
            fg=TEXT_MUTED,
            font=FONT_NORMAL
        ).pack(anchor="w", pady=(4, 28))

        tk.Label(
            card,
            text="EMAIL ADDRESS",
            bg=CARD,
            fg=TEXT_MUTED,
            font=FONT_LABEL
        ).pack(anchor="w")

        email_frame = tk.Frame(
            card,
            bg=INPUT,
            highlightthickness=1,
            highlightbackground=BORDER
        )
        email_frame.pack(fill="x", pady=(5, 16))

        self.email_entry = tk.Entry(
            email_frame,
            bg=INPUT,
            fg=TEXT,
            font=FONT_NORMAL,
            width=34,
            relief="flat",
            bd=0,
            insertbackground=ACCENT
        )
        self.email_entry.pack(fill="x", padx=12, pady=10)

        tk.Label(
            card,
            text="PASSWORD",
            bg=CARD,
            fg=TEXT_MUTED,
            font=FONT_LABEL
        ).pack(anchor="w")

        pass_frame = tk.Frame(
            card,
            bg=INPUT,
            highlightthickness=1,
            highlightbackground=BORDER
        )
        pass_frame.pack(fill="x", pady=(5, 24))

        self.pass_entry = tk.Entry(
            pass_frame,
            bg=INPUT,
            fg=TEXT,
            font=FONT_NORMAL,
            relief="flat",
            bd=0,
            insertbackground=ACCENT,
            show="●"
        )
        self.pass_entry.pack(side="left", fill="x", expand=True, padx=(12, 4), pady=10)

        self.eye_btn = tk.Button(
            pass_frame,
            text="👁",
            command=self.toggle_password,
            bg=INPUT,
            fg=TEXT_MUTED,
            font=("Segoe UI", 11),
            relief="flat",
            bd=0,
            cursor="hand2",
            activebackground=INPUT,
            activeforeground=ACCENT,
            padx=8
        )
        self.eye_btn.pack(side="right", padx=(0, 10))

        tk.Button(
            card,
            text="Sign in",
            command=self.handle_login,
            bg=ACCENT,
            fg="white",
            font=FONT_BUTTON,
            relief="flat",
            bd=0,
            cursor="hand2",
            pady=12,
            activebackground=ACCENT_DARK,
            activeforeground="white"
        ).pack(fill="x")

        tk.Label(
            card,
            text="Use your company email and password to continue.",
            bg=CARD,
            fg=TEXT_MUTED,
            font=FONT_NORMAL
        ).pack(anchor="w", pady=(18, 0))

        self.email_entry.bind("<Return>", lambda e: self.handle_login())
        self.pass_entry.bind("<Return>", lambda e: self.handle_login())
        self.email_entry.focus_set()

    def toggle_password(self):
        self.password_visible = not self.password_visible

        if self.password_visible:
            self.pass_entry.config(show="")
            self.eye_btn.config(text="🙈", fg=ACCENT)
        else:
            self.pass_entry.config(show="●")
            self.eye_btn.config(text="👁", fg=TEXT_MUTED)

    def handle_login(self):
        email = self.email_entry.get().strip()
        password = self.pass_entry.get().strip()

        if not email or not password:
            messagebox.showerror("Missing Fields", "Please enter email and password.")
            return

        result = login(email, password)

        if result:
            self.on_login_success(result)
        else:
            messagebox.showerror("Login Failed", "Invalid email or password.")
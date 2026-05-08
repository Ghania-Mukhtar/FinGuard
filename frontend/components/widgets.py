import tkinter as tk
from tkinter import ttk
from frontend.theme import *


class ModernUI:
    def action_btn(self, parent, text, cmd, color=ACCENT):
        return tk.Button(
            parent,
            text=text,
            command=cmd,
            bg=color,
            fg="white",
            font=FONT_BUTTON,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=8,
            bd=0,
            activebackground=ACCENT_DARK,
            activeforeground="white"
        )

    def light_btn(self, parent, text, cmd):
        return tk.Button(
            parent,
            text=text,
            command=cmd,
            bg=BG_SOFT,
            fg=TEXT,
            font=FONT_BUTTON,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=8,
            bd=0,
            activebackground=HOVER,
            activeforeground=TEXT
        )

    def field(self, parent, label, secret=False, width=34):
        tk.Label(
            parent,
            text=label.upper(),
            bg=CARD,
            fg=TEXT_MUTED,
            font=FONT_LABEL
        ).pack(anchor="w", pady=(10, 4))

        frame = tk.Frame(
            parent,
            bg=INPUT,
            highlightthickness=1,
            highlightbackground=BORDER
        )
        frame.pack(fill="x")

        entry = tk.Entry(
            frame,
            bg=INPUT,
            fg=TEXT,
            font=FONT_NORMAL,
            width=width,
            relief="flat",
            bd=0,
            insertbackground=ACCENT,
            show="●" if secret else ""
        )
        entry.pack(fill="x", padx=10, pady=9)
        return entry

    def page_title(self, parent, title, sub=""):
        tk.Label(
            parent,
            text=title,
            bg=BG,
            fg=TEXT,
            font=FONT_TITLE
        ).pack(anchor="w")

        if sub:
            tk.Label(
                parent,
                text=sub,
                bg=BG,
                fg=TEXT_MUTED,
                font=FONT_NORMAL
            ).pack(anchor="w", pady=(3, 18))
        else:
            tk.Frame(parent, bg=BG, height=18).pack()

    def stat_card(self, parent, label, value, color=ACCENT):
        card = tk.Frame(
            parent,
            bg=CARD,
            padx=18,
            pady=16,
            highlightthickness=1,
            highlightbackground=BORDER
        )
        card.pack(side="left", fill="both", expand=True, padx=(0, 12))

        tk.Label(
            card,
            text=str(value),
            bg=CARD,
            fg=color,
            font=FONT_BIG
        ).pack(anchor="w")

        tk.Label(
            card,
            text=label,
            bg=CARD,
            fg=TEXT_MUTED,
            font=FONT_SMALL
        ).pack(anchor="w", pady=(4, 0))

        return card

    def style_tree(self, tag="Modern"):
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            f"{tag}.Treeview",
            background=CARD,
            foreground=TEXT,
            fieldbackground=CARD,
            rowheight=32,
            font=FONT_NORMAL,
            borderwidth=0
        )

        style.configure(
            f"{tag}.Treeview.Heading",
            background=BG_SOFT,
            foreground=TEXT_MUTED,
            font=FONT_LABEL,
            relief="flat"
        )

        style.map(
            f"{tag}.Treeview",
            background=[("selected", "#dbeafe")],
            foreground=[("selected", TEXT)]
        )

    def make_tree(self, parent, cols, data, height=10, tag="Modern"):
        self.style_tree(tag)

        outer = tk.Frame(
            parent,
            bg=CARD,
            highlightthickness=1,
            highlightbackground=BORDER
        )
        outer.pack(fill="both", expand=True)

        tree = ttk.Treeview(
            outer,
            columns=cols,
            show="headings",
            height=height,
            style=f"{tag}.Treeview"
        )

        scroll = ttk.Scrollbar(
            outer,
            orient="vertical",
            command=tree.yview
        )
        tree.configure(yscrollcommand=scroll.set)

        for col in cols:
            tree.heading(col, text=col.upper())
            tree.column(col, width=130, anchor="center", minwidth=80)

        for row in data:
            tree.insert("", "end", values=row)

        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        return tree

    def clear_content(self):
        for widget in self.content.winfo_children():
            widget.destroy()

    def toggle_sidebar(self):
        if self.sidebar_visible:
            self.sidebar.pack_forget()
            self.sidebar_visible = False
        else:
            self.sidebar.pack(side="left", fill="y", before=self.content)
            self.sidebar_visible = True

    def build_shell(self, title, role_name, sign_out_color=DANGER):
        self.pack(fill="both", expand=True)

        self.sidebar_visible = False

        top = tk.Frame(self, bg=BG, height=58)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Button(
            top,
            text="⋮",
            command=self.toggle_sidebar,
            bg=BG,
            fg=TEXT,
            font=("Segoe UI", 20, "bold"),
            relief="flat",
            bd=0,
            cursor="hand2"
        ).pack(side="left", padx=(16, 8))

        tk.Label(
            top,
            text=title,
            bg=BG,
            fg=TEXT,
            font=FONT_HEADING
        ).pack(side="left")

        right = tk.Frame(top, bg=BG)
        right.pack(side="right", padx=16)

        tk.Label(
            right,
            text=self.session.get("user_name", ""),
            bg=BG,
            fg=TEXT,
            font=FONT_SUBHEAD
        ).pack(side="left", padx=10)

        tk.Label(
            right,
            text=role_name.upper(),
            bg=WARNING,
            fg=TEXT_MUTED,
            font=FONT_LABEL,
            padx=8,
            pady=4
        ).pack(side="left", padx=8)

        self.action_btn(right, "Sign out", self.on_logout, sign_out_color).pack(side="left")

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x")

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(
            body,
            bg=SIDEBAR,
            width=230,
            highlightthickness=1,
            highlightbackground=BORDER
        )
        self.sidebar.pack_propagate(False)

        self.content = tk.Frame(body, bg=BG, padx=26, pady=22)
        self.content.pack(side="left", fill="both", expand=True)

    def sidebar_title(self, text):
        tk.Label(
            self.sidebar,
            text=text.upper(),
            bg=SIDEBAR,
            fg=TEXT_MUTED,
            font=FONT_LABEL
        ).pack(anchor="w", padx=18, pady=(18, 6))

    def sidebar_button(self, text, command):
        btn = tk.Button(
            self.sidebar,
            text=text,
            command=lambda: [command(), self.toggle_sidebar()],
            bg=SIDEBAR,
            fg=TEXT,
            font=FONT_NORMAL,
            relief="flat",
            bd=0,
            cursor="hand2",
            anchor="w",
            padx=18,
            pady=10,
            activebackground=HOVER,
            activeforeground=TEXT
        )
        btn.pack(fill="x")
        return btn
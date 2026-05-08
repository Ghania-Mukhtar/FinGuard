import tkinter as tk
from tkinter import messagebox, filedialog
from frontend.theme import *
from frontend.components.widgets import ModernUI
from frontend.components.image_viewer import ImageViewer

from services.employee import (
    submit_claim,
    get_my_claims,
    get_categories,
    get_claim_image
)


class EmployeeDashboard(tk.Frame, ModernUI):
    def __init__(self, master, session, on_logout):
        super().__init__(master, bg=BG)
        self.master = master
        self.session = session
        self.on_logout = on_logout
        self.selected_file_path = None
        self.build()

    def build(self):
        self.build_shell("ExpenseFlow", "Employee")

        self.sidebar_title("Overview")
        self.sidebar_button("Dashboard", self.show_dashboard)

        self.sidebar_title("Expenses")
        self.sidebar_button("Submit Claim", self.show_submit_claim)
        self.sidebar_button("My Claims", self.show_my_claims)

        self.show_dashboard()

    # ───────────────── DASHBOARD ─────────────────

    def show_dashboard(self):
        self.clear_content()
        self.page_title(self.content, "Employee Dashboard", "Your personal expense overview")

        claims = get_my_claims(self.session["user_id"])

        total = len(claims)
        pending = 0
        approved = 0
        rejected = 0
        under_review = 0

        total_amount = 0
        pending_amount = 0
        approved_amount = 0

        for claim in claims:
            try:
                amount = float(claim[3])
            except:
                amount = 0

            status = str(claim[4]).strip().lower().replace("_", " ")

            total_amount += amount

            if status == "pending":
                pending += 1
                pending_amount += amount
            elif status == "approved":
                approved += 1
                approved_amount += amount
            elif status == "rejected":
                rejected += 1
            elif "review" in status:
                under_review += 1
                pending_amount += amount

        approval_rate = (approved / total * 100) if total > 0 else 0

        if total == 0:
            performance = "No Claims Yet"
            performance_color = ACCENT
            insight = "Submit your first claim with a clear receipt and correct category."
        elif approval_rate >= 70:
            performance = "Strong"
            performance_color = SUCCESS
            insight = "Most of your claims are approved. Keep submitting clean receipts."
        elif approval_rate >= 40:
            performance = "Average"
            performance_color = ORANGE
            insight = "Some claims are rejected. Check receipt clarity and category before submitting."
        else:
            performance = "Needs Attention"
            performance_color = DANGER
            insight = "Many claims are not approved. Review rejected claims before submitting again."

        # ───────────── HERO SECTION ─────────────

        hero = tk.Frame(
            self.content,
            bg=CARD,
            padx=18,
            pady=14,
            highlightthickness=1,
            highlightbackground=BORDER
        )
        hero.pack(fill="x", pady=(0, 14))

        tk.Label(
            hero,
            text=f"Claim Performance: {performance}",
            bg=CARD,
            fg=performance_color,
            font=FONT_HEADING
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(
            hero,
            text=f"Approval Rate: {approval_rate:.1f}%  |  Approved Amount: PKR {approved_amount:,.0f}",
            bg=CARD,
            fg=TEXT_MUTED,
            font=FONT_NORMAL
        ).pack(anchor="w", pady=(0, 8))

        bar_bg = tk.Frame(hero, bg=BG_SOFT, height=14)
        bar_bg.pack(fill="x")
        bar_bg.pack_propagate(False)

        bar_fill = tk.Frame(bar_bg, bg=performance_color)
        bar_fill.place(
            relx=0,
            rely=0,
            relwidth=max(min(approval_rate / 100, 1), 0.01),
            relheight=1
        )

        tk.Label(
            hero,
            text=insight,
            bg=CARD,
            fg=TEXT_MUTED,
            font=FONT_NORMAL,
            wraplength=900,
            justify="left"
        ).pack(anchor="w", pady=(8, 0))

        # ───────────── CLAIM STATUS ─────────────

        row = tk.Frame(self.content, bg=BG)
        row.pack(fill="x", pady=(0, 14))

        self.stat_card(row, "Total Claims", total, ACCENT)
        self.stat_card(row, "Pending", pending, WARNING)
        self.stat_card(row, "Approved", approved, SUCCESS)
        self.stat_card(row, "Rejected", rejected, DANGER)

        if row.winfo_children():
            row.winfo_children()[-1].pack_configure(padx=0)

        # ───────────── AMOUNT SUMMARY ─────────────

        row2 = tk.Frame(self.content, bg=BG)
        row2.pack(fill="x", pady=(0, 14))

        self.stat_card(row2, "Total Submitted", f"PKR {total_amount:,.0f}", ACCENT)
        self.stat_card(row2, "Approved Amount", f"PKR {approved_amount:,.0f}", SUCCESS)
        self.stat_card(row2, "Pending Amount", f"PKR {pending_amount:,.0f}", WARNING)
        self.stat_card(row2, "Under Review", under_review, PURPLE)

        if row2.winfo_children():
            row2.winfo_children()[-1].pack_configure(padx=0)

    # ───────────────── SUBMIT CLAIM ─────────────────

    def show_submit_claim(self):
        self.clear_content()
        self.selected_file_path = None

        self.page_title(self.content, "Submit Claim", "Submit a new expense for manager approval")

        card = tk.Frame(
            self.content,
            bg=CARD,
            padx=28,
            pady=24,
            highlightthickness=1,
            highlightbackground=BORDER
        )
        card.pack(anchor="w")

        amount_e = self.field(card, "Amount (PKR)")

        cats = get_categories()
        cat_names = [c[1] for c in cats]
        cat_var = tk.StringVar(value=cat_names[0] if cat_names else "")

        tk.Label(
            card,
            text="CATEGORY",
            bg=CARD,
            fg=TEXT_MUTED,
            font=FONT_LABEL
        ).pack(anchor="w", pady=(12, 6))

        cat_menu = tk.OptionMenu(card, cat_var, *cat_names)
        cat_menu.pack(fill="x")

        tk.Label(
            card,
            text="RECEIPT",
            bg=CARD,
            fg=TEXT_MUTED,
            font=FONT_LABEL
        ).pack(anchor="w", pady=(14, 6))

        file_lbl = tk.Label(
            card,
            text="No file selected",
            bg=CARD,
            fg=TEXT_MUTED,
            font=FONT_NORMAL
        )
        file_lbl.pack(anchor="w", pady=(0, 10))

        def browse():
            path = filedialog.askopenfilename(
                title="Select Receipt",
                filetypes=[
                    ("Images", "*.png *.jpg *.jpeg *.gif *.bmp"),
                    ("PDF Files", "*.pdf"),
                    ("All Files", "*.*")
                ]
            )

            if path:
                self.selected_file_path = path
                file_lbl.config(
                    text=path.split("/")[-1].split("\\")[-1],
                    fg=TEXT
                )

        self.action_btn(card, "Browse Receipt", browse, PURPLE).pack(fill="x")

        def submit():
            amount = amount_e.get().strip()
            category = cat_var.get()

            if not amount:
                messagebox.showerror("Error", "Enter amount.")
                return

            if not self.selected_file_path:
                messagebox.showerror("Error", "Please browse and select receipt.")
                return

            try:
                with open(self.selected_file_path, "rb") as f:
                    img = f.read()

                filename = self.selected_file_path.split("/")[-1].split("\\")[-1]

                if submit_claim(
                    self.session["user_id"],
                    self.session["dep_id"],
                    float(amount),
                    category,
                    filename,
                    img
                ):
                    messagebox.showinfo("Submitted", "Claim submitted successfully.")
                    self.selected_file_path = None
                    self.show_submit_claim()
                else:
                    messagebox.showerror("Error", "Claim submission failed.")

            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        tk.Frame(card, bg=CARD, height=16).pack()
        self.action_btn(card, "Submit Claim", submit, SUCCESS).pack(fill="x")

    # ───────────────── MY CLAIMS ─────────────────

    def show_my_claims(self):
        self.clear_content()
        self.page_title(self.content, "My Claims", "Track your submitted expenses")

        claims = get_my_claims(self.session["user_id"])

        filter_row = tk.Frame(self.content, bg=BG)
        filter_row.pack(fill="x", pady=(0, 12))

        total = len(claims)
        pending = sum(1 for r in claims if str(r[4]).lower() == "pending")
        approved = sum(1 for r in claims if str(r[4]).lower() == "approved")
        rejected = sum(1 for r in claims if str(r[4]).lower() == "rejected")
        review = sum(1 for r in claims if "review" in str(r[4]).lower())

        self.light_btn(filter_row, f"All ({total})", self.show_my_claims).pack(side="left", padx=(0, 8))
        self.light_btn(filter_row, f"Pending ({pending})", self.show_my_claims).pack(side="left", padx=(0, 8))
        self.light_btn(filter_row, f"Approved ({approved})", self.show_my_claims).pack(side="left", padx=(0, 8))
        self.light_btn(filter_row, f"Rejected ({rejected})", self.show_my_claims).pack(side="left", padx=(0, 8))
        self.light_btn(filter_row, f"Under Review ({review})", self.show_my_claims).pack(side="left")

        cols = ("ID", "User ID", "Category", "Amount", "Status", "Date", "Receipt")

        tree = self.make_tree(
            self.content,
            cols,
            claims,
            height=12,
            tag="EmployeeClaims"
        )

        btns = tk.Frame(self.content, bg=BG)
        btns.pack(fill="x", pady=12)

        def selected_id():
            sel = tree.selection()

            if not sel:
                messagebox.showerror("Error", "Select a claim first.")
                return None

            return tree.item(sel[0])["values"][0]

        def view_receipt():
            cid = selected_id()

            if not cid:
                return

            result = get_claim_image(cid)

            if result and result[0]:
                ImageViewer(self.master, result[0], f"Receipt — Claim #{cid}")
            else:
                messagebox.showinfo("No Image", "No receipt found for this claim.")

        self.action_btn(btns, "View Receipt", view_receipt, ACCENT).pack(side="left", padx=(0, 6))
        self.light_btn(btns, "Refresh", self.show_my_claims).pack(side="left")
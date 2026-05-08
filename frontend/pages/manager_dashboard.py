import tkinter as tk
from tkinter import messagebox, filedialog
from frontend.theme import *
from frontend.components.widgets import ModernUI
from frontend.components.image_viewer import ImageViewer

from services.manager import (
    get_department_claims, get_pending_count,
    set_under_review, approve_expense,
    get_budget_summary, submit_claim,
    get_my_claims, get_claim_image
)
from services.employee import get_categories


class ManagerDashboard(tk.Frame, ModernUI):
    def __init__(self, master, session, on_logout):
        super().__init__(master, bg=BG)
        self.master = master
        self.session = session
        self.on_logout = on_logout
        self.selected_file_path = None
        self.build()

    def build(self):
        self.build_shell("ExpenseFlow", "Manager")

        self.sidebar_title("Overview")
        self.sidebar_button("Dashboard", self.show_dashboard)
        self.sidebar_button("Employee Claims", self.show_employee_claims)
        self.sidebar_button("My Claims", self.show_my_claims)

        self.sidebar_title("Actions")
        self.sidebar_button("Submit Claim", self.show_submit_claim)
        self.sidebar_button("Budget Summary", self.show_budget_summary)

        self.show_dashboard()

    def show_dashboard(self):
        self.clear_content()
        self.page_title(self.content, "Manager Dashboard", "Department control center")

        data = get_budget_summary(self.session["dep_id"])
        claims = get_department_claims(self.session["dep_id"])
        pending = get_pending_count(self.session["dep_id"])

        budget_limit = 0
        remaining = 0
        total_spent = 0
        dept_name = "-"
        dept_id = self.session["dep_id"]

        if data:
            dept_id = data[0]
            dept_name = data[1]
            budget_limit = float(data[2])
            remaining = float(data[3])
            total_spent = float(data[4])

        pending_amount = 0
        approved_count = 0
        rejected_count = 0
        review_count = 0

        for claim in claims:
            status = str(claim[6]).lower()
            amount = float(claim[5])

            if status in ["pending", "under review"]:
                pending_amount += amount

            if status == "approved":
                approved_count += 1
            elif status == "rejected":
                rejected_count += 1
            elif status == "under review":
                review_count += 1

        used_percent = (total_spent / budget_limit * 100) if budget_limit > 0 else 0
        projected_percent = ((total_spent + pending_amount) / budget_limit * 100) if budget_limit > 0 else 0

        # Main cards
        row = tk.Frame(self.content, bg=BG)
        row.pack(fill="x", pady=(0, 18))

        self.stat_card(row, "Department", dept_name, ACCENT)
        self.stat_card(row, "Budget Limit", f"PKR {budget_limit:,.0f}", SUCCESS)
        self.stat_card(row, "Total Spent", f"PKR {total_spent:,.0f}", ORANGE)
        self.stat_card(row, "Remaining", f"PKR {remaining:,.0f}", PURPLE)

        if row.winfo_children():
            row.winfo_children()[-1].pack_configure(padx=0)

        # Decision cards
        row2 = tk.Frame(self.content, bg=BG)
        row2.pack(fill="x", pady=(0, 18))

        self.stat_card(row2, "Pending Employee Claims", pending, WARNING)
        self.stat_card(row2, "Pending Amount", f"PKR {pending_amount:,.0f}", ORANGE)
        self.stat_card(row2, "Approved Claims", approved_count, SUCCESS)
        self.stat_card(row2, "Under Review", review_count, PURPLE)

        if row2.winfo_children():
            row2.winfo_children()[-1].pack_configure(padx=0)

        # Budget usage card
        usage_card = tk.Frame(
            self.content,
            bg=CARD,
            padx=28,
            pady=22,
            highlightthickness=1,
            highlightbackground=BORDER
        )
        usage_card.pack(fill="x", pady=(0, 18))

        tk.Label(
            usage_card,
            text="Budget Health",
            bg=CARD,
            fg=TEXT,
            font=FONT_HEADING
        ).pack(anchor="w", pady=(0, 10))

        tk.Label(
            usage_card,
            text=f"Approved Usage: {used_percent:.1f}%   |   Projected Usage After Pending Claims: {projected_percent:.1f}%",
            bg=CARD,
            fg=TEXT_MUTED,
            font=FONT_NORMAL
        ).pack(anchor="w", pady=(0, 10))

        bar_bg = tk.Frame(usage_card, bg=BG_SOFT, height=20)
        bar_bg.pack(fill="x", pady=(0, 8))
        bar_bg.pack_propagate(False)

        bar_fill = tk.Frame(
            bar_bg,
            bg=SUCCESS if used_percent < 70 else ORANGE if used_percent < 90 else DANGER
        )
        bar_fill.place(relx=0, rely=0, relwidth=max(min(used_percent / 100, 1), 0.01), relheight=1)

        tk.Label(
            usage_card,
            text="Green = healthy, orange = warning, red = critical",
            bg=CARD,
            fg=TEXT_MUTED,
            font=FONT_NORMAL
        ).pack(anchor="w")

        # Recent claims only, no duplicate action buttons
        tk.Label(
            self.content,
            text="Recent Department Claims",
            bg=BG,
            fg=TEXT,
            font=FONT_HEADING
        ).pack(anchor="w", pady=(0, 10))

        cols = ("ID", "Dept ID", "Department", "Employee", "Category", "Amount", "Status", "Date")
        self.make_tree(self.content, cols, claims, height=7, tag="ManagerDash")

    def show_employee_claims(self):
        self.clear_content()
        self.page_title(self.content, "Employee Claims", "Review employee expenses")

        cols = ("ID", "Dept ID", "Department", "Employee", "Category", "Amount", "Status", "Date")
        data = get_department_claims(self.session["dep_id"])

        tree = self.make_tree(
            self.content,
            cols,
            data,
            height=11,
            tag="ManagerClaims"
        )

        btns = tk.Frame(self.content, bg=BG)
        btns.pack(fill="x", pady=12)

        def get_id():
            sel = tree.selection()
            if not sel:
                messagebox.showerror("Error", "Select a claim first!")
                return None
            return tree.item(sel[0])["values"][0]

        def review():
            cid = get_id()
            if cid and set_under_review(cid, self.session["dep_id"]):
                messagebox.showinfo("Done", "Claim moved to review.")
                self.show_employee_claims()

        def approve():
            cid = get_id()
            if cid and approve_expense(cid, self.session["user_id"], self.session["dep_id"], "Approved"):
                messagebox.showinfo("Approved", "Claim approved.")
                self.show_employee_claims()

        def reject():
            cid = get_id()
            if cid and approve_expense(cid, self.session["user_id"], self.session["dep_id"], "Rejected"):
                messagebox.showinfo("Rejected", "Claim rejected.")
                self.show_employee_claims()

        def view_receipt():
            cid = get_id()
            if cid:
                result = get_claim_image(cid)
                if result and result[0]:
                    ImageViewer(self.master, result[0], f"Receipt — Claim #{cid}")
                else:
                    messagebox.showinfo("No Image", "No image found.")

        self.action_btn(btns, "Move to Review", review, WARNING).pack(side="left", padx=(0, 6))
        self.action_btn(btns, "Approve", approve, SUCCESS).pack(side="left", padx=(0, 6))
        self.action_btn(btns, "Reject", reject, DANGER).pack(side="left", padx=(0, 6))
        self.action_btn(btns, "View Receipt", view_receipt).pack(side="left", padx=(0, 6))
        self.light_btn(btns, "Refresh", self.show_employee_claims).pack(side="left")

    def show_my_claims(self):
        self.clear_content()
        self.page_title(self.content, "My Claims", "Track your submitted claims")

        cols = ("ID", "User ID", "Category", "Amount", "Status", "Date", "Receipt")
        data = get_my_claims(self.session["user_id"])

        tree = self.make_tree(
            self.content,
            cols,
            data,
            height=11,
            tag="MyClaims"
        )

        btns = tk.Frame(self.content, bg=BG)
        btns.pack(fill="x", pady=12)

        def view_receipt():
            sel = tree.selection()
            if not sel:
                messagebox.showerror("Error", "Select a claim first!")
                return

            cid = tree.item(sel[0])["values"][0]
            result = get_claim_image(cid)

            if result and result[0]:
                ImageViewer(self.master, result[0], f"Receipt — Claim #{cid}")
            else:
                messagebox.showinfo("No Image", "No image found.")

        self.action_btn(btns, "View Receipt", view_receipt, PURPLE).pack(side="left", padx=(0, 6))
        self.light_btn(btns, "Refresh", self.show_my_claims).pack(side="left")

    def show_submit_claim(self):
        self.clear_content()
        self.page_title(self.content, "Submit Claim", "Submit a new expense")

        card = tk.Frame(
            self.content,
            bg=CARD,
            padx=28,
            pady=24,
            highlightthickness=1,
            highlightbackground=BORDER
        )
        card.pack(anchor="w")

        amt_e = self.field(card, "Amount (PKR)")

        cats = get_categories()
        cat_names = [c[1] for c in cats]
        cat_var = tk.StringVar(value=cat_names[0] if cat_names else "")

        tk.Label(
            card,
            text="CATEGORY",
            bg=CARD,
            fg=TEXT_MUTED,
            font=FONT_LABEL
        ).pack(anchor="w", pady=(10, 0))

        tk.OptionMenu(card, cat_var, *cat_names).pack(fill="x")

        file_lbl = tk.Label(card, text="No file selected", bg=CARD, fg=TEXT_MUTED)
        file_lbl.pack(anchor="w", pady=10)

        def browse():
            path = filedialog.askopenfilename()
            if path:
                self.selected_file_path = path
                file_lbl.config(text=path.split("/")[-1])

        self.action_btn(card, "Browse Receipt", browse, PURPLE).pack(fill="x")

        def submit():
            try:
                if not self.selected_file_path:
                    messagebox.showerror("Error", "Please browse and select a receipt first.")
                    return

                with open(self.selected_file_path, "rb") as f:
                    img = f.read()

                if submit_claim(
                    self.session["user_id"],
                    self.session["dep_id"],
                    float(amt_e.get()),
                    cat_var.get(),
                    self.selected_file_path,
                    img
                ):
                    messagebox.showinfo("Submitted", "Claim submitted successfully.")
                    self.selected_file_path = None
                    self.show_submit_claim()

            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        tk.Frame(card, bg=CARD, height=16).pack()
        self.action_btn(card, "Submit Claim", submit, SUCCESS).pack(fill="x")

    def show_budget_summary(self):
        self.clear_content()
        self.page_title(self.content, "Budget Summary", "Department budget decision screen")

        data = get_budget_summary(self.session["dep_id"])

        if not data:
            tk.Label(self.content, text="No data found.", bg=BG, fg=DANGER).pack(pady=20)
            return

        department_id = data[0]
        department_name = data[1]
        budget_limit = float(data[2])
        remaining = float(data[3])
        total_spent = float(data[4])

        pending_claims = get_pending_count(self.session["dep_id"])
        all_claims = get_department_claims(self.session["dep_id"])

        pending_amount = 0
        approved_count = 0
        rejected_count = 0
        review_count = 0

        for claim in all_claims:
            status = str(claim[6]).lower()
            amount = float(claim[5])

            if status in ["pending", "under review"]:
                pending_amount += amount

            if status == "approved":
                approved_count += 1
            elif status == "rejected":
                rejected_count += 1
            elif status == "under review":
                review_count += 1

        projected_spent = total_spent + pending_amount
        projected_remaining = budget_limit - projected_spent

        approved_percent = (total_spent / budget_limit * 100) if budget_limit > 0 else 0
        projected_percent = (projected_spent / budget_limit * 100) if budget_limit > 0 else 0

        if projected_percent >= 100:
            risk_text = "Over Budget Risk"
            risk_color = DANGER
            insight = "Pending claims may exceed the department budget. Review high-value claims carefully."
        elif projected_percent >= 90:
            risk_text = "Critical"
            risk_color = DANGER
            insight = "Budget usage is near the limit. Approvals should be reviewed carefully."
        elif projected_percent >= 70:
            risk_text = "Warning"
            risk_color = ORANGE
            insight = "Budget is still available, but pending claims may increase usage significantly."
        else:
            risk_text = "Healthy"
            risk_color = SUCCESS
            insight = "Current budget position is healthy. Pending claims are within a safe range."

        top_row = tk.Frame(self.content, bg=BG)
        top_row.pack(fill="x", pady=(0, 18))

        self.stat_card(top_row, "Department Name", department_name, ACCENT)
        self.stat_card(top_row, "Department ID", department_id, PURPLE)
        self.stat_card(top_row, "Pending Employee Claims", pending_claims, WARNING)

        if top_row.winfo_children():
            top_row.winfo_children()[-1].pack_configure(padx=0)

        budget_row = tk.Frame(self.content, bg=BG)
        budget_row.pack(fill="x", pady=(0, 18))

        self.stat_card(budget_row, "Budget Limit", f"PKR {budget_limit:,.0f}", SUCCESS)
        self.stat_card(budget_row, "Approved Spent", f"PKR {total_spent:,.0f}", ORANGE)
        self.stat_card(budget_row, "Current Remaining", f"PKR {remaining:,.0f}", PURPLE)

        if budget_row.winfo_children():
            budget_row.winfo_children()[-1].pack_configure(padx=0)

        risk_row = tk.Frame(self.content, bg=BG)
        risk_row.pack(fill="x", pady=(0, 18))

        self.stat_card(risk_row, "Pending Amount", f"PKR {pending_amount:,.0f}", WARNING)
        self.stat_card(risk_row, "Projected Remaining", f"PKR {projected_remaining:,.0f}", DANGER if projected_remaining < 0 else SUCCESS)
        self.stat_card(risk_row, "Budget Risk", risk_text, risk_color)

        if risk_row.winfo_children():
            risk_row.winfo_children()[-1].pack_configure(padx=0)

        usage_card = tk.Frame(
            self.content,
            bg=CARD,
            padx=28,
            pady=22,
            highlightthickness=1,
            highlightbackground=BORDER
        )
        usage_card.pack(fill="x", pady=(0, 18))

        tk.Label(
            usage_card,
            text="Budget Usage",
            bg=CARD,
            fg=TEXT,
            font=FONT_HEADING
        ).pack(anchor="w", pady=(0, 14))

        tk.Label(
            usage_card,
            text=f"Approved Budget Usage: {approved_percent:.1f}%",
            bg=CARD,
            fg=TEXT,
            font=FONT_NORMAL
        ).pack(anchor="w", pady=(0, 6))

        approved_bar_bg = tk.Frame(usage_card, bg=BG_SOFT, height=22)
        approved_bar_bg.pack(fill="x", pady=(0, 14))
        approved_bar_bg.pack_propagate(False)

        approved_bar_fill = tk.Frame(
            approved_bar_bg,
            bg=SUCCESS if approved_percent < 70 else ORANGE if approved_percent < 90 else DANGER
        )
        approved_bar_fill.place(
            relx=0,
            rely=0,
            relwidth=max(min(approved_percent / 100, 1), 0.01),
            relheight=1
        )

        tk.Label(
            usage_card,
            text=f"Projected Budget Usage After Pending Claims: {projected_percent:.1f}%",
            bg=CARD,
            fg=TEXT,
            font=FONT_NORMAL
        ).pack(anchor="w", pady=(0, 6))

        projected_bar_bg = tk.Frame(usage_card, bg=BG_SOFT, height=22)
        projected_bar_bg.pack(fill="x")
        projected_bar_bg.pack_propagate(False)

        projected_bar_fill = tk.Frame(
            projected_bar_bg,
            bg=SUCCESS if projected_percent < 70 else ORANGE if projected_percent < 90 else DANGER
        )
        projected_bar_fill.place(
            relx=0,
            rely=0,
            relwidth=max(min(projected_percent / 100, 1), 0.01),
            relheight=1
        )

        insight_card = tk.Frame(
            self.content,
            bg=CARD,
            padx=28,
            pady=22,
            highlightthickness=1,
            highlightbackground=BORDER
        )
        insight_card.pack(fill="x")

        tk.Label(
            insight_card,
            text="Manager Insight",
            bg=CARD,
            fg=TEXT,
            font=FONT_HEADING
        ).pack(anchor="w", pady=(0, 10))

        tk.Label(
            insight_card,
            text=insight,
            bg=CARD,
            fg=risk_color,
            font=FONT_NORMAL,
            wraplength=850,
            justify="left"
        ).pack(anchor="w")
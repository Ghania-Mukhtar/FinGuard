import tkinter as tk
from tkinter import messagebox
from frontend.theme import *
from frontend.components.widgets import ModernUI
from frontend.components.image_viewer import ImageViewer

from services.admin import (
    add_department,
    add_funds,
    get_financial_report,
    get_manager_claims,
    move_claim_to_review,
    approve_manager_expense,
    set_yearly_budget
)

from services.auth import add_user
from backup.sync import postgres_to_firebase, firebase_to_postgres


class AdminDashboard(tk.Frame, ModernUI):
    def __init__(self, master, session, on_logout):
        super().__init__(master, bg=BG)
        self.master = master
        self.session = session
        self.on_logout = on_logout
        self.build()

    def build(self):
        self.build_shell("ExpenseFlow", "Admin")

        self.sidebar_title("Overview")
        self.sidebar_button("Dashboard", self.show_dashboard)
        self.sidebar_button("Financial Report", self.show_financial_report)

        self.sidebar_title("Management")
        self.sidebar_button("Add Department", self.show_add_department)
        self.sidebar_button("Add Funds", self.show_add_funds)
        self.sidebar_button("Add User", self.show_add_user)
        self.sidebar_button("Yearly Budget", self.show_yearly_budget)
        self.sidebar_button("Manager Claims", self.show_manager_claims)

        self.sidebar_title("System")
        self.sidebar_button("Backup to Firebase", self.do_backup)
        self.sidebar_button("Restore Firebase", self.do_restore)

        self.show_dashboard()

    def show_dashboard(self):
        self.clear_content()
        self.page_title(self.content, "Admin Dashboard", "Company budget command center")

        data = get_financial_report()
        manager_claims = get_manager_claims()

        total_departments = len(data) if data else 0
        total_budget = sum(float(r[2]) for r in data) if data else 0
        total_spent = sum(float(r[4]) for r in data) if data else 0
        remaining = total_budget - total_spent

        pending_manager_claims = 0
        under_review_claims = 0
        approved_claims = 0
        rejected_claims = 0
        pending_amount = 0

        for claim in manager_claims:
            amount = float(claim[4])
            status = str(claim[5]).lower()

            if status in ["pending", "under review"]:
                pending_manager_claims += 1
                pending_amount += amount

            if status == "under review":
                under_review_claims += 1
            elif status == "approved":
                approved_claims += 1
            elif status == "rejected":
                rejected_claims += 1

        projected_spent = total_spent + pending_amount
        approved_percent = (total_spent / total_budget * 100) if total_budget > 0 else 0
        projected_percent = (projected_spent / total_budget * 100) if total_budget > 0 else 0

        if projected_percent >= 100:
            risk_text = "Over Budget Risk"
            risk_color = DANGER
        elif projected_percent >= 90:
            risk_text = "Critical"
            risk_color = DANGER
        elif projected_percent >= 70:
            risk_text = "Warning"
            risk_color = ORANGE
        else:
            risk_text = "Healthy"
            risk_color = SUCCESS

        def mini_card(parent, title, value, color):
            card = tk.Frame(
                parent,
                bg=CARD,
                padx=18,
                pady=12,
                highlightthickness=1,
                highlightbackground=BORDER
            )
            card.pack(side="left", fill="both", expand=True, padx=(0, 10))

            tk.Label(
                card,
                text=str(value),
                bg=CARD,
                fg=color,
                font=("Segoe UI", 22, "bold")
            ).pack(anchor="w")

            tk.Label(
                card,
                text=title,
                bg=CARD,
                fg=TEXT_MUTED,
                font=FONT_NORMAL
            ).pack(anchor="w")

            return card

        # Compact health section
        hero = tk.Frame(
            self.content,
            bg=CARD,
            padx=18,
            pady=12,
            highlightthickness=1,
            highlightbackground=BORDER
        )
        hero.pack(fill="x", pady=(0, 10))

        tk.Label(
            hero,
            text=f"Company Budget Health: {risk_text}",
            bg=CARD,
            fg=risk_color,
            font=FONT_HEADING
        ).pack(anchor="w", pady=(0, 6))

        tk.Label(
            hero,
            text=f"Approved Usage {approved_percent:.1f}%  |  Projected Usage {projected_percent:.1f}%",
            bg=CARD,
            fg=TEXT_MUTED,
            font=FONT_NORMAL
        ).pack(anchor="w", pady=(0, 6))

        bar_bg = tk.Frame(hero, bg=BG_SOFT, height=12)
        bar_bg.pack(fill="x")
        bar_bg.pack_propagate(False)

        bar_fill = tk.Frame(
            bar_bg,
            bg=SUCCESS if projected_percent < 70 else ORANGE if projected_percent < 90 else DANGER
        )
        bar_fill.place(
            relx=0,
            rely=0,
            relwidth=max(min(projected_percent / 100, 1), 0.01),
            relheight=1
        )

        # Row 1
        row1 = tk.Frame(self.content, bg=BG)
        row1.pack(fill="x", pady=(0, 10))

        mini_card(row1, "Total Budget", f"PKR {total_budget:,.0f}", SUCCESS)
        mini_card(row1, "Total Spent", f"PKR {total_spent:,.0f}", ORANGE)
        mini_card(row1, "Remaining", f"PKR {remaining:,.0f}", PURPLE)
        row1.winfo_children()[-1].pack_configure(padx=0)

        # Row 2
        row2 = tk.Frame(self.content, bg=BG)
        row2.pack(fill="x", pady=(0, 10))

        mini_card(row2, "Departments", total_departments, ACCENT)
        mini_card(row2, "Pending Manager Claims", pending_manager_claims, WARNING)
        mini_card(row2, "Pending Manager Amount", f"PKR {pending_amount:,.0f}", ORANGE)
        mini_card(row2, "Budget Risk", risk_text, risk_color)
        row2.winfo_children()[-1].pack_configure(padx=0)

        # Department report
        tk.Label(
            self.content,
            text="Department Overview",
            bg=BG,
            fg=TEXT,
            font=FONT_HEADING
        ).pack(anchor="w", pady=(0, 6))

        self.make_tree(
            self.content,
            ("ID", "Department", "Budget", "Balance", "Spent"),
            data,
            height=8,
            tag="AdminDash"
        )

    def show_financial_report(self):
        self.clear_content()
        self.page_title(self.content, "Financial Report", "Live department budget overview")

        data = get_financial_report()

        self.make_tree(
            self.content,
            ("ID", "Department", "Budget Limit", "Live Balance", "Total Spent", "Remaining"),
            data,
            height=14,
            tag="AdminReport"
        )

        tk.Frame(self.content, bg=BG, height=12).pack()
        self.action_btn(self.content, "Refresh", self.show_financial_report).pack(anchor="w")

    def show_add_department(self):
        self.clear_content()
        self.page_title(self.content, "Add Department", "Create a new department with budget")

        card = tk.Frame(self.content, bg=CARD, padx=28, pady=24, highlightthickness=1, highlightbackground=BORDER)
        card.pack(anchor="w")

        name_e = self.field(card, "Department Name")
        budget_e = self.field(card, "Initial Budget PKR")

        def submit():
            name = name_e.get().strip()
            budget = budget_e.get().strip()

            if not name or not budget:
                messagebox.showerror("Error", "Fill all fields.")
                return

            try:
                if add_department(name, float(budget)):
                    messagebox.showinfo("Created", "Department added successfully.")
                    name_e.delete(0, tk.END)
                    budget_e.delete(0, tk.END)
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        tk.Frame(card, bg=CARD, height=16).pack()
        self.action_btn(card, "Create Department", submit).pack(fill="x")

    def show_add_funds(self):
        self.clear_content()
        self.page_title(self.content, "Add Funds", "Top up department budget")

        card = tk.Frame(self.content, bg=CARD, padx=28, pady=24, highlightthickness=1, highlightbackground=BORDER)
        card.pack(anchor="w")

        name_e = self.field(card, "Department Name")
        amount_e = self.field(card, "Amount PKR")

        def submit():
            name = name_e.get().strip()
            amount = amount_e.get().strip()

            if not name or not amount:
                messagebox.showerror("Error", "Fill all fields.")
                return

            try:
                if add_funds(name, float(amount)):
                    messagebox.showinfo("Success", "Funds added successfully.")
                    name_e.delete(0, tk.END)
                    amount_e.delete(0, tk.END)
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        tk.Frame(card, bg=CARD, height=16).pack()
        self.action_btn(card, "Add Funds", submit, SUCCESS).pack(fill="x")

    def show_add_user(self):
        self.clear_content()
        self.page_title(self.content, "Add User", "Create employee, manager, or admin account")

        card = tk.Frame(self.content, bg=CARD, padx=28, pady=24, highlightthickness=1, highlightbackground=BORDER)
        card.pack(anchor="w")

        name_e = self.field(card, "Full Name")
        email_e = self.field(card, "Email Address")
        pwd_e = self.field(card, "Password", secret=True)
        dept_e = self.field(card, "Department Name")

        tk.Label(card, text="ROLE", bg=CARD, fg=TEXT_MUTED, font=FONT_LABEL).pack(anchor="w", pady=(12, 6))

        role_var = tk.StringVar(value="Employee")
        role_row = tk.Frame(card, bg=CARD)
        role_row.pack(anchor="w")

        for role in ["Employee", "Manager", "Admin"]:
            tk.Radiobutton(
                role_row,
                text=role,
                variable=role_var,
                value=role,
                bg=CARD,
                fg=TEXT,
                selectcolor=BG_SOFT,
                activebackground=CARD,
                font=FONT_NORMAL
            ).pack(side="left", padx=(0, 14))

        def submit():
            name = name_e.get().strip()
            email = email_e.get().strip()
            pwd = pwd_e.get().strip()
            dept = dept_e.get().strip()
            role = role_var.get()

            if not all([name, email, pwd, dept]):
                messagebox.showerror("Error", "Fill all fields.")
                return

            if add_user(name, email, pwd, role, dept):
                messagebox.showinfo("Created", f"{role} user created successfully.")
                for entry in [name_e, email_e, pwd_e, dept_e]:
                    entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", "Failed. Please check department name.")

        tk.Frame(card, bg=CARD, height=16).pack()
        self.action_btn(card, "Create User", submit, PURPLE).pack(fill="x")

    def show_yearly_budget(self):
        self.clear_content()
        self.page_title(self.content, "Yearly Budget", "Set annual department budget")

        card = tk.Frame(self.content, bg=CARD, padx=28, pady=24, highlightthickness=1, highlightbackground=BORDER)
        card.pack(anchor="w")

        name_e = self.field(card, "Department Name")
        year_e = self.field(card, "Year")
        budget_e = self.field(card, "Budget Amount PKR")

        def submit():
            name = name_e.get().strip()
            year = year_e.get().strip()
            budget = budget_e.get().strip()

            if not all([name, year, budget]):
                messagebox.showerror("Error", "Fill all fields.")
                return

            try:
                if set_yearly_budget(name, int(year), float(budget)):
                    messagebox.showinfo("Success", "Yearly budget set.")
            except Exception as ex:
                messagebox.showerror("Error", str(ex))

        tk.Frame(card, bg=CARD, height=16).pack()
        self.action_btn(card, "Set Budget", submit, WARNING).pack(fill="x")

    def show_manager_claims(self):
        self.clear_content()
        self.page_title(self.content, "Manager Claims", "Review and approve manager expenses")

        data = get_manager_claims()

        tree = self.make_tree(
            self.content,
            ("ID", "Manager", "Department", "Category", "Amount", "Status", "Date", "Receipt"),
            data,
            height=11,
            tag="ManagerClaims"
        )

        btns = tk.Frame(self.content, bg=BG)
        btns.pack(fill="x", pady=12)

        def selected_id():
            sel = tree.selection()
            if not sel:
                messagebox.showerror("Error", "Select a claim first.")
                return None
            return tree.item(sel[0])["values"][0]

        def review():
            cid = selected_id()
            if cid and move_claim_to_review(cid):
                messagebox.showinfo("Done", "Moved to Under Review.")
                self.show_manager_claims()

        def approve():
            cid = selected_id()
            if cid and approve_manager_expense(cid, self.session["user_id"], "Approved"):
                messagebox.showinfo("Approved", "Claim approved.")
                self.show_manager_claims()

        def reject():
            cid = selected_id()
            if cid and approve_manager_expense(cid, self.session["user_id"], "Rejected"):
                messagebox.showinfo("Rejected", "Claim rejected.")
                self.show_manager_claims()

        def view_receipt():
            cid = selected_id()
            if not cid:
                return
            from services.manager import get_claim_image
            result = get_claim_image(cid)
            if result and result[0]:
                ImageViewer(self.master, result[0], f"Receipt — Claim #{cid}")
            else:
                messagebox.showinfo("No Image", "No image for this claim.")

        self.action_btn(btns, "Move to Review", review, WARNING).pack(side="left", padx=(0, 6))
        self.action_btn(btns, "Approve", approve, SUCCESS).pack(side="left", padx=(0, 6))
        self.action_btn(btns, "Reject", reject, DANGER).pack(side="left", padx=(0, 6))
        self.action_btn(btns, "View Receipt", view_receipt).pack(side="left", padx=(0, 6))
        self.light_btn(btns, "Refresh", self.show_manager_claims).pack(side="left")

    def do_backup(self):
        try:
            postgres_to_firebase()
            messagebox.showinfo("Backup Done", "Data backed up to Firebase.")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    def do_restore(self):
        try:
            firebase_to_postgres()
            messagebox.showinfo("Restore Done", "Data restored from Firebase.")
        except Exception as ex:
            messagebox.showerror("Error", str(ex))
import tkinter as tk
from frontend.pages.login import LoginPage
from frontend.pages.admin_dashboard import AdminDashboard
from frontend.pages.manager_dashboard import ManagerDashboard
from frontend.pages.employee_dashboard import EmployeeDashboard

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Expense Management System")
        self.geometry("1100x700")
        self.configure(bg="#1e1e2e")
        self.resizable(True, True)
        self.current_frame = None
        self.show_login()

    def clear(self):
        if self.current_frame:
            self.current_frame.destroy()

    def show_login(self):
        self.clear()
        self.current_frame = LoginPage(self, self.on_login)

    def on_login(self, session):
        self.clear()
        role = session["role"]
        if role == "Admin":
            self.current_frame = AdminDashboard(
                self, session, self.show_login)
        elif role == "Manager":
            self.current_frame = ManagerDashboard(
                self, session, self.show_login)
        elif role == "Employee":
            self.current_frame = EmployeeDashboard(
                self, session, self.show_login)

if __name__ == "__main__":
    app = App()
    app.mainloop()
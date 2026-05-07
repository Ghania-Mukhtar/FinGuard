# FinGuard

# **ExpenseFlow – Expense Management System**

## **Overview**
**ExpenseFlow** is a modern desktop-based Expense Management System developed using **Python Tkinter** with a clean and professional user interface.  
The system streamlines the process of expense submission, approval, budget tracking, and department-level financial management.

It supports three different user roles:

- **Admin**
- **Manager**
- **Employee**

The application includes secure login authentication, receipt image handling, claim approval workflows, budget monitoring, and Firebase/PostgreSQL backup support.

---

# **Features**

## **Authentication System**
- Secure login system
- Role-based dashboard access
- Separate interfaces for:
  - Admin
  - Manager
  - Employee

---

# **Admin Features**

## **Dashboard**
- View company financial overview
- Monitor:
  - Total budget
  - Total spending
  - Remaining balance
  - Pending manager claims
  - Budget health indicators

## **Department Management**
- Add new departments
- Assign department budgets
- Add funds to departments
- Set yearly budgets

## **User Management**
- Create:
  - Employees
  - Managers
  - Admin accounts

## **Claim Management**
- Review manager claims
- Approve or reject claims
- Move claims to under review
- View uploaded receipts

## **Backup & Restore**
- Backup PostgreSQL data to Firebase
- Restore Firebase data back to PostgreSQL

---

# **Manager Features**

## **Department Dashboard**
- Monitor department expenses
- View:
  - Budget usage
  - Remaining budget
  - Pending employee claims
  - Budget risk indicators

## **Employee Claim Handling**
- Review employee claims
- Approve or reject expenses
- Move claims to under review
- View receipt images

## **Personal Claims**
- Submit manager expense claims
- Track personal claim status

## **Budget Summary**
- Department financial analysis
- Budget usage visualization
- Risk monitoring system

---

# **Employee Features**

## **Dashboard**
- Track personal expenses
- View:
  - Approval rate
  - Pending claims
  - Approved claims
  - Rejected claims
  - Total submitted amount

## **Expense Claim Submission**
- Submit expense claims
- Select expense categories
- Upload receipt images/files

## **Claim Tracking**
- Monitor claim status
- View uploaded receipts
- Refresh claim history

---

# **Technologies Used**

## **Frontend**
- Python Tkinter
- ttk Widgets
- PIL (Pillow)

## **Backend**
- Python

## **Database**
- PostgreSQL

## **Cloud Backup**
- Firebase

---

# **Project Structure**

```bash
ExpenseFlow/
│
├── frontend/
│   ├── components/
│   │   ├── widgets.py
│   │   └── image_viewer.py
│   │
│   ├── pages/
│   │   ├── login.py
│   │   ├── admin_dashboard.py
│   │   ├── manager_dashboard.py
│   │   └── employee_dashboard.py
│   │
│   └── theme.py
│
├── services/
│   ├── admin.py
│   ├── manager.py
│   ├── employee.py
│   └── auth.py
│
├── backup/
│   └── sync.py
│
├── app.py
└── README.md
```

---

# **System Workflow**

## **Employee Workflow**
1. Employee logs into the system
2. Submits expense claim
3. Uploads receipt
4. Manager reviews claim
5. Claim gets approved/rejected

---

## **Manager Workflow**
1. Manager reviews employee claims
2. Tracks department budget
3. Approves or rejects expenses
4. Admin reviews manager claims

---

## **Admin Workflow**
1. Monitors company financial activity
2. Manages departments and users
3. Controls yearly budgets
4. Handles manager approvals
5. Performs system backup/restore

---

# **Installation**

## **Clone Repository**

```bash
git clone <https://github.com/Ghania-Mukhtar/FinGuard>
cd ExpenseFlow
```

---

# **Install Dependencies**

```bash
pip install pillow
pip install psycopg2
pip install firebase-admin
```

---

# **Run Application**

```bash
python main.py
```

---

# **Database Requirements**

Make sure PostgreSQL is installed and configured.

Required tables include:
- Users
- Departments
- Expense_Claims
- Expense_Categories
- Departments_Budgets
- Audit_Trail
- Verified_Transaction
---

# **User Roles**

| Role     | Permissions             |
|----------|-------------------------|
| Admin    | Full system control     |
| Manager  | Department management   |
| Employee | Submit and track claims |

---

# **UI Features**

- Responsive dashboard layout
- Sidebar navigation
- Custom themed widgets
- Budget visualization bars
- Receipt image viewer
- Interactive tables using ttk Treeview

---

# **Security Features**

- Role-based access control
- Secure authentication
- Protected financial workflows
- Controlled approval hierarchy

---




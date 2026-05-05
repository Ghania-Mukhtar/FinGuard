-- =====================================================
-- TABLE: Departments
-- PURPOSE:
-- Stores the current financial state of each department.
-- This table represents the main budget container.
--
-- budget_limit      → Total allocated funds for department
-- current_balance   → Remaining funds after approved expenses
--
-- Every user and expense claim belongs to a department.
-- =====================================================
CREATE TABLE IF NOT EXISTS Departments(
    dep_id SERIAL PRIMARY KEY,
    dep_name VARCHAR(50) UNIQUE NOT NULL,
    budget_limit NUMERIC(15,2) NOT NULL,
    current_balance NUMERIC(15,2) NOT NULL CHECK (current_balance >= 0),
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


-- =====================================================
-- TABLE: Department_Budgets
-- PURPOSE:
-- Stores historical yearly budgets for each department.
-- This enables financial tracking and analysis per year.
--
-- UNIQUE(dep_id, year) ensures only one budget per year
-- per department.
-- =====================================================
CREATE TABLE IF NOT EXISTS Department_Budgets (
    budget_id SERIAL PRIMARY KEY,
    year INT NOT NULL,
    yearly_budget NUMERIC(15,2) NOT NULL CHECK (yearly_budget > 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    dep_id INT NOT NULL,
    FOREIGN KEY (dep_id) REFERENCES Departments(dep_id),
    UNIQUE (dep_id, year)
);

-- =====================================================
-- TABLE: Users
-- PURPOSE:
-- Stores all system users who interact with the platform.
--
-- Roles:
-- Employee → submits expense claims
-- Manager  → approves/rejects claims
-- Admin    → full system control
--
-- Each user belongs to exactly one department.
-- =====================================================
CREATE TABLE IF NOT EXISTS Users (
    user_id SERIAL PRIMARY KEY,
    user_name VARCHAR(50) NOT NULL,
    user_email VARCHAR(100) UNIQUE NOT NULL,
    user_password TEXT NOT NULL, -- stores bcrypt hashed password, never plain text
    user_role VARCHAR(50) NOT NULL CHECK (user_role IN ('Employee', 'Manager', 'Admin')),
    dep_id INT NOT NULL,
    FOREIGN KEY (dep_id) REFERENCES Departments(dep_id)
);


-- =====================================================
-- TABLE: Expense_Categories
-- PURPOSE:
-- Defines types of expenses (Travel, Equipment, Food etc.)
-- Used to categorize expense claims for reporting.
-- =====================================================
CREATE TABLE IF NOT EXISTS Expense_Categories (
    cat_id SERIAL PRIMARY KEY,
    cat_name VARCHAR(50) UNIQUE NOT NULL ,
    description TEXT
);

-- =====================================================
-- TABLE: Expense_Claims
-- PURPOSE:
-- Core table of the system.
-- Stores all expense requests submitted by employees.
--
-- status values:
-- Pending       → newly submitted
-- Under_Review  → manager is reviewing
-- Approved      → accepted and ready for payment
-- Rejected      → denied
--
-- receipt_url links Firebase storage for proof images.
-- =====================================================
CREATE TABLE IF NOT EXISTS Expense_Claims (
    claim_id SERIAL PRIMARY KEY,
    amount NUMERIC(15,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'Pending' CHECK (status IN ('Pending', 'Approved', 'Rejected', 'Under_Review')),
    receipt_url  TEXT NOT NULL,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    cat_id INT NOT NULL,
    FOREIGN KEY (cat_id) REFERENCES Expense_Categories(cat_id),
    dep_id INT NOT NULL,
    FOREIGN KEY (dep_id) REFERENCES Departments(dep_id)
);

-- =====================================================
-- TABLE: Verified_Transaction
-- PURPOSE:
-- Stores FINAL approved payments after verification.
--
-- This acts as the financial proof that money
-- was actually deducted from department balance.
--
-- Uses UUID for secure transaction tracking.
-- =====================================================

CREATE TABLE IF NOT EXISTS Verified_Transaction (
    trx_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id INT NOT NULL,
    FOREIGN KEY (claim_id) REFERENCES Expense_Claims(claim_id),
    final_amount NUMERIC(15,2) NOT NULL CHECK (final_amount > 0),
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_by INT NOT NULL,
    FOREIGN KEY (verified_by) REFERENCES Users(user_id)
);


-- =====================================================
-- TABLE: Audit_Trail
-- PURPOSE:
-- Security and accountability table.
-- Tracks ALL database changes (INSERT/UPDATE/DELETE).
--
-- old_data → data before change
-- new_data → data after change
--
-- Ensures transparency and prevents fraud.
-- =====================================================
CREATE TABLE IF NOT EXISTS Audit_Trail (
    log_id  BIGSERIAL PRIMARY KEY,
    target_table VARCHAR(50) NOT NULL,
    operation VARCHAR(50) NOT NULL CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE')),
    old_data JSONB,
    new_data JSONB,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES Users(user_id),
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- indexes
CREATE INDEX IF NOT EXISTS idx_claim_status ON Expense_Claims(status);
CREATE INDEX IF NOT EXISTS idx_users_department ON Users(dep_id);
CREATE INDEX IF NOT EXISTS idx_verified_claim ON Verified_Transaction(claim_id);
-- composite indexes
CREATE INDEX IF NOT EXISTS idx_claim_dep_status ON Expense_Claims(dep_id, status);
CREATE INDEX IF NOT EXISTS idx_budget_dep_year ON Department_Budgets(dep_id, year);

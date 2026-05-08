CREATE EXTENSION IF NOT EXISTS pgcrypto;
-- add_user
CREATE OR REPLACE PROCEDURE add_user(
    p_name     VARCHAR(50),
    p_email    VARCHAR(100),
    p_password TEXT,
    p_role     VARCHAR(50),
    p_dep_name VARCHAR(100)
)
LANGUAGE plpgsql AS $$
DECLARE
    v_dep_id INT;
BEGIN
    SELECT dep_id INTO v_dep_id
    FROM Departments
    WHERE dep_name = p_dep_name;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Department "%" does not exist', p_dep_name;
    END IF;

    INSERT INTO Users(user_name, user_email, user_password, user_role, dep_id)
    VALUES (
        p_name,
        p_email,
        crypt(p_password, gen_salt('bf')),  -- bf = bcrypt, most secure option
        p_role,
        v_dep_id
    );
END;
$$;


-- Login: verify email + password, return user info
CREATE OR REPLACE FUNCTION user_login(
    p_email    TEXT,
    p_password TEXT
)
RETURNS TABLE(
    user_id       INT,
    role          VARCHAR,
    department_id INT,
    user_name     TEXT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT u.user_id, u.user_role, u.dep_id, u.user_name::TEXT
    FROM Users u
    WHERE u.user_email    = p_email
      AND u.user_password = crypt(p_password, u.user_password);  -- hashed comparison

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Invalid email or password';
    END IF;
END;
$$;

-- Get user role
CREATE OR REPLACE FUNCTION get_user_role(u_id INT)
RETURNS VARCHAR AS $$
DECLARE
    users_role VARCHAR(50);
BEGIN
    SELECT user_role INTO users_role
    FROM Users
    WHERE user_id = u_id;
    RETURN users_role;
END;
$$ LANGUAGE plpgsql;

-- Admin part

-- Get current balance of a department
-- UTILITY FUNCTION: returns live department balance
-- Used by frontend to display balance before claim submission
-- Not used internally by procedures — balance check is
-- handled atomically inside transaction blocks
CREATE OR REPLACE FUNCTION get_current_balance(d_id INT)
RETURNS NUMERIC AS $$
DECLARE
    remaining_balance NUMERIC(15,2);
BEGIN
    SELECT current_balance INTO remaining_balance
    FROM Departments
    WHERE dep_id = d_id;
    RETURN remaining_balance;
END;
$$ LANGUAGE plpgsql;


-- =====================================================
-- SECTION 4: TRIGGERS
-- =====================================================

-- Auto-set current_balance = budget_limit on new department INSERT
CREATE OR REPLACE FUNCTION set_initial_balance()
RETURNS TRIGGER AS $$
BEGIN
    NEW.current_balance = NEW.budget_limit;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_set_initial_balance
BEFORE INSERT ON Departments
FOR EACH ROW
EXECUTE FUNCTION set_initial_balance();


-- Audit trail: log every UPDATE on Expense_Claims
CREATE OR REPLACE FUNCTION log_claim_update()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO Audit_Trail(target_table, operation, old_data, new_data, user_id)
    VALUES (
        'Expense_Claims',
        'UPDATE',
        row_to_json(OLD),
        row_to_json(NEW),
        NEW.user_id
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_claim_audit
AFTER UPDATE ON Expense_Claims
FOR EACH ROW
EXECUTE FUNCTION log_claim_update();


-- =====================================================
-- SECTION 5: ADMIN PROCEDURES
-- =====================================================

-- 1. Add a new department
--    The trg_set_initial_balance trigger will auto-set current_balance.
CREATE OR REPLACE PROCEDURE add_department(
    p_dep_name VARCHAR(50),
    p_budget   NUMERIC(15,2)
)
LANGUAGE plpgsql AS $$
BEGIN
    INSERT INTO Departments(dep_name, budget_limit)
    VALUES (p_dep_name, p_budget);
END;
$$;


-- 2. Add extra funds to an existing department
-- 2. Add funds using department NAME
CREATE OR REPLACE PROCEDURE add_department_funds(
    p_dep_name VARCHAR(100),
    p_amount   NUMERIC(15,2)
)
LANGUAGE plpgsql AS $$
DECLARE
    v_dep_id INT;
BEGIN
    IF p_amount <= 0 THEN
        RAISE EXCEPTION 'Amount must be greater than zero';
    END IF;

    SELECT dep_id INTO v_dep_id
    FROM Departments
    WHERE dep_name = p_dep_name;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Department "%" does not exist', p_dep_name;
    END IF;

    UPDATE Departments
    SET budget_limit = budget_limit + p_amount,
        current_balance = current_balance + p_amount
    WHERE dep_id = v_dep_id;

    RAISE NOTICE 'Added % to department "%"', p_amount, p_dep_name;
END;
$$;


-- 3. Set (or update) the next year budget using department NAME
CREATE OR REPLACE PROCEDURE set_next_yearly_budget(
    p_dep_name VARCHAR(100),
    p_year     INT,
    p_budget   NUMERIC(15,2)
)
LANGUAGE plpgsql AS $$
DECLARE
    v_dep_id INT;
BEGIN
    IF p_budget <= 0 THEN
        RAISE EXCEPTION 'Yearly budget must be greater than zero';
    END IF;

    -- Resolve name → id
    SELECT dep_id INTO v_dep_id
    FROM Departments
    WHERE dep_name = p_dep_name;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Department "%" does not exist', p_dep_name;
    END IF;

    INSERT INTO Department_Budgets(dep_id, year, yearly_budget)
    VALUES (v_dep_id, p_year, p_budget)
    ON CONFLICT (dep_id, year)
    DO UPDATE SET yearly_budget = EXCLUDED.yearly_budget;

    RAISE NOTICE 'Budget for "%" in year % set to %', p_dep_name, p_year, p_budget;
END;
$$;


-- 4. Activate new year budgets (called by pg_cron on Jan 1)
--    Sets budget_limit and current_balance to the pre-set yearly_budget.
--    If you want to carry forward unspent balance instead, change the
--    current_balance line to: current_balance + b.yearly_budget
CREATE OR REPLACE PROCEDURE activate_new_year_budget()
LANGUAGE plpgsql AS $$
DECLARE
    v_year INT;
BEGIN
    v_year := EXTRACT(YEAR FROM CURRENT_DATE);

    UPDATE Departments d
    SET budget_limit = b.yearly_budget,
   		current_balance = d.current_balance + b.yearly_budget
    FROM Department_Budgets b
    WHERE d.dep_id = b.dep_id
      AND b.year = v_year;

    RAISE NOTICE 'New fiscal year % budgets activated', v_year;
END;
$$;


-- 5. Move a claim from Pending → Under_Review
--    Admin calls this before reviewing/approving a manager's claim.
CREATE OR REPLACE PROCEDURE move_claim_to_review(p_claim_id INT)
LANGUAGE plpgsql AS $$
BEGIN
    UPDATE Expense_Claims
    SET status = 'Under_Review'
    WHERE claim_id = p_claim_id
      AND status   = 'Pending';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Claim % is not in Pending status', p_claim_id;
    END IF;
END;
$$;


-- 6. Admin approves or rejects a manager's expense claim
--    Claim must be Under_Review before calling this.
--    On approval: inserts Verified_Transaction + deducts from balance.
--    On rejection or insufficient balance: marks claim Rejected.
CREATE OR REPLACE PROCEDURE approve_manager_expense(
    p_claim_id  INT,
    p_admin_id  INT,
    p_decision  VARCHAR(50)   -- 'Approved' or 'Rejected'
)
LANGUAGE plpgsql AS $$
DECLARE
    v_amount  NUMERIC(15,2);
    v_dep_id  INT;
    v_balance NUMERIC(15,2);
BEGIN
    -- Fetch claim details (must be Under_Review)
    SELECT amount, dep_id
    INTO   v_amount, v_dep_id
    FROM   Expense_Claims
    WHERE  claim_id = p_claim_id
      AND  status = 'Under_Review';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Claim % not found or not Under_Review', p_claim_id;
    END IF;

    -- Handle rejection
    IF p_decision = 'Rejected' THEN
        UPDATE Expense_Claims SET status = 'Rejected' WHERE claim_id = p_claim_id;
        RAISE NOTICE 'Claim % rejected by admin %', p_claim_id, p_admin_id;
        RETURN;
    END IF;

    -- Handle approval: check balance
    -- Record verified transaction
    BEGIN
        INSERT INTO Verified_Transaction(claim_id, final_amount, verified_by)
        VALUES (p_claim_id, v_amount, p_admin_id);

        UPDATE Departments
        SET current_balance = current_balance - v_amount
        WHERE dep_id = v_dep_id
          AND current_balance >= v_amount;

	    IF NOT FOUND THEN
	            RAISE EXCEPTION 'Insufficient balance during transaction';
	        END IF;
	
	        UPDATE Expense_Claims
	        SET status = 'Approved'
	        WHERE claim_id = p_claim_id;
	
	    EXCEPTION WHEN OTHERS THEN
	        RAISE EXCEPTION 'Approval transaction failed and rolled back: %', SQLERRM;
	    END;
	
	    RAISE NOTICE 'Claim % approved. Amount % deducted from department %',
	                 p_claim_id, v_amount, v_dep_id;
END;
$$;


-- =====================================================
-- SECTION 6: ADMIN VIEWS
-- =====================================================

-- View 1: All departments financial report
--   Shows budget_limit, total_spent (from verified transactions),
--   and remaining_budget per department.
CREATE OR REPLACE VIEW admin_company_financial_report AS
SELECT
    d.dep_id,
    d.dep_name,
    d.budget_limit,
    d.current_balance  AS live_balance,
    COALESCE(SUM(v.final_amount), 0) AS total_spent,
    d.budget_limit - COALESCE(SUM(v.final_amount), 0) AS calculated_remaining
FROM Departments d
LEFT JOIN Expense_Claims c  ON d.dep_id   = c.dep_id
LEFT JOIN Verified_Transaction v ON c.claim_id = v.claim_id
GROUP BY d.dep_id, d.dep_name, d.budget_limit, d.current_balance;


-- View 2: All manager claims waiting for admin action
--   Shows Pending and Under_Review claims submitted by Managers only.
CREATE OR REPLACE VIEW admin_manager_claims AS
SELECT
    c.claim_id,
    u.user_name  AS manager_name,
    d.dep_name,
    cat.cat_name AS category,
    c.amount,
    c.status,
    c.submitted_at,
    c.receipt_url
FROM Expense_Claims c
JOIN Users u  ON c.user_id  = u.user_id
JOIN Departments d ON c.dep_id   = d.dep_id
JOIN Expense_Categories cat ON c.cat_id   = cat.cat_id
WHERE u.user_role = 'Manager'
  AND c.status IN ('Pending', 'Under_Review');


-- View 3: All departments with their upcoming yearly budgets
CREATE OR REPLACE VIEW admin_yearly_budgets AS
SELECT
    d.dep_id,
    d.dep_name,
    b.year,
    b.yearly_budget,
    b.created_at AS set_on
FROM Departments d
JOIN Department_Budgets b ON d.dep_id = b.dep_id
ORDER BY b.year DESC, d.dep_name;


-- =====================================================
-- SECTION 7: CURSOR REPORT
-- =====================================================

-- Prints total spending per department using an explicit cursor.
CREATE OR REPLACE PROCEDURE generate_yearly_report()
LANGUAGE plpgsql AS $$
DECLARE
    dept_record RECORD;
    total NUMERIC(15,2);

    dept_cursor CURSOR FOR
        SELECT dep_id, dep_name FROM Departments ORDER BY dep_name;
BEGIN
    OPEN dept_cursor;

    LOOP
        FETCH dept_cursor INTO dept_record;
        EXIT WHEN NOT FOUND;

        SELECT COALESCE(SUM(v.final_amount), 0)
        INTO  total
        FROM  Verified_Transaction v
        JOIN  Expense_Claims c ON v.claim_id = c.claim_id
        WHERE  c.dep_id = dept_record.dep_id;

        RAISE NOTICE 'Department: %-30s | Total spent: %',
                     dept_record.dep_name, total;
    END LOOP;

    CLOSE dept_cursor;
END;
$$;


-- =====================================================
-- SECTION 8: PG_CRON SCHEDULER
-- =====================================================

CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Fires at midnight on Jan 1 every year to activate new budgets
SELECT cron.schedule(
    'activate_new_year_budget',
    '0 0 1 1 *',
    $$ CALL activate_new_year_budget(); $$
);

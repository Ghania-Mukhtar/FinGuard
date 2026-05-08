CREATE OR REPLACE VIEW manager_department_claims AS
SELECT
    c.claim_id,
    c.dep_id,
    d.dep_name,
    u.user_name AS employee_name,
    cat.cat_name AS category,
    c.amount,
    c.status,
    c.submitted_at,
    c.receipt_url
FROM Expense_Claims c
JOIN Users u ON c.user_id = u.user_id
JOIN Departments d ON c.dep_id  = d.dep_id
JOIN Expense_Categories cat ON c.cat_id  = cat.cat_id
WHERE u.user_role = 'Employee'
  AND c.status IN ('Pending', 'Under_Review');

-- dep_id is included so frontend can filter:
-- WHERE dep_id = session.dep_id


-- View 3: Manager's own submitted claims
--   Frontend filters: WHERE user_id = session.user_id
CREATE OR REPLACE VIEW my_submitted_claims AS
SELECT
    c.claim_id,
    c.user_id,
    cat.cat_name  AS category,
    c.amount,
    c.status,
    c.submitted_at,
    c.receipt_url
FROM Expense_Claims c
JOIN Expense_Categories cat ON c.cat_id  = cat.cat_id
JOIN Users u ON c.user_id = u.user_id
WHERE u.user_role IN ('Employee', 'Manager');
-- frontend filters: WHERE user_id = session.user_id


-- =====================================================
-- SECTION 3: MANAGER FUNCTIONS
-- Functions return data to the frontend.
-- session values (user_id, dep_id) passed by frontend — never typed.
-- =====================================================

-- Function 1: Pending claims count for dashboard badge
--   Frontend passes session.dep_id — manager never types it.
--   Returns a single INT — e.g. frontend shows badge "3 pending"
CREATE OR REPLACE FUNCTION pending_claims_count(p_dep_id INT)
RETURNS INT
LANGUAGE plpgsql AS $$
DECLARE
    v_count INT;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM Expense_Claims
    WHERE dep_id = p_dep_id
      AND status = 'Pending';

    RETURN COALESCE(v_count, 0);
END;
$$;


-- Function 2: Manager views their own department budget report
--   Frontend passes session.dep_id.
--   Returns one row — the manager's own department only.
-- database enforces the restriction — no risk of frontend forgetting the filter
CREATE OR REPLACE FUNCTION manager_budget_summary(p_dep_id INT)
RETURNS TABLE(
    dep_id INT,
    dep_name VARCHAR(100),
    budget_limit NUMERIC(15,2),
    remaining_balance NUMERIC(15,2),
    total_spent NUMERIC(15,2)
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        d.dep_id,
        d.dep_name,
        d.budget_limit,
        d.current_balance,
        (d.budget_limit - d.current_balance)::NUMERIC(15,2)
    FROM Departments d
    WHERE d.dep_id = p_dep_id;  -- enforced in DB, not left to frontend
END;
$$;


-- Frontend calls this when the claim submission form loads.
-- Returns all available categories for the dropdown.
-- Both Employee and Manager use this.
CREATE OR REPLACE FUNCTION get_expense_categories()
RETURNS TABLE(
    cat_id      INT,
    cat_name    VARCHAR(50),
    description TEXT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT c.cat_id, c.cat_name, c.description
    FROM Expense_Categories c
    ORDER BY c.cat_name;
END;
$$;

-- =====================================================
-- SECTION 4: MANAGER PROCEDURES
-- Procedures perform actions — insert, update.
-- session values passed by frontend silently.
-- =====================================================

-- Procedure 1: Submit an expense claim
--   Used by both Employee and Manager.
--   p_user_id  → session.user_id  (never typed)
--   p_dep_id   → session.dep_id   (never typed)
--   p_cat_name → chosen from dropdown in UI (name, not id)
--   p_receipt_url → uploaded file URL from frontend
CREATE OR REPLACE PROCEDURE submit_expense_claim(
    p_user_id INT,
    p_dep_id INT,
    p_amount NUMERIC(15,2),
    p_cat_name VARCHAR(50),
    p_receipt_url TEXT
)
LANGUAGE plpgsql AS $$
DECLARE
    v_cat_id INT;
BEGIN
    IF p_amount <= 0 THEN
        RAISE EXCEPTION 'Claim amount must be greater than zero';
    END IF;

	IF NOT EXISTS (
        SELECT 1 FROM Users
        WHERE user_id = p_user_id
          AND dep_id  = p_dep_id
    ) THEN
        RAISE EXCEPTION 'User does not belong to this department';
    END IF;

    -- resolve category name → id (manager picks name from dropdown)
    SELECT cat_id INTO v_cat_id
    FROM Expense_Categories
    WHERE cat_name = p_cat_name;

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Category "%" does not exist', p_cat_name;
    END IF;

    INSERT INTO Expense_Claims(user_id, dep_id, cat_id, amount, receipt_url)
    VALUES (p_user_id, p_dep_id, v_cat_id, p_amount, p_receipt_url);

    RAISE NOTICE 'Claim submitted successfully';
END;
$$;


-- Procedure 2: Move a claim Pending → Under_Review
--   Manager clicks a claim row in the UI — this fires automatically.
--   p_claim_id → from UI row click  (never typed)
--   p_user_id  → session.user_id    (never typed)
--   p_dep_id   → session.dep_id     (never typed)
--   Department boundary enforced: manager can only touch their own dept claims.
CREATE OR REPLACE PROCEDURE set_claim_under_review(
    p_claim_id INT,
    p_dep_id   INT
)
LANGUAGE plpgsql AS $$
DECLARE
    v_claim_dep INT;
BEGIN
    -- get the claim's department
    SELECT dep_id INTO v_claim_dep
    FROM Expense_Claims
    WHERE claim_id = p_claim_id
      AND status   = 'Pending';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Claim % not found or not Pending', p_claim_id;
    END IF;

    -- enforce department boundary
    IF v_claim_dep <> p_dep_id THEN
        RAISE EXCEPTION 'You can only review claims from your own department';
    END IF;

    UPDATE Expense_Claims
    SET status = 'Under_Review'
    WHERE claim_id = p_claim_id;

    RAISE NOTICE 'Claim % is now Under_Review', p_claim_id;
END;
$$;


-- Procedure 3: Approve or reject an employee claim
--   p_claim_id → from UI row click  (never typed)
--   p_user_id  → session.user_id    (never typed)
--   p_dep_id   → session.dep_id     (never typed)
--   p_decision → 'Approved' or 'Rejected' from button click
--
--   Safety checks:
--   1. Claim must be Under_Review
--   2. Claim must belong to manager's own department
--   3. Claim owner must be an Employee (not another manager)
--   4. Manager cannot approve their own claim
--   5. Balance must cover the amount — else auto-rejected
CREATE OR REPLACE PROCEDURE approve_expense(
    p_claim_id INT,
    p_user_id  INT,
    p_dep_id   INT,
    p_decision VARCHAR(50)
)
LANGUAGE plpgsql AS $$
DECLARE
    v_amount NUMERIC(15,2);
    v_claim_dep INT;
    v_claim_owner INT;
    v_owner_role VARCHAR(50);
    v_balance NUMERIC(15,2);
BEGIN
    -- fetch claim — must be Under_Review
    SELECT amount, dep_id, user_id
    INTO   v_amount, v_claim_dep, v_claim_owner
    FROM   Expense_Claims
    WHERE  claim_id = p_claim_id
      AND  status   = 'Under_Review';

    IF NOT FOUND THEN
        RAISE EXCEPTION 'Claim % not found or not Under_Review', p_claim_id;
    END IF;

    -- department boundary: manager can only act on their own dept
    IF v_claim_dep <> p_dep_id THEN
        RAISE EXCEPTION 'You can only approve claims from your own department';
    END IF;

    -- self-approval block
    IF v_claim_owner = p_user_id THEN
        RAISE EXCEPTION 'You cannot approve your own claim';
    END IF;

    -- only employee claims — manager cannot approve another manager's claim
    v_owner_role := get_user_role(v_claim_owner);
    IF v_owner_role <> 'Employee' THEN
        RAISE EXCEPTION 'Managers can only approve Employee claims';
    END IF;

    -- handle rejection
    IF p_decision = 'Rejected' THEN
        UPDATE Expense_Claims 
		SET status = 'Rejected' 
		WHERE claim_id = p_claim_id;
        RAISE NOTICE 'Claim % rejected', p_claim_id;
        RETURN;
    END IF;

    -- balance check

	 BEGIN
        INSERT INTO Verified_Transaction(claim_id, final_amount, verified_by)
        VALUES (p_claim_id, v_amount, p_user_id);

        UPDATE Departments
        SET current_balance = current_balance - v_amount
        WHERE dep_id = v_claim_dep
          AND current_balance >= v_amount;

		IF NOT FOUND THEN
            RAISE EXCEPTION 'Insufficient balance during transaction';
        END IF;

    -- mark approved
    UPDATE Expense_Claims
    SET status = 'Approved'
    WHERE claim_id = p_claim_id;

    EXCEPTION WHEN OTHERS THEN
        RAISE EXCEPTION 'Approval transaction failed and rolled back: %', SQLERRM;
    END;

    RAISE NOTICE 'Claim % approved. % deducted from department %',
                 p_claim_id, v_amount, v_claim_dep;
END;
$$;


CREATE OR REPLACE FUNCTION log_transaction_insert()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO Audit_Trail(target_table, operation, new_data, user_id)
    VALUES (
        'Verified_Transaction',
        'INSERT',
        row_to_json(NEW),
        NEW.verified_by
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_transaction_audit
AFTER INSERT ON Verified_Transaction
FOR EACH ROW
EXECUTE FUNCTION log_transaction_insert();

-- =====================================================
-- SECTION 5: MANAGER USAGE GUIDE
-- =====================================================
--
-- step 1 — LOGIN (manager enters email + password):
--   SELECT * FROM user_login('manager@company.com', 'password123');
--   → returns: user_id=5, role='Manager', dep_id=2, user_name='Ali'
--   → frontend stores all of this in session silently
--
-- step 2 — DASHBOARD badge (how many pending):
--   SELECT pending_claims_count(session.dep_id);
--   → returns: 3
--
-- step 3 — VIEW employee claims in my department:
--   SELECT * FROM manager_department_claims
--   WHERE dep_id = session.dep_id;
--
-- step 4 — OPEN a claim (moves it to Under_Review):
--   CALL set_claim_under_review(claim_id, session.dep_id);
--   → claim_id comes from clicking the row in UI
--
-- step 5 — APPROVE a claim:
--   CALL approve_expense(claim_id, session.user_id, session.dep_id, 'Approved');
--
-- step 6 — REJECT a claim:
--   CALL approve_expense(claim_id, session.user_id, session.dep_id, 'Rejected');
--
-- step 7 — VIEW my department budget report:
--  SELECT * FROM manager_budget_summary(session.dep_id);
--
-- step 8 — SUBMIT my own expense claim:
--   CALL submit_expense_claim(
--       session.user_id,
--       session.dep_id,
--       250.00,
--       'Travel',
--       'https://receipt-url.com/img.jpg'
--   );
--
-- step 9 — VIEW my own submitted claims:
--   SELECT * FROM my_submitted_claims
--   WHERE user_id = session.user_id;
--
-- =====================================================
-- same for employee but employee have only two options submit claim and review sumbit claims

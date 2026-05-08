from db.postgres import get_connection

def get_department_claims(dep_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT * FROM manager_department_claims
            WHERE dep_id = %s
        """, (dep_id,))
        return cur.fetchall()
    except Exception as e:
        print("Error:", e)
        return []
    finally:
        cur.close()
        conn.close()

def get_pending_count(dep_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT pending_claims_count(%s)", (dep_id,))
        result = cur.fetchone()
        return result[0] if result else 0
    except Exception as e:
        print("Error:", e)
        return 0
    finally:
        cur.close()
        conn.close()

def set_under_review(claim_id, dep_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL set_claim_under_review(%s, %s)",
                    (claim_id, dep_id))
        conn.commit()
        return True
    except Exception as e:
        print("Error:", e)
        return False
    finally:
        cur.close()
        conn.close()

def approve_expense(claim_id, user_id, dep_id, decision):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL approve_expense(%s, %s, %s, %s)",
                    (claim_id, user_id, dep_id, decision))
        conn.commit()
        return True
    except Exception as e:
        print("Error:", e)
        return False
    finally:
        cur.close()
        conn.close()

def get_budget_summary(dep_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM manager_budget_summary(%s)",
                    (dep_id,))
        return cur.fetchone()
    except Exception as e:
        print("Error:", e)
        return None
    finally:
        cur.close()
        conn.close()

def submit_claim(user_id, dep_id, amount,
                 cat_name, receipt_url, image_data=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO Expense_Claims
            (user_id, dep_id, cat_id, amount, 
             receipt_url, receipt_image)
            SELECT %s, %s, c.cat_id, %s, %s, %s
            FROM Expense_Categories c
            WHERE c.cat_name = %s
        """, (user_id, dep_id, amount,
              receipt_url, image_data, cat_name))
        conn.commit()
        return True
    except Exception as e:
        print("Error:", e)
        conn.rollback()
        return False
    finally:
        cur.close()
        conn.close()

def get_my_claims(user_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT * FROM my_submitted_claims
            WHERE user_id = %s
        """, (user_id,))
        return cur.fetchall()
    except Exception as e:
        print("Error:", e)
        return []
    finally:
        cur.close()
        conn.close()

def get_claim_image(claim_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT receipt_image, receipt_url
            FROM Expense_Claims
            WHERE claim_id = %s
        """, (claim_id,))
        return cur.fetchone()
    except Exception as e:
        print("Error:", e)
        return None
    finally:
        cur.close()
        conn.close()
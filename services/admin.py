from db.postgres import get_connection

def add_department(dep_name, budget):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL add_department(%s, %s)", (dep_name, budget))
        conn.commit()
        return True
    except Exception as e:
        print("Error:", e)
        return False
    finally:
        cur.close()
        conn.close()

def add_funds(dep_name, amount):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL add_department_funds(%s, %s)", (dep_name, amount))
        conn.commit()
        return True
    except Exception as e:
        print("Error:", e)
        return False
    finally:
        cur.close()
        conn.close()

def get_financial_report():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM admin_company_financial_report")
        return cur.fetchall()
    except Exception as e:
        print("Error:", e)
        return []
    finally:
        cur.close()
        conn.close()

def get_manager_claims():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM admin_manager_claims")
        return cur.fetchall()
    except Exception as e:
        print("Error:", e)
        return []
    finally:
        cur.close()
        conn.close()

def move_claim_to_review(claim_id):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL move_claim_to_review(%s)", (claim_id,))
        conn.commit()
        return True
    except Exception as e:
        print("Error:", e)
        return False
    finally:
        cur.close()
        conn.close()

def approve_manager_expense(claim_id, admin_id, decision):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL approve_manager_expense(%s, %s, %s)",
                    (claim_id, admin_id, decision))
        conn.commit()
        return True
    except Exception as e:
        print("Error:", e)
        return False
    finally:
        cur.close()
        conn.close()

def set_yearly_budget(dep_name, year, budget):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("CALL set_next_yearly_budget(%s, %s, %s)",
                    (dep_name, year, budget))
        conn.commit()
        return True
    except Exception as e:
        print("Error:", e)
        return False
    finally:
        cur.close()
        conn.close()

def get_yearly_budgets():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM admin_yearly_budgets")
        return cur.fetchall()
    except Exception as e:
        print("Error:", e)
        return []
    finally:
        cur.close()
        conn.close()


from db.postgres import get_connection
import base64

def submit_claim(user_id, dep_id, amount, cat_name, receipt_url, image_data=None):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO Expense_Claims
            (user_id, dep_id, cat_id, amount, receipt_url, receipt_image)
            SELECT %s, %s, c.cat_id, %s, %s, %s
            FROM Expense_Categories c
            WHERE c.cat_name = %s
        """, (user_id, dep_id, amount, receipt_url, image_data, cat_name))
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

def get_categories():
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT * FROM get_expense_categories()")
        return cur.fetchall()
    except Exception as e:
        print("Error:", e)
        return []
    finally:
        cur.close()
        conn.close()

def get_claim_image(claim_id):
    """Get image data for a specific claim"""
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
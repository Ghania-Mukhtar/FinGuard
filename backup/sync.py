from db.postgres import get_connection
from db.firebase import get_firestore
import base64

def postgres_to_firebase():
    conn = get_connection()
    cur = conn.cursor()
    db = get_firestore()
    print("Starting PostgreSQL → Firebase backup...")

    # Sync Departments
    cur.execute("""
        SELECT dep_id, dep_name, budget_limit, current_balance 
        FROM Departments
    """)
    for row in cur.fetchall():
        db.collection("departments").document(str(row[0])).set({
            "dep_id": row[0],
            "dep_name": row[1],
            "budget_limit": float(row[2]),
            "current_balance": float(row[3])
        })
    print("Departments synced")

    # Sync Users (no passwords)
    cur.execute("""
        SELECT user_id, user_name, user_email, user_role, dep_id 
        FROM Users
    """)
    for row in cur.fetchall():
        db.collection("users").document(str(row[0])).set({
            "user_id": row[0],
            "user_name": row[1],
            "user_email": row[2],
            "user_role": row[3],
            "dep_id": row[4]
        })
    print("Users synced")

    # Sync Expense Claims
    # Image stored as base64 string in Firebase
    cur.execute("""
        SELECT claim_id, amount, status, user_id, 
               dep_id, cat_id, receipt_url, receipt_image 
        FROM Expense_Claims
    """)
    for row in cur.fetchall():
        # Convert binary image to base64 string for Firebase
        image_b64 = None
        if row[7]:  # if receipt_image exists
            image_bytes = bytes(row[7])
            image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        db.collection("expense_claims").document(str(row[0])).set({
            "claim_id": row[0],
            "amount": float(row[1]),
            "status": row[2],
            "user_id": row[3],
            "dep_id": row[4],
            "cat_id": row[5],
            "receipt_url": row[6] or "",
            "receipt_image_b64": image_b64 or ""
        })
    print("Expense Claims synced")

    # Sync Verified Transactions
    cur.execute("""
        SELECT trx_id::TEXT, claim_id, final_amount, 
               verified_at::TEXT, verified_by 
        FROM Verified_Transaction
    """)
    for row in cur.fetchall():
        db.collection("verified_transactions").document(str(row[0])).set({
            "trx_id": row[0],
            "claim_id": row[1],
            "final_amount": float(row[2]),
            "verified_at": row[3],
            "verified_by": row[4]
        })
    print("Verified Transactions synced")

    # Sync Expense Categories
    cur.execute("""
        SELECT cat_id, cat_name, description 
        FROM Expense_Categories
    """)
    for row in cur.fetchall():
        db.collection("expense_categories").document(str(row[0])).set({
            "cat_id": row[0],
            "cat_name": row[1],
            "description": row[2] or ""
        })
    print("Categories synced")

    cur.close()
    conn.close()
    print("PostgreSQL → Firebase COMPLETE")


def firebase_to_postgres():
    db = get_firestore()
    conn = get_connection()
    cur = conn.cursor()
    print("Starting Firebase → PostgreSQL restore...")

    # Restore Departments
    for doc in db.collection("departments").stream():
        d = doc.to_dict()
        cur.execute("""
            INSERT INTO Departments
            (dep_id, dep_name, budget_limit, current_balance)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (dep_id) DO UPDATE
            SET budget_limit = EXCLUDED.budget_limit,
                current_balance = EXCLUDED.current_balance
        """, (d["dep_id"], d["dep_name"],
              d["budget_limit"], d["current_balance"]))
    print("Departments restored")

    # Restore Expense Categories
    for doc in db.collection("expense_categories").stream():
        d = doc.to_dict()
        cur.execute("""
            INSERT INTO Expense_Categories
            (cat_id, cat_name, description)
            VALUES (%s, %s, %s)
            ON CONFLICT (cat_id) DO UPDATE
            SET cat_name = EXCLUDED.cat_name,
                description = EXCLUDED.description
        """, (d["cat_id"], d["cat_name"], d["description"]))
    print("Categories restored")

    # Restore Users
    for doc in db.collection("users").stream():
        d = doc.to_dict()
        cur.execute("""
            INSERT INTO Users
            (user_id, user_name, user_email, user_role, dep_id, user_password)
            VALUES (%s, %s, %s, %s, %s, 'restored_from_firebase')
            ON CONFLICT (user_id) DO UPDATE
            SET user_name = EXCLUDED.user_name,
                user_role = EXCLUDED.user_role
        """, (d["user_id"], d["user_name"],
              d["user_email"], d["user_role"], d["dep_id"]))
    print("Users restored")

    # Restore Expense Claims
    # Convert base64 image back to binary
    for doc in db.collection("expense_claims").stream():
        d = doc.to_dict()
        image_data = None
        if d.get("receipt_image_b64"):
            image_data = base64.b64decode(
                d["receipt_image_b64"])

        cur.execute("""
            INSERT INTO Expense_Claims
            (claim_id, amount, status, user_id, 
             dep_id, cat_id, receipt_url, receipt_image)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (claim_id) DO UPDATE
            SET status = EXCLUDED.status,
                amount = EXCLUDED.amount,
                receipt_image = EXCLUDED.receipt_image
        """, (d["claim_id"], d["amount"], d["status"],
              d["user_id"], d["dep_id"], d["cat_id"],
              d.get("receipt_url", ""), image_data))
    print("Expense Claims restored")

    conn.commit()
    cur.close()
    conn.close()
    print("Firebase → PostgreSQL COMPLETE")
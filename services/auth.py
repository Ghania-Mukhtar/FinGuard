from db.postgres import get_connection

def login(email, password):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT * FROM user_login(%s, %s)",
            (email, password))
        result = cur.fetchone()
        if result:
            return {
                "user_id": result[0],
                "role": result[1],
                "dep_id": result[2],
                "user_name": result[3]
            }
        return None
    except Exception as e:
        print("Login error:", e)
        return None
    finally:
        cur.close()
        conn.close()

def add_user(name, email, password, role, dep_name):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "CALL add_user(%s, %s, %s, %s, %s)",
            (name, email, password, role, dep_name))
        conn.commit()
        return True
    except Exception as e:
        print("Add user error:", e)
        return False
    finally:
        cur.close()
        conn.close()
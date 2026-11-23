
from config import ADMIN_EMAIL, ADMIN_PASSWORD
from database import init_db, get_db
from auth import hash_password


def reset_admin():
    email = ADMIN_EMAIL.strip().lower()
    password = ADMIN_PASSWORD

    if not email or not password:
        print("ERROR: Check ADMIN_EMAIL and ADMIN_PASSWORD in .env")
        return

    if len(password) < 10:
        print("ERROR: Password must have at least 10 characters.")
        return

    init_db()

    with get_db() as db:
        user = db.execute(
            "SELECT id FROM users WHERE email = ?",
            (email,)
        ).fetchone()

        if user:
            db.execute(
                """
                UPDATE users
                SET password_hash = ?,
                    role = 'admin',
                    is_active = 1
                WHERE id = ?
                """,
                (hash_password(password), user["id"])
            )
            print("Existing account updated successfully.")

        else:
            cursor = db.execute(
                """
                INSERT INTO users
                (name, email, password_hash, role, is_active)
                VALUES (?, ?, ?, 'admin', 1)
                """,
                ("A SQUARE Admin", email, hash_password(password))
            )

            db.execute(
                "INSERT INTO carts(user_id) VALUES(?)",
                (cursor.lastrowid,)
            )
            print("New administrator account created.")

    print("ADMIN ACCOUNT READY!")
    print("Email:", email)


if __name__ == "__main__":
    reset_admin()

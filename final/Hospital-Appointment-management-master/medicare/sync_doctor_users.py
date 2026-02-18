import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('hospital.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT id, name, email FROM doctors")
doctors = cur.fetchall()

created = 0
for doc in doctors:
    cur.execute("SELECT id FROM users WHERE email = ?", (doc["email"],))
    exists = cur.fetchone()
    if not exists:
        cur.execute(
            "INSERT INTO users (name, email, password, role) VALUES (?,?,?,?)",
            (doc["name"], doc["email"], generate_password_hash("password"), "doctor"),
        )
        created += 1

conn.commit()
conn.close()
print(f"Synced doctor accounts. Created {created} new user(s). Default password: 'password'.")

import sqlite3

conn = sqlite3.connect('hospital.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()

cur.execute("SELECT name, email FROM doctors ORDER BY name")
rows = cur.fetchall()

print("Doctor credentials (default password: password)\n")
for r in rows:
    print(f"- {r['name']}  |  {r['email']}  |  password")

conn.close()

import sqlite3
from werkzeug.security import generate_password_hash

def reset_receptionist_password():
    try:
        # Connect to the database
        conn = sqlite3.connect('hospital.db')
        c = conn.cursor()
        
        # New password
        new_password = "reception123"
        hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
        
        # Update the password
        c.execute("UPDATE users SET password = ? WHERE email = ?", 
                 (hashed_password, 'reception@example.com'))
        conn.commit()
        
        # Verify the update
        c.execute("SELECT id, email, role FROM users WHERE email = ?", 
                 ('reception@example.com',))
        user = c.fetchone()
        
        print(f"Password for reception@example.com has been reset to: {new_password}")
        print(f"Updated user: ID={user[0]}, Email={user[1]}, Role={user[2]}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    reset_receptionist_password()

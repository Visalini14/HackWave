import sqlite3
from werkzeug.security import generate_password_hash

def fix_doctor_logins():
    try:
        conn = sqlite3.connect('hospital.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get all doctors from doctors table
        c.execute('SELECT * FROM doctors')
        doctors = c.fetchall()
        
        print("=== Updating Doctor Logins ===\n")
        
        for doc in doctors:
            email = doc['email']
            name = doc['name']
            
            # Check if user exists
            c.execute('SELECT id FROM users WHERE email = ?', (email,))
            user = c.fetchone()
            
            # Create or update user with doctor role
            password_hash = generate_password_hash('doctor123')
            if user:
                # Update existing user
                c.execute('''
                    UPDATE users 
                    SET name = ?, password = ?, role = 'doctor'
                    WHERE email = ?
                ''', (name, password_hash, email))
                print(f"Updated: {name} <{email}>")
            else:
                # Insert new user
                c.execute('''
                    INSERT INTO users (name, email, password, role)
                    VALUES (?, ?, ?, 'doctor')
                ''', (name, email, password_hash))
                print(f"Created: {name} <{email}>")
        
        conn.commit()
        print("\n=== Doctor logins updated successfully! ===")
        print("All doctors can now log in with their email and password: doctor123")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_doctor_logins()

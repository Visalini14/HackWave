import sqlite3

def get_doctor_logins():
    try:
        # Connect to the database
        conn = sqlite3.connect('hospital.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Query to get all doctors
        c.execute('''
            SELECT name, email, specialization_english as specialization 
            FROM doctors 
            ORDER BY name
        ''')
        
        doctors = c.fetchall()
        
        if not doctors:
            print("No doctors found in the database.")
            return
            
        print("\n=== Doctor Login Details ===")
        print("Note: Default password for all doctors is 'doctor123'\n")
        
        # Print each doctor's details
        for i, doctor in enumerate(doctors, 1):
            print(f"{i}. Name: {doctor['name']}")
            print(f"   Email: {doctor['email']}")
            print(f"   Specialization: {doctor['specialization'] or 'N/A'}")
            print("   Password: doctor123\n")
            
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    get_doctor_logins()

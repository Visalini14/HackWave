import sqlite3

def get_doctors():
    try:
        conn = sqlite3.connect('hospital.db')
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get all doctors
        c.execute('SELECT * FROM doctors')
        doctors = c.fetchall()
        
        print("\n=== Doctor Login Details ===")
        print("Note: Default password for all doctors is 'doctor123'\n")
        
        for i, doc in enumerate(doctors, 1):
            print(f"{i}. Name: {doc['name']}")
            print(f"   Email: {doc['email']}")
            print(f"   Specialization: {doc['specialization_english'] if 'specialization_english' in dict(doc) and doc['specialization_english'] else 'N/A'}")
            print(f"   Hospital ID: {doc['hospital_id'] if 'hospital_id' in dict(doc) else 'N/A'}")
            print(f"   Contact: {doc['contact'] if 'contact' in dict(doc) and doc['contact'] else 'N/A'}")
            print("   Password: doctor123\n")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    get_doctors()

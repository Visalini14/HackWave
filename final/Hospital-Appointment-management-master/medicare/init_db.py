import sqlite3
import pandas as pd
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('hospital.db')
c = conn.cursor()

# Drop existing tables
c.execute('DROP TABLE IF EXISTS users')
c.execute('DROP TABLE IF EXISTS appointments')
c.execute('DROP TABLE IF EXISTS hospitals')
c.execute('DROP TABLE IF EXISTS doctors')

# Create tables
c.execute('''CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    password TEXT,
    role TEXT
)''')

c.execute('''CREATE TABLE appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER,
    doctor_id INTEGER,
    hospital_id INTEGER,
    date TEXT,
    time TEXT,
    status TEXT,
    specialization TEXT,
    FOREIGN KEY (patient_id) REFERENCES users (id),
    FOREIGN KEY (doctor_id) REFERENCES doctors (id),
    FOREIGN KEY (hospital_id) REFERENCES hospitals (id)
)''')

c.execute('''CREATE TABLE hospitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    location TEXT,
    contact TEXT
)''')

c.execute('''CREATE TABLE doctors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    specialization_english TEXT,
    specialization_tamil TEXT,
    hospital_id INTEGER,
    email TEXT,
    contact TEXT,
    FOREIGN KEY (hospital_id) REFERENCES hospitals (id)
)''')

# Import CSV data
try:
    df = pd.read_csv('HospitalDataset.csv')
    expected_cols = {'Hospital_Name', 'Doctor_Name', 'Specialization_English', 'Specialization_TamilEnglish'}
    if not expected_cols.issubset(set(df.columns)):
        # Fallback: lines are fully quoted; parse manually
        df_raw = pd.read_csv('HospitalDataset.csv', header=None, names=['raw'], dtype=str)
        df_raw = df_raw.dropna(subset=['raw'])
        parts = df_raw['raw'].astype(str).str.strip('"').str.split(',', expand=True)
        header = parts.iloc[0].tolist()
        data = parts.iloc[1:].reset_index(drop=True)
        data.columns = header
        df = data
    
    # Trim whitespace
    for col in ['Hospital_Name','Doctor_Name','Specialization_English','Specialization_TamilEnglish']:
        df[col] = df[col].astype(str).str.strip()
    
    # Insert hospitals
    hospitals = df[['Hospital_Name']].drop_duplicates()
    hospital_map = {}
    for idx, row in hospitals.iterrows():
        c.execute('INSERT INTO hospitals (name, location, contact) VALUES (?, ?, ?)',
                 (row['Hospital_Name'], 'Erode, Tamil Nadu', 'Contact: +91-XXX-XXXX'))
        hospital_id = c.lastrowid
        hospital_map[row['Hospital_Name']] = hospital_id
    
    # Insert doctors
    for idx, row in df.iterrows():
        hospital_id = hospital_map.get(row['Hospital_Name'])
        if not hospital_id:
            continue
        email = f"{row['Doctor_Name'].replace(' ', '').replace('.', '').lower()}@medicare.com"
        c.execute('''INSERT INTO doctors (name, specialization_english, specialization_tamil, 
                                        hospital_id, email, contact) 
                     VALUES (?, ?, ?, ?, ?, ?)''',
                 (row['Doctor_Name'], row['Specialization_English'], 
                  row['Specialization_TamilEnglish'], hospital_id, email, 'Contact: +91-XXX-XXXX'))
    
    print(f"Imported {len(df)} records from CSV")
except Exception as e:
    print(f"Error importing CSV: {e}")

# Sample users
c.execute('INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)',
          ('Dr. Smith','doctor@example.com', generate_password_hash('password'),'doctor'))
c.execute('INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)',
          ('John Doe','patient@example.com', generate_password_hash('password'),'patient'))
c.execute('INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)',
          ('Front Desk','reception@example.com', generate_password_hash('password'),'receptionist'))

conn.commit()
conn.close()
print('Database initialized with CSV data.')

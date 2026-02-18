# Hospital Appointment Scheduling App (Flask)

## Quick start
1. Create virtualenv and install requirements:
   ```bash
   python -m venv venv
   source venv/bin/activate    # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
2. Initialize DB and optionally import CSV:
   ```bash
   python init_db.py
   python import_csv.py erode_hospital_appointments_tamil.csv
   ```
3. Run the app:
   ```bash
   set FLASK_APP=app.py   # Windows PowerShell: $env:FLASK_APP="app.py"
   python -m flask run
   ```

Open http://127.0.0.1:5000

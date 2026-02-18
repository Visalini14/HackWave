from flask import Flask, render_template, request, redirect, url_for, session, flash, send_from_directory, abort
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
except Exception:
    # reportlab may not be installed during import; runtime route will fail gracefully
    A4 = None
    canvas = None

app = Flask(__name__)
app.secret_key = 'secret123'
ALLOWED_ROLES = {'patient', 'doctor', 'receptionist'}

@app.after_request
def add_no_cache_headers(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def get_db():
    conn = sqlite3.connect('hospital.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if not email or not password:
            flash('Email and password are required')
            return render_template('login.html')
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            flash('Invalid email format')
            return render_template('login.html')
        conn = get_db()
        user = conn.execute('SELECT * FROM users WHERE email=?',(email,)).fetchone()
        # Pre-fetch doctor id if applicable
        doctor_id = None
        if user and user['role'] == 'doctor':
            d = conn.execute('SELECT id FROM doctors WHERE email=?', (email,)).fetchone()
            if d:
                doctor_id = d['id']
        conn.close()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']
            session['email'] = email
            if user['role'] == 'doctor' and doctor_id:
                session['doctor_id'] = doctor_id
            if user['role'] == 'doctor':
                return redirect(url_for('doctor_dashboard'))
            if user['role'] == 'receptionist':
                return redirect(url_for('receptionist_dashboard'))
            else:
                return redirect(url_for('patient_dashboard'))
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password_raw = request.form['password']
        role = request.form['role']

        # Basic validations
        if not name or not email or not password_raw or not role:
            flash('All fields are required')
            return render_template('register.html')
        if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
            flash('Invalid email format')
            return render_template('register.html')
        if role not in ALLOWED_ROLES:
            flash('Invalid role selected')
            return render_template('register.html')
        if len(password_raw) < 8:
            flash('Password must be at least 8 characters')
            return render_template('register.html')

        password = generate_password_hash(password_raw)
        conn = get_db()
        # Check for existing email
        existing = conn.execute('SELECT id FROM users WHERE email=?', (email,)).fetchone()
        if existing:
            conn.close()
            flash('Email already registered')
            return render_template('register.html')
        conn.execute('INSERT INTO users (name,email,password,role) VALUES (?,?,?,?)',
                     (name,email,password,role))
        conn.commit()
        conn.close()
        flash('Registered successfully, please login')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/patient/dashboard')
def patient_dashboard():
    if session.get('role') != 'patient':
        return redirect(url_for('login'))
    conn = get_db()
    appointments = conn.execute('''SELECT a.*, d.name as doctor_name, h.name as hospital_name 
                                  FROM appointments a 
                                  LEFT JOIN doctors d ON a.doctor_id = d.id 
                                  LEFT JOIN hospitals h ON a.hospital_id = h.id 
                                  WHERE a.patient_id=? 
                                  ORDER BY a.date DESC, a.time DESC''',
                                (session['user_id'],)).fetchall()
    conn.close()
    return render_template('patient_dashboard.html', appointments=appointments)

@app.route('/doctor/dashboard')
def doctor_dashboard():
    if session.get('role') != 'doctor':
        return redirect(url_for('login'))
    conn = get_db()
    # Filter by logged-in doctor
    doctor_email = session.get('email')
    if doctor_email:
        appointments = conn.execute('''SELECT a.*, u.name as patient_name
                                       FROM appointments a
                                       JOIN users u ON a.patient_id = u.id
                                       JOIN doctors d ON a.doctor_id = d.id
                                       WHERE d.email = ?
                                       ORDER BY a.date DESC, a.time DESC''', (doctor_email,)).fetchall()
    else:
        appointments = []
    conn.close()
    return render_template('doctor_dashboard.html', appointments=appointments)

@app.route('/receptionist/dashboard')
def receptionist_dashboard():
    if session.get('role') != 'receptionist':
        return redirect(url_for('login'))
    conn = get_db()
    appointments = conn.execute('''SELECT a.*, 
                                          u.name as patient_name, 
                                          d.name as doctor_name, 
                                          h.name as hospital_name 
                                   FROM appointments a 
                                   JOIN users u ON a.patient_id = u.id 
                                   JOIN doctors d ON a.doctor_id = d.id 
                                   JOIN hospitals h ON a.hospital_id = h.id 
                                   ORDER BY a.date DESC, a.time DESC''').fetchall()
    conn.close()
    return render_template('receptionist_dashboard.html', appointments=appointments)

@app.route('/book', methods=['GET','POST'])
def book():
    if session.get('role') != 'patient':
        return redirect(url_for('login'))
    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        doctor_id = request.form['doctor_id']
        hospital_id = request.form['hospital_id']
        specialization = request.form['specialization']
        conn = get_db()
        cur = conn.cursor()
        cur.execute('''INSERT INTO appointments (patient_id,doctor_id,hospital_id,date,time,status,specialization) 
                        VALUES (?,?,?,?,?,?,?)''',
                    (session['user_id'],doctor_id,hospital_id,date,time,'Pending',specialization))
        appointment_id = cur.lastrowid
        conn.commit()

        # Fetch full appointment details for receipt
        appt = conn.execute('''SELECT a.id, a.date, a.time, a.status, a.specialization,
                                      u.name as patient_name, d.name as doctor_name, h.name as hospital_name
                               FROM appointments a
                               JOIN users u ON a.patient_id = u.id
                               JOIN doctors d ON a.doctor_id = d.id
                               JOIN hospitals h ON a.hospital_id = h.id
                               WHERE a.id = ?''', (appointment_id,)).fetchone()

        # Generate PDF receipt if reportlab is available
        try:
            if canvas is not None:
                receipts_dir = os.path.join(os.getcwd(), 'receipts')
                os.makedirs(receipts_dir, exist_ok=True)
                pdf_path = os.path.join(receipts_dir, f"appointment_{appointment_id}.pdf")

                c = canvas.Canvas(pdf_path, pagesize=A4)
                width, height = A4

                y = height - 50
                c.setFont("Helvetica-Bold", 18)
                c.drawString(50, y, "MediCare - Appointment Receipt")
                y -= 30
                c.setFont("Helvetica", 12)
                c.drawString(50, y, f"Receipt ID: APPT-{appointment_id:06d}")
                y -= 20
                c.drawString(50, y, f"Patient: {appt['patient_name']}")
                y -= 20
                c.drawString(50, y, f"Doctor: {appt['doctor_name']}")
                y -= 20
                c.drawString(50, y, f"Hospital: {appt['hospital_name']}")
                y -= 20
                c.drawString(50, y, f"Specialization: {appt['specialization']}")
                y -= 20
                c.drawString(50, y, f"Date: {appt['date']}    Time: {appt['time']}")
                y -= 20
                c.drawString(50, y, f"Status: {appt['status']}")
                y -= 40
                c.setFont("Helvetica-Oblique", 10)
                c.drawString(50, y, "This is a system generated receipt. For assistance contact support@medicare.com")
                c.showPage()
                c.save()
        except Exception:
            # Do not block booking if PDF generation fails
            pass

        conn.close()
        flash('Appointment booked successfully!')
        return redirect(url_for('patient_dashboard'))
    
    conn = get_db()
    doctors = conn.execute('''SELECT d.*, h.name as hospital_name 
                             FROM doctors d 
                             JOIN hospitals h ON d.hospital_id = h.id 
                             ORDER BY d.name''').fetchall()
    conn.close()
    
    from datetime import date
    today = date.today().strftime('%Y-%m-%d')
    return render_template('book.html', doctors=doctors, today=today)

@app.route('/hospitals')
def hospitals():
    conn = get_db()
    hospitals = conn.execute('''SELECT h.*, d.name as doctor_name, d.specialization_english, d.specialization_tamil
                               FROM hospitals h 
                               LEFT JOIN doctors d ON h.id = d.hospital_id 
                               ORDER BY h.name''').fetchall()
    conn.close()
    return render_template('hospitals.html', hospitals=hospitals)

@app.route('/doctors')
def doctors():
    specialization = request.args.get('specialization', '')
    hospital = request.args.get('hospital', '')
    conn = get_db()
    
    # Build the query based on filters
    query = '''SELECT d.*, h.name as hospital_name 
               FROM doctors d 
               JOIN hospitals h ON d.hospital_id = h.id'''
    
    conditions = []
    params = []
    
    if specialization:
        conditions.append('d.specialization_english LIKE ?')
        params.append(f'%{specialization}%')
    
    if hospital:
        conditions.append('h.name = ?')
        params.append(hospital)
    
    if conditions:
        query += ' WHERE ' + ' AND '.join(conditions)
    
    query += ' ORDER BY d.name'
    
    doctors = conn.execute(query, params).fetchall()
    conn.close()
    return render_template('doctors.html', doctors=doctors, specialization=specialization, hospital=hospital)

# Confirm appointment (doctor-only)
@app.route('/appointments/<int:appointment_id>/confirm', methods=['POST'])
def confirm_appointment(appointment_id: int):
    if session.get('role') != 'receptionist':
        flash('Unauthorized')
        return redirect(url_for('login'))
    conn = get_db()
    conn.execute('UPDATE appointments SET status=? WHERE id=?', ('Confirmed', appointment_id))
    conn.commit()
    conn.close()
    flash('Appointment confirmed')
    return redirect(url_for('receptionist_dashboard'))

# Download appointment receipt PDF
@app.route('/appointments/<int:appointment_id>/receipt')
def download_receipt(appointment_id: int):
    if not session.get('user_id'):
        return redirect(url_for('login'))
    receipts_dir = os.path.join(os.getcwd(), 'receipts')
    filename = f"appointment_{appointment_id}.pdf"
    file_path = os.path.join(receipts_dir, filename)
    if not os.path.exists(file_path):
        abort(404)
    return send_from_directory(receipts_dir, filename, as_attachment=True)

# Reschedule appointment (patient can reschedule own; doctor and receptionist can reschedule their appointments)
@app.route('/appointments/<int:appointment_id>/reschedule', methods=['GET','POST'])
def reschedule_appointment(appointment_id: int):
    role = session.get('role')
    if role not in ('patient', 'receptionist', 'doctor'):
        flash('Unauthorized')
        return redirect(url_for('login'))
        
    conn = get_db()
    appt = conn.execute('''SELECT a.*, u.name as patient_name, d.name as doctor_name, h.name as hospital_name, d.email as doctor_email
                           FROM appointments a
                           JOIN users u ON a.patient_id = u.id
                           JOIN doctors d ON a.doctor_id = d.id
                           JOIN hospitals h ON a.hospital_id = h.id
                           WHERE a.id = ?''', (appointment_id,)).fetchone()
    if not appt:
        conn.close()
        abort(404)
        
    # Check authorization
    if role == 'patient' and appt['patient_id'] != session.get('user_id'):
        conn.close()
        flash('You can only reschedule your own appointments')
        return redirect(url_for('patient_dashboard'))
        
    if role == 'doctor' and appt['doctor_email'] != session.get('email'):
        conn.close()
        flash('You can only reschedule your own appointments')
        return redirect(url_for('doctor_dashboard'))
    
    if request.method == 'POST':
        new_date = request.form.get('date')
        new_time = request.form.get('time')
        if not new_date or not new_time:
            flash('Date and Time are required')
            return render_template('reschedule.html', appt=appt)
            
        conn.execute('UPDATE appointments SET date=?, time=?, status=? WHERE id=?',
                     (new_date, new_time, 'Pending' if role == 'patient' else 'Scheduled', appointment_id))
        conn.commit()
        conn.close()
        
        flash('Appointment rescheduled')
        if role == 'receptionist':
            return redirect(url_for('receptionist_dashboard'))
        elif role == 'doctor':
            return redirect(url_for('doctor_dashboard'))
        return redirect(url_for('patient_dashboard'))
        
    conn.close()
    return render_template('reschedule.html', appt=appt)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

if __name__ == '__main__':
    use_https = os.getenv('FLASK_HTTPS', '0') == '1'
    if use_https:
        # Uses a self-signed certificate for local development
        app.run(debug=True, ssl_context='adhoc')
    else:
        app.run(debug=True)

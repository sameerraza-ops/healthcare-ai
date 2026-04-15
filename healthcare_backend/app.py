import os
from flask import Flask, jsonify, request
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)


# =========================
# Database Connection Helper
# =========================
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        port=int(os.getenv("DB_PORT", 3306))
    )


# =========================
# Home Route
# =========================
@app.route('/')
def home():
    return jsonify({"message": "Flask backend is running successfully!"})


# =========================
# Doctors Routes
# =========================
@app.route('/doctors', methods=['GET'])
def get_doctors():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM doctors")
    doctors = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(doctors)


@app.route('/admins', methods=['GET'])
def get_admins():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM admins")
    admins = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(admins)


# =========================
# Patient Routes
# =========================
@app.route('/add-patient', methods=['POST'])
def add_patient():
    try:
        data = request.get_json()

        full_name = data.get('full_name')
        age = data.get('age')
        gender = data.get('gender')
        phone = data.get('phone')
        symptoms = data.get('symptoms')
        urgency_level = data.get('urgency_level')

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO patients (full_name, age, gender, phone, symptoms, urgency_level)
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        values = (full_name, age, gender, phone, symptoms, urgency_level)

        cursor.execute(sql, values)
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Patient added successfully!"})
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@app.route('/patients', methods=['GET'])
def get_patients():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM patients")
    patients = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(patients)


# =========================
# Consultation Routes
# =========================
@app.route('/save-consultation', methods=['POST'])
def save_consultation():
    try:
        data = request.get_json()

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO consultation_requests 
        (patient_name, extracted_symptoms, risk_level, doctor_suggestion, status, payment_status)
        VALUES (%s, %s, %s, %s, 'Pending', 'Pending')
        """
        values = (
            data.get('patient_name'),
            data.get('extracted_symptoms'),
            data.get('risk_level'),
            data.get('doctor_suggestion')
        )

        cursor.execute(sql, values)
        conn.commit()

        new_id = cursor.lastrowid

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Data saved! Proceed to payment.",
            "request_id": new_id
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/consultations', methods=['GET'])
def get_consultations():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM consultation_requests ORDER BY created_at DESC")
    consultations = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(consultations)


@app.route('/update-status', methods=['POST'])
def update_status():
    try:
        data = request.get_json()
        request_id = data.get('request_id')
        status = data.get('status')
        payment_status = data.get('payment_status')

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = "UPDATE consultation_requests SET status=%s, payment_status=%s WHERE request_id=%s"
        cursor.execute(sql, (status, payment_status, request_id))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Status and Payment updated successfully!"})
    except Exception as e:
        return jsonify({"message": str(e)}), 500


@app.route('/save-prescription', methods=['POST'])
def save_prescription():
    try:
        data = request.get_json()

        request_id = data.get('request_id')
        medicines = data.get('medicines')
        prescription_note = data.get('prescription_note')

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
        UPDATE consultation_requests 
        SET medicines = %s, prescription_note = %s, status = 'Completed' 
        WHERE request_id = %s
        """
        values = (medicines, prescription_note, request_id)

        cursor.execute(sql, values)
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Prescription saved and consultation marked as completed!"
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# =========================
# Dashboard Routes
# =========================
@app.route('/dashboard-summary', methods=['GET'])
def dashboard_summary():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total_doctors FROM doctors")
    total_doctors = cursor.fetchone()['total_doctors']

    cursor.execute("SELECT COUNT(*) AS total_requests FROM consultation_requests")
    total_requests = cursor.fetchone()['total_requests']

    cursor.execute("SELECT COUNT(*) AS completed_requests FROM consultation_requests WHERE status = 'Completed'")
    completed_requests = cursor.fetchone()['completed_requests']

    cursor.close()
    conn.close()

    return jsonify({
        "total_doctors": total_doctors,
        "total_requests": total_requests,
        "completed_requests": completed_requests
    })


@app.route('/home-data', methods=['GET'])
def home_data():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total_doctors FROM doctors")
    total_doctors = cursor.fetchone()['total_doctors']

    cursor.execute("SELECT COUNT(*) AS total_requests FROM consultation_requests")
    total_requests = cursor.fetchone()['total_requests']

    cursor.execute("SELECT COUNT(*) AS completed_requests FROM consultation_requests WHERE status = 'Completed'")
    completed_requests = cursor.fetchone()['completed_requests']

    cursor.execute("""
        SELECT patient_name, extracted_symptoms, risk_level, status, created_at
        FROM consultation_requests
        ORDER BY created_at DESC
        LIMIT 1
    """)
    latest_request = cursor.fetchone()

    cursor.execute("""
        SELECT patient_name, status, created_at
        FROM consultation_requests
        WHERE status = 'Completed'
        ORDER BY created_at DESC
        LIMIT 1
    """)
    latest_completed = cursor.fetchone()

    cursor.close()
    conn.close()

    return jsonify({
        "total_doctors": total_doctors,
        "total_requests": total_requests,
        "completed_requests": completed_requests,
        "latest_request": latest_request,
        "latest_completed": latest_completed
    })


# =========================
# Register & Login Routes
# =========================
@app.route('/register-user', methods=['POST'])
def register_user():
    try:
        data = request.get_json()

        role = data.get('role')
        full_name = data.get('full_name')
        age = data.get('age')
        email = data.get('email')
        password = data.get('password')

        conn = get_db_connection()
        cursor = conn.cursor()

        if role == 'patient':
            sql = """
            INSERT INTO patients (full_name, age, email, password)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (full_name, age, email, password))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"message": "Patient registered successfully!"})

        elif role == 'doctor':
            sql = """
            INSERT INTO doctors (full_name, specialization, email, password)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(sql, (full_name, "General Physician", email, password))
            conn.commit()
            cursor.close()
            conn.close()
            return jsonify({"message": "Doctor registered successfully!"})

        cursor.close()
        conn.close()
        return jsonify({"message": "Invalid role"}), 400

    except Exception as e:
        return jsonify({"message": str(e)}), 500


@app.route('/patient-login', methods=['POST'])
def patient_login():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    sql = "SELECT * FROM patients WHERE email=%s AND password=%s"
    cursor.execute(sql, (email, password))
    patient = cursor.fetchone()

    cursor.close()
    conn.close()

    if patient:
        return jsonify({
            "message": "Patient login successful",
            "role": "patient",
            "full_name": patient['full_name']
        })
    else:
        return jsonify({"message": "Invalid patient credentials"}), 401


@app.route('/doctor-login', methods=['POST'])
def doctor_login():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    sql = "SELECT * FROM doctors WHERE email=%s AND password=%s"
    cursor.execute(sql, (email, password))
    doctor = cursor.fetchone()

    cursor.close()
    conn.close()

    if doctor:
        return jsonify({
            "message": "Doctor login successful",
            "role": "doctor",
            "full_name": doctor['full_name']
        })
    else:
        return jsonify({"message": "Invalid doctor credentials"}), 401


@app.route('/admin-login', methods=['POST'])
def admin_login():
    data = request.get_json()

    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    sql = "SELECT * FROM admins WHERE username=%s AND password=%s"
    cursor.execute(sql, (username, password))
    admin = cursor.fetchone()

    cursor.close()
    conn.close()

    if admin:
        return jsonify({
            "message": "Admin login successful",
            "role": "admin",
            "username": admin['username']
        })
    else:
        return jsonify({"message": "Invalid admin credentials"}), 401


# =========================
# Admin Routes
# =========================
@app.route('/admin-summary', methods=['GET'])
def admin_summary():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total_patients FROM patients")
    total_patients = cursor.fetchone()['total_patients']

    cursor.execute("SELECT COUNT(*) AS total_doctors FROM doctors")
    total_doctors = cursor.fetchone()['total_doctors']

    cursor.execute("SELECT COUNT(*) AS total_consultations FROM consultation_requests")
    total_consultations = cursor.fetchone()['total_consultations']

    cursor.execute("SELECT COUNT(*) AS completed_cases FROM consultation_requests WHERE status = 'Completed'")
    completed_cases = cursor.fetchone()['completed_cases']

    cursor.execute("""
        SELECT patient_name, extracted_symptoms, risk_level, status, created_at
        FROM consultation_requests
        ORDER BY created_at DESC
        LIMIT 5
    """)
    recent_requests = cursor.fetchall()

    cursor.execute("""
        SELECT doctor_id, full_name, specialization, email, availability_status, status
        FROM doctors
        ORDER BY doctor_id DESC
        LIMIT 5
    """)
    recent_doctors = cursor.fetchall()

    cursor.close()
    conn.close()

    return jsonify({
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "total_consultations": total_consultations,
        "completed_cases": completed_cases,
        "recent_requests": recent_requests,
        "recent_doctors": recent_doctors
    })


@app.route('/update-doctor-status', methods=['POST'])
def update_doctor_status():
    try:
        data = request.get_json()

        doctor_id = data.get('doctor_id')
        status = data.get('status')

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = "UPDATE doctors SET status=%s WHERE doctor_id=%s"
        cursor.execute(sql, (status, doctor_id))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Doctor status updated successfully!"})
    except Exception as e:
        return jsonify({"message": str(e)}), 500


# =========================
# Payment Routes
# =========================
@app.route('/process_payment', methods=['POST'])
def process_payment():
    try:
        data = request.get_json()

        reference_id = data.get('reference_id')
        patient_name = data.get('patient_name')
        email = data.get('email')
        phone = data.get('phone')
        amount = data.get('amount')
        method = data.get('method')

        if not reference_id or not patient_name or not amount or not method:
            return jsonify({"status": "error", "message": "Missing required fields"}), 400

        conn = get_db_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO payments (reference_id, patient_name, email, phone, amount, method, payment_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (reference_id, patient_name, email, phone, amount, method, "Success"))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "status": "success",
            "message": "Payment saved successfully",
            "redirect_url": "/records-patient"
        })

    except mysql.connector.Error as err:
        return jsonify({"status": "error", "message": str(err)}), 500

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/get-my-prescription', methods=['GET'])
def get_my_prescription():
    try:
        patient_name = request.args.get('name')

        if not patient_name:
            return jsonify({"status": "error", "message": "Name is required"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        sql = """
            SELECT patient_name, extracted_symptoms, risk_level, medicines, prescription_note, created_at 
            FROM consultation_requests 
            WHERE patient_name = %s AND status = 'Completed' 
            ORDER BY created_at DESC LIMIT 1
        """
        cursor.execute(sql, (patient_name,))
        prescription = cursor.fetchone()

        cursor.close()
        conn.close()

        if prescription:
            return jsonify({
                "status": "success",
                "data": prescription
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Abhi tak koi prescription nahi mili."
            })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/records-patient', methods=['GET'])
def records_patient():
    return """
    <h1>Payment Successful</h1>
    <p>Your payment has been saved and verified in database.</p>
    <a href='/'>Go Home</a>
    """


if __name__ == '__main__':
    app.run(debug=True)
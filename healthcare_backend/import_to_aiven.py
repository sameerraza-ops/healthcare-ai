import getpass
import re
import mysql.connector

SQL_FILE = r"R:\healthcare_ai.sql"

config = {
    "host": "healthcare-db-healthcare-ai.i.aivencloud.com",
    "port": 21148,
    "user": "avnadmin",
    "password": getpass.getpass("Enter Aiven password: "),
    "database": "healthcare_ai",
    "autocommit": True,
}

SCHEMA_SQL = [
    "DROP TABLE IF EXISTS consultations",
    "DROP TABLE IF EXISTS payments",
    "DROP TABLE IF EXISTS consultation_requests",
    "DROP TABLE IF EXISTS admins",
    "DROP TABLE IF EXISTS doctors",
    "DROP TABLE IF EXISTS patients",

    """
    CREATE TABLE admins (
      admin_id INT NOT NULL AUTO_INCREMENT,
      username VARCHAR(50) NOT NULL,
      password VARCHAR(255) NOT NULL,
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (admin_id),
      UNIQUE KEY username (username)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """,

    """
    CREATE TABLE doctors (
      doctor_id INT NOT NULL AUTO_INCREMENT,
      full_name VARCHAR(100) NOT NULL,
      specialization VARCHAR(100) NOT NULL,
      phone VARCHAR(15) DEFAULT NULL,
      email VARCHAR(100) DEFAULT NULL,
      password VARCHAR(255) NOT NULL,
      availability_status VARCHAR(20) DEFAULT 'Available',
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      status VARCHAR(20) DEFAULT 'Pending',
      PRIMARY KEY (doctor_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """,

    """
    CREATE TABLE patients (
      patient_id INT NOT NULL AUTO_INCREMENT,
      full_name VARCHAR(100) NOT NULL,
      age INT NOT NULL,
      gender VARCHAR(20) DEFAULT '',
      phone VARCHAR(15) DEFAULT NULL,
      symptoms TEXT DEFAULT NULL,
      urgency_level VARCHAR(20) DEFAULT NULL,
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      email VARCHAR(100) DEFAULT NULL,
      password VARCHAR(255) DEFAULT NULL,
      PRIMARY KEY (patient_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """,

    """
    CREATE TABLE consultation_requests (
      request_id INT NOT NULL AUTO_INCREMENT,
      patient_name VARCHAR(100) NOT NULL,
      extracted_symptoms TEXT NOT NULL,
      risk_level VARCHAR(50) NOT NULL,
      doctor_suggestion VARCHAR(255) DEFAULT NULL,
      status VARCHAR(20) DEFAULT 'Pending',
      medicines TEXT DEFAULT NULL,
      prescription_note TEXT DEFAULT NULL,
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      payment_status ENUM('Pending','Paid') DEFAULT 'Pending',
      amount DECIMAL(10,2) DEFAULT 499.00,
      PRIMARY KEY (request_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """,

    """
    CREATE TABLE payments (
      payment_id INT NOT NULL AUTO_INCREMENT,
      reference_id VARCHAR(50) NOT NULL,
      patient_name VARCHAR(100) NOT NULL,
      email VARCHAR(100) DEFAULT NULL,
      phone VARCHAR(20) DEFAULT NULL,
      amount DECIMAL(10,2) NOT NULL,
      method VARCHAR(20) NOT NULL,
      payment_status VARCHAR(20) DEFAULT 'Success',
      created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      PRIMARY KEY (payment_id),
      UNIQUE KEY reference_id (reference_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """,

    """
    CREATE TABLE consultations (
      consultation_id INT NOT NULL AUTO_INCREMENT,
      patient_id INT NOT NULL,
      doctor_id INT NOT NULL,
      consultation_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
      diagnosis TEXT DEFAULT NULL,
      prescription TEXT DEFAULT NULL,
      status VARCHAR(20) DEFAULT 'Pending',
      PRIMARY KEY (consultation_id),
      KEY patient_id (patient_id),
      KEY doctor_id (doctor_id),
      CONSTRAINT consultations_ibfk_1 FOREIGN KEY (patient_id) REFERENCES patients (patient_id),
      CONSTRAINT consultations_ibfk_2 FOREIGN KEY (doctor_id) REFERENCES doctors (doctor_id)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci
    """,
]

ALLOWED_TABLES = {
    "admins",
    "doctors",
    "patients",
    "consultation_requests",
    "payments",
    "consultations",
}

def extract_insert_statements(sql_text: str):
    pattern = r"INSERT INTO\s+`?([a-zA-Z0-9_]+)`?.*?;"
    matches = re.finditer(pattern, sql_text, flags=re.IGNORECASE | re.DOTALL)
    inserts = []

    for m in matches:
        table_name = m.group(1).lower()
        stmt = m.group(0).strip()
        if table_name in ALLOWED_TABLES:
            inserts.append(stmt)

    return inserts

try:
    print("Connecting to Aiven MySQL...")
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()

    print("Creating schema...")
    for stmt in SCHEMA_SQL:
        cursor.execute(stmt)

    print("Reading SQL dump...")
    with open(SQL_FILE, "r", encoding="utf-8", errors="ignore") as f:
        raw_sql = f.read()

    print("Extracting INSERT statements...")
    inserts = extract_insert_statements(raw_sql)
    print(f"Found {len(inserts)} INSERT statements")

    executed = 0
    failed = 0

    for stmt in inserts:
        try:
            cursor.execute(stmt)
            executed += 1
        except Exception as e:
            failed += 1
            print("\n❌ Insert failed:")
            print(str(e))
            print(stmt[:1200])
            print()

    conn.commit()

    print(f"\nExecuted inserts: {executed}")
    print(f"Failed inserts: {failed}")

    print("\nChecking row counts...")
    for table in ["admins", "doctors", "patients", "consultation_requests", "payments", "consultations"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"{table}: {count}")

    cursor.close()
    conn.close()
    print("\nImport successful ✅")

except Exception as e:
    print("Import failed ❌")
    print(str(e))
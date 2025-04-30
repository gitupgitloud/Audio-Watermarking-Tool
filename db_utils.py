import sqlite3
from hashlib import sha256

DB_PATH = 'watermarking.db'

def get_db_connection():
    return sqlite3.connect(DB_PATH)

# Hash passwords for basic security
def hash_password(password):
    return sha256(password.encode()).hexdigest()

# Register a new user
def register_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hash_password(password)))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False  # Username already exists
    finally:
        conn.close()

# Log in an existing user
def login_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, hash_password(password)))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None  # Return user ID or None

# Store a file entry
def store_file(user_id, filename, watermark_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO files (user_id, filename, watermark) VALUES (?, ?, ?)",
                   (user_id, filename, watermark_data))
    conn.commit()
    conn.close()

# Fetch all files for a user
def get_user_files(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, timestamp FROM files WHERE user_id = ?", (user_id,))
    results = cursor.fetchall()
    conn.close()
    return results

# Fetch watermark by file ID
def get_watermark_by_file_id(file_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT watermark FROM files WHERE id = ?", (file_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

def init_db():
    conn = sqlite3.connect("watermarking.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_watermarked_file(user_id, file_path, method, watermark, audio_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO watermarked_audio (user_id, file_path, method, watermark, audio_data)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, file_path, method, watermark, audio_data))
    conn.commit()
    conn.close()

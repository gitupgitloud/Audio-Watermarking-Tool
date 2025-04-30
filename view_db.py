import sqlite3

def view_users():
    try:
        conn = sqlite3.connect("watermarking.db")
        cursor = conn.cursor()

        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("Tables:", tables)

        # Try to read users table if it exists
        if ('users',) in tables:
            cursor.execute("SELECT * FROM users;")
            users = cursor.fetchall()
            print("\nUsers:")
            for user in users:
                print(user)
        else:
            print("\nNo 'users' table found!")

    except sqlite3.Error as e:
        print("SQLite error:", e)
    finally:
        conn.close()

if __name__ == "__main__":
    view_users()

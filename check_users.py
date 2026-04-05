import sqlite3
import os

db_path = os.path.join(os.getcwd(),'shield_ai.db')
if not os.path.exists(db_path):
    print("Database not found")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT username FROM users")
    users = cursor.fetchall()
    print(f"Users found: {users}")
    conn.close()

import sqlite3

def setup():
    conn = sqlite3.connect("shield_ai.db")
    cursor = conn.cursor()
    
    # Create Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        full_name TEXT NOT NULL
    )
    """)
    
    # Create Alerts table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        amount REAL,
        confidence REAL,
        status TEXT,
        owner TEXT DEFAULT 'deephalder'
    )
    """)
    
    # Pre-add the user deep1234 if not existing
    try:
        cursor.execute("INSERT INTO users (username, password, full_name) VALUES (?, ?, ?)", 
                       ("deep1234", "shield123", "Deep Halder Pro"))
        print("✅ User 'deep1234' created.")
    except:
        print("ℹ️ User 'deep1234' already exists.")
        
    conn.commit()
    conn.close()
    print("✅ Database Schema Ready.")

if __name__ == "__main__":
    setup()

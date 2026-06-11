import sqlite3
import os

# Make sure this points to your actual database file
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skincare_catalog.db")

def update_database():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # This SQL command adds the missing column to your table
        cursor.execute("ALTER TABLE products ADD COLUMN original_price TEXT;")
        
        conn.commit()
        print("✅ Success! The 'original_price' column was added to your database.")
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("✅ The column already exists! You are good to go.")
        else:
            print(f"❌ Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    update_database()
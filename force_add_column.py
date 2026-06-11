import sqlite3
import os

# Path to your database
db_path = 'skincare_catalog.db'

if os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Manually inject the missing column into the 'products' table
        cursor.execute('ALTER TABLE products ADD COLUMN image_filename varchar(255);')
        
        conn.commit()
        conn.close()
        print("✅ SUCCESS: The 'image_filename' column has been manually injected into the database!")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ NOTE: The column already exists, you are good to go!")
        else:
            print(f"❌ ERROR: {e}")
else:
    print("❌ ERROR: Database file not found!")
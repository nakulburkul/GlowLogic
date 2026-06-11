import sqlite3
import os

# 1. Connect to your database
db_path = 'skincare_catalog.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 2. Wipe the migration history for the shop app
    print("🧼 Cleaning shop migration history from database...")
    cursor.execute("DELETE FROM django_migrations WHERE app='shop';")
    
    conn.commit()
    conn.close()
    print("✅ Database memory cleared!")
else:
    print("❌ Error: Database file not found.")
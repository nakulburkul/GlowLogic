import sqlite3
import os

# 1. We find the database file automatically
db_files = [f for f in os.listdir('.') if f.endswith('.db')]
if not db_files:
    print("❌ Error: No .db file found in this folder!")
    exit()

db_path = db_files[0]
print(f"📁 Found Database: {db_path}")

def fix():
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Manually add the column to the products table
    print("🛠️ Injecting 'image_filename' column...")
    try:
        cursor.execute('ALTER TABLE products ADD COLUMN image_filename varchar(255);')
        conn.commit()
        print("✅ SUCCESS: Column added to SQL table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ Info: Column already exists.")
        else:
            print(f"❌ SQL Error: {e}")

    # 2. Check the table structure to be 100% sure
    cursor.execute("PRAGMA table_info(products);")
    columns = [col[1] for col in cursor.fetchall()]
    print(f"📋 Current Database Columns: {columns}")

    conn.close()

if __name__ == "__main__":
    fix()
    print("\n🚀 Now run: python manage.py generate_images")
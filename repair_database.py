import sqlite3
import os

db_path = 'skincare_catalog.db'

def repair():
    if not os.path.exists(db_path):
        print(f"❌ Error: {db_path} not found!")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🔍 Checking 'products' table structure...")
    cursor.execute("PRAGMA table_info(products);")
    columns = [column[1] for column in cursor.fetchall()]

    if 'image_filename' not in columns:
        print("🛠️ Column 'image_filename' is missing. Injecting it now...")
        try:
            cursor.execute('ALTER TABLE products ADD COLUMN image_filename varchar(255);')
            conn.commit()
            print("✅ SUCCESS: Column added!")
        except Exception as e:
            print(f"❌ SQL Error: {e}")
    else:
        print("✅ Column 'image_filename' already exists in the database.")

    # Final Step: Clear the stuck migration history for the shop app
    print("\n🧼 Cleaning migration history...")
    try:
        cursor.execute("DELETE FROM django_migrations WHERE app='shop';")
        conn.commit()
        print("✅ Shop migration history cleared. Django will now treat it as fresh.")
    except Exception as e:
        print(f"⚠️ Note: Could not clear history (it might be empty): {e}")

    conn.close()
    print("\n🚀 Repair complete! Now follow the final sync steps.")

if __name__ == "__main__":
    repair()
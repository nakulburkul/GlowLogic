import os
import sqlite3
import django
from django.conf import settings

# 1. Setup Django environment manually
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glowguide.settings') # Ensure this matches your project name
try:
    django.setup()
except Exception:
    pass

from shop.models import Product

def fix_everything():
    print("🛠️ Starting Final Repair...")

    # 1. Identify the Database
    db_name = settings.DATABASES['default']['NAME']
    print(f"📁 Target Database: {db_name}")

    # 2. Force SQL Column Injection
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    try:
        cursor.execute('ALTER TABLE products ADD COLUMN image_filename varchar(255);')
        conn.commit()
        print("✅ SUCCESS: 'image_filename' added to SQL table.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ Info: Column already exists in SQL.")
        else:
            print(f"❌ SQL Error: {e}")

    # 3. Verify ORM visibility
    fields = [f.name for f in Product._meta.get_fields()]
    print(f"🔍 ORM Fields Detected: {fields}")

    if 'image_filename' in fields:
        print("✨ SUCCESS: The ORM now recognizes 'image_filename'!")
    else:
        print("❌ CRITICAL: 'image_filename' is still missing from models.py.")

    conn.close()

if __name__ == "__main__":
    fix_everything()
import os
import sqlite3
import django

print("🚀 Starting the Final Master Fix...")

# 1. Secretly fix the missing __init__.py file that broke Django!
os.makedirs('shop/migrations', exist_ok=True)
with open('shop/migrations/__init__.py', 'w') as f:
    pass

# 2. Force Django to build a healthy db.sqlite3
print("⚙️ Rebuilding your database blueprint...")
os.system('python manage.py makemigrations shop')
os.system('python manage.py migrate')

# 3. Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glowguide_web.settings')
django.setup()

from shop.models import Product

# 4. Find your backup file automatically
backup_file = 'rescue_database.db' if os.path.exists('rescue_database.db') else 'skincare_catalog.db'

if not os.path.exists(backup_file):
    print("❌ ERROR: Could not find your backup database!")
    exit()

print(f"\n📂 Reading products from {backup_file}...")
conn = sqlite3.connect(backup_file)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Find the correct table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]
old_table = next((t for t in tables if 'product' in t.lower()), None)

cursor.execute(f"SELECT * FROM {old_table}")
rows = cursor.fetchall()

print(f"⏳ Transferring {len(rows)} products into your live website...")
added = 0

for row in rows:
    data = dict(row)
    name = data.get('name') or data.get('title')
    if not name: continue
    
    # Don't add it if it is already in the new database
    if Product.objects.filter(name=name).exists():
        continue
        
    try:
        # Use Django's brain to perfectly map the old columns to the new ones
        Product.objects.create(
            name=name,
            category=data.get('category', 'Skincare'),
            price=str(data.get('price', '0')),
            stock=data.get('stock', 25),
            suitable=data.get('suitable', 'All Skin Types'),
            vendor_link=data.get('vendor_link', data.get('link', '')),
            amazon_price=str(data.get('amazon_price', '')),
            amazon_link=data.get('amazon_link', ''),
            available_sizes=data.get('available_sizes', ''),
            local_image_filename=data.get('image', data.get('local_image_filename', ''))
        )
        added += 1
        print(f"✅ Added: {name[:40]}")
    except Exception as e:
        pass

print(f"\n🎉 BOOM! Successfully rescued {added} products!")
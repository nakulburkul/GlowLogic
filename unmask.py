import os
import sqlite3
import django
import sys

print("🚨 Unmasking the Silent Django Crash: Final Recovery Mode...\n")

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glowguide_web.settings')
django.setup()
from shop.models import Product

print("✅ Django setup complete. Connecting to SQLite...")

conn = sqlite3.connect('rescue_database.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Find the table
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = [t[0] for t in cursor.fetchall()]
old_table = next((t for t in tables if 'product' in t.lower()), None)

if not old_table:
    print("❌ Could not find a table containing 'product' in the SQLite DB!")
    sys.exit(1)

cursor.execute(f"SELECT * FROM {old_table}")
rows = cursor.fetchall()
print(f"📊 Found {len(rows)} rows to process.\n")

skipped_count = 0
failed_count = 0
updated_count = 0
created_count = 0

for row in rows:
    data = dict(row)
    name = data.get('name') or data.get('title')
    
    # ONLY skip if the row is completely missing a name
    if not name:
        skipped_count += 1
        continue
        
    try:
        obj, created = Product.objects.update_or_create(
            name=name,
            defaults={
                'category': data.get('category', 'Skincare'),
                'price': str(data.get('price', '0')),
                'stock': data.get('stock', 25),
                'suitable': data.get('suitable', 'All Skin Types'),
                'vendor_link': data.get('vendor_link', data.get('link', '')),
                'amazon_price': str(data.get('amazon_price', '')),
                'amazon_link': data.get('amazon_link', ''),
                'available_sizes': data.get('available_sizes', ''),
                'image': data.get('image', data.get('local_image_filename', ''))
            }
        )
        
        if created:
            print(f"✨ CREATED: {name[:30]}")
            created_count += 1
        else:
            # If we already imported it on the last run, it just updates here
            print(f"🔄 UPDATED: {name[:30]}")
            updated_count += 1
            
    except Exception as e:
        print(f"❌ CRASH ON '{name[:30]}':")
        print(f"   ---> THE ERROR: {e}\n")
        failed_count += 1
        
    if failed_count >= 3:
        print("🛑 Stopped after 3 errors so we can read them!")
        break

print(f"\n🏁 Finished! Updated: {updated_count} | Created: {created_count} | Failed: {failed_count} | Skipped: {skipped_count}")
import os
import django
import sqlite3

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glowguide_web.settings') 
django.setup()

from shop.models import Product

def diagnostic_rescue():
    print("🚀 Starting DIAGNOSTIC Brand Rescue...")
    
    db_files = [f for f in os.listdir() if f.endswith('.db') or f.endswith('.sqlite3')]
    if 'db.sqlite3' in db_files:
        db_files.remove('db.sqlite3')
        
    total_added = 0
    
    for db_file in db_files:
        print(f"\n📂 Opening backup file: {db_file}")
        conn = sqlite3.connect(db_file)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [t[0] for t in cursor.fetchall() if 'product' in t[0].lower()]
        
        for table in tables:
            print(f"  🔍 Scanning inside table '{table}'...")
            try:
                cursor.execute(f"SELECT * FROM {table}")
                rows = cursor.fetchall()
            except Exception:
                continue
            
            if not rows:
                print("    ⚠️ Table is empty.")
                continue
                
            # THIS IS THE MAGIC LINE: Print the exact columns!
            print(f"    📋 COLUMNS FOUND: {list(rows[0].keys())}\n")
            
            for row in rows:
                keys = row.keys()
                
                # Try every possible variation of the word "name"
                name = None
                if 'name' in keys: name = row['name']
                elif 'title' in keys: name = row['title']
                elif 'product_name' in keys: name = row['product_name']
                elif 'item_name' in keys: name = row['item_name']
                
                if not name:
                    print(f"    ❌ Skipped: Could not find a name/title column. Data: {dict(row)}")
                    continue
                    
                # If it already exists in the live DB, skip it (but only if it's EXACTLY the same)
                if Product.objects.filter(name=name).exists():
                    continue
                    
                # Extract data safely
                category = row['category'] if 'category' in keys else 'Skincare'
                price = str(row['price']) if 'price' in keys else '0'
                stock = row['stock'] if 'stock' in keys else 25
                suitable = row['suitable'] if 'suitable' in keys else 'All Skin Types'
                vendor_link = row['vendor_link'] if 'vendor_link' in keys else row['link'] if 'link' in keys else ''
                amazon_price = str(row['amazon_price']) if 'amazon_price' in keys else ''
                amazon_link = row['amazon_link'] if 'amazon_link' in keys else ''
                available_sizes = row['available_sizes'] if 'available_sizes' in keys else ''
                
                img_file = ""
                if 'local_image_filename' in keys: img_file = row['local_image_filename']
                elif 'image_filename' in keys: img_file = row['image_filename']
                elif 'image' in keys: img_file = row['image']
                
                try:
                    Product.objects.create(
                        name=name,
                        category=category,
                        price=price,
                        stock=stock,
                        suitable=suitable,
                        vendor_link=vendor_link,
                        amazon_price=amazon_price,
                        amazon_link=amazon_link,
                        available_sizes=available_sizes,
                        local_image_filename=img_file
                    )
                    total_added += 1
                    print(f"    ✨ RESTORED: {name[:50]}")
                except Exception as e:
                    # Print the exact reason Django rejected it!
                    print(f"    ❌ FAILED to add '{name[:30]}': {e}")
                    
    print(f"\n🎉 ALL DONE! Successfully restored {total_added} products.")

if __name__ == "__main__":
    diagnostic_rescue()
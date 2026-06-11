import sqlite3
import os

print("🔍 Injecting Truth Serum into rescue_database.db...\n")

backup_file = 'rescue_database.db' if os.path.exists('rescue_database.db') else 'skincare_catalog.db'

try:
    conn = sqlite3.connect(backup_file)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Find the products table
    c.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in c.fetchall()]
    table_name = next((t for t in tables if 'product' in t.lower()), None)
    
    if not table_name:
        print("❌ No product table found!")
        exit()
        
    c.execute(f"SELECT * FROM {table_name}")
    rows = c.fetchall()
    
    names = []
    for row in rows:
        data = dict(row)
        name = data.get('name') or data.get('title') or 'Unknown'
        names.append(name)

    print(f"📦 Total products found in file: {len(names)}")
    print(f"   First product: {names[0]}")
    print(f"   Last product:  {names[-1]}\n")

    # Count the specific brands
    plix_count = sum(1 for n in names if 'plix' in n.lower())
    minimalist_count = sum(1 for n in names if 'minimalist' in n.lower())
    dot_count = sum(1 for n in names if 'dot & key' in n.lower() or 'dot and key' in n.lower())
    
    print("--- 📊 EXACT BRAND COUNT IN THIS FILE ---")
    print(f"💧 Dot & Key products:  {dot_count}")
    print(f"🌿 Plix products:       {plix_count}")
    print(f"🧪 Minimalist products: {minimalist_count}")
    
    other = len(names) - (dot_count + plix_count + minimalist_count)
    print(f"❓ Other brands:        {other}")

except Exception as e:
    print(f"❌ Error reading file: {e}")
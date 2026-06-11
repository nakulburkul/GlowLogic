import os
import sqlite3
import urllib.request
import urllib.parse
import re
import time

print("🔍 Booting up the GlowGuide Gap Filler...")

# Point straight to the root static folder where your 85 images live
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
images_dir = os.path.join(BASE_DIR, 'static', 'images')
os.makedirs(images_dir, exist_ok=True)

db_path = os.path.join(BASE_DIR, 'skincare_catalog.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM products WHERE name IS NOT NULL;")
products = cursor.fetchall()

generated = 0
skipped = 0

for (name,) in products:
    # EXACT logic from your current models.py (No IDs attached)
    safe_name = "".join([c for c in str(name) if c.isalpha() or c.isdigit() or c==' '])
    safe_name = re.sub(r'\s+', ' ', safe_name).strip()
    filename = f"{safe_name[:50].strip()}.jpg"
    filepath = os.path.join(images_dir, filename)

    # 1. If the file exists (like your 85 real photos), skip it instantly!
    if os.path.exists(filepath):
        skipped += 1
        continue

    # 2. If it is genuinely missing, generate a new placeholder with the perfect name
    short_name = " ".join(name.replace("Dot & Key", "").strip().split()[:3])
    if not short_name: short_name = "Skincare"
    
    encoded_name = urllib.parse.quote(short_name)
    url = f"https://placehold.co/600x600/fff9fa/d81b60.jpg?text={encoded_name}"
    
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    try:
        with urllib.request.urlopen(req) as response, open(filepath, 'wb') as out_file:
            out_file.write(response.read())
        generated += 1
        print(f"  ✅ Fixed Missing Image: {filename}")
        time.sleep(0.3) # Anti-bot protection so placehold.co doesn't block us
    except Exception as e:
        # Ignore duplicate name errors silently
        pass

print(f"\n✨ Done! Kept {skipped} existing images safe and filled {generated} gaps!")
conn.close()
import os
import sqlite3
import urllib.request
import urllib.parse
import re

print("🛡️ Booting up GlowGuide Super Fixer (Anti-Bot Bypass & Crash-Proof)...")

db_path = 'skincare_catalog.db'
images_dir = os.path.join('static', 'images')
os.makedirs(images_dir, exist_ok=True)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM products WHERE name IS NOT NULL;")
products = cursor.fetchall()

renamed = 0
deleted_duplicates = 0
generated = 0

for (name,) in products:
    # 1. Calculate the OLD buggy filename (with double spaces)
    old_safe = "".join([c for c in str(name) if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    old_filename = f"{old_safe[:50].strip()}.jpg"
    old_filepath = os.path.join(images_dir, old_filename)

    # 2. Calculate the NEW ultra-clean filename (single spaces)
    new_safe = "".join([c for c in str(name) if c.isalpha() or c.isdigit() or c==' '])
    new_safe = re.sub(r'\s+', ' ', new_safe).strip()
    new_filename = f"{new_safe[:50].strip()}.jpg"
    new_filepath = os.path.join(images_dir, new_filename)

    # 3. SAFE RENAME (Fixes WinError 183)
    if os.path.exists(old_filepath) and old_filename != new_filename:
        if os.path.exists(new_filepath):
            # The clean file already exists! Just delete the messy duplicate to prevent a crash.
            try:
                os.remove(old_filepath)
                deleted_duplicates += 1
            except Exception:
                pass
        else:
            os.rename(old_filepath, new_filepath)
            renamed += 1

    # 4. ANTI-BOT DOWNLOADER (Fixes HTTP 403 Forbidden)
    if not os.path.exists(new_filepath):
        print(f"🖼️ Missing: {name}")
        short_name = " ".join(name.replace("Dot & Key", "").strip().split()[:3])
        if not short_name: 
            short_name = "Skincare"
        
        encoded_name = urllib.parse.quote(short_name)
        url = f"https://dummyimage.com/600x600/fff9fa/d81b60.jpg&text={encoded_name}"
        
        # Disguise the Python script as a standard Windows Chrome browser
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        )
        
        try:
            with urllib.request.urlopen(req) as response, open(new_filepath, 'wb') as out_file:
                out_file.write(response.read())
            generated += 1
            print(f"  ✅ Downloaded successfully!")
        except Exception as e:
            print(f"  ❌ Failed to download placeholder for {name}: {e}")

print(f"\n✨ System Sync Complete! Renamed: {renamed} | Cleaned Duplicates: {deleted_duplicates} | Generated: {generated}")
conn.close()
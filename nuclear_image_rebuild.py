import os
import shutil
import sqlite3
import urllib.request
import urllib.parse
import re
import time

print("☢️ INITIATING SCORCHED EARTH IMAGE REBUILD...")

db_path = 'skincare_catalog.db'
images_dir = os.path.join('static', 'images')

# STEP 1: NUKE THE FOLDER
if os.path.exists(images_dir):
    print("🧹 Wiping old images directory...")
    shutil.rmtree(images_dir)
    time.sleep(1) # Give Windows a second to release the files

os.makedirs(images_dir, exist_ok=True)
print("✅ Clean directory created.")

# STEP 2: CONNECT TO DATABASE
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM products WHERE name IS NOT NULL;")
products = cursor.fetchall()

generated = 0
failed = 0

print(f"📦 Found {len(products)} products. Starting fresh generation...")

for (name,) in products:
    # Match the exact logic from models.py
    safe_name = "".join([c for c in str(name) if c.isalpha() or c.isdigit() or c==' '])
    safe_name = re.sub(r'\s+', ' ', safe_name).strip()
    filename = f"{safe_name[:50].strip()}.jpg"
    filepath = os.path.join(images_dir, filename)

    # Clean up name for the image text
    short_name = " ".join(name.replace("Dot & Key", "").strip().split()[:3])
    if not short_name: 
        short_name = "Skincare"
    
    encoded_name = urllib.parse.quote(short_name)
    # Using placehold.co as it has better limits than dummyimage
    url = f"https://placehold.co/600x600/fff9fa/d81b60.jpg?text={encoded_name}"
    
    # Chrome Disguise
    req = urllib.request.Request(
        url, 
        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
    )
    
    try:
        with urllib.request.urlopen(req) as response, open(filepath, 'wb') as out_file:
            out_file.write(response.read())
        generated += 1
        print(f"  ✅ [{generated}/{len(products)}] Generated: {filename}")
        
        # 🛡️ THE MAGIC SHIELD: Sleep for 0.5 seconds to prevent rate-limiting (403 Forbidden)
        time.sleep(0.5) 
        
    except Exception as e:
        failed += 1
        print(f"  ❌ Failed {name}: {e}")

print(f"\n✨ REBUILD COMPLETE! Successfully generated {generated} fresh images. ({failed} failed)")
conn.close()
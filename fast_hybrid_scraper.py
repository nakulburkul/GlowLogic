import os
import sqlite3
import re
import time
import requests
import random

print("🛡️ Booting up GlowGuide Guerrilla Scraper (Bypassing Ratelimits)...")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
images_dir = os.path.join(BASE_DIR, 'static', 'images')
db_path = os.path.join(BASE_DIR, 'skincare_catalog.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM products WHERE name IS NOT NULL;")
products = cursor.fetchall()

# Advanced Header Rotation to look like multiple different real users
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
]

real_count = 0
failed_count = 0
skipped_count = 0

print(f"📦 Processing {len(products)} products...\n")

for (name,) in products:
    safe_name = "".join([c for c in str(name) if c.isalpha() or c.isdigit() or c==' '])
    safe_name = re.sub(r'\s+', ' ', safe_name).strip()
    filename = f"{safe_name[:50].strip()}.jpg"
    filepath = os.path.join(images_dir, filename)

    # Size-check: Don't overwrite high-quality images
    if os.path.exists(filepath) and (os.path.getsize(filepath) / 1024) > 20:
        skipped_count += 1
        continue

    # Clean the query
    clean_name = name.split('|')[0].replace('%', ' percent').replace('/', ' ')
    short_query = " ".join(clean_name.split()[:4])
    
    print(f"🔍 Hunting for: {short_query}...")

    try:
        # Use a secondary image provider (Bing-based proxy) which is faster and has fewer 403s
        search_url = f"https://www.bing.com/images/search?q={short_query}+skincare+product+white+background&FORM=HDRSC2"
        
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        response = requests.get(search_url, headers=headers, timeout=10)
        
        # Regex to find the first image link in the HTML source
        # This bypasses the need for an API library entirely
        img_links = re.findall(r'murl&quot;:&quot;(http.*?)&quot;', response.text)
        
        if img_links:
            image_url = img_links[0]
            img_data = requests.get(image_url, headers=headers, timeout=10, verify=False).content
            
            with open(filepath, 'wb') as f:
                f.write(img_data)
            
            real_count += 1
            print(f"  ✅ SUCCESS: {filename}")
        else:
            print("  ⚠️ Image not found in search results.")
            failed_count += 1

    except Exception as e:
        print(f"  🛑 SYSTEM ERROR: {e}")
        failed_count += 1
        # If we see a 403, we stop and wait longer
        if "403" in str(e):
            print("⏳ Ratelimit detected. Cooling down for 30 seconds...")
            time.sleep(30)

    # SLOW DOWN: 4 seconds between items is the only way to do 800+ images for free
    time.sleep(4)

print(f"\n✨ FINISHED! Real Photos: {real_count} | Failed: {failed_count} | Skipped: {skipped_count}")
conn.close()
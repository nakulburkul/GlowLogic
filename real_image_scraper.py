import os
import sqlite3
import re
import time
import requests
from duckduckgo_search import DDGS

print("🕷️ Booting up GlowGuide Real Image Auto-Scraper (Smart Query Edition)...")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
images_dir = os.path.join(BASE_DIR, 'static', 'images')
db_path = os.path.join(BASE_DIR, 'skincare_catalog.db')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM products WHERE name IS NOT NULL;")
products = cursor.fetchall()

success_count = 0
fail_count = 0

with DDGS() as ddgs:
    for (name,) in products:
        safe_name = "".join([c for c in str(name) if c.isalpha() or c.isdigit() or c==' '])
        safe_name = re.sub(r'\s+', ' ', safe_name).strip()
        filename = f"{safe_name[:50].strip()}.jpg"
        filepath = os.path.join(images_dir, filename)

        if os.path.exists(filepath):
            file_size_kb = os.path.getsize(filepath) / 1024
            if file_size_kb > 20:
                continue # Silently skip images we already successfully downloaded

        # 🧠 THE FIX: Chop off everything after the "|" character, and only take the first 5 words
        clean_name = name.split('|')[0].replace('-', ' ').replace(',', '')
        short_query = " ".join(clean_name.split()[:5])
        
        print(f"🔍 Searching: '{short_query}'...")
        
        try:
            search_results = list(ddgs.images(
                keywords=f"{short_query} skincare bottle", 
                max_results=1, 
                safesearch="on"
            ))
            
            if not search_results:
                print("  ⚠️ No image found.")
                fail_count += 1
                continue
                
            image_url = search_results[0]['image']
            
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}
            response = requests.get(image_url, headers=headers, stream=True, timeout=10)
            
            if response.status_code == 200:
                with open(filepath, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                success_count += 1
                print(f"  ✅ Downloaded: {filename}")
            else:
                print(f"  ❌ Blocked (Status {response.status_code})")
                fail_count += 1
                
        except Exception as e:
            error_str = str(e)
            if "403" in error_str or "Ratelimit" in error_str:
                print("  🛑 RATE LIMIT HIT! Script will sleep for 60 seconds to cool down...")
                time.sleep(60) # Auto-pause if we get caught
            else:
                print(f"  ❌ Error: {e}")
            fail_count += 1
            
        # Keep this delay! It keeps you out of bot jail.
        time.sleep(3)

print(f"\n✨ SCRAPE COMPLETE! Grabbed {success_count} real images. ({fail_count} failed)")
conn.close()
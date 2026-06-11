import os
import sqlite3
import re
import time
import requests
import random
from io import BytesIO
from PIL import Image

print("🚀 Booting up the Ultimate GlowGuide Full-Catalog Updater...")

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
images_dir = os.path.join(BASE_DIR, 'static', 'images')
db_path = os.path.join(BASE_DIR, 'skincare_catalog.db')
log_file_path = os.path.join(BASE_DIR, 'successful_replacements.txt')

conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM shop_product WHERE name IS NOT NULL;")
products = cursor.fetchall()

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0'
]

successful_products = []
failed_count = 0

print(f"📦 Total products to process: {len(products)}. This will take some time.\n")

for (name,) in products:
    safe_name = "".join([c for c in str(name) if c.isalpha() or c.isdigit() or c==' '])
    safe_name = re.sub(r'\s+', ' ', safe_name).strip()
    filename = f"{safe_name[:50].strip()}.jpg"
    filepath = os.path.join(images_dir, filename)

    # Clean the query to get better search results
   # Clean the query heavily to match exact Amazon listings
    clean_name = name.split('|')[0].replace('-', ' ').replace(',', '')
    short_query = " ".join(clean_name.split()[:4])
    
    print(f"🔍 Hunting official e-commerce domains for: {short_query}...")

    try:
        search_query = f"{short_query} skincare site:amazon.in"
        
        # 1. THE SIZE FILTER: &qft=+filterui:imagesize-large forces HD results
        search_url = f"https://www.bing.com/images/search?q={search_query}&qft=+filterui:imagesize-large&FORM=HDRSC2"
        headers = {'User-Agent': random.choice(USER_AGENTS)}
        response = requests.get(search_url, headers=headers, timeout=10)
        
        img_links = re.findall(r'murl&quot;:&quot;(http.*?)&quot;', response.text)
        
        success = False
        
        for img_url in img_links[:3]:
            if success: break
            
            # 2. THE AMAZON URL CLEANSER: Remove the compression modifiers to get the HD original
            if "images-amazon.com" in img_url or "m.media-amazon.com" in img_url:
                # Changes ".../71xyz._AC_UL320_.jpg" to ".../71xyz.jpg"
                img_url = re.sub(r'\._.*?_\.', '.', img_url)
            
            try:
                img_response = requests.get(img_url, headers=headers, timeout=8, verify=False)
                img_data = BytesIO(img_response.content)
                
                img = Image.open(img_data)
                width, height = img.size
                
                # 3. RESOLUTION CHECK: Only accept images larger than 400x400 pixels
                if width < 400 or height < 400:
                    print(f"  ⏭️ Rejected low-res thumbnail ({width}x{height})")
                    continue

                aspect_ratio = width / height
                
                if 0.85 <= aspect_ratio <= 1.15:
                    with open(filepath, 'wb') as f:
                        f.write(img_response.content)
                    print(f"  ✅ SAVED HD SQUARE: {filename} ({width}x{height})")
                    success = True
                else:
                    print(f"  ⏭️ Rejected irregular shape ({width}x{height})")
            except Exception:
                continue

        if not success:
            print("  ⚠️ No HD professional image found.")

    except Exception as e:
        print(f"  🛑 SYSTEM ERROR: {e}")
        time.sleep(5)

    # 3-second delay to protect against ratelimits across the entire catalog
    time.sleep(3)

# --- GENERATE THE FINAL REPORT ---
print("\n📝 Generating successful replacement list...")
with open(log_file_path, 'w', encoding='utf-8') as log_file:
    log_file.write(f"Total Images Successfully Replaced: {len(successful_products)}\n")
    log_file.write("="*50 + "\n\n")
    for item in successful_products:
        log_file.write(f"- {item}\n")

print(f"\n✨ FULL CATALOG SYNC FINISHED!")
print(f"📸 Total Replaced: {len(successful_products)}")
print(f"❌ Total Failed: {failed_count}")
print(f"📄 Your list has been saved to: {log_file_path}")

conn.close()
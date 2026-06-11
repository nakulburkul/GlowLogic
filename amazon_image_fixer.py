import os
import time
import random
import requests
import re
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile
from django.conf import settings
import django

# --- Setup Django Environment ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glowguide_web.settings') 
django.setup()
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from shop.models import Product

print("🛡️ Booting Armored Amazon Image Fixer...")

# Realistic headers to mimic a real user session 
HEADERS_LIST = [
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
    }
]

# TARGET: Only products that do NOT have an image yet 
products = Product.objects.filter(image='')
print(f"📦 Found {products.count()} products still missing images.")

updated_count = 0
session = requests.Session() # Use a session to store cookies like a real browser

for p in products:
    link = p.amazon_link if p.amazon_link and 'amazon' in p.amazon_link.lower() else p.vendor_link
        
    if not link or 'amazon' not in link.lower():
        continue 
        
    print(f"🔍 Scraping: {p.name[:40]}...")
    
    try:
        # Use random delay and headers to avoid detection 
        response = session.get(link, headers=random.choice(HEADERS_LIST), timeout=15)
        
        if response.status_code == 503:
            print("  ❌ 503 Blocked. Waiting 60 seconds...")
            time.sleep(60)
            continue
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check for Amazon's bot detection page 
        if "captcha" in soup.title.text.lower() or "robot" in soup.title.text.lower():
            print("  🤖 CAPTCHA detected. Switching network/stopping is advised.")
            time.sleep(20)
            continue
            
        # Strategy: Look for the High-Res image source directly in the page script 
        img_url = None
        scripts = soup.find_all('script', type='text/javascript')
        for script in scripts:
            if 'colorImages' in str(script):
                matches = re.findall(r'"hiRes":"(https://.*?\.jpg)"', str(script))
                if matches:
                    img_url = matches[0]
                    break

        # Fallback to OG meta tag if script fails 
        if not img_url:
            og_img = soup.find('meta', property='og:image')
            if og_img: img_url = og_img.get('content')
                
        if img_url:
            img_response = session.get(img_url, timeout=10)
            if img_response.status_code == 200:
                # Generate safe filename and save directly to Admin field 
                safe_name = "".join([c for c in p.name if c.isalpha() or c.isdigit()]).strip()[:30]
                file_name = f"{safe_name}_fixed.jpg"
                p.image.save(file_name, ContentFile(img_response.content), save=True)
                updated_count += 1
                print(f"  ✅ SUCCESS: Saved as {file_name}")
        else:
            print("  ⚠️ Image not found in page source.")
            
    except Exception as e:
        print(f"  🛑 Error: {str(e)[:50]}")
        
    # Long, variable sleep timer to mimic human reading speed 
    time.sleep(random.uniform(5.0, 10.0))

print(f"\n🎉 OPERATION COMPLETE! Auto-uploaded {updated_count} new product images.")
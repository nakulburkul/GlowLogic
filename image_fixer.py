import os
import time
import random
import requests
import json
from bs4 import BeautifulSoup
from urllib.parse import urlparse

import django
from django.core.files.base import ContentFile
from django.db.models import Q

# --- Setup Django Environment ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glowguide_web.settings') 
django.setup()
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from shop.models import Product

print("📸 Booting Auto-Image Fetcher...")

HEADERS_LIST = [
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml',
        'Accept-Language': 'en-US,en;q=0.9',
    },
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
        'Accept-Language': 'en-US,en;q=0.9',
    }
]

# Find products that currently have NO uploaded image
# (If your image field is empty, it will pull one from Amazon)
products_missing_images = Product.objects.filter(
    Q(image__isnull=True) | Q(image__exact='')
)

print(f"🔍 Found {products_missing_images.count()} products missing an official image.")

session = requests.Session()
updated_count = 0

for p in products_missing_images:
    # We need a direct Amazon link to know where to steal the image from!
    if not p.amazon_link or 's?k=' in p.amazon_link:
        print(f"  ⏭️ Skipping: {p.name[:30]}... (No direct Amazon link found)")
        continue
        
    print(f"  📸 Fetching image for: {p.name[:40]}...")
    
    try:
        headers = random.choice(HEADERS_LIST)
        response = session.get(p.amazon_link, headers=headers, timeout=15)
        
        if response.status_code == 503:
            print("    ❌ Blocked by Amazon! Pausing for 30s...")
            time.sleep(30)
            continue
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Amazon usually stores the main image in an img tag with id="landingImage"
        img_tag = soup.find('img', id='landingImage')
        
        if not img_tag:
            print("    ⚠️ Could not find main image on the Amazon page.")
            time.sleep(3)
            continue
            
        # Amazon hides the high-res image inside a special data attribute
        img_url = img_tag.get('src')
        if 'data-a-dynamic-image' in img_tag.attrs:
            try:
                # This grabs the largest/highest resolution image available!
                img_dict = json.loads(img_tag['data-a-dynamic-image'])
                img_url = list(img_dict.keys())[-1] 
            except:
                pass
                
        print(f"    ⬇️ Downloading image...")
        img_response = requests.get(img_url, headers=headers, timeout=10)
        
        if img_response.status_code == 200:
            # Create a clean file name based on the product name
            ext = urlparse(img_url).path.split('.')[-1]
            if ext not in ['jpg', 'jpeg', 'png', 'webp']:
                ext = 'jpg' # Default to jpg if it's weird
            
            # Clean up the name so Windows/Mac doesn't get mad at special characters
            safe_name = "".join([c for c in p.name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            file_name = f"{safe_name.replace(' ', '_').lower()[:40]}.{ext}"
            
            # THE MAGIC: Save the downloaded bytes directly to the Django Image Field!
            p.image.save(file_name, ContentFile(img_response.content), save=True)
            updated_count += 1
            print(f"    ✅ Success! Saved as {file_name}")
        else:
            print("    ❌ Failed to download the actual image file.")
            
    except Exception as e:
        print(f"    🛑 Error: {str(e)[:50]}")
        
    # Be polite to Amazon's servers
    time.sleep(random.uniform(3.0, 6.0))

print(f"\n🎉 DONE! Successfully fetched and saved {updated_count} missing images.")
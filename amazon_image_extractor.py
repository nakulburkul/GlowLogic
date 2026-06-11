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

print("🎯 Booting up the Direct Amazon Image Extractor with Failure Logger...")

USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
]

products = Product.objects.filter(image='')
updated_count = 0

# 🧠 NEW: Our failure ledger
failed_reports = [] 

for p in products:
    link = ""
    if p.amazon_link and 'amazon' in p.amazon_link.lower(): 
        link = p.amazon_link
    elif p.vendor_link and 'amazon' in p.vendor_link.lower(): 
        link = p.vendor_link
        
    if not link:
        continue 
        
    print(f"🔍 Inspecting Amazon for: {p.name[:40]}...")
    
    try:
        headers = {
            'User-Agent': random.choice(USER_AGENTS),
            'Accept-Language': 'en-US,en;q=0.9',
        }
        
        # 1. Visit the actual Amazon Product Page
        response = requests.get(link, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"  ❌ Blocked by Amazon (Status {response.status_code})")
            failed_reports.append(f"{p.name} | Blocked HTTP {response.status_code}")
            time.sleep(4)
            continue
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check if Amazon served a CAPTCHA
        if "captcha" in soup.title.text.lower() or "robot" in soup.title.text.lower():
            print("  🤖 CAPTCHA detected. Cooling down for 15 seconds...")
            failed_reports.append(f"{p.name} | CAPTCHA Blocked")
            time.sleep(15)
            continue
            
        # 2. Extract the official image URL
        img_url = None
        
        og_img = soup.find('meta', property='og:image')
        if og_img and og_img.get('content'):
            img_url = og_img['content']
        
        if not img_url:
            landing_img = soup.find('img', id='landingImage')
            if landing_img:
                img_url = landing_img.get('data-old-hires') or landing_img.get('src')
                
        if img_url:
            img_url = re.sub(r'\._.*?_\.', '.', img_url)
            
            # 3. Download the HD Image
            img_response = requests.get(img_url, headers=headers, timeout=10)
            
            if img_response.status_code == 200:
                safe_name = "".join([c for c in p.name if c.isalpha() or c.isdigit()]).strip()[:30]
                file_name = f"{safe_name}_amazon.jpg"
                
                p.image.save(file_name, ContentFile(img_response.content), save=True)
                updated_count += 1
                print(f"  ✅ SAVED DIRECTLY TO ADMIN: {file_name}")
            else:
                print("  ⚠️ Found URL but failed to download image data.")
                failed_reports.append(f"{p.name} | Image Download Failed (HTTP {img_response.status_code})")
        else:
            print("  ⚠️ Could not locate the main product image in the HTML.")
            failed_reports.append(f"{p.name} | No Image Found in HTML")
            
    except Exception as e:
        error_msg = str(e)[:50]
        print(f"  🛑 Error: {error_msg}")
        failed_reports.append(f"{p.name} | System Error: {error_msg}")
        
    # CRITICAL: Wait randomly between 3 to 6 seconds
    time.sleep(random.uniform(3.0, 6.0))

# --- GENERATE THE FAILURE REPORT ---
if failed_reports:
    log_path = os.path.join(settings.BASE_DIR, 'amazon_image_failures.txt')
    with open(log_path, 'w', encoding='utf-8') as f:
        f.write(f"GlowGuide Failed Amazon Image Extracts ({len(failed_reports)} items)\n")
        f.write("="*60 + "\n\n")
        for report in failed_reports:
            f.write(f"- {report}\n")
    print(f"\n📄 A failure report has been saved to: {log_path}")

print(f"\n🎉 DONE! Auto-uploaded {updated_count} perfect Amazon images.")
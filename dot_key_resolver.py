import os
import time
import random
import urllib.parse
import requests
import re
from bs4 import BeautifulSoup
import django
from django.db.models import Q

# --- Setup Django Environment ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glowguide_web.settings') 
django.setup()
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from shop.models import Product

print("🛡️ Booting Dual-Action Resolver (Amazon + Official Dot & Key)...")

HEADERS_LIST = [
    {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/',
        'Upgrade-Insecure-Requests': '1'
    },
    {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    }
]

# 🧠 Target ANY Dot & Key product that needs fixing
products = Product.objects.filter(name__icontains='dot')

print(f"📦 Found {products.count()} Dot & Key products to scan.")

updated_count = 0
session = requests.Session()

for p in products:
    print(f"\n👉 Checking: {p.name[:50]}...")
    needs_save = False
    headers = random.choice(HEADERS_LIST)
    safe_name = urllib.parse.quote_plus(p.name)

    # ==========================================
    # 🎯 PHASE 1: FIX AMAZON LINK
    # ==========================================
    if not p.amazon_link or '/s?k=' in p.amazon_link or '/sspa/' in p.amazon_link:
        try:
            amazon_search_url = f"https://www.amazon.in/s?k=dot+and+key+{safe_name}"
            
            res_amz = session.get(amazon_search_url, headers=headers, timeout=15)
            
            if res_amz.status_code == 200 and "captcha" not in res_amz.text.lower():
                soup_amz = BeautifulSoup(res_amz.text, 'html.parser')
                search_results = soup_amz.find_all('div', {'data-component-type': 's-search-result'})
                
                for result in search_results:
                    link_tag = result.find('a', class_='a-link-normal s-no-outline') or result.find('h2').find('a')
                    
                    if link_tag and 'href' in link_tag.attrs:
                        raw_href = link_tag['href']
                        
                        # Skip Sponsored Ads
                        if '/sspa/' in raw_href or 'slredirect' in raw_href:
                            continue
                            
                        # First organic link found!
                        clean_path = raw_href.split('?')[0].split('/ref=')[0]
                        p.amazon_link = f"https://www.amazon.in{clean_path}?tag=glowguide-21"
                        needs_save = True
                        print(f"    ✅ AMZ Fixed! -> {p.amazon_link}")
                        break 
            else:
                print(f"    ⚠️ Amazon Blocked/Failed (Status {res_amz.status_code})")
                time.sleep(10)
                
        except Exception as e:
            print(f"    🛑 Amazon Error: {str(e)[:50]}")
            
        time.sleep(random.uniform(2.0, 4.0)) # Mini pause between sites

    # ==========================================
    # 🎯 PHASE 2: FIX OFFICIAL WEBSITE LINK
    # ==========================================
    # If there is no link, or the link is just a generic search page
    if not p.vendor_link or '/products/' not in p.vendor_link:
        try:
            official_search_url = f"https://www.dotandkey.com/search?q={safe_name}"
            
            res_off = session.get(official_search_url, headers=headers, timeout=15)
            
            if res_off.status_code == 200:
                soup_off = BeautifulSoup(res_off.text, 'html.parser')
                
                # Shopify stores its individual product URLs with "/products/" in the path
                product_link_tag = soup_off.find('a', href=re.compile(r'/products/'))
                
                if product_link_tag and 'href' in product_link_tag.attrs:
                    raw_href = product_link_tag['href']
                    
                    # Some hrefs are relative (e.g. "/products/serum"), some are full
                    if raw_href.startswith('/'):
                        p.vendor_link = f"https://www.dotandkey.com{raw_href}"
                    else:
                        p.vendor_link = raw_href
                        
                    needs_save = True
                    print(f"    ✨ Official Fixed! -> {p.vendor_link}")
                else:
                    print(f"    ⚠️ Could not find an exact match on official site.")
            else:
                print(f"    ⚠️ Official Site Blocked/Failed (Status {res_off.status_code})")
                
        except Exception as e:
            print(f"    🛑 Official Site Error: {str(e)[:50]}")

    # ==========================================
    # 💾 SAVE AND COOLDOWN
    # ==========================================
    if needs_save:
        p.save()
        updated_count += 1
        
    # We are hitting two websites per product, so we need a slightly longer cooldown 
    # to avoid getting banned by both Amazon and Shopify!
    time.sleep(random.uniform(4.0, 7.0))

print(f"\n🎉 DONE! Upgraded and Repaired {updated_count} Dot & Key products with DUAL links.")
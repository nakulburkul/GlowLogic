import os
import time
import random
import urllib.parse
import requests
from bs4 import BeautifulSoup
import django
from django.db.models import Q

# --- Setup Django Environment ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glowguide_web.settings') 
django.setup()
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from shop.models import Product

print("🛡️ Booting UNIVERSAL Amazon Direct-Link Resolver...")

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

# 🧠 THE FIX: Target ANY product that has a search link, a sponsored link, or no link at all!
products = Product.objects.filter(
    Q(amazon_link__isnull=True) | 
    Q(amazon_link__exact='') | 
    Q(amazon_link__contains='/s?k=') | 
    Q(amazon_link__contains='/sspa/')
)

print(f"📦 Found {products.count()} products needing direct product page links.")

updated_count = 0
session = requests.Session()

for p in products:
    print(f"  👉 Resolving: {p.name[:40]}...")
    try:
        headers = random.choice(HEADERS_LIST)
        safe_name = urllib.parse.quote_plus(p.name)
        
        # Always search for the exact product name
        target_url = f"https://www.amazon.in/s?k={safe_name}"
        
        response = session.get(target_url, headers=headers, timeout=15)
        
        if response.status_code == 503:
            print(f"    ❌ 503 Blocked! Amazon's firewall caught us. Pausing for 30s...")
            time.sleep(30)
            continue
        elif response.status_code != 200:
            print(f"    ❌ Failed. HTTP Status: {response.status_code}")
            time.sleep(5)
            continue
            
        soup = BeautifulSoup(response.text, 'html.parser')
        
        if "captcha" in soup.title.text.lower() or "robot" in soup.title.text.lower():
            print("    🤖 CAPTCHA hit! Cooling down for 20 seconds...")
            time.sleep(20)
            continue

        # Grab ALL search results on the page
        search_results = soup.find_all('div', {'data-component-type': 's-search-result'})
        direct_link = None
        
        for result in search_results:
            link_tag = result.find('a', class_='a-link-normal s-no-outline') or result.find('h2').find('a')
            
            if link_tag and 'href' in link_tag.attrs:
                raw_href = link_tag['href']
                
                # Skip Sponsored Ads to ensure we get the real product detail page
                if '/sspa/' in raw_href or 'slredirect' in raw_href:
                    continue
                    
                # 🎯 THE MAGIC: Extract the exact product detail page path
                clean_path = raw_href.split('?')[0].split('/ref=')[0]
                direct_link = f"https://www.amazon.in{clean_path}?tag=glowguide-21"
                break 
        
        if direct_link:
            p.amazon_link = direct_link
            p.save()
            updated_count += 1
            print(f"    ✅ Found Direct Link! -> {direct_link}")
        else:
            print("    ⚠️ Could not find a valid product page.")
            
    except Exception as e:
        print(f"    🛑 Error: {str(e)[:50]}")
        
    time.sleep(random.uniform(3.0, 6.0))

print(f"\n🎉 DONE! Saved direct product pages for {updated_count} products.")
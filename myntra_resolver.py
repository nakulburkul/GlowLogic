import os
import time
import random
import urllib.parse
import requests
import re
import json
import django
from difflib import get_close_matches

# --- Setup Django Environment ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glowguide_web.settings') 
django.setup()
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from shop.models import Product

print("🛡️ Booting Myntra JSON-Backdoor Resolver...")

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.google.com/',
}

# Get all products that don't have a Myntra link yet
products = Product.objects.filter(myntra_link__isnull=True) | Product.objects.filter(myntra_link__exact='')
print(f"📦 Found {products.count()} products to scan against Myntra.")

session = requests.Session()
updated_count = 0

for p in products:
    print(f"\n👉 Searching Myntra for: {p.name[:40]}...")
    
    # Create a clean search term (e.g., "Dot & Key Vitamin C" -> "dot and key vitamin c")
    search_term = p.name.replace('&', 'and').lower()
    safe_query = urllib.parse.quote_plus(search_term)
    
    # Myntra's internal search structure
    myntra_url = f"https://www.myntra.com/{safe_query}?rawQuery={safe_query}"
    
    try:
        response = session.get(myntra_url, headers=HEADERS, timeout=15)
        
        if response.status_code != 200:
            print(f"    ❌ Blocked by Myntra! Status: {response.status_code}")
            time.sleep(10)
            continue
            
        # 🧠 THE MAGIC: Rip the hidden JSON out of the Javascript
        match = re.search(r'window\.__myx\s*=\s*(\{.*?\})</script>', response.text)
        
        if match:
            myx_data = json.loads(match.group(1))
            
            # Dig through Myntra's complex data structure to find the search results
            try:
                search_data = myx_data.get('searchData', {}).get('results', {}).get('products', [])
                
                if not search_data:
                    print("    ⚠️ No products found on this Myntra page.")
                    time.sleep(3)
                    continue
                
                # Extract titles to do a smart AI-like match
                myntra_products = {}
                for item in search_data:
                    # Combine brand + product name for a better match
                    full_name = f"{item.get('brand', '')} {item.get('productName', item.get('name', ''))}".strip().lower()
                    
                    price = str(item.get('price', ''))
                    # Myntra stores the link ending (e.g., "skin-care/dot-and-key/serum/12345/buy")
                    link_path = item.get('dre_landing_page_url', item.get('landingPageUrl', ''))
                    
                    myntra_products[full_name] = {
                        'link': f"https://www.myntra.com/{link_path}" if link_path else '',
                        'price': price
                    }
                
                # Use fuzzy matching to pair your DB product to the Myntra product
                myntra_titles = list(myntra_products.keys())
                best_matches = get_close_matches(search_term, myntra_titles, n=1, cutoff=0.5)
                
                if best_matches:
                    matched_title = best_matches[0]
                    matched_data = myntra_products[matched_title]
                    
                    if matched_data['link']:
                        p.myntra_link = matched_data['link']
                        p.myntra_price = matched_data['price']
                        p.save()
                        updated_count += 1
                        
                        print(f"    ✨ MYNTRA MATCH FOUND: {matched_title[:40]}")
                        print(f"       -> Price: ₹{matched_data['price']}")
                        print(f"       -> Link: {matched_data['link']}")
                else:
                    print("    ⚠️ No close match found in Myntra's search results.")
                    
            except KeyError:
                print("    🛑 Myntra changed their internal data structure!")
        else:
            print("    🛑 Could not find the hidden JSON data on the page.")
            
    except Exception as e:
        print(f"    🛑 Crash: {str(e)[:50]}")
        
    # Be polite to Myntra's servers to avoid a ban
    time.sleep(random.uniform(3.0, 6.0))

print(f"\n🎉 DONE! Successfully linked {updated_count} products to Myntra.")
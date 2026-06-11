import os
import requests
import django
from difflib import get_close_matches

# --- Setup Django Environment ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glowguide_web.settings') 
django.setup()
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from shop.models import Product

print("🛡️ Booting Shopify Backdoor Link Resolver...")

# ==========================================
# 🎯 PHASE 1: DOWNLOAD OFFICIAL CATALOG
# ==========================================
print("📥 Downloading official catalog data from Dot & Key...")

official_products = {}
page = 1

while True:
    # This is the hidden URL that returns pure Shopify product data
    json_url = f"https://www.dotandkey.com/products.json?limit=250&page={page}"
    response = requests.get(json_url, headers={'User-Agent': 'Mozilla/5.0'})
    
    if response.status_code != 200:
        print(f"❌ Failed to reach Shopify API. Status: {response.status_code}")
        break
        
    data = response.json()
    products_list = data.get('products', [])
    
    if not products_list:
        break # No more products to download
        
    for item in products_list:
        title = item['title'].lower().strip()
        handle = item['handle']
        # Map the exact title to its official link
        official_products[title] = f"https://www.dotandkey.com/products/{handle}"
        
    page += 1

print(f"✅ Successfully mapped {len(official_products)} official products from their website!\n")

# ==========================================
# 🎯 PHASE 2: MATCH AND UPDATE DATABASE
# ==========================================
# Get our database products that need links
db_products = Product.objects.filter(name__icontains='dot')
print(f"📦 Checking {db_products.count()} Dot & Key products in your database...")

official_titles = list(official_products.keys())
updated_count = 0

for p in db_products:
    # We only want to fix links that are missing or broken
    if p.vendor_link and '/products/' in p.vendor_link:
        continue 
        
    db_name = p.name.lower().strip()
    
    # Use difflib to find the closest matching product name from the official site
    # This handles slight differences (like "Vitamin C Serum" vs "10% Vitamin C Serum")
    best_matches = get_close_matches(db_name, official_titles, n=1, cutoff=0.4)
    
    if best_matches:
        matched_title = best_matches[0]
        official_link = official_products[matched_title]
        
        p.vendor_link = official_link
        p.save()
        updated_count += 1
        print(f"  ✨ FIXED: {p.name[:40]}")
        print(f"     -> {official_link}")
    else:
        print(f"  ⚠️ No match found for: {p.name[:40]}")

print(f"\n🎉 BOOM! Successfully injected official links into {updated_count} products.")
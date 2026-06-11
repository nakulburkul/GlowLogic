import os
import re
import json
import requests
import django
from bs4 import BeautifulSoup
from django.core.files.base import ContentFile

# --- Setup Django Environment ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glowguide_web.settings') 
django.setup()
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from shop.models import Product

def scrape_mamaearth_catalog():
    print("🚀 Engaging 'Sitemap Hack' + 'Triple Net' Deep Fetch...")
    
    sitemap_urls = [
        "https://mamaearth.in/sitemap.xml",
        "https://mamaearth.in/product-sitemap.xml",
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    }
    
    valid_urls = []
    
    try:
        # --- PHASE 1: GET THE URLS ---
        for url in sitemap_urls:
            print(f"📡 Scanning SEO Data at {url}...")
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                links = re.findall(r'(https://mamaearth\.in/product/[a-zA-Z0-9\-]+)', response.text)
                valid_urls.extend(links)
                
        unique_urls = list(set(valid_urls))
        print(f"👀 Extracted {len(unique_urls)} product URLs! Starting Triple Net Deep Fetch...\n")
        
        if len(unique_urls) == 0:
            print("🛑 Sitemap extraction failed.")
            return

        added_count = 0
        stacked_count = 0
        
        # --- PHASE 2: TRIPLE NET DEEP FETCH ---
        for vendor_url in unique_urls:
            raw_slug = vendor_url.split('/product/')[-1].split('/')[0].split('?')[0]
            raw_name = raw_slug.replace('-', ' ').title()
            
            if len(raw_name) < 10 or 'Category' in raw_name:
                continue
                
            name = f"Mamaearth {raw_name}" if "Mamaearth" not in raw_name else raw_name
            
            # Smart Categories
            category = "Skincare"
            if "serum" in name.lower(): category = "Serum"
            elif "wash" in name.lower() or "cleanser" in name.lower(): category = "Face Wash"
            elif "sunscreen" in name.lower() or "spf" in name.lower(): category = "Sunscreen"
            elif "cream" in name.lower() or "moisturizer" in name.lower(): category = "Moisturizer"
            elif "oil" in name.lower() or "shampoo" in name.lower(): category = "Haircare"

            print(f"  🔍 Inspecting: {name[:30]}...")
            price = "0"
            img_url = ""
            
            try:
                prod_response = requests.get(vendor_url, headers=headers, timeout=10)
                if prod_response.status_code == 200:
                    html_text = prod_response.text
                    soup = BeautifulSoup(html_text, 'html.parser')
                    
                    # 🕸️ NET 1: JSON-LD SEO Data
                    scripts = soup.find_all('script', type='application/ld+json')
                    for script in scripts:
                        if not script.string: continue
                        try:
                            data = json.loads(script.string)
                            # Sometimes it's a list of dicts, sometimes just a dict
                            if isinstance(data, list):
                                for item in data:
                                    if item.get('@type') == 'Product':
                                        if 'image' in item and not img_url:
                                            img_url = item['image'][0] if isinstance(item['image'], list) else item['image']
                                        if 'offers' in item and price == "0":
                                            offers = item['offers']
                                            offer_data = offers[0] if isinstance(offers, list) else offers
                                            price = str(int(float(offer_data.get('price', 0))))
                            elif data.get('@type') == 'Product':
                                if 'image' in data and not img_url:
                                    img_url = data['image'][0] if isinstance(data['image'], list) else data['image']
                                if 'offers' in data and price == "0":
                                    offers = data['offers']
                                    offer_data = offers[0] if isinstance(offers, list) else offers
                                    price = str(int(float(offer_data.get('price', 0))))
                        except: pass

                    # 🕸️ NET 2: Open Graph Meta Tags (Fallback)
                    if price == "0":
                        meta_price = soup.find('meta', property='product:price:amount') or soup.find('meta', property='og:price:amount')
                        if meta_price and meta_price.get('content'):
                            try: price = str(int(float(meta_price['content'])))
                            except: pass

                    if not img_url:
                        meta_img = soup.find('meta', property='og:image')
                        if meta_img and meta_img.get('content'):
                            img_url = meta_img['content']

                    # 🕸️ NET 3: Brute Force Regex (Final Fallback)
                    if price == "0":
                        price_match = re.search(r'"price"\s*:\s*(\d+)', html_text)
                        if price_match:
                            price = price_match.group(1)

                    if not img_url:
                        # Looking for standard image extensions in the raw code
                        img_match = re.search(r'"image"\s*:\s*"([^"]+\.(?:jpg|png|webp))"', html_text)
                        if img_match:
                            img_url = img_match.group(1).replace('\\u002F', '/') # Clean escaped URLs

            except Exception as e:
                print(f"     ⚠️ Could not load page data: {e}")

            amazon_link = f"https://www.amazon.in/s?k=mamaearth+{raw_slug.replace('-', '+')}"

            # --- PHASE 3: DATABASE SAVE & IMAGE DOWNLOAD ---
            existing_product = Product.objects.filter(name__icontains=raw_name[:15]).first()

            if existing_product:
                existing_product.vendor_link = vendor_url
                if price != "0": existing_product.price = price
                if not existing_product.amazon_link: existing_product.amazon_link = amazon_link
                
                # Image Download for Existing
                if img_url and not existing_product.image:
                    try:
                        img_res = requests.get(img_url, timeout=10)
                        if img_res.status_code == 200:
                            safe_name = "".join([c for c in name if c.isalpha() or c.isdigit()]).strip()[:30]
                            existing_product.image.save(f"{safe_name}.jpg", ContentFile(img_res.content), save=False)
                    except: pass
                    
                existing_product.save()
                print(f"    🔄 Stacked & Updated (₹{price})")
                stacked_count += 1
            else:
                new_product = Product(
                    name=name[:200],
                    category=category,
                    suitable="All Skin Types",
                    price=price,
                    stock=50,
                    vendor_link=vendor_url,
                    amazon_link=amazon_link
                )
                
                # Image Download for New
                if img_url:
                    try:
                        img_res = requests.get(img_url, timeout=10)
                        if img_res.status_code == 200:
                            safe_name = "".join([c for c in name if c.isalpha() or c.isdigit()]).strip()[:30]
                            new_product.image.save(f"{safe_name}.jpg", ContentFile(img_res.content), save=False)
                    except: pass
                    
                new_product.save()
                print(f"    ➕ Added (₹{price})")
                added_count += 1
                
        print(f"\n🎉 MASSIVE PIPELINE COMPLETE! Added {added_count} new products and stacked {stacked_count} existing ones.")
        
    except Exception as e:
        print(f"🛑 Critical Pipeline Error: {e}")

if __name__ == "__main__":
    scrape_mamaearth_catalog()
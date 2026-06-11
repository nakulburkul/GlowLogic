import os
import django
import requests

# 1. Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glowguide_web.settings') 
django.setup()
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from shop.models import Product

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "static", "images")
os.makedirs(IMAGE_DIR, exist_ok=True)

def download_image(image_url, product_name):
    if not image_url: return
    if image_url.startswith('//'): image_url = "https:" + image_url
        
    # EXACT MATCH TO YOUR MODEL'S LOGIC
    safe_name = "".join([c for c in product_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    safe_name = safe_name[:50].strip() # Added the 50 character limit!
    filename = f"{safe_name}.jpg"
    filepath = os.path.join(IMAGE_DIR, filename)

    if os.path.exists(filepath): return

    try:
        response = requests.get(image_url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)
    except Exception:
        pass

def scrape_shopify_json_api():
    print("🚀 Connecting directly to Dot & Key's Secret Database API...")
    
    # This URL fetches up to 250 products directly from their backend in pure JSON!
    url = "https://www.dotandkey.com/products.json?limit=250"
    
    response = requests.get(url)
    if response.status_code != 200:
        print("❌ Failed to connect to API.")
        return
        
    data = response.json()
    products = data.get('products', [])
    
    print(f"👀 API successfully returned {len(products)} products!")
    
    added_count = 0
    for item in products:
        try:
            # 1. Get Title
            raw_name = item.get('title', '')
            name = raw_name if "Dot & Key" in raw_name else f"Dot & Key {raw_name}"
            
           # 2. Get Price (Cleaned for the database!)
            variants = item.get('variants', [])
            if not variants: continue
            raw_price = variants[0].get('price', '0')
            
            # Remove any decimals or commas so the DB doesn't crash
            try:
                clean_price = str(int(float(raw_price.replace(',', ''))))
            except ValueError:
                clean_price = "0"
                
            # 3. Get Link
            handle = item.get('handle', '')
            link = f"https://www.dotandkey.com/products/{handle}?utm_source=ppipl&utm_medium=affiliate&irclid=m8tFz6fM0mDf"
            
            # Dummy Amazon Link for demo
            amazon_link = f"https://www.amazon.in/s?k=dot+and+key+{handle.replace('-', '+')}&tag=your_amazon_affiliate_tag-21"
            
            # 4. Get Image
            images = item.get('images', [])
            image_url = images[0].get('src', '') if images else ''
            
            # 5. Smart Category
            product_type = item.get('product_type', '').lower()
            if "serum" in product_type or "serum" in name.lower(): category = "Serum"
            elif "moisturizer" in product_type or "cream" in name.lower(): category = "Moisturizer"
            elif "sunscreen" in product_type or "spf" in name.lower(): category = "Sunscreen"
            elif "wash" in product_type or "cleanser" in name.lower(): category = "Face Wash"
            else: category = "Skincare"

            download_image(image_url, name)

          # Save to Database
            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'suitable': "All Skin Types",
                    'price': clean_price,             # <--- FIXED!
                    'stock': 25,
                    'vendor_link': link,
                    'amazon_price': amazon_price_str,
                    'amazon_link': amazon_link
                }
            )
            
            if created:
                added_count += 1
                print(f"🛍️ Added: {name[:35]}... (D&K: ₹{price} | Amazon: ₹{amazon_price_str})")
                
        except Exception as e:
            continue

    print(f"\n🎉 ULTIMATE VICTORY! Added {added_count} new Dot & Key products instantly.")

if __name__ == "__main__":
    scrape_shopify_json_api()
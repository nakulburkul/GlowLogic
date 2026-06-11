import os
import requests
import django
from django.core.files.base import ContentFile

# --- Setup Django Environment ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glowguide_web.settings') 
django.setup()
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from shop.models import Product

def scrape_dermaco_catalog():
    print("🚀 Connecting to The Derma Co Backend...")
    
    # Using the Shopify/Headless JSON backend trick
    url = "https://thedermaco.com/collections/all/products.json?limit=250"
    
    try:
        # Added a User-Agent to prevent The Derma Co from blocking our script
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ Failed to connect to API. Status: {response.status_code}")
            return
            
        data = response.json()
        products = data.get('products', [])
        
        print(f"👀 Successfully bypassed frontend. Found {len(products)} products!")
        
        added_count = 0
        stacked_count = 0
        
        for item in products:
            # 1. Clean Title
            raw_name = item.get('title', '')
            name = raw_name if "Derma Co" in raw_name or "derma co" in raw_name.lower() else f"The Derma Co {raw_name}"
            
            # 2. Extract and Clean Price
            variants = item.get('variants', [])
            if not variants: continue
            raw_price = str(variants[0].get('price', '0'))
            
            try:
                clean_price = str(int(float(raw_price.replace(',', ''))))
            except ValueError:
                clean_price = "0"
                
            # 3. Generate Links
            handle = item.get('handle', '')
            vendor_link = f"https://thedermaco.com/product/{handle}"
            amazon_link = f"https://www.amazon.in/s?k=the+derma+co+{handle.replace('-', '+')}"
            
            # 4. Smart Category Routing
            product_type = item.get('product_type', '').lower()
            if "serum" in product_type or "serum" in name.lower(): category = "Serum"
            elif "wash" in product_type or "cleanser" in name.lower(): category = "Face Wash"
            elif "sunscreen" in product_type or "spf" in name.lower(): category = "Sunscreen"
            elif "cream" in product_type or "moisturizer" in name.lower(): category = "Moisturizer"
            else: category = "Skincare"

            # ==========================================
            # 🛑 THE STACKING LOGIC
            # ==========================================
            # Check if this product already exists in your catalog
            existing_product = Product.objects.filter(name__icontains=raw_name[:15]).first()

            if existing_product:
                # If it exists, JUST UPDATE the vendor link and price! Don't duplicate.
                existing_product.vendor_link = vendor_link
                existing_product.price = clean_price
                if not existing_product.amazon_link:
                    existing_product.amazon_link = amazon_link
                existing_product.save()
                
                print(f"  🔄 Stacked & Updated: {name[:40]}")
                stacked_count += 1
            else:
                # 5. Save New Product to Database
                product = Product.objects.create(
                    name=name,
                    category=category,
                    suitable="All Skin Types",
                    price=clean_price,
                    stock=50,
                    vendor_link=vendor_link,
                    amazon_link=amazon_link
                )
                
                # 6. Direct Image Download
                images = item.get('images', [])
                if images:
                    img_url = images[0].get('src', '')
                    if img_url:
                        try:
                            img_response = requests.get(img_url, timeout=10)
                            if img_response.status_code == 200:
                                safe_name = "".join([c for c in name if c.isalpha() or c.isdigit()]).strip()[:30]
                                file_name = f"{safe_name}_dermaco.jpg"
                                product.image.save(file_name, ContentFile(img_response.content), save=True)
                        except Exception:
                            pass
                
                added_count += 1
                print(f"  ➕ Added New Product: {name[:40]}")
                
        print(f"\n🎉 COMPLETE! Added {added_count} new products and updated/stacked {stacked_count} existing ones.")
        
    except Exception as e:
        print(f"🛑 Critical Pipeline Error: {e}")

if __name__ == "__main__":
    scrape_dermaco_catalog()
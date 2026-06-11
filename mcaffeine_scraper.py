import os
import requests
import django
from django.core.files.base import ContentFile

# --- Setup Django Environment ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glowguide_web.settings') 
django.setup()
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from shop.models import Product

def scrape_mcaffeine_special_offer():
    print("🚀 Connecting to mCaffeine's Shopify Backend...")
    
    # We append /products.json to the exact collection URL you provided
    url = "https://www.mcaffeine.com/collections/special-offer/products.json?limit=250"
    
    # Your specific affiliate tracking string
    affiliate_params = "?utm_source=affiliate&utm_medium=partnerships&utm_campaign=trackier_cashkaro1&utm_term=ENKR20260429A1948631783&click_id=69f1fd80319a1ecccc3fa0f7"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            print(f"❌ Failed to connect to API. Status: {response.status_code}")
            return
            
        data = response.json()
        products = data.get('products', [])
        
        print(f"👀 Successfully bypassed frontend. Found {len(products)} products in the collection!")
        
        added_count = 0
        
        for item in products:
            # 1. Clean Title (Ensure 'mCaffeine' is in the name for the template trigger)
            raw_name = item.get('title', '')
            name = raw_name if "mCaffeine" in raw_name or "mcaffeine" in raw_name.lower() else f"mCaffeine {raw_name}"
            
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
            vendor_link = f"https://www.mcaffeine.com/products/{handle}{affiliate_params}"
            amazon_link = f"https://www.amazon.in/s?k=mcaffeine+{handle.replace('-', '+')}"
            
            # 4. Smart Category Routing
            product_type = item.get('product_type', '').lower()
            if "serum" in product_type or "serum" in name.lower(): category = "Serum"
            elif "wash" in product_type or "cleanser" in name.lower(): category = "Face Wash"
            elif "scrub" in product_type or "exfoliat" in name.lower(): category = "Exfoliant"
            elif "mask" in product_type: category = "Mask"
            else: category = "Skincare"

            # 5. Save to Database (First pass)
            product, created = Product.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'suitable': "All Skin Types",
                    'price': clean_price,
                    'stock': 50,
                    'vendor_link': vendor_link,
                    'amazon_link': amazon_link
                }
            )
            
            # 6. Direct Image Download to Admin Hook
            if created and not product.image:
                images = item.get('images', [])
                if images:
                    img_url = images[0].get('src', '')
                    if img_url:
                        try:
                            img_response = requests.get(img_url, timeout=10)
                            if img_response.status_code == 200:
                                safe_name = "".join([c for c in name if c.isalpha() or c.isdigit()]).strip()[:30]
                                file_name = f"{safe_name}_mcaffeine.jpg"
                                # Native Django Admin save
                                product.image.save(file_name, ContentFile(img_response.content), save=True)
                        except Exception:
                            pass
            
            if created:
                added_count += 1
                print(f"  ✅ Added & Linked: {name[:40]}")
                
        print(f"\n🎉 OPERATION COMPLETE! {added_count} mCaffeine items injected into GlowGuide.")
        
    except Exception as e:
        print(f"🛑 Critical Pipeline Error: {e}")

if __name__ == "__main__":
    scrape_mcaffeine_special_offer()
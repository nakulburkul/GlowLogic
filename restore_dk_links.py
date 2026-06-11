import os
import requests
import django

# --- Setup Django Environment ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glowguide_web.settings') 
django.setup()
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"

from shop.models import Product

def restore_dot_and_key_links():
    print("🔄 Connecting to Dot & Key API to restore lost links...")
    
    # Hit the Shopify backend directly
    url = "https://www.dotandkey.com/products.json?limit=250"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code != 200:
            print(f"❌ Failed to connect. Status: {response.status_code}")
            return
            
        data = response.json()
        products = data.get('products', [])
        
        print(f"👀 Found {len(products)} products in the D&K database.")
        
        restored_count = 0
        missing_count = 0
        
        for item in products:
            # 1. Reconstruct the exact name saved in your database
            raw_name = item.get('title', '')
            name = raw_name if "Dot & Key" in raw_name else f"Dot & Key {raw_name}"
            
            # 2. Grab the Shopify handle and rebuild your official affiliate link
            handle = item.get('handle', '')
            correct_link = f"https://www.dotandkey.com/products/{handle}?utm_source=ppipl&utm_medium=affiliate&irclid=m8tFz6fM0mDf"
            
            # 3. Find the product in your database
            db_product = Product.objects.filter(name=name).first()
            
            # 4. Inject the correct link
            if db_product:
                db_product.vendor_link = correct_link
                db_product.save()
                restored_count += 1
                print(f"  ✅ Restored: {name[:45]}...")
            else:
                missing_count += 1
                
        print(f"\n🎉 SUCCESS! Restored {restored_count} official Dot & Key links.")
        if missing_count > 0:
            print(f"  ℹ️ Note: {missing_count} products from the API were not found in your local database.")
        
    except Exception as e:
        print(f"🛑 Critical Error: {e}")

if __name__ == "__main__":
    restore_dot_and_key_links()
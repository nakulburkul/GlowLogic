import os
import django
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glowguide_web.settings')
django.setup()

from shop.models import Product

def import_data():
    print("✨ Starting Amazon Data Import...")
    
    # Target your specific uploaded datasets
    files_to_import = [
        'dataset_Amazon-crawler_2026-04-27_08-44-47-069.json',
        'dataset_Amazon-crawler_2026-04-27_09-04-15-888.json'
    ]

    added_count = 0

    # Loop through each dataset file
    for filename in files_to_import:
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                products_data = json.load(file)
                print(f"📂 Opened {filename} ({len(products_data)} items found)")
        except FileNotFoundError:
            print(f"❌ Error: Could not find '{filename}'. Make sure it is in the same folder as this script!")
            continue

        # Loop through the data in the current file
        for item in products_data:
            # Amazon scrapers use various keys, so we check a few common ones
            name = item.get('title') or item.get('name') or item.get('productName')
            price = item.get('price') or item.get('price_string') or item.get('priceInfo', {}).get('price') or "0"
            link = item.get('url') or item.get('link') or item.get('productUrl')
            
            # Skip if essential data is missing from the scrape
            if not name or not link:
                continue

            # Advanced category guessing for better algorithm filtering
            category = "Serum"
            name_lower = name.lower()
            if "cleanser" in name_lower or "wash" in name_lower or "micellar" in name_lower: category = "Cleanser"
            elif "moisturizer" in name_lower or "cream" in name_lower or "lotion" in name_lower: category = "Moisturizer"
            elif "sunscreen" in name_lower or "spf" in name_lower: category = "Sunscreen"
            elif "toner" in name_lower or "mist" in name_lower: category = "Toner"
            elif "exfolia" in name_lower or "scrub" in name_lower or "peel" in name_lower: category = "Exfoliant"

            # Save to Database securely
            try:
                Product.objects.get_or_create(
                    name=name[:200], # Limit length to prevent database crashes
                    defaults={
                        'category': category,
                        'suitable': "All Skin Types",
                        'price': str(price)[:50],
                        'stock': 100, 
                        'vendor_link': link[:500]
                    }
                )
                added_count += 1
            except Exception as e:
                # Silently skip errors (like super long unformatted links) to keep the script running
                pass

    print(f"\n🎉 Success! Added {added_count} valid Amazon products into the GlowGuide catalog.")

if __name__ == "__main__":
    import_data()
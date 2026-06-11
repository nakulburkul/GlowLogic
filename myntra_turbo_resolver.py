import os
import urllib.parse
import re
import django

# --- Setup Django Environment ---
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glowguide_web.settings') 
django.setup()

from shop.models import Product

print("⚡ Booting Myntra Zero-Block Link Generator (SEO-Trimmer Edition)...")

products = Product.objects.all()
total = products.count()

updated_count = 0

for p in products:
    # 1. Use the clean Core Name
    base_name = p.core_name if p.core_name else p.name
    base_name = str(base_name)
    
    # 2. Grab the specific size (if it exists)
    size = p.size_variant if p.size_variant and p.size_variant != "Standard" else ""
    
    # 3. Strip special characters from the core name
    clean_name = re.sub(r'[^a-zA-Z0-9\s]', ' ', base_name)
    words = clean_name.split()
    short_name = " ".join(words[:5]) 
    
    # 🧠 THE MAGIC: Combine the short name WITH the exact size!
    # e.g., "minimalist vitamin c serum 30ml"
    final_query = f"{short_name} {size}".strip()
    
    safe_query = urllib.parse.quote_plus(final_query)
    direct_search_link = f"https://www.myntra.com/{safe_query}?rawQuery={safe_query}"
    
    # Update the database
    p.myntra_link = direct_search_link
    p.myntra_price = "None" 
    
    # Use update() instead of save() here so we don't accidentally re-trigger the utils.py extractor!
    Product.objects.filter(id=p.id).update(myntra_link=direct_search_link, myntra_price="None")
    
    updated_count += 1
    if updated_count % 100 == 0:
        print(f"  ✅ Processed {updated_count}/{total} products...")

print(f"\n🎉 DONE! All {updated_count} products now have short, highly-accurate Myntra search links.")
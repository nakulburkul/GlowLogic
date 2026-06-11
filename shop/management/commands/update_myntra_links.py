import time
from django.core.management.base import BaseCommand
from shop.models import Product
from googlesearch import search

class Command(BaseCommand):
    help = 'Automatically finds and saves Myntra links (Pure Python Check)'

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Booting Auto-Linker (Pure Python Override)...")
        
        all_products = Product.objects.all()
        products_to_update = []
        
        # 🛡️ THE PURE PYTHON SHIELD
        # We check every product manually instead of asking the database to guess.
        for p in all_products:
            # Convert whatever is in the database to a standard, clean string
            link = str(p.myntra_link).strip().lower()
            
            # 1. Does it literally say 'none', 'null', or is it totally empty?
            if link in ['none', 'null', '']:
                products_to_update.append(p)
            # 2. Does it NOT start with http? (Catches random typed text)
            elif not link.startswith('http'):
                products_to_update.append(p)
            # 3. Is it too short? (Catches 'https://www.myntra.com' which is only 22 chars)
            # Real Myntra product URLs are massive (e.g., https://www.myntra.com/face-wash/brand/item/123/buy)
            elif len(link) < 28:
                products_to_update.append(p)

        self.stdout.write(f"Found {len(products_to_update)} products missing valid links.")
        
        if len(products_to_update) == 0:
            self.stdout.write(self.style.WARNING("⚠️ Wait... if it STILL says 0, double-check that you actually have products saved in your database!"))
            return

        for product in products_to_update:
            # Create a highly specific Google query
            query = f'site:myntra.com "{product.name}"'
            
            try:
                # Ask Google for the top 1 result, pause for 3 seconds so Google doesn't block us
                for url in search(query, num_results=1, sleep_interval=3):
                    if 'myntra.com' in url:
                        product.myntra_link = url
                        product.save()
                        self.stdout.write(self.style.SUCCESS(f"✅ Linked: {product.name[:30]} -> {url}"))
                        break # Move to the next product
            
            except Exception as e:
                self.stdout.write(self.style.WARNING(f"⚠️ Failed to find link for: {product.name}"))
            
        self.stdout.write(self.style.SUCCESS("🎉 Link pipeline complete! Your manual links are safe."))
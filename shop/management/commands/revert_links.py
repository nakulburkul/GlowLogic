import urllib.parse
from django.core.management.base import BaseCommand
from shop.models import Product

class Command(BaseCommand):
    help = 'Removes broken TechTrack/EarnKaro prefixes and restores original URLs'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("🔄 Reverting TechTrack links back to originals..."))
        
        # CHANGED: Now searching for the TechTrack domain you discovered!
        products = Product.objects.filter(vendor_link__icontains='track.techtrack.in')
        updated_count = 0

        for product in products:
            try:
                # The original link is still hidden at the very end after '&url='
                if '&url=' in product.vendor_link:
                    encoded_original_url = product.vendor_link.split('&url=')[1]
                    
                    # Decode it (turns %3A back into slashes, etc.)
                    clean_original_url = urllib.parse.unquote(encoded_original_url)
                    
                    # Save it back to the database
                    product.vendor_link = clean_original_url
                    product.save()
                    updated_count += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error fixing {product.name[:30]}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"✅ Successfully restored {updated_count} product links!"))
import urllib.parse
from django.core.management.base import BaseCommand
from shop.models import Product

class Command(BaseCommand):
    help = 'Batch converts raw Dot & Key URLs into EarnKaro Affiliate Deep Links'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("🔗 Booting up EarnKaro Deep Link Engine..."))
        
        # Target only Dot & Key links that haven't been converted to EarnKaro tracking yet
        products = Product.objects.filter(vendor_link__icontains='dotandkey.com').exclude(vendor_link__icontains='earnkaro')
        
        updated_count = 0

        # --- IMPORTANT EARNKARO CONFIGURATION ---
        # You need to locate your universal tracking prefix from your EarnKaro dashboard.
        # It typically requires your specific Affiliate ID and the Store's Offer ID.
        # Replace the placeholders below with your actual account credentials.
        
        # --- IMPORTANT EARNKARO CONFIGURATION ---
        # Updated to use the TechTrack routing you discovered!
        PUB_ID = "590"
        CAMPAIGN_ID = "24"
        
        # We leave out the "source=" part because EarnKaro generates that dynamically per click
        EARNKARO_PREFIX = f"https://track.techtrack.in/click?campaign_id={CAMPAIGN_ID}&pub_id={PUB_ID}&url="

        for product in products:
            try:
                # 1. Grab the raw original Dot & Key URL
                raw_url = product.vendor_link
                
                # 2. URL-Encode it (converts slashes and symbols into a safe format for tracking)
                safe_encoded_url = urllib.parse.quote(raw_url, safe='')
                
                # 3. Merge them together to create the finalized Deep Link
                deep_link = f"{EARNKARO_PREFIX}{safe_encoded_url}"
                
                # 4. Overwrite the raw URL in your database with the monetized link
                product.vendor_link = deep_link
                product.save()
                
                self.stdout.write(f"✅ Converted: {product.name[:30]}...")
                updated_count += 1
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ Error converting {product.name[:30]}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\n🎉 Deep Link Pipeline Complete! Monetized {updated_count} products."))
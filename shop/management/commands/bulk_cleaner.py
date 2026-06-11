from django.core.management.base import BaseCommand
from shop.models import Product

class Command(BaseCommand):
    help = 'Smart deduplication and cleaning of product names.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("🧹 Booting up GlowGuide Bulk Database Cleaner..."))

        # Put ALL your bad scraper names on the left, and the correct names on the right
        name_fixes = {
            "Dot & Key Very Dry Skin": "Dot & Key Blueberry Moisturizer for Very Dry Skin",
            "Dot & Key BESTSELLER": "Dot & Key Vitamin C + E Super Bright Sunscreen", 
            "Dot & Key All Skin Types": "Dot & Key Watermelon Superglow Matte Moisturizer", 
            "Dot & Key 4 Shades Available": "Dot & Key Strawberry Tinted Lip Balm",
            "Dot & Key Oily & Combination Skin": "Dot & Key Cica Niacinamide Night Gel",
            "Dot & Key Normal, Dry & Sensitive Skin": "Dot & Key Ceramide Barrier Repair Cream",
            "Dot & Key NORMAL, DRY & SENSITIVE SKIN": "Dot & Key Ceramide Barrier Repair Cream",
            # Keep adding any other weird names you find here!
        }

        deleted_count = 0
        renamed_count = 0

        for junk_name, correct_name in name_fixes.items():
            # Find any product that has the junk name
            junk_products = Product.objects.filter(name__icontains=junk_name)

            for junk_prod in junk_products:
                # Check if the PERFECT product already exists in your database
                perfect_product_exists = Product.objects.filter(name=correct_name).exists()

                if perfect_product_exists:
                    # The real one is already there! This junk one is just a duplicate causing the image/name mismatch.
                    self.stdout.write(self.style.ERROR(f"🗑️ Deleting Junk Duplicate: '{junk_prod.name}'"))
                    junk_prod.delete()
                    deleted_count += 1
                else:
                    # The real one doesn't exist yet, so we safely rename this one.
                    self.stdout.write(self.style.SUCCESS(f"✏️ Safely Renaming: '{junk_prod.name}' -> '{correct_name}'"))
                    junk_prod.name = correct_name
                    junk_prod.save()
                    renamed_count += 1

        self.stdout.write(self.style.SUCCESS(f"\n✅ Database Cleaned! Renamed {renamed_count} products and deleted {deleted_count} junk duplicates."))
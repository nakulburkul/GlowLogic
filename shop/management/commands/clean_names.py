from django.core.management.base import BaseCommand
from shop.models import Product
from django.db import IntegrityError

class Command(BaseCommand):
    help = 'Cleans and standardizes poorly scraped product names.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("🧹 Booting up GlowGuide Name Cleaner..."))
        
        # 1. THE OVERRIDE DICTIONARY
        name_fixes = {
            "Dot & Key Very Dry Skin": "Dot & Key Blueberry Moisturizer for Very Dry Skin",
            "Dot & Key BESTSELLER": "Dot & Key Vitamin C + E Super Bright Sunscreen", 
            "Dot & Key All Skin Types": "Dot & Key Watermelon Superglow Matte Moisturizer", 
            "Dot & Key 4 Shades Available": "Dot & Key Strawberry Tinted Lip Balm",
            "Dot & Key Oily & Combination Skin": "Dot & Key Cica Niacinamide Night Gel",
            "Dot & Key Normal, Dry & Sensitive Skin": "Dot & Key Ceramide Barrier Repair Cream",
            "Dot & Key NORMAL, DRY & SENSITIVE SKIN": "Dot & Key Ceramide Barrier Repair Cream",
        }

        updated_count = 0
        
        # Apply the exact dictionary fixes
        for old_name, new_name in name_fixes.items():
            products = Product.objects.filter(name__icontains=old_name)
            for p in products:
                # Safety check for duplicates
                if not Product.objects.filter(name=new_name).exclude(id=p.id).exists():
                    self.stdout.write(f"✏️ Renaming: '{p.name}' -> '{new_name}'")
                    p.name = new_name
                    p.save()
                    updated_count += 1
                
        # 2. THE SMART CATEGORY APPENDER
        all_dk_products = Product.objects.filter(name__icontains="Dot & Key")
        
        for p in all_dk_products:
            cat = str(p.category).lower()
            current_name = str(p.name).lower()
            
            if cat not in current_name and cat != 'other' and cat != '':
                old_name = p.name
                new_name = f"{old_name} {p.category.capitalize()}"
                
                # CRASH PREVENTION: Check if the name we are trying to create already exists!
                if Product.objects.filter(name=new_name).exists():
                    self.stdout.write(self.style.ERROR(f"⚠️ Skipping: '{new_name}' already exists in database."))
                else:
                    try:
                        p.name = new_name
                        p.save()
                        self.stdout.write(f"🔧 Smart Fix: '{old_name}' -> '{p.name}'")
                        updated_count += 1
                    except IntegrityError:
                        self.stdout.write(self.style.ERROR(f"⚠️ Failed to save '{new_name}' due to database constraints."))

        self.stdout.write(self.style.SUCCESS(f"\n✅ Cleaned up {updated_count} product names without crashing!"))
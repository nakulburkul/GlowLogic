from django.core.management.base import BaseCommand
from shop.models import Product
from django.db.models import Q
import os

class Command(BaseCommand):
    help = 'Generates a report of product link routing and saves it to a file.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("🚀 Booting up GlowGuide Database Scanner..."))

        # --- LIST 1: Linked to BOTH Official Site & Direct Amazon Page ---
        both_linked = Product.objects.filter(
            (Q(vendor_link__icontains='dotandkey') | Q(vendor_link__icontains='techtrack')),
            amazon_link__isnull=False
        ).exclude(amazon_link__exact='')

        # --- LIST 2: Using the Amazon Search Page Fallback ---
        search_fallback = Product.objects.filter(
            Q(amazon_link__isnull=True) | Q(amazon_link__exact='')
        )

        # --- DIRECT FILE CREATION (Bypasses Windows Terminal Limits) ---
        # We explicitly use encoding='utf-8' so it never crashes on weird characters again
        file_path = os.path.join(os.getcwd(), 'link_data.txt')
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("📊 GLOWGUIDE LINK ROUTING REPORT 📊\n")
            f.write("="*60 + "\n\n")
            
            f.write(f"✅ CATEGORY 1: Linked to BOTH Official & Amazon Direct ({both_linked.count()} products found):\n")
            for p in both_linked:
                f.write(f"  - {p.name}\n")
                
            f.write("\n" + "="*60 + "\n\n")
            
            f.write(f"🔍 CATEGORY 2: Linked to Amazon Search Page Fallback ({search_fallback.count()} products found):\n")
            for p in search_fallback:
                f.write(f"  - {p.name}\n")

        self.stdout.write(self.style.SUCCESS(f"✅ Report Complete! Data safely extracted and saved to: {file_path}"))
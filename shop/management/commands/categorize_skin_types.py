from django.core.management.base import BaseCommand
from shop.models import Product

class Command(BaseCommand):
    help = 'Auto-categorizes products into specific skin types based on keywords.'

    def handle(self, *args, **kwargs):
        self.stdout.write("🚀 Booting Skin Type Classifier...")
        
        products = Product.objects.all()
        updated_count = 0

        # Define our classification rules (Keywords must be lowercase)
        rules = {
            'Oily': ['salicylic', 'foaming', 'gel', 'clay', 'matte', 'oil-free', 'charcoal', 'niacinamide', 'pore'],
            'Dry': ['ceramide', 'hydrating', 'cream', 'hyaluronic', 'lotion', 'nourishing', 'shea butter', 'squalane'],
            'Sensitive': ['gentle', 'fragrance free', 'fragrance-free', 'calming', 'cica', 'centella', 'soothing', 'oat'],
            'Acne-Prone': ['acne', 'pimple', 'benzoyl', 'clarifying', 'tea tree', 'aha', 'bha'],
            'Normal / Combination': ['balancing', 'daily', 'essential']
        }

        for product in products:
            name = product.name.lower()
            assigned_type = None

            # Check the product name against our keyword rules
            for skin_type, keywords in rules.items():
                if any(keyword in name for keyword in keywords):
                    assigned_type = skin_type
                    break # Stop at the first match we find

            # If we found a specific match and it's currently generic or empty
            if assigned_type and (not product.suitable or 'all' in product.suitable.lower()):
                product.suitable = assigned_type
                product.save()
                self.stdout.write(self.style.SUCCESS(f"✅ Classified: {product.name[:40]} -> {assigned_type}"))
                updated_count += 1

        self.stdout.write(self.style.SUCCESS(f"🎉 Classification Complete! Updated {updated_count} products."))
from django.core.management.base import BaseCommand
from shop.models import Product, Wishlist, Notification

class Command(BaseCommand):
    help = 'Scans wishlists and alerts users if their saved products have dropped in price.'

    def handle(self, *args, **kwargs):
        self.stdout.write("🔍 Scanning for Price Drops...")
        
        # Grab all wishlist items across the entire platform
        wishlist_items = Wishlist.objects.select_related('user', 'product').all()
        alerts_sent = 0

        for item in wishlist_items:
            product = item.product
            user = item.user
            
            # Check if the product has a valid lowest price and base price
            if product.lowest_price and product.price:
                try:
                    current_deal = float(product.lowest_price)
                    base_price = float(product.price)
                    
                    # If the current price is at least 10% cheaper than the base price
                    if current_deal <= (base_price * 0.90):
                        
                        # Check if we already notified them today to prevent spam
                        recent_alert = Notification.objects.filter(
                            user=user, 
                            link=f"/shop/product/{product.id}/",
                            is_read=False
                        ).exists()
                        
                        if not recent_alert:
                            Notification.objects.create(
                                user=user,
                                title="📉 Price Drop Alert!",
                                message=f"{product.name[:30]}... dropped to ₹{current_deal}! Grab it before it sells out.",
                                link=f"/shop/product/{product.id}/"
                            )
                            alerts_sent += 1
                except ValueError:
                    continue
                    
        self.stdout.write(self.style.SUCCESS(f"✅ Scan complete. Sent {alerts_sent} price drop notifications!"))
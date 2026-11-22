# shop/tasks.py
from celery import shared_task
from django.utils import timezone
from .models import Wishlist, Product, Notification

@shared_task
def scan_for_price_drops():
    """
    Background worker that iterates over all Wishlisted items.
    If a price drops below a threshold, it generates an in-app Notification.
    """
    # Grab all unique products currently saved in any user's wishlist
    wishlisted_product_ids = Wishlist.objects.values_list('product_id', flat=True).distinct()
    products_to_check = Product.objects.filter(id__in=wishlisted_product_ids)
    
    alerts_sent = 0
    
    for product in products_to_check:
        # In a real app, you would fire a scraping script or API call here
        # Example: current_amazon_price = check_amazon_api(product.amazon_link)
        
        # For this logic engine, we simulate detecting a massive price drop
        current_live_price = float(product.lowest_price or product.price)
        historical_average = current_live_price * 1.20 # Simulating it used to be 20% higher
        
        if current_live_price < historical_average:
            # The price dropped! Find everyone who wishlisted it.
            users_tracking_this = Wishlist.objects.filter(product=product).select_related('user')
            
            for item in users_tracking_this:
                # Fire off the notification!
                Notification.objects.create(
                    user=item.user,
                    title="🔥 Massive Price Drop!",
                    message=f"{product.name} just dropped to ₹{current_live_price}! Grab it before it sells out.",
                    link=f"/shop/product/{product.id}/"
                )
                alerts_sent += 1
                
    return f"Task Complete: Scanned {products_to_check.count()} products. Dispatched {alerts_sent} alerts."
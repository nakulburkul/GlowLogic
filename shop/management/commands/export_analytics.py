import pandas as pd
from django.core.management.base import BaseCommand
from shop.models import OutboundClick, Wishlist

class Command(BaseCommand):
    help = 'Generates clean datasets for dashboard visualizations'

    def handle(self, *args, **kwargs):
        self.stdout.write("📊 Crunching GlowGuide Analytics...")
        
        # 1. Affiliate Click Data
        clicks = list(OutboundClick.objects.all().values('product_name', 'store_name', 'clicked_at'))
        if clicks:
            df_clicks = pd.DataFrame(clicks)
            # Remove timezone for clean BI software compatibility
            df_clicks['clicked_at'] = pd.to_datetime(df_clicks['clicked_at']).dt.tz_localize(None) 
            
            df_clicks.to_csv('analytics_clicks.csv', index=False)
            self.stdout.write(self.style.SUCCESS("✅ Exported analytics_clicks.csv"))
        
        # 2. Wishlist Popularity & Trending
        wishlist = list(Wishlist.objects.all().values('product__name', 'product__category', 'product__price'))
        if wishlist:
            df_wish = pd.DataFrame(wishlist)
            # Count the total saves per product to see what's trending
            df_trending = df_wish.groupby(['product__name', 'product__category']).size().reset_index(name='total_saves')
            df_trending = df_trending.sort_values(by='total_saves', ascending=False)
            
            df_trending.to_csv('analytics_trending.csv', index=False)
            self.stdout.write(self.style.SUCCESS("✅ Exported analytics_trending.csv"))
            
        self.stdout.write("🚀 Datasets generated! Ready for ingestion.")
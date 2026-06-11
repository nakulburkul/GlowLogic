import os
import time
import random
import requests
import urllib.parse
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.management.base import BaseCommand
from django.conf import settings
from shop.models import Product

class Command(BaseCommand):
    help = 'Stealth Amazon scraper to avoid CAPTCHA blocks'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("🚀 Booting Stealth Price Pipeline..."))
        
        # Only check products that ACTUALLY have an Amazon link
        products = list(Product.objects.exclude(vendor_link__isnull=True).exclude(vendor_link__exact=''))
        
        failed_reports = []
        updated_count = 0

        # Expanded stealth headers
        HEADERS_LIST = [
            {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36', 'Accept-Language': 'en-US,en;q=0.9', 'Sec-Fetch-Dest': 'document'},
            {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15', 'Accept-Language': 'en-US,en;q=0.9', 'Sec-Fetch-Dest': 'document'},
            {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36', 'Accept-Language': 'en-US,en;q=0.9', 'Sec-Fetch-Dest': 'document'}
        ]

        def fetch_price(product):
            session = requests.Session()
            headers = random.choice(HEADERS_LIST)
            
            # 🚀 STEALTH MODE: Sleep for 4 to 8 seconds like a human reading a page
            time.sleep(random.uniform(4.0, 8.0))

            try:
                response = session.get(product.vendor_link, headers=headers, timeout=15)
                
                if response.status_code != 200:
                    return {'product': product, 'price': None, 'error': f"HTTP {response.status_code} Blocked"}

                soup = BeautifulSoup(response.content, 'html.parser')
                domain = urllib.parse.urlparse(product.vendor_link).netloc.lower()
                
                if 'amazon' in domain:
                    page_title = soup.title.text.lower() if soup.title else ""
                    if "robot check" in page_title or "captcha" in page_title:
                        return {'product': product, 'price': None, 'error': "Amazon CAPTCHA Block"}
                        
                    possible_price_classes = [
                        ('span', 'a-price-whole'),
                        ('span', 'a-offscreen'),
                        ('span', 'a-color-price'),
                        ('span', 'priceblock_ourprice')
                    ]
                    
                    for tag, class_name in possible_price_classes:
                        price_element = soup.find(tag, class_=class_name)
                        if price_element and price_element.text:
                            raw_text = price_element.text.strip()
                            if any(char.isdigit() for char in raw_text):
                                clean_num = ''.join(c for c in raw_text if c.isdigit() or c == '.')
                                try:
                                    return {'product': product, 'price': str(int(float(clean_num))), 'error': None}
                                except ValueError:
                                    pass

                return {'product': product, 'price': None, 'error': "Out of stock or missing"}

            except requests.exceptions.RequestException as e:
                return {'product': product, 'price': None, 'error': f"Connection Error"}

        self.stdout.write(f"📦 Processing {len(products)} products in STEALTH mode...")
        
        # 🚀 STEALTH MODE: Reduced from 5 to 1 to stop Amazon from banning your IP
        with ThreadPoolExecutor(max_workers=1) as executor:
            future_to_product = {executor.submit(fetch_price, p): p for p in products}
            
            for future in as_completed(future_to_product):
                result = future.result()
                product = result['product']
                new_price = result['price']
                error_msg = result['error']
                
                if new_price:
                    product.price = new_price
                    product.save()
                    self.stdout.write(f"  ✅ [UPDATED] {product.name[:35]} -> ₹{new_price}")
                    updated_count += 1
                else:
                    self.stdout.write(self.style.WARNING(f"  ⚠️ [FAILED] {product.name[:35]} ({error_msg})"))
                    failed_reports.append(f"{product.name} | ERROR: {error_msg}")

        self.stdout.write(self.style.SUCCESS(f"\n🎉 Pipeline Complete! Updated {updated_count} products."))
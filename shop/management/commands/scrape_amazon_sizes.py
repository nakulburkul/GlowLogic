import os
import re
import time
import random
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from shop.models import Product, ExtraSize

class Command(BaseCommand):
    help = 'God-Mode Amazon Scraper: Hunts raw ASINs and Prices across any layout.'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS("🚀 Booting Upgraded Amazon Variant Scraper (God Mode)..."))
        
        products = Product.objects.exclude(amazon_link__isnull=True).exclude(amazon_link__exact='')
        
        # Ironclad Headers to force Amazon to serve the desktop site
        HEADERS_LIST = [
            {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
        ]

        total_added = 0

        for product in products:
            self.stdout.write(f"\n🔍 Checking: {product.name[:40]}...")
            
            session = requests.Session()
            headers = random.choice(HEADERS_LIST)
            time.sleep(random.uniform(2.5, 5.0)) # Anti-ban sleep

            try:
                response = session.get(product.amazon_link, headers=headers, timeout=15)
                
                if response.status_code != 200:
                    self.stdout.write(self.style.WARNING(f"  ⚠️ Blocked (HTTP {response.status_code})"))
                    continue

                soup = BeautifulSoup(response.content, 'html.parser')
                
                if "robot check" in soup.title.text.lower() if soup.title else "":
                    self.stdout.write(self.style.ERROR("  🛑 CAPTCHA Hit. Skipping."))
                    continue

                # Figure out the base ASIN so we don't save the main product as an "extra" size
                base_asin_match = re.search(r'([A-Z0-9]{10})', product.amazon_link)
                base_asin = base_asin_match.group(1) if base_asin_match else ""

                variants_found = {}

                # 🚀 THE VACUUM: Scan EVERY list item, button, and dropdown option on the page
                elements_to_check = soup.find_all(['li', 'button', 'option'])

                for element in elements_to_check:
                    asin = None
                    
                    # Look for hidden ASINs in common Amazon attributes
                    raw_asin = element.get('data-defaultasin') or element.get('data-csa-c-item-id') or element.get('value', '')
                    dp_url = element.get('data-dp-url', '')
                    
                    # Extract 10-digit ASIN using Regex
                    asin_match = re.search(r'([A-Z0-9]{10})', str(raw_asin) + str(dp_url))
                    if asin_match:
                        asin = asin_match.group(1)

                    if not asin or asin == base_asin:
                        continue # Skip if no ASIN or if it's the exact product we are already on

                    raw_text = element.text.strip()
                    if not raw_text or 'Select' in raw_text:
                        continue

                    # Split the tile text line-by-line
                    lines = [line.strip() for line in raw_text.split('\n') if line.strip()]
                    if not lines:
                        continue

                    # The first line is almost always the Size Name
                    size_name = re.sub(r'(?i)Click to select\s*', '', lines[0]).strip()
                    
                    # If the entire tile just says "₹300", it's a false positive. Skip.
                    if '₹' in size_name and len(lines) == 1:
                        continue

                    # 🚀 PRICE EXTRACTION: Scan all lines in the tile for a price tag
                    price_val = None
                    for line in lines:
                        if '₹' in line or 'Rs' in line:
                            # Strip out everything except numbers and decimals
                            clean_num = ''.join(c for c in line if c.isdigit() or c == '.')
                            if clean_num:
                                try:
                                    price_val = str(int(float(clean_num)))
                                    break # Got it! Stop searching lines.
                                except ValueError:
                                    pass

                    # Store in dictionary to prevent duplicates from the same page
                    if asin not in variants_found:
                        variants_found[asin] = {
                            'size': size_name, 
                            'price': price_val, 
                            'link': f"https://www.amazon.in/dp/{asin}"
                        }

                if not variants_found:
                    self.stdout.write(self.style.WARNING("  ⚪ No sizes found on this page."))
                    continue

                # Process the found variants
                for asin, data in variants_found.items():
                    size_name = data['size']
                    
                    # --- CATALOG DUPLICATE CHECK ---
                    if str(product.size_variant).strip().lower() == size_name.lower():
                        continue
                        
                    if ExtraSize.objects.filter(product=product, size_name__iexact=size_name).exists():
                        continue
                        
                    if product.core_name and Product.objects.filter(core_name=product.core_name, size_variant__iexact=size_name).exists():
                        continue

                    # --- SAVE NEW DATA ---
                    ExtraSize.objects.create(
                        product=product,
                        size_name=size_name,
                        amazon_link=data['link'],
                        price=data['price'] # 🚀 It now saves the price!
                    )
                    
                    if data['price']:
                        self.stdout.write(self.style.SUCCESS(f"  ➕ Added Size: {size_name} (₹{data['price']})"))
                    else:
                        self.stdout.write(self.style.SUCCESS(f"  ➕ Added Size: {size_name} (Price Check Pending)"))
                    
                    total_added += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  ❌ Error fetching page: {str(e)[:40]}"))

        self.stdout.write(self.style.SUCCESS(f"\n🎉 Pipeline Complete! Automatically extracted and added {total_added} new sizes with prices."))
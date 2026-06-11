import time
import requests
import re
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from shop.models import Product

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class Command(BaseCommand):
    help = 'Safe Mode Scraper: Perfected Search detection and Shopify paise/cents correction.'

    def resolve_deep_link(self, url, headers):
        session = requests.Session()
        try:
            response = session.get(url, headers=headers, timeout=(3, 8), allow_redirects=True)
            if any(short in response.url for short in ["fktr.in", "myntr.it", "ekaro.in", "bit.ly", "bitli.in"]):
                soup = BeautifulSoup(response.content, 'html.parser')
                meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
                
                if meta_refresh and 'url=' in meta_refresh.get('content', '').lower():
                    next_url = meta_refresh['content'].split('url=')[-1].strip("'\" ")
                    response = session.get(next_url, headers=headers, timeout=(3, 8), allow_redirects=True)
                else:
                    js_redirect = re.search(r'window\.location\.(?:replace|href)\s*=\s*[\'"]([^\'"]+)[\'"]', response.text)
                    if js_redirect:
                        next_url = js_redirect.group(1)
                        response = session.get(next_url, headers=headers, timeout=(3, 8), allow_redirects=True)
            return response.url
        except Exception:
            return url

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.page_load_strategy = 'eager'
        
        prefs = {
            "profile.managed_default_content_settings.images": 2,
            "profile.managed_default_content_settings.stylesheet": 2,
            "profile.managed_default_content_settings.fonts": 2
        }
        chrome_options.add_experimental_option("prefs", prefs)
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36")

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {"userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36'})
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        return driver

    def is_search_page(self, url, platform_name):
        """Strictly detects actual search and category listing pages across all platforms."""
        url_lower = url.lower()
        
        if platform_name == 'amazon':
            if '/s?k=' in url_lower or '/s?' in url_lower:
                return True
                
        if platform_name == 'flipkart':
            if '/search?' in url_lower:
                return True
                
        if platform_name == 'myntra':
            # Blocks actual search pages, raw queries, and generic "Shop/Brand" listing grids
            if any(bad_path in url_lower for bad_path in ['/search', 'rawquery=', '/shop/', 'myntra.com/brand/']):
                return True
            # Removed the overly strict '/buy' requirement!
                
        if platform_name == 'vendor':
            # Blocks explicit searches AND Shopify "Category/Collection" grids
            if '/search' in url_lower or '/collections/' in url_lower:
                return True
                
        return False
    def clean_price(self, raw_text):
        """Extracts price while actively blocking weights, percentages, and variant sizes."""
        if not raw_text: return None
            
        text = str(raw_text).replace(',', '')
        
        # 🛡️ THE VARIANT SHIELD: Strip out sizes and percentages before looking for money!
        # This stops "10% Niacinamide", "30ml", or "20g" from turning into ₹10, ₹30, or ₹20.
        text = re.sub(r'\d+\s*(?:ml|g|gm|kg|oz|%)\b', '', text, flags=re.IGNORECASE)
        
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        
        if numbers:
            # Filter out tiny numbers (like star ratings or pack quantities)
            valid_prices = [float(n) for n in numbers if float(n) > 10]
            if valid_prices:
                price = min(valid_prices) # Grab the sale price instead of MRP
                
                # The Shopify Cents Fix
                if price > 10000: 
                    price = price / 100.0
                    
                return price
        return None

    def scrape_with_browser(self, driver, final_url, platform_name):
        if not final_url or "http" not in final_url: return None

        if self.is_search_page(final_url, platform_name):
            self.stdout.write(self.style.WARNING(f"      ⚠️ Skipping Search Page: {platform_name.upper()}"))
            return None

        try:
            driver.get(final_url)
            time.sleep(2) 
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            raw_price = None

            # 🚀 STRICT VISUAL TARGETING: Only grab the price currently rendered on the screen
            if platform_name == 'amazon':
                price_elem = soup.select_one('.a-price-whole')
                if price_elem: raw_price = price_elem.get_text(separator=" ", strip=True)
            elif platform_name == 'flipkart':
                price_elem = soup.select_one('.Nx9bqj') or soup.select_one('._30jeq3') or soup.select_one('div.Nx9bqj.Crvsdt')
                if price_elem: raw_price = price_elem.get_text(separator=" ", strip=True)
            elif platform_name == 'myntra':
                price_elem = soup.select_one('.pdp-price') or soup.select_one('span.pdp-price') or soup.select_one('strong')
                if price_elem: raw_price = price_elem.get_text(separator=" ", strip=True)
            elif platform_name == 'vendor':
                # Targeted specifically to avoid picking up the text inside the "20ml / 30ml" buttons
                price_elem = soup.select_one('.price__sale .price-item--sale') or soup.select_one('.price-item--sale') or soup.select_one('.product-single__price') or soup.select_one('.price')
                if price_elem: raw_price = price_elem.get_text(separator=" ", strip=True)

            # We only use the dangerous regex fallback if the CSS completely fails
            if not raw_price:
                match = re.search(r'"(?:price|mrp|discountedPrice)"\s*:\s*"?(\d+(?:\.\d+)?)"?', html, re.IGNORECASE)
                if match: raw_price = match.group(1)

            return self.clean_price(raw_price)

        except Exception:
            return None
        
    def scrape_with_browser(self, driver, final_url, platform_name):
        if not final_url or "http" not in final_url: return None

        # 🚀 STRICT SEARCH PAGE BLOCKER
        if self.is_search_page(final_url, platform_name):
            self.stdout.write(self.style.WARNING(f"      ⚠️ Skipping Search Page: {platform_name.upper()}"))
            return None

        try:
            driver.get(final_url)
            time.sleep(2) 
            
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            raw_price = None

            # 🚀 Use get_text(separator=" ") to prevent HTML tags from smooshing numbers
            if platform_name == 'amazon':
                price_elem = soup.select_one('.a-price-whole')
                if price_elem: raw_price = price_elem.get_text(separator=" ", strip=True)
            elif platform_name == 'flipkart':
                price_elem = soup.select_one('.Nx9bqj') or soup.select_one('._30jeq3') or soup.select_one('div.Nx9bqj.Crvsdt')
                if price_elem: raw_price = price_elem.get_text(separator=" ", strip=True)
            elif platform_name == 'myntra':
                price_elem = soup.select_one('.pdp-price') or soup.select_one('span.pdp-price') or soup.select_one('strong')
                if price_elem: raw_price = price_elem.get_text(separator=" ", strip=True)
            elif platform_name == 'vendor':
                price_elem = soup.select_one('.price-item--sale') or soup.select_one('.price-item--regular') or soup.select_one('.price')
                if price_elem: raw_price = price_elem.get_text(separator=" ", strip=True)

            if not raw_price:
                match = re.search(r'"(?:price|mrp|discountedPrice)"\s*:\s*"?(\d+(?:\.\d+)?)"?', html, re.IGNORECASE)
                if match: raw_price = match.group(1)

            return self.clean_price(raw_price)

        except Exception:
            return None

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("🚀 Firing up SAFE MODE Scraper..."))
        start_time = time.time()

        # 🚀 Only grabs products that are currently marked as active!
        products = list(Product.objects.filter(is_active=True).order_by('-id'))[10:20]
        
        if not products:
            self.stdout.write("No products found.")
            return

        driver = self.setup_driver()
        req_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36",
        }

        try:
            for product in products:
                self.stdout.write(f"\n🔄 Scanning: {product.name[:40]}...") 
                updates = []
                has_changed = False

                for platform, link_field, price_field in [
                    ('amazon', 'amazon_link', 'amazon_price'),
                    ('flipkart', 'flipkart_link', 'flipkart_price'),
                    ('myntra', 'myntra_link', 'myntra_price'),
                    ('vendor', 'vendor_link', 'vendor_price')
                ]:
                    url = getattr(product, link_field)
                    if url:
                        final_url = self.resolve_deep_link(url, req_headers)
                        new_price = self.scrape_with_browser(driver, final_url, platform)
                        
                        current_price = getattr(product, price_field)
                        if new_price and str(new_price) != str(current_price):
                            setattr(product, price_field, new_price)
                            has_changed = True
                            updates.append(f"{platform.title()}: ₹{new_price}")

                if has_changed:
                    product.save()
                    self.stdout.write(self.style.SUCCESS(f"  ✅ Updated! [{', '.join(updates)}]"))
                else:
                    self.stdout.write(f"  ➖ (No changes)")
                
                time.sleep(3) 

        finally:
            driver.quit()

        elapsed = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f"\n🏁 Finished updating batch in {elapsed:.2f} seconds!"))
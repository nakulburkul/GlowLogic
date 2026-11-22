import time
import requests
import re
import os
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.conf import settings
from shop.models import Product

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

class Command(BaseCommand):
    help = 'Scraper with Smart Image Fixer, Vendor Summary, and Missing Image Audit.'

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
        url_lower = url.lower()
        if platform_name == 'amazon' and ('/s?k=' in url_lower or '/s?' in url_lower): return True
        if platform_name == 'flipkart' and '/search?' in url_lower: return True
        if platform_name == 'myntra' and any(bad in url_lower for bad in ['/search', 'rawquery=', '/shop/', 'myntra.com/brand/']): return True
        if platform_name == 'vendor' and ('/search' in url_lower or '/collections/' in url_lower): return True
        return False

    def clean_price(self, raw_text):
        if not raw_text: return None
        text = str(raw_text).replace(',', '')
        text = re.sub(r'\d+\s*(?:ml|g|gm|kg|oz|%)\b', '', text, flags=re.IGNORECASE)
        numbers = re.findall(r'\d+(?:\.\d+)?', text)
        
        if numbers:
            valid_prices = [float(n) for n in numbers if float(n) > 10]
            if valid_prices:
                price = min(valid_prices)
                if price > 10000: price = price / 100.0
                return price
        return None

    def scrape_with_browser(self, driver, final_url, platform_name):
        if not final_url or "http" not in final_url: return None
        if self.is_search_page(final_url, platform_name): return None

        try:
            driver.get(final_url)
            time.sleep(2) 
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            raw_price = None

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
                price_elem = soup.select_one('.price__sale .price-item--sale') or soup.select_one('.price-item--sale') or soup.select_one('.product-single__price') or soup.select_one('.price')
                if price_elem: raw_price = price_elem.get_text(separator=" ", strip=True)

            if not raw_price:
                match = re.search(r'"(?:price|mrp|discountedPrice)"\s*:\s*"?(\d+(?:\.\d+)?)"?', html, re.IGNORECASE)
                if match: raw_price = match.group(1)

            return self.clean_price(raw_price)
        except Exception:
            return None

    def fix_image_path(self, product):
        """Scans local folders and returns (Success_Boolean, Target_Filename)"""
        media_folder = os.path.join(settings.BASE_DIR, 'product_images')
        static_folder = os.path.join(settings.BASE_DIR, 'static', 'images')
        
        possible_paths = [
            str(product.image) if product.image else "",
            str(getattr(product, 'image_filename', '')),
            str(getattr(product, 'local_image_filename', ''))
        ]
        
        target_filename = "NONE"
        
        for messy_path in possible_paths:
            if not messy_path: continue
            
            clean_filename = os.path.basename(messy_path.replace('\\', '/'))
            target_filename = clean_filename
            
            if os.path.exists(os.path.join(media_folder, clean_filename)) or os.path.exists(os.path.join(static_folder, clean_filename)):
                product.image = clean_filename
                return True, clean_filename
                
        return False, target_filename

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("🚀 Firing up SAFE MODE Scraper..."))
        start_time = time.time()

        self.stdout.write("  🔍 Fetching products from the database...")
        products = list(Product.objects.filter(is_active=True).order_by('-id'))[61:101]
        
        if not products:
            self.stdout.write(self.style.ERROR("  ❌ No active products found."))
            return
            
        self.stdout.write(self.style.SUCCESS(f"  📦 Found {len(products)} products to scan."))
        self.stdout.write("  ⏳ Booting up Headless Chrome (Checking WebDriver... this may take 15 seconds)...")

        driver = self.setup_driver()
        self.stdout.write(self.style.SUCCESS("  ✅ Chrome Driver successfully started! Beginning scan..."))
        
        req_headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/122.0.0.0 Safari/537.36"}
        
        # Tracking lists for our end-of-script summaries
        updated_vendor_links = []
        missing_images = []

        try:
            for product in products:
                self.stdout.write(f"\n🔄 Scanning: {product.name[:40]}...") 
                updates = []
                has_changed = False

                # --- 1. IMAGE FIXER & AUDIT ---
                image_fixed, clean_name = self.fix_image_path(product)
                if image_fixed:
                    if str(product.image) != clean_name:
                        has_changed = True
                        updates.append("🖼️ Image Path Cleaned")
                else:
                    # Log it for the summary report
                    missing_images.append(f"ID {product.id:<4} | {product.name[:35]:<35} | Missing: {clean_name}")

                # --- 2. PRICE SCRAPER ---
                for platform, link_field, price_field in [
                    ('amazon', 'amazon_link', 'amazon_price'),
                    ('flipkart', 'flipkart_link', 'flipkart_price'),
                    ('myntra', 'myntra_link', 'myntra_price'),
                    ('vendor', 'vendor_link', 'vendor_price')
                ]:
                    url = getattr(product, link_field)
                    if url:
                        self.stdout.write(f"      ➔ Checking {platform.title()}...")
                        final_url = self.resolve_deep_link(url, req_headers)
                        new_price = self.scrape_with_browser(driver, final_url, platform)
                        
                        current_price = getattr(product, price_field)
                        if new_price and str(new_price) != str(current_price):
                            setattr(product, price_field, new_price)
                            has_changed = True
                            updates.append(f"{platform.title()}: ₹{new_price}")
                            
                            if platform == 'vendor':
                                updated_vendor_links.append({"id": product.id, "link": final_url})

                # --- 3. SAVE ---
                if has_changed:
                    product.save()
                    self.stdout.write(self.style.SUCCESS(f"  ✅ Updated! [{', '.join(updates)}]"))
                else:
                    self.stdout.write("  ➖ (No changes)")
                
                time.sleep(3) 

        finally:
            self.stdout.write("\n  🧹 Closing Chrome browser...")
            driver.quit()

        # --- 4. PRINT VENDOR SUMMARY ---
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.WARNING("📋 SUMMARY: UPDATED VENDOR LINKS"))
        self.stdout.write("="*80)
        if updated_vendor_links:
            for item in updated_vendor_links:
                self.stdout.write(self.style.SUCCESS(f"ID {item['id']}: {item['link']}"))
        else:
            self.stdout.write("No vendor links were updated during this run.")
            
        # --- 5. PRINT MISSING IMAGE AUDIT ---
        self.stdout.write("\n" + "="*80)
        self.stdout.write(self.style.ERROR("🚨 AUDIT: MISSING PHYSICAL IMAGES"))
        self.stdout.write("="*80)
        if missing_images:
            for item in missing_images:
                self.stdout.write(item)
            self.stdout.write("-" * 80)
            self.stdout.write(self.style.ERROR(f"Total missing: {len(missing_images)} products."))
            self.stdout.write("Action: Download these exact filenames and put them in 'product_images/'")
        else:
            self.stdout.write(self.style.SUCCESS("✅ All scanned products have perfect, working images!"))
        self.stdout.write("="*80 + "\n")

        elapsed = time.time() - start_time
        self.stdout.write(self.style.SUCCESS(f"🏁 Finished updating batch in {elapsed:.2f} seconds!"))
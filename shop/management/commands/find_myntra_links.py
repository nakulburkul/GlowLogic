from django.core.management.base import BaseCommand
from shop.models import Product
import time
import random
import re
from urllib.parse import quote_plus
from playwright.sync_api import sync_playwright

def get_smart_query(name):
    """Cleans the product name for a perfect search query."""
    clean_name = re.sub(r'\(.*?\)', '', name)
    for delimiter in ['|', ' - ', ':', '[']:
        clean_name = clean_name.split(delimiter)[0]
    
    words = [w for w in clean_name.split() if len(w) > 2]
    return " ".join(words[:4]) 

class Command(BaseCommand):
    help = 'The Final Boss: Playwright Headless Browser Myntra Scraper.'

    def handle(self, *args, **kwargs):
        products = Product.objects.all()
        protected_domains = ['myntr.it', 'ekaro.in', 'bitli.in', 'fktr.in']
        
        tasks = []
        for p in products:
            link = p.myntra_link or ""
            if any(domain in link for domain in protected_domains): 
                continue
            tasks.append(p)

        if not tasks:
            self.stdout.write(self.style.SUCCESS("\n✅ No valid Myntra links to process."))
            return

        # 🚀 BATCH SIZE: 50 at a time. 
        tasks = tasks[:50]

        self.stdout.write(self.style.SUCCESS(f"\n🚀 Launching PLAYWRIGHT ENGINE for {len(tasks)} products...\n"))

        # 🚀 THE MAGIC: Booting up a literal browser in the background
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True) # headless=True means it hides the window
            
            # Create a context that perfectly mimics a real human's desktop Chrome
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080},
                java_script_enabled=True # 🚀 This solves the Akamai math challenges!
            )
            page = context.new_page()

            for product in tasks:
                search_query = get_smart_query(product.name)
                url = f"https://www.myntra.com/search?q={quote_plus(search_query)}"
                short_words = [w.lower() for w in search_query.split() if len(w) > 2]

                try:
                    # Human scrolling delay
                    time.sleep(random.uniform(2.5, 4.5))
                    
                    # Navigate to Myntra and wait for the page to visually render
                    page.goto(url, wait_until='domcontentloaded', timeout=20000)
                    
                    # Double-check if we hit a hard CAPTCHA wall
                    if 'Access Denied' in page.title() or 'captcha' in page.content().lower():
                        self.stdout.write(self.style.ERROR(f"🚫 CAPTCHA HIT: {product.name} (Change Hotspot IP!)"))
                        continue

                    # 🚀 Force the browser's JavaScript to grab every single link on the page
                    hrefs = page.eval_on_selector_all('a', 'elements => elements.map(e => e.href)')
                    
                    exact_url = None
                    for href in hrefs:
                        href_lower = href.lower()
                        if any(junk in href_lower for junk in ['login', 'cart', 'profile', 'contact', 'search?']):
                            continue
                        
                        title_slug = href_lower.replace('-', ' ').replace('/', ' ').split('?')[0]
                        match_count = sum(1 for word in short_words if word in title_slug)
                        match_ratio = match_count / len(short_words) if short_words else 0
                        
                        # Verify the URL structure and match ratio
                        if 'myntra.com' in href_lower and re.search(r'[0-9]{5,9}', href_lower) and match_ratio >= 0.35:
                            exact_url = href.split('?')[0]
                            break 

                    if exact_url:
                        product.myntra_link = exact_url
                        product.save()
                        self.stdout.write(self.style.SUCCESS(f"✅ Exact Match: {product.name}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"⚠️ No Match Found: {product.name}"))

                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"⏳ Timeout on: {product.name} (Skipping)"))

            # Clean up the browser when the batch is done
            browser.close()
            self.stdout.write(self.style.SUCCESS('\n🏁 Playwright Batch complete! Wait 2 minutes before the next 50.'))
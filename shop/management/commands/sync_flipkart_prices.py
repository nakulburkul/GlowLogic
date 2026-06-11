import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from shop.models import Product
import re
import time
import random
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------------------------------------
# THE STEALTH SESSION BUILDER
# ---------------------------------------------------------
def get_stealth_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1.0, status_forcelist=[403, 429, 500, 502, 503])
    adapter = HTTPAdapter(max_retries=retry, pool_connections=10, pool_maxsize=10)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

# ---------------------------------------------------------
# THE FLIPKART MICRO-TASK
# ---------------------------------------------------------
def fetch_flipkart_price(task):
    product_id, name, url = task
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Connection': 'keep-alive',
        'X-Forwarded-For': f"{random.randint(10,250)}.{random.randint(10,250)}.{random.randint(10,250)}.{random.randint(10,250)}"
    }

    session = get_stealth_session()
    result = {'id': product_id, 'name': name, 'price': None, 'mrp': None, 'blocked': False}

    def extract_price(text):
        if not text: return None
        clean = re.sub(r'[^\d.]', '', str(text).strip())
        if clean.endswith('.'): clean = clean[:-1]
        return clean if clean else None

    try:
        # Throttle to prevent instant bans
        time.sleep(random.uniform(0.8, 2.0))
        
        res = session.get(url, headers=headers, timeout=10, allow_redirects=True)
        
        # Detect if we got served a CAPTCHA page instead of a product page
        if res.status_code in [403, 429] or 'captcha' in res.url.lower() or 'Verify you are human' in res.text:
            result['blocked'] = True
            return result

        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')

        # JSON-LD Backend Database Extraction (Immune to UI changes)
        schema = soup.find('script', id='jsonLD')
        if schema and schema.string:
            price_match = re.search(r'"price":\s*"?(\d+(\.\d+)?)"?', schema.string)
            if price_match:
                result['price'] = price_match.group(1)

        # Fallback to SEO Meta Tags
        if not result['price']:
            meta_price = soup.select_one('meta[itemprop="price"]')
            if meta_price and meta_price.get('content'):
                result['price'] = extract_price(meta_price['content'])

        # Fallback to Standard UI
        if not result['price']:
            p_elem = soup.select_one('.Nx9bqj.C-vnqG, div._30jeq3._16Jk6d, ._1vC4OE, .hl05eU')
            if p_elem: result['price'] = extract_price(p_elem.text)
        
        # Original MRP Extraction
        m_elem = soup.select_one('.yRaY8j.A6EBE2, div._3I9_wc._2p6lqe, ._2p6lqe')
        if m_elem: result['mrp'] = extract_price(m_elem.text)
        
        # Genuine Out of Stock Check
        sold_out = soup.select_one('._1kVtvW, .sold-out, ._36yEn5, button.FFs-b-')
        if sold_out and ('out of stock' in sold_out.text.lower() or 'sold out' in sold_out.text.lower()):
            result['price'] = None

    except Exception:
        pass 

    return result

# ---------------------------------------------------------
# THE MAIN COMMAND
# ---------------------------------------------------------
class Command(BaseCommand):
    help = 'Googlebot-Spoofed Scraper with REAL-TIME Database Saving.'

    def handle(self, *args, **kwargs):
        products = list(Product.objects.all())
        product_dict = {p.id: p for p in products}
        
        tasks = []
        for p in products:
            if p.flipkart_link:
                tasks.append((p.id, p.name, p.flipkart_link))

        self.stdout.write(self.style.SUCCESS(f"\n🚀 Launching Real-Time Flipkart Sync for {len(tasks)} products...\n"))

        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = {executor.submit(fetch_flipkart_price, task): task for task in tasks}
            
            for future in as_completed(futures):
                data = future.result()
                pid = data['id']
                p = product_dict[pid]
                needs_update = False
                
                # Check for silent CAPTCHA blocks
                if data.get('blocked'):
                    self.stdout.write(self.style.ERROR(f"❌ BLOCKED BY CAPTCHA: {data['name']}"))
                    continue

                if data['price'] or data['mrp']:
                    self.stdout.write(f"✅ Extracted: {data['name']}")

                # 1. Update Flipkart Price
                if data['price'] and p.flipkart_price != data['price']:
                    p.flipkart_price = data['price']
                    needs_update = True
                    self.stdout.write(self.style.SUCCESS(f"   ↳ Live Price updated: ₹{data['price']}"))

                # 2. Check and Apply Genuine MRP
                if data['mrp'] and p.lowest_price:
                    try:
                        if float(data['mrp']) > float(p.lowest_price) and p.mrp != data['mrp']:
                            p.mrp = data['mrp']
                            needs_update = True
                            self.stdout.write(self.style.WARNING(f"   ↳ Genuine MRP applied: ₹{data['mrp']}"))
                    except ValueError:
                        pass

                # 🚀 THE FIX: REAL-TIME SAVING
                if needs_update:
                    p.save() # Saves to the database instantly!
                    self.stdout.write(self.style.SUCCESS(f"   💾 Saved to database instantly!"))

        self.stdout.write(self.style.SUCCESS('\n🏁 Flipkart Sync Complete!'))
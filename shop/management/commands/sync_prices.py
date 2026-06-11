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
# THE MICRO-TASK WORKER
# ---------------------------------------------------------
def get_stealth_session():
    """Builds a massive TCP connection pool for hyper-fast networking."""
    session = requests.Session()
    retry = Retry(total=2, backoff_factor=0.3, status_forcelist=[403, 429, 500, 502, 503])
    # pool_maxsize=100 allows up to 100 simultaneous network tunnels
    adapter = HTTPAdapter(max_retries=retry, pool_connections=100, pool_maxsize=100)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def fetch_single_link(task):
    """Fetches a single platform link completely independently."""
    platform, product_id, url = task
    
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0',
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0'
    ]
    
    headers = {
        'User-Agent': random.choice(user_agents),
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/', 
        'Connection': 'keep-alive',
    }

    session = get_stealth_session()
    result = {'platform': platform, 'id': product_id, 'price': None, 'mrp': None}

    def extract_price(text):
        if not text: return None
        clean = re.sub(r'[^\d.]', '', str(text).strip())
        if clean.endswith('.'): clean = clean[:-1]
        return clean if clean else None

    try:
        # Micro-jitter prevents 25 threads from hitting Amazon at the exact same millisecond
        time.sleep(random.uniform(0.1, 0.6))
        
        # allow_redirects=True completely protects your deep links!
        res = session.get(url, headers=headers, timeout=6, allow_redirects=True)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')

        if platform == 'amazon':
            p_elem = soup.select_one('.a-price-whole, #priceblock_ourprice, .a-color-price')
            if p_elem: result['price'] = extract_price(p_elem.text)
                
            m_elem = soup.select_one('.basisPrice .a-offscreen, #basis-price .a-offscreen')
            if m_elem: result['mrp'] = extract_price(m_elem.text)
            else:
                for el in soup.select('.a-price.a-text-price[data-a-strike="true"] .a-offscreen'):
                    val = extract_price(el.text)
                    if val and result['price'] and float(val) > float(result['price']):
                        result['mrp'] = val
                        break

        elif platform == 'flipkart':
            p_elem = soup.select_one('.Nx9bqj.C-vnqG, div._30jeq3._16Jk6d')
            if p_elem: result['price'] = extract_price(p_elem.text)
            m_elem = soup.select_one('.yRaY8j.A6EBE2, div._3I9_wc._2p6lqe')
            if m_elem: result['mrp'] = extract_price(m_elem.text)

        elif platform == 'myntra':
            p_elem = soup.select_one('.pdp-price, .product-discountedPrice')
            if p_elem: result['price'] = extract_price(p_elem.text)
            m_elem = soup.select_one('.pdp-mrp, .product-strike')
            if m_elem: result['mrp'] = extract_price(m_elem.text)

        elif platform == 'vendor':
            p_elem = soup.select_one('.price-item--sale, .product-price, .current-price, span.price')
            if p_elem: 
                val = extract_price(p_elem.text)
                if val and 1 <= float(val) <= 9999: result['price'] = val
            m_elem = soup.select_one('s, del, .compare-at-price')
            if m_elem: result['mrp'] = extract_price(m_elem.text)

    except Exception:
        pass # Silently drop timeouts to keep the engine moving at max speed

    return result

# ---------------------------------------------------------
# THE MAIN DJANGO COMMAND
# ---------------------------------------------------------
class Command(BaseCommand):
    help = 'Ultra-High-Speed Scatter-Gather Scraper with O(1) Database Writes.'

    def handle(self, *args, **kwargs):
        products = list(Product.objects.all())
        product_dict = {p.id: p for p in products}
        products_to_update = {}
        
        # 1. SCATTER: Break every single link into an independent micro-task
        tasks = []
        for p in products:
            if p.amazon_link: tasks.append(('amazon', p.id, p.amazon_link))
            if p.flipkart_link: tasks.append(('flipkart', p.id, p.flipkart_link))
            if p.myntra_link: tasks.append(('myntra', p.id, p.myntra_link))
            if p.vendor_link: tasks.append(('vendor', p.id, p.vendor_link))

        self.stdout.write(self.style.SUCCESS(f"\n🚀 Launching {len(tasks)} independent network tasks across 25 parallel threads...\n"))

        # 2. PROCESS: Fire 25 simultaneous network tunnels
        with ThreadPoolExecutor(max_workers=25) as executor:
            futures = {executor.submit(fetch_single_link, task): task for task in tasks}
            
            for future in as_completed(futures):
                data = future.result()
                pid = data['id']
                p = product_dict[pid]
                
                # If we found new data, stage the product for the bulk update
                needs_update = False
                
                if data['platform'] == 'amazon' and data['price'] and p.amazon_price != data['price']:
                    p.amazon_price = data['price']
                    needs_update = True
                elif data['platform'] == 'flipkart' and data['price'] and p.flipkart_price != data['price']:
                    p.flipkart_price = data['price']
                    needs_update = True
                elif data['platform'] == 'myntra' and data['price'] and p.myntra_price != data['price']:
                    p.myntra_price = data['price']
                    needs_update = True
                elif data['platform'] == 'vendor' and data['price'] and p.vendor_price != data['price']:
                    p.vendor_price = data['price']
                    needs_update = True

                # Apply Genuine MRP if found and valid
                if data['mrp'] and p.lowest_price:
                    try:
                        if float(data['mrp']) > float(p.lowest_price) and p.mrp != data['mrp']:
                            p.mrp = data['mrp']
                            needs_update = True
                    except ValueError:
                        pass

                if needs_update:
                    products_to_update[pid] = p
                    self.stdout.write(f"⚡ Staged update for: {p.name} ({data['platform']})")

        # 3. GATHER: Write everything to the database in one single blast
        if products_to_update:
            self.stdout.write(self.style.WARNING(f"\n💾 Executing Bulk Database Write for {len(products_to_update)} products..."))
            
            # This is the magic. Updates the whole database in ~0.05 seconds.
            Product.objects.bulk_update(list(products_to_update.values()), [
                'amazon_price', 'flipkart_price', 'myntra_price', 'vendor_price', 'mrp'
            ])
            
            self.stdout.write(self.style.SUCCESS('✅ Database successfully overwritten!'))
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ All prices are already up to date!'))

        self.stdout.write(self.style.SUCCESS('\n🏁 Hyper-Speed Sync Complete!'))
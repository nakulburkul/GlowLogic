import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from shop.models import Product
import time
import random
import re
from urllib.parse import quote_plus, urlparse, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed

def get_stealth_session():
    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1.0, status_forcelist=[403, 429, 500, 502, 503])
    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    return session

def get_smart_query(name):
    """
    Strips out SEO fluff (e.g. '| Removes Impurities | For Men') 
    so Flipkart's search engine doesn't get confused.
    """
    clean_name = name
    # Cut off anything after these common SEO separators
    for delimiter in ['|', ' - ', ':', '(', '[']:
        clean_name = clean_name.split(delimiter)[0]
    
    clean_name = clean_name.strip()
    
    # If the name is STILL insanely long, just take the first 7 words
    words = clean_name.split()
    if len(words) > 7:
        clean_name = " ".join(words[:7])
        
    return clean_name

def fetch_flipkart_search(task):
    product_id, original_name = task
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/', 
    }

    session = get_stealth_session()
    result = {'id': product_id, 'name': original_name, 'exact_url': None}
    
    # 🚀 FIX: Use the smart, shortened query for the search
    search_query = get_smart_query(original_name)
    search_url = f"https://www.flipkart.com/search?q={quote_plus(search_query)}"

    # 🚀 VALIDATION: Still extract the size from the FULL original name
    size_match = re.search(r'(\d+\s*(?:ml|g|oz|kg|l))', original_name, re.IGNORECASE)
    expected_size = size_match.group(1).lower().replace(" ", "") if size_match else None
    
    # Core words to check (from the short query)
    short_words = [w for w in search_query.lower().split() if len(w) > 2]

    try:
        time.sleep(random.uniform(0.5, 2.0))
        res = session.get(search_url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')

        links = soup.find_all('a', href=True)
        
        for a in links:
            href = a['href']
            if '/p/' in href and 'pid=' in href:
                title = ""
                img = a.find('img')
                if img and img.get('alt'):
                    title = img['alt'].lower()
                else:
                    title = a.text.lower()
                    
                if len(title) < 5:
                    title = href.split('/')[1].replace('-', ' ').lower()

                # 🛑 STRICT CHECK 1: Size Match
                if expected_size and expected_size not in title.replace(" ", ""):
                    continue 
                
                # 🛑 STRICT CHECK 2: Brand/Name Match
                # Uses the short words (e.g., "chemist", "at", "play", "brightening", "body", "wash")
                match_count = sum(1 for word in short_words if word in title)
                match_ratio = match_count / len(short_words) if short_words else 0
                
                # Lowered the threshold slightly to 55% to account for weird Flipkart abbreviations
                if match_ratio >= 0.55:
                    parsed = urlparse(href)
                    qs = parse_qs(parsed.query)
                    if 'pid' in qs:
                        pid = qs['pid'][0]
                        result['exact_url'] = f"https://www.flipkart.com{parsed.path}?pid={pid}"
                        break 

    except Exception:
        pass 

    return result

class Command(BaseCommand):
    help = 'Smart Flipkart Link Finder (Bypasses SEO Stuffing).'

    def handle(self, *args, **kwargs):
        products = Product.objects.all()
        protected_domains = ['fktr.in', 'ekaro.in', 'bitli.in', 'myntr.it']
        
        tasks = []
        for p in products:
            link = p.flipkart_link or ""
            
            if any(domain in link for domain in protected_domains): 
                continue
            
            tasks.append((p.id, p.name))

        if not tasks:
            self.stdout.write(self.style.SUCCESS("\n✅ No valid links to process."))
            return

        self.stdout.write(self.style.SUCCESS(f"\n🚀 Launching Smart Flipkart Finder for {len(tasks)} products...\n"))

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_flipkart_search, task): task for task in tasks}
            
            for future in as_completed(futures):
                data = future.result()
                if data['exact_url']:
                    try:
                        p = Product.objects.get(id=data['id'])
                        p.flipkart_link = data['exact_url']
                        p.save() 
                        self.stdout.write(self.style.SUCCESS(f"✅ Exact Match Applied: {data['name']}"))
                    except Exception: pass
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️ No Match Found (Left alone): {data['name']}"))

        self.stdout.write(self.style.SUCCESS('\n🏁 Mass Flipkart Linking complete!'))
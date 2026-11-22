import time
import re
import json
import cloudscraper
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from shop.models import Product

class Command(BaseCommand):
    help = 'ULTIMATE Image Scraper - Cloudscraper + SEO Data Hijacker'

    def resolve_deep_link(self, url):
        """Unrolls affiliate shortlinks using Cloudscraper to bypass security checks."""
        if not url: return url
        try:
            scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
            response = scraper.get(url, timeout=10, allow_redirects=True)
            
            if any(short in response.url for short in ["fktr.in", "myntr.it", "ekaro.in", "bit.ly", "bitli.in"]):
                soup = BeautifulSoup(response.content, 'html.parser')
                meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
                if meta_refresh and 'url=' in meta_refresh.get('content', '').lower():
                    next_url = meta_refresh['content'].split('url=')[-1].strip("'\" ")
                    response = scraper.get(next_url, timeout=10, allow_redirects=True)
            return response.url
        except Exception:
            return url

    def extract_from_json_ld(self, soup):
        """Hijacks the SEO data websites prepare for Google to find the perfect image."""
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                # Sometimes script tags are empty or badly formatted
                if not script.string: continue
                
                data = json.loads(script.string)
                
                # Helper function to dig out the image URL from the JSON mess
                def get_img(obj):
                    if isinstance(obj, dict) and obj.get('@type') == 'Product' and 'image' in obj:
                        img_data = obj['image']
                        if isinstance(img_data, str): return img_data
                        elif isinstance(img_data, list) and len(img_data) > 0: 
                            return img_data[0] if isinstance(img_data[0], str) else img_data[0].get('url')
                        elif isinstance(img_data, dict): return img_data.get('url')
                    return None

                # JSON-LD can be a list of items or a single dictionary
                if isinstance(data, list):
                    for item in data:
                        if img := get_img(item): return img
                elif isinstance(data, dict):
                    if '@graph' in data: # Common in Yoast SEO
                        for item in data['@graph']:
                            if img := get_img(item): return img
                    else:
                        if img := get_img(data): return img
            except Exception:
                continue
        return None

    def fetch_image_url(self, final_url, platform):
        if not final_url or "http" not in final_url: return None

        try:
            scraper = cloudscraper.create_scraper(browser={'browser': 'chrome', 'platform': 'windows', 'desktop': True})
            response = scraper.get(final_url, timeout=15)
            
            # If the site outright blocks us (403 Forbidden), return None
            if response.status_code != 200: return None
            
            html_text = response.text
            soup = BeautifulSoup(html_text, 'html.parser')

            # ---------------------------------------------------------
            # 1. THE NEW SEO HIJACKER (Works brilliantly for Vendor links)
            # ---------------------------------------------------------
            seo_image = self.extract_from_json_ld(soup)
            if seo_image and "http" in seo_image:
                # Make sure it's not a tiny thumbnail or logo
                bad_seo = ["logo", "avatar", "50x50", "placeholder"]
                if not any(bad in seo_image.lower() for bad in bad_seo):
                    return seo_image

            # ---------------------------------------------------------
            # 2. X-RAY EXTRACTION LOGIC (For Amazon/Flipkart/Myntra)
            # ---------------------------------------------------------
            if platform == 'amazon':
                match = re.search(r'"large":"(https://m\.media-amazon\.com/images/I/[^"]+)"', html_text)
                if match: return match.group(1)
                
            elif platform == 'flipkart':
                matches = re.findall(r'(https://rukminim[^"\'\)]+)', html_text)
                for img in matches:
                    if 'logo' not in img.lower() and 'q=' in img:
                        return re.sub(r'/[0-9]+/[0-9]+/', '/832/832/', img)
                        
            elif platform == 'myntra':
                match = re.search(r'"imageURL":"([^"]+)"', html_text)
                if match: return match.group(1)

            elif platform == 'vendor':
                vendor_img = soup.select_one('.product-image img, .product-featured-media, #ProductPhotoImg, .product__media img, .product-single__photo')
                if vendor_img:
                    img_src = vendor_img.get('data-src') or vendor_img.get('src')
                    if img_src:
                        return f"https:{img_src}" if img_src.startswith('//') else img_src

            # ---------------------------------------------------------
            # 3. FALLBACK: Safe Open Graph Meta Tags
            # ---------------------------------------------------------
            if og_image := soup.find('meta', property='og:image'):
                if img_url := og_image.get('content'):
                    bad_strings = ["50_.jpg", "SR38,50", "ckassets", "flipkart-direct", "amazon_logo", "myntra_logo", "default", "icon"]
                    if not any(bad in img_url.lower() for bad in bad_strings):
                        return img_url

        except Exception:
            return None
            
        return None

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("⚡ Firing up the SEO Hijacker Scraper..."))
        start_time = time.time()

        products = Product.objects.filter(is_active=True).order_by('-id')
        missing_image_products = [
            p for p in products 
            if not p.image_url or 'ckassets' in p.image_url or 'flipkart-direct' in p.image_url
        ]
        
        if not missing_image_products:
            self.stdout.write(self.style.SUCCESS("✅ All products have valid image URLs!"))
            return

        self.stdout.write(self.style.ERROR(f"🚨 Found {len(missing_image_products)} products needing images. Fetching..."))

        priority_queue = [
            ('vendor', 'vendor_link'),   # Moved Vendor to the TOP because SEO extraction is highly reliable!
            ('amazon', 'amazon_link'),
            ('flipkart', 'flipkart_link'),
            ('myntra', 'myntra_link')
        ]

        success_count = 0

        for product in missing_image_products:
            self.stdout.write(f"\n🔄 Scraping: {product.name[:35]}...")
            downloaded = False

            for platform, link_field in priority_queue:
                url = getattr(product, link_field)
                if url and url != 'None':
                    self.stdout.write(f"      ➔ Scanning {platform.title()}...")
                    
                    final_url = self.resolve_deep_link(url)
                    img_url = self.fetch_image_url(final_url, platform)
                    
                    if img_url and img_url.startswith('http'):
                        product.image_url = img_url
                        product.save()
                        
                        self.stdout.write(self.style.SUCCESS(f"      ✅ Success! Saved High-Res Link from {platform.title()}."))
                        success_count += 1
                        downloaded = True
                        break 
                        
            if not downloaded:
                self.stdout.write(self.style.ERROR(f"      ❌ Failed. Websites are blocking the bot for this item."))

            time.sleep(2) # Adjusted to 2 seconds

        elapsed = time.time() - start_time
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"🏁 Finished! Linked {success_count} images in {elapsed:.2f} seconds."))
        self.stdout.write("="*50 + "\n")
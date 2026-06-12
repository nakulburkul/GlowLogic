import time
import requests
import re
import os
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.text import slugify
from shop.models import Product

class Command(BaseCommand):
    help = 'LIGHTNING FAST Image Scraper based on Priority Queue (Amazon > Flipkart > Myntra > Vendor)'

    def resolve_deep_link(self, url, headers):
        """Quickly unrolls affiliate shortlinks to get the real URL."""
        if not url: return url
        try:
            session = requests.Session()
            response = session.get(url, headers=headers, timeout=5, allow_redirects=True)
            if any(short in response.url for short in ["fktr.in", "myntr.it", "ekaro.in", "bit.ly", "bitli.in"]):
                soup = BeautifulSoup(response.content, 'html.parser')
                meta_refresh = soup.find('meta', attrs={'http-equiv': 'refresh'})
                if meta_refresh and 'url=' in meta_refresh.get('content', '').lower():
                    next_url = meta_refresh['content'].split('url=')[-1].strip("'\" ")
                    response = session.get(next_url, headers=headers, timeout=5, allow_redirects=True)
            return response.url
        except Exception:
            return url

    def is_image_missing(self, product):
        """Checks if the physical file is missing from your hard drive."""
        media_folder = os.path.join(settings.BASE_DIR, 'product_images')
        static_folder = os.path.join(settings.BASE_DIR, 'static', 'images')
        
        possible_paths = [str(product.image) if product.image else ""]
        
        for messy_path in possible_paths:
            if not messy_path: continue
            clean_filename = os.path.basename(messy_path.replace('\\', '/'))
            if os.path.exists(os.path.join(media_folder, clean_filename)) or os.path.exists(os.path.join(static_folder, clean_filename)):
                return False # Image exists!
        return True # Image is missing

    def fetch_image_url(self, final_url, platform):
        """Uses fast HTTP requests to rip the image URL from meta tags."""
        if not final_url or "http" not in final_url: return None

        # Anti-bot headers to trick Amazon/Flipkart into giving us the HTML
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        }

        try:
            response = requests.get(final_url, headers=headers, timeout=5)
            if response.status_code != 200: return None

            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 1. The universal fast method: Open Graph Meta Tags
            og_image = soup.find('meta', property='og:image')
            if og_image and og_image.get('content'):
                img_url = og_image['content']
                # Amazon sometimes puts a tiny 50x50 image in the OG tag. We reject those.
                if "50_.jpg" not in img_url and "SR38,50" not in img_url:
                    return img_url

            # 2. Platform specific fast fallbacks if OG tags fail
            if platform == 'amazon':
                img_elem = soup.select_one('#landingImage, #imgBlkFront')
                if img_elem: return img_elem.get('data-old-hires') or img_elem.get('src')
            elif platform == 'flipkart':
                img_elem = soup.select_one('img._396cs4, img._2r_T1I')
                if img_elem: return img_elem.get('src')
            elif platform == 'myntra':
                # Myntra puts images in a script tag sometimes
                match = re.search(r'"image"\s*:\s*"([^"]+)"', response.text)
                if match: return match.group(1)

        except Exception:
            return None
        return None

    def auto_download_image(self, product, img_url):
        """Downloads the actual file and saves it cleanly to Django."""
        if not img_url or not img_url.startswith('http'): return False
            
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(img_url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                # Creates a perfect filename with no spaces
                safe_name = slugify(product.name)[:30]
                filename = f"{product.id}_{safe_name}.jpg"
                
                # Save it
                product.image.save(filename, ContentFile(response.content), save=True)
                return True
        except Exception:
            pass
        return False

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.WARNING("⚡ Firing up LIGHTNING FAST Image Scraper..."))
        start_time = time.time()

        # Grab all active products
        products = Product.objects.filter(is_active=True).order_by('-id')
        
        # Filter down to ONLY products that are physically missing their image
        missing_image_products = [p for p in products if self.is_image_missing(p)]
        
        if not missing_image_products:
            self.stdout.write(self.style.SUCCESS("✅ All products already have perfect images! Nothing to do."))
            return

        self.stdout.write(self.style.ERROR(f"🚨 Found {len(missing_image_products)} products missing images. Beginning rapid download..."))
        
        req_headers = {"User-Agent": "Mozilla/5.0"}

        # 🚀 THE PRIORITY QUEUE
        priority_queue = [
            ('amazon', 'amazon_link'),
            ('flipkart', 'flipkart_link'),
            ('myntra', 'myntra_link'),
            ('vendor', 'vendor_link')
        ]

        success_count = 0

        for product in missing_image_products:
            self.stdout.write(f"\n🔄 Fixing: {product.name[:35]}...")
            downloaded = False

            for platform, link_field in priority_queue:
                url = getattr(product, link_field)
                if url:
                    self.stdout.write(f"      ➔ Trying {platform.title()}...")
                    final_url = self.resolve_deep_link(url, req_headers)
                    
                    # Try to grab the image URL quickly
                    img_url = self.fetch_image_url(final_url, platform)
                    
                    if img_url:
                        # If we found an image URL, download it immediately
                        if self.auto_download_image(product, img_url):
                            self.stdout.write(self.style.SUCCESS(f"      ✅ Success! Downloaded from {platform.title()}."))
                            success_count += 1
                            downloaded = True
                            break # 🚀 STOP CHECKING! Move to the next product.

            if not downloaded:
                self.stdout.write(self.style.ERROR(f"      ❌ Failed. Could not find image on any provided links."))

        elapsed = time.time() - start_time
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS(f"🏁 Finished! Fixed {success_count} images in {elapsed:.2f} seconds."))
        self.stdout.write("="*50 + "\n")
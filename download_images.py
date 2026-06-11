import os
import json
import requests
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'glowguide_web.settings')
django.setup()

from shop.models import Product

# Path to your datasets
files = [
    'dataset_Amazon-crawler_2026-04-27_08-44-47-069.json',
    'dataset_Amazon-crawler_2026-04-27_09-04-15-888.json'
]

# Ensure static/images exists
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "static", "images")
os.makedirs(IMAGE_DIR, exist_ok=True)

def download_images():
    print("📸 Starting image download process...")
    download_count = 0
    skip_count = 0
    retry_count = 0

    for filename in files:
        print(f"\n📂 Processing {filename}...")
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            print(f"❌ Could not find {filename}")
            continue

        for item in data:
            name = item.get('title') or item.get('name') or item.get('productName')
            if not name: 
                continue

            # Clean the name AND shorten it to 50 characters to prevent Windows crash
            safe_name = "".join([c for c in name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
            safe_name = safe_name[:50].strip()
            
            final_filename = f"{safe_name}.jpg"
            filepath = os.path.join(IMAGE_DIR, final_filename)

            # --- SMART SKIP & RETRY LOGIC ---
            if os.path.exists(filepath):
                file_size = os.path.getsize(filepath)
                # If the file is larger than 2KB (2048 bytes), it was a successful download. Skip it!
                if file_size > 2048: 
                    skip_count += 1
                    continue
                else:
                    # If it's less than 2KB, it's likely a broken/error file. Let's retry it.
                    print(f"🔄 Retrying broken/incomplete file for: {safe_name}...")
                    retry_count += 1

            # Find the image URL
            img_url = item.get('image') or item.get('mainImage') or item.get('imageUrl') or item.get('thumbnailImage')
            
            if not img_url and item.get('images') and len(item.get('images')) > 0:
                img_url = item.get('images')[0] 
                
            if not img_url and item.get('imageUrls') and len(item.get('imageUrls')) > 0:
                img_url = item.get('imageUrls')[0]

            if not img_url:
                continue

            # Attempt to download the image
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8'
                }
                response = requests.get(img_url, headers=headers, timeout=10)
                
                if response.status_code == 200:
                    with open(filepath, 'wb') as handler:
                        handler.write(response.content)
                    download_count += 1
                    print(f"✅ Downloaded: {safe_name}...")
                elif response.status_code == 404:
                    print(f"⚠️ 404 Not Found for: {safe_name}...")
                elif response.status_code == 403:
                    print(f"🚫 403 Forbidden for: {safe_name}...")

            except Exception as e:
                print(f"⚠️ Network error for {safe_name}: {e}")

    print("\n" + "="*40)
    print("🎉 DOWNLOAD SUMMARY 🎉")
    print("="*40)
    print(f"⏩ Skipped (Already Downloaded): {skip_count}")
    print(f"✅ Successfully Downloaded New: {download_count}")
    print(f"🔄 Retried Broken Files: {retry_count}")
    print("="*40)

if __name__ == "__main__":
    download_images()
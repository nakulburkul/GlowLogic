import os
import time
import random
import sqlite3
import requests
from ddgs import DDGS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "skincare_catalog.db")
IMAGE_DIR = os.path.join(BASE_DIR, "product_images")

def download_image(ddgs, query, filepath):
    """Helper function to download a single image."""
    if os.path.exists(filepath):
        return True # Already have it
        
    results = list(ddgs.images(query, max_results=5))
    if not results:
        return False
        
    for res in results:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
            img_response = requests.get(res['image'], headers=headers, timeout=5)
            img_response.raise_for_status() 
            
            with open(filepath, 'wb') as handler:
                handler.write(img_response.content)
            
            time.sleep(random.uniform(2.0, 4.0))
            return True
        except Exception:
            continue
    return False

def bulk_download_images():
    os.makedirs(IMAGE_DIR, exist_ok=True)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM products")
        products = cursor.fetchall()
        conn.close()
    except sqlite3.OperationalError:
        print("Database not found!")
        return

    print(f"📦 Found {len(products)} products. Checking for Main and Ad images...\n")

    for (product_name,) in products:
        safe_name = "".join([c for c in product_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        main_filepath = os.path.join(IMAGE_DIR, f"{safe_name}.jpg")
        ad_filepath = os.path.join(IMAGE_DIR, f"{safe_name}_ad.jpg") # The Ad Image file!

        with DDGS() as ddgs:
            # 1. Main Product Image (White Background)
            if not os.path.exists(main_filepath):
                print(f"🖼️ Downloading MAIN image: {product_name}")
                query = product_name + " skincare product white background"
                download_image(ddgs, query, main_filepath)
            
            # 2. Advertising / Lifestyle Image
            if not os.path.exists(ad_filepath):
                print(f"✨ Downloading AD image: {product_name}")
                query = product_name + " skincare advertisement lifestyle aesthetic"
                download_image(ddgs, query, ad_filepath)

    print("\n🎉 All missing images and advertisements have been downloaded!")

if __name__ == "__main__":
    bulk_download_images()
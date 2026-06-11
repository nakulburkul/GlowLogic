import os
import sqlite3
import urllib.request
import urllib.parse

print("⚡ Booting up GlowGuide Lightning Image Fixer...")

db_path = 'skincare_catalog.db'
images_dir = os.path.join('static', 'images')
os.makedirs(images_dir, exist_ok=True)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # We just need the names to calculate what the HTML is looking for
    cursor.execute("SELECT name FROM products WHERE name IS NOT NULL;")
    products = cursor.fetchall()
    
    generated_count = 0
    skipped_count = 0
    
    for (name,) in products:
        # EXACT logic from your models.py @property def local_image_filename
        safe_name = "".join([c for c in name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        expected_filename = f"{safe_name[:50].strip()}.jpg"
        filepath = os.path.join(images_dir, expected_filename)
        
        # FAST CHECK: Does the file already exist in static/images?
        if os.path.exists(filepath):
            skipped_count += 1
            continue # Skip immediately! This makes it insanely fast.

        # If missing, generate the pink placeholder!
        print(f"🖼️ Missing image found. Generating for: {name}")
        short_name = " ".join(name.replace("Dot & Key", "").strip().split()[:3])
        if not short_name:
            short_name = "Skincare"
            
        encoded_name = urllib.parse.quote(short_name)
        image_url = f"https://dummyimage.com/600x600/fff9fa/d81b60.jpg&text={encoded_name}"
        
        try:
            # Save it with the EXACT name your Django template expects
            urllib.request.urlretrieve(image_url, filepath)
            generated_count += 1
        except Exception as e:
            print(f"  ❌ Failed to download for {name}: {e}")

    print(f"\n🎉 Done! Generated {generated_count} missing images. Skipped {skipped_count} existing ones.")
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
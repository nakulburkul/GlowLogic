import os
import sqlite3
import urllib.request
import urllib.parse

print("🎨 Booting up GlowGuide RAW-SQL Image Generator (Smart Mode)...")

db_path = 'skincare_catalog.db'
images_dir = os.path.join('static', 'images')
os.makedirs(images_dir, exist_ok=True)

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. DATABASE CHECK: Only select products where the image column is completely blank
    cursor.execute("SELECT id, name FROM products WHERE image_filename IS NULL OR image_filename = '';")
    missing_images = cursor.fetchall()
    
    generated_count = 0
    skipped_count = 0
    
    for pid, name in missing_images:
        filename = f"generated_fix_{pid}.png"
        filepath = os.path.join(images_dir, filename)
        
        # 2. FILE SYSTEM CHECK: If the image was already generated previously, just link it and SKIP!
        if os.path.exists(filepath):
            cursor.execute("UPDATE products SET image_filename = ? WHERE id = ?", (filename, pid))
            conn.commit()
            skipped_count += 1
            print(f"  ⏭️ Skipped generating for {name} (Image already exists on disk, linked it!)")
            continue

        print(f"⏳ Generating NEW image for: {name}")
        
        # Clean the name up for the placeholder graphic
        short_name = " ".join(name.replace("Dot & Key", "").strip().split()[:3])
        if not short_name:
            short_name = "Skincare Product"
            
        encoded_name = urllib.parse.quote(short_name)
        image_url = f"https://dummyimage.com/600x600/fff9fa/d81b60.png&text={encoded_name}"
        
        try:
            # Download the new image
            urllib.request.urlretrieve(image_url, filepath)
            
            # Update the database
            cursor.execute("UPDATE products SET image_filename = ? WHERE id = ?", (filename, pid))
            conn.commit()
            generated_count += 1
            print(f"  ✅ Saved and linked as {filename}")
        except Exception as e:
            print(f"  ❌ Failed to download image for {name}: {e}")

    print(f"\n🎉 Success! Generated {generated_count} NEW images and linked {skipped_count} existing ones!")
    conn.close()

except Exception as e:
    print(f"❌ SQL Error: {e}")
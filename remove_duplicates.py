import os
import hashlib

# Path to your images
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "static", "images")

def get_file_hash(filepath):
    """Reads the file and returns a unique MD5 hash based on its byte data."""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        # Read the file in chunks to handle large files safely
        while chunk := f.read(8192):
            hasher.update(chunk)
    return hasher.hexdigest()

def clean_duplicates():
    print(f"🔍 Scanning for duplicate images in: {IMAGE_DIR}\n")
    
    if not os.path.exists(IMAGE_DIR):
        print("❌ Directory not found. Check your paths.")
        return

    seen_hashes = {}
    duplicates_deleted = 0
    bytes_saved = 0

    # Go through every file in the folder
    for filename in os.listdir(IMAGE_DIR):
        filepath = os.path.join(IMAGE_DIR, filename)
        
        # Only check files (skip any sub-folders)
        if os.path.isfile(filepath):
            file_hash = get_file_hash(filepath)
            
            # If we've already seen this exact image data...
            if file_hash in seen_hashes:
                file_size = os.path.getsize(filepath)
                bytes_saved += file_size
                
                print(f"🗑️ Deleting duplicate: {filename}")
                print(f"   -> (Identical to: {seen_hashes[file_hash]})\n")
                
                os.remove(filepath)
                duplicates_deleted += 1
            else:
                # Store the hash and the original file name so we can compare future files against it
                seen_hashes[file_hash] = filename

    # Calculate MB saved
    mb_saved = bytes_saved / (1024 * 1024)

    print("="*40)
    print("🎉 CLEANUP COMPLETE 🎉")
    print("="*40)
    print(f"✅ Unique Images Kept: {len(seen_hashes)}")
    print(f"❌ Duplicates Deleted: {duplicates_deleted}")
    print(f"💾 Storage Saved: {mb_saved:.2f} MB")
    print("="*40)

if __name__ == "__main__":
    clean_duplicates()
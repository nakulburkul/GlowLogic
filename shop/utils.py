# shop/utils.py
import re

def universal_normalize(name):
    """
    Cleans and standardizes product names for bulletproof cross-platform searching.
    (Used by older scripts and standard search queries)
    """
    if not name:
        return ""
        
    # 1. Convert to lowercase and remove special characters/symbols
    clean_name = name.lower().replace('&', 'and').replace('®', '').replace('™', '').replace('|', '')
    
    # 2. Strip out size/weight patterns (e.g., 100ml, 50g, 3.4oz, Pack of 2)
    clean_name = re.sub(r'\d+\s?(ml|g|gm|oz|kg|count|pcs|pack of \d+)', '', clean_name)
    
    # 3. Remove common search "noise" words
    noise_words = [
        'for men', 'for women', 'daily', 'best', 'dermatologist recommended', 
        'skincare', 'face serum', 'face wash', 'body wash'
    ]
    for word in noise_words:
        clean_name = clean_name.replace(word, '')
    
    # 4. Remove non-alphanumeric chars and collapse spaces
    clean_name = re.sub(r'[^a-z0-9\s]', ' ', clean_name)
    clean_name = " ".join(clean_name.split()).strip()
    
    return clean_name


def extract_size_and_normalize(name):
    """
    Splits a raw product name into a clean 'Core Name' and a 'Size Variant'.
    (Used by models.py for Size Stacking and Variant UI)
    """
    if not name:
        return "", "Standard"
        
    clean_name = name.lower()
    
    # 1. Regex to find the size (e.g., 50ml, 100 g, 3.4oz, 200 gm)
    size_pattern = r'(\d+(?:\.\d+)?\s*(?:ml|g|gm|oz|kg|l\b|pack of \d+))'
    size_match = re.search(size_pattern, clean_name)
    
    if size_match:
        # Extract the size and remove spaces (e.g., " 50 ml " -> "50ml")
        size_variant = size_match.group(1).replace(' ', '')
        # Remove the size from the main string so it becomes the Core Name
        clean_name = re.sub(size_pattern, '', clean_name)
    else:
        size_variant = "Standard"
        
    # 2. Clean the Core Name
    clean_name = clean_name.replace('&', 'and').replace('®', '').replace('™', '').replace('|', '')
    
    # Remove special characters
    clean_name = re.sub(r'[^a-z0-9\s]', ' ', clean_name)
    
    # Remove search "noise" words
    noise_words = [
        'for men', 'for women', 'daily', 'best', 'dermatologist recommended', 
        'skincare', 'face serum', 'face wash', 'body wash'
    ]
    for word in noise_words:
        clean_name = clean_name.replace(word, ' ')
        
    # Collapse multiple spaces into one
    core_name = " ".join(clean_name.split()).strip()
    
    return core_name, size_variant
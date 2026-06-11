import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "skincare_catalog.db")

original_products = [
    # Cleansers
    ("Cetaphil Gentle Skin Cleanser (125ml)", "Cleanser", "All, Sensitive", "₹ 333", 50),
    ("CeraVe Hydrating Cleanser (236ml)", "Cleanser", "Dry, Normal", "₹ 990", 50),
    ("Minimalist 2% Salicylic Acid Face Wash", "Cleanser", "Oily, Acne", "₹ 299", 50),
    ("Plum Green Tea Pore Cleansing Face Wash", "Cleanser", "Oily, Combination", "₹ 345", 50),
    ("Bioderma Sensibio Gel Moussant (200ml)", "Cleanser", "Sensitive, All", "₹ 1,079", 50),
    ("Himalaya Purifying Neem Face Wash (150ml)", "Cleanser", "Oily, Acne", "₹ 180", 50),
    ("Simple Kind to Skin Refreshing Face Wash", "Cleanser", "All, Sensitive", "₹ 325", 50),
    ("La Roche-Posay Effaclar Purifying Foaming Gel", "Cleanser", "Oily, Combination", "₹ 2,999", 50),

    # Moisturizers
    ("Neutrogena Hydro Boost Water Gel (50g)", "Moisturizer", "All, Oily", "₹ 1,050", 50),
    ("Pond's Super Light Gel Oil Free Moisturiser", "Moisturizer", "Oily, Combination", "₹ 200", 50),
    ("CeraVe Moisturizing Cream (50g)", "Moisturizer", "Dry, Normal", "₹ 550", 50),
    ("Emolene Cream (100g)", "Moisturizer", "Dry, Sensitive", "₹ 350", 50),
    ("Dot & Key Ceramide & Hyaluronic Face Cream", "Moisturizer", "Dry, Normal", "₹ 395", 50),
    ("Re'equil Oil Free Moisturiser", "Moisturizer", "Oily, Acne", "₹ 350", 50),
    ("Sebamed Clear Face Care Gel (50g)", "Moisturizer", "Oily, Sensitive", "₹ 476", 50),
    ("Bioderma Atoderm Intensive Baume (75ml)", "Moisturizer", "Dry, Sensitive", "₹ 1,199", 50),
    ("Vanicream Daily Facial Moisturizer", "Moisturizer", "Sensitive, Dry", "₹ 1,120", 50),

    # Sunscreens
    ("Aqualogica Radiance+ Dewy Sunscreen", "Sunscreen", "All", "₹ 399", 50),
    ("The Derma Co 1% Hyaluronic Sunscreen Aqua Gel", "Sunscreen", "All", "₹ 499", 50),
    ("Minimalist Sunscreen SPF 50 PA++++", "Sunscreen", "All", "₹ 399", 50),
    ("Re'equil Ultra Matte Dry Touch Sunscreen", "Sunscreen", "Oily, Combination", "₹ 695", 50),
    ("Neutrogena Ultra Sheer Dry-Touch SPF 50+", "Sunscreen", "All", "₹ 260", 50),
    ("UV Doux Silicone Sunscreen Gel", "Sunscreen", "Oily, Acne", "₹ 650", 50),
    ("EltaMD UV Clear SPF 46 (48g)", "Sunscreen", "Sensitive, Oily", "₹ 6,289", 50),
    ("Blynds Emulgel SPF 40+ (50g)", "Sunscreen", "All, Sensitive", "₹ 445", 50),

    # Serums
    ("The Ordinary Niacinamide 10% + Zinc 1%", "Serum", "Oily, All", "₹ 550", 50),
    ("Minimalist 10% Vitamin C Face Serum", "Serum", "All", "₹ 699", 50),
    ("Plum 15% Vitamin C Face Serum", "Serum", "All", "₹ 550", 50),
    ("The Derma Co 2% Salicylic Acid Face Serum", "Serum", "Oily, Acne", "₹ 499", 50),
    ("L'Oreal Paris Revitalift Hyaluronic Acid", "Serum", "All", "₹ 499", 50),
    ("COSRX The Vitamin C 23 Serum", "Serum", "All", "₹ 1,200", 50),
    ("Estee Lauder Advanced Night Repair (30ml)", "Serum", "All", "₹ 6,500", 50),

    # Exfoliants & Toners
    ("Paula's Choice 2% BHA Liquid Exfoliant (30ml)", "Exfoliant", "Oily, Combination", "₹ 1,200", 50),
    ("Minimalist 8% Glycolic Acid Toner", "Toner", "Normal, Oily", "₹ 499", 50),
    ("Pixi Glow Tonic (100ml)", "Toner", "All", "₹ 1,400", 50),
    ("The Ordinary AHA 30% + BHA 2% Peeling Solution", "Exfoliant", "All", "₹ 950", 50),
    ("COSRX AHA/BHA Clarifying Treatment Toner", "Toner", "Oily, Acne", "₹ 1,090", 50),

    # Essence & Treatments
    ("COSRX Advanced Snail 96 Mucin Power Essence", "Essence", "Dry, Sensitive", "₹ 999", 50),
    ("Laneige Lip Sleeping Mask (20g)", "Treatment", "All", "₹ 1,300", 50),
    ("Sebamed Clear Face Anti-Pimple Gel", "Treatment", "Acne", "₹ 450", 50),
    ("Mario Badescu Drying Lotion", "Treatment", "Acne", "₹ 1,650", 50)
]

def restore():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create table just in case it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            category TEXT,
            suitable TEXT,
            price TEXT,
            stock INTEGER
        )
    ''')
    
    print("📦 Restoring full 41-product catalog to database...")
    for item in original_products:
        cursor.execute('''
            INSERT INTO products (name, category, suitable, price, stock)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET 
                category=excluded.category,
                suitable=excluded.suitable,
                price=excluded.price, 
                stock=excluded.stock
        ''', item)
        
    conn.commit()
    conn.close()
    print("✅ Complete! You can now safely delete this script.")
    print("Make sure to restart app.py to see all your products.")

if __name__ == "__main__":
    restore()
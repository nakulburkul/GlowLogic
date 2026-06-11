import pandas as pd
import sqlite3

def ingest_kaggle_dataset(csv_filepath):
    # 1. Load the raw dataset into a DataFrame
    df = pd.read_csv(csv_filepath)
    
    # 2. Reshape and clean the dataset to match your database schema
    # (Assuming the CSV has columns like 'Product Name', 'MRP', 'Price', 'URL')
    clean_df = pd.DataFrame({
        'name': df['Product Name'],
        'category': 'Skincare', # Or map this from a column if available
        'suitable': 'All', 
        'price': df['Price'],
        'stock': 100,
        'vendor_link': df['URL'],
        'original_price': df['MRP']
    })
    
    # 3. Drop any duplicate product names to respect the UNIQUE constraint
    clean_df = clean_df.drop_duplicates(subset=['name'])
    
    # 4. Connect to DB and push the DataFrame directly to SQL
    conn = sqlite3.connect('skincare_catalog.db')
    clean_df.to_sql('products', conn, if_exists='append', index=False)
    conn.close()
    
    print(f"Successfully ingested {len(clean_df)} products from CSV.")

# Usage:
# ingest_kaggle_dataset('nykaa_dataset.csv')
# ingest_kaggle_dataset('nykaa_dataset.csv')
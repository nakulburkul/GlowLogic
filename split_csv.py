import pandas as pd

# 1. Load your big file
file_name = 'Product-2026-06-12.csv'
df = pd.read_csv(file_name)

# 2. Define batch size (e.g., 400 products per file)
batch_size = 100
chunks = [df[i:i+batch_size] for i in range(0, df.shape[0], batch_size)]

# 3. Save as batch_1.csv, batch_2.csv, etc.
for i, chunk in enumerate(chunks):
    chunk.to_csv(f'batch_{i+1}.csv', index=False)
    print(f"Created batch_{i+1}.csv with {len(chunk)} products.")
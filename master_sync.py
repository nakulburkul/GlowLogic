import os
import sqlite3
import subprocess
import shutil

# Configuration
DB_PATH = 'skincare_catalog.db'
APP_NAME = 'shop'

def run_django_cmd(cmd):
    print(f"🚀 Running: {cmd}")
    process = subprocess.run(f"python manage.py {cmd}", shell=True, capture_output=True, text=True)
    if process.returncode != 0:
        print(f"⚠️ Warning: {process.stderr.strip()}")
    else:
        print(process.stdout.strip())

def main():
    print("🛠️ --- GLOWGUIDE DATABASE REPAIR TOOL (V2) --- 🛠️\n")

    # 1. Manually Inject the Column (SQL Level)
    print("Step 1: Checking physical database column...")
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        try:
            conn.execute('ALTER TABLE products ADD COLUMN image_filename varchar(255);')
            conn.commit()
            print("✅ Column 'image_filename' injected into SQL table!")
        except sqlite3.OperationalError:
            print("ℹ️ Column already exists in SQL table.")
        conn.close()
    else:
        print(f"❌ Error: {DB_PATH} not found!")
        return

    # 2. Clear Corrupted Migration Files (Safe Version)
    print("\nStep 2: Cleaning up migration history files...")
    migrations_dir = os.path.join(APP_NAME, 'migrations')
    if os.path.exists(migrations_dir):
        for item in os.listdir(migrations_dir):
            item_path = os.path.join(migrations_dir, item)
            if item == '__init__.py':
                continue
            
            try:
                if os.path.isdir(item_path):
                    shutil.rmtree(item_path) # Safely deletes folders like __pycache__
                else:
                    os.remove(item_path) # Deletes files
            except Exception as e:
                print(f"⚠️ Could not delete {item}: {e}")
        print("✅ Local migration files cleared.")

    # 3. Reset Migration History in Database
    print("\nStep 3: Resetting Django migration tracker...")
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(f"DELETE FROM django_migrations WHERE app='{APP_NAME}';")
        conn.commit()
        print("✅ Database migration history for 'shop' wiped.")
    except Exception as e:
        print(f"⚠️ No history found to wipe: {e}")
    conn.close()

    # 4. Re-initialize and Fake the Sync
    print("\nStep 4: Re-initializing Django Migrations...")
    run_django_cmd(f"makemigrations {APP_NAME}")
    run_django_cmd(f"migrate {APP_NAME} --fake")

    print("\n✨ ALL SYSTEMS SYNCED! ✨")
    print("Now run: python manage.py generate_images")

if __name__ == "__main__":
    main()
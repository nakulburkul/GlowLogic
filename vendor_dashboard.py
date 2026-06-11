import os
import time
import random
import sqlite3
import requests
import threading
import customtkinter as ctk
from tkinter import messagebox
from ddgs import DDGS

# --- STRICT PATHS ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "skincare_catalog.db")
IMAGE_DIR = os.path.join(BASE_DIR, "glowguide_web", "shop", "static", "images")

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue") 

class VendorDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("📦 GlowGuide: Vendor Portal")
        self.root.geometry("500x650")
        
        self.setup_database()
        os.makedirs(IMAGE_DIR, exist_ok=True)

        self.product_db = {}
        self._search_timer = None # Timer to prevent spamming Google
        
        self.load_existing_products()
        self.build_ui()

    def setup_database(self):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
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
        conn.commit()
        conn.close()

    def load_existing_products(self):
        """Fetches local products so you can update stock instantly."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name, category, suitable, price, stock FROM products")
            
            for row in cursor.fetchall():
                name, category, suitable, price, stock = row
                self.product_db[name] = {
                    "category": category,
                    "suitable": suitable,
                    "price": price,
                    "stock": stock
                }
            conn.close()
        except sqlite3.OperationalError:
            pass 

    def build_ui(self):
        # Header
        header_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        header_frame.pack(fill="x", pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="Vendor Portal", font=ctk.CTkFont(size=28, weight="bold")).pack()
        ctk.CTkLabel(header_frame, text="Type a brand to search the global database", text_color="gray").pack()
        
        ctk.CTkFrame(self.root, height=2).pack(fill="x", padx=20, pady=10)

        # Form Container
        form_frame = ctk.CTkFrame(self.root, corner_radius=10)
        form_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # 1. Product Name (Now connected to Google!)
        ctk.CTkLabel(form_frame, text="Product Name:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20, pady=(15, 0))
        
        self.name_var = ctk.StringVar()
        # Trace every keystroke to trigger the internet search
        self.name_var.trace_add("write", self.schedule_live_search)
        
        self.name_combo = ctk.CTkComboBox(form_frame, variable=self.name_var, width=400, command=self.autofill_data)
        self.name_combo.pack(padx=20, pady=(5, 10))
        self.name_combo.set("") 

        # 2. Category
        ctk.CTkLabel(form_frame, text="Category:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20)
        self.category_var = ctk.StringVar(value="Cleanser")
        categories = ["Cleanser", "Moisturizer", "Sunscreen", "Serum", "Exfoliant", "Toner", "Essence", "Treatment"]
        self.category_dropdown = ctk.CTkOptionMenu(form_frame, variable=self.category_var, values=categories, width=400)
        self.category_dropdown.pack(padx=20, pady=(5, 10))

        # 3. Suitable Skin Types
        ctk.CTkLabel(form_frame, text="Suitable Skin Types (comma separated):", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=20)
        self.suitable_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g., Dry, Normal, Sensitive", width=400)
        self.suitable_entry.pack(padx=20, pady=(5, 10))

        # 4. Price & Stock (Side by side)
        row_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        row_frame.pack(fill="x", padx=20, pady=5)

        price_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        price_frame.pack(side="left", expand=True, fill="x", padx=(0, 10))
        ctk.CTkLabel(price_frame, text="Price (e.g., ₹ 500):", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.price_entry = ctk.CTkEntry(price_frame, placeholder_text="₹ 0")
        self.price_entry.pack(fill="x", pady=(5, 0))

        stock_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        stock_frame.pack(side="right", expand=True, fill="x", padx=(10, 0))
        ctk.CTkLabel(stock_frame, text="Stock Quantity:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.stock_entry = ctk.CTkEntry(stock_frame, placeholder_text="e.g., 50")
        self.stock_entry.pack(fill="x", pady=(5, 0))

        # Action Buttons
        self.status_label = ctk.CTkLabel(self.root, text="", text_color="orange", font=ctk.CTkFont(weight="bold"))
        self.status_label.pack(pady=(10, 0))

        self.submit_btn = ctk.CTkButton(self.root, text="➕ Add / Update Product", font=ctk.CTkFont(weight="bold", size=14), 
                                        height=45, command=self.save_product)
        self.submit_btn.pack(pady=(10, 20), padx=20, fill="x")

    # ==========================================
    # GLOBAL AUTOCOMPLETE ENGINE
    # ==========================================
    def schedule_live_search(self, *args):
        """Waits 400ms after you stop typing to search the internet."""
        if self._search_timer is not None:
            self.root.after_cancel(self._search_timer)
        self._search_timer = self.root.after(400, self.start_thread_search)

    def start_thread_search(self):
        """Starts a background thread so the GUI doesn't freeze."""
        query = self.name_var.get().strip()
        if len(query) < 3: 
            return # Don't search if they only typed 1 or 2 letters
            
        threading.Thread(target=self.fetch_google_suggestions, args=(query,), daemon=True).start()

    def fetch_google_suggestions(self, query):
        """Asks Google for products matching what you typed."""
        try:
            # We append 'skincare' to the query so Google knows we want cosmetics, not unrelated items
            url = f"https://suggestqueries.google.com/complete/search?client=firefox&q={query} skincare"
            response = requests.get(url, timeout=3)
            data = response.json()
            
            # Google returns data in a list where the 2nd item is the suggestions array
            raw_suggestions = data[1]
            
            # Clean up the word "skincare" from the results to make them look professional
            clean_suggestions = [s.replace(" skincare", "").title() for s in raw_suggestions]
            
            # Get any local products that also match what you typed
            local_matches = [name for name in self.product_db.keys() if query.lower() in name.lower()]
            
            # Merge local database + global internet results (removing duplicates)
            combined_results = list(dict.fromkeys(local_matches + clean_suggestions))
            
            # Safely update the ComboBox dropdown choices back on the main GUI thread
            self.root.after(0, lambda: self.name_combo.configure(values=combined_results))
            
        except Exception as e:
            pass # If internet drops, fail silently and just use local db

    def autofill_data(self, selected_product):
        """If the product is already in our DB, autofill the fields to update stock."""
        if selected_product in self.product_db:
            data = self.product_db[selected_product]
            self.category_var.set(data["category"])
            
            self.suitable_entry.delete(0, 'end')
            self.suitable_entry.insert(0, data["suitable"])
            
            self.price_entry.delete(0, 'end')
            self.price_entry.insert(0, data["price"])
            
            self.stock_entry.delete(0, 'end')
            self.stock_entry.insert(0, str(data["stock"]))
        else:
            # If it's a brand new product from the global internet, clear the fields for the vendor to fill
            self.suitable_entry.delete(0, 'end')
            self.price_entry.delete(0, 'end')
            self.stock_entry.delete(0, 'end')

    # ==========================================
    # SAVE & IMAGE DOWNLOAD LOGIC
    # ==========================================
    def download_image(self, product_name):
        safe_name = "".join([c for c in product_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        filepath = os.path.join(IMAGE_DIR, f"{safe_name}.jpg")

        if os.path.exists(filepath):
            return 

        try:
            with DDGS() as ddgs:
                search_query = product_name + " skincare product white background"
                results = list(ddgs.images(search_query, max_results=1))
                
                if results:
                    image_url = results[0]['image']
                    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
                    img_data = requests.get(image_url, headers=headers, timeout=10).content
                    
                    with open(filepath, 'wb') as handler:
                        handler.write(img_data)
                    
                    time.sleep(random.uniform(1.0, 2.5)) 
        except Exception as e:
            print(f"Failed to download image: {e}")

    def save_product(self):
        name = self.name_combo.get().strip()
        category = self.category_var.get()
        suitable = self.suitable_entry.get().strip()
        price = self.price_entry.get().strip()
        stock_str = self.stock_entry.get().strip()

        if not name or not suitable or not price or not stock_str:
            messagebox.showwarning("Missing Fields", "Please fill out all fields before submitting.")
            return

        try:
            stock = int(stock_str)
        except ValueError:
            messagebox.showerror("Invalid Stock", "Stock quantity must be a whole number.")
            return

        self.submit_btn.configure(state="disabled")
        self.status_label.configure(text="Saving to database and fetching image... Please wait ⏳")
        self.root.update()

        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO products (name, category, suitable, price, stock)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET 
                    category=excluded.category,
                    suitable=excluded.suitable,
                    price=excluded.price, 
                    stock=excluded.stock
            ''', (name, category, suitable, price, stock))
            
            conn.commit()
            conn.close()

            self.download_image(name)

            self.product_db[name] = {
                "category": category,
                "suitable": suitable,
                "price": price,
                "stock": stock
            }
            
            self.status_label.configure(text="")
            messagebox.showinfo("Success!", f"Successfully updated '{name}'!")
            
            self.name_combo.set("")
            self.suitable_entry.delete(0, 'end')
            self.price_entry.delete(0, 'end')
            self.stock_entry.delete(0, 'end')
            self.name_combo.focus()

        except Exception as e:
            messagebox.showerror("Database Error", f"An error occurred: {e}")
        finally:
            self.submit_btn.configure(state="normal")
            self.status_label.configure(text="")

if __name__ == "__main__":
    root = ctk.CTk()
    app = VendorDashboard(root)
    root.mainloop()
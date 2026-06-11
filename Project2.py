import os
import sqlite3
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image

# ==========================================
# CONFIGURATION & THEME SETUP
# ==========================================
ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("green")  

# Get the exact folder this script is saved in (fixes the image path bug!)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGE_DIR = os.path.join(BASE_DIR, "product_images")
DB_PATH = os.path.join(BASE_DIR, "skincare_catalog.db")

# ==========================================
# CUSTOM TOOLTIP WIDGET
# ==========================================
class ToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.widget.bind("<Enter>", self.show_tooltip)
        self.widget.bind("<Leave>", self.hide_tooltip)

    def show_tooltip(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        self.tooltip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        is_dark = ctk.get_appearance_mode() == "Dark"
        bg_color = "#333333" if is_dark else "#F0F0F0"
        fg_color = "white" if is_dark else "black"
        
        label = tk.Label(tw, text=self.text, justify='left',
                         background=bg_color, foreground=fg_color, 
                         relief='solid', borderwidth=1, font=("Segoe UI", 10))
        label.pack(ipadx=8, ipady=5)

    def hide_tooltip(self, event=None):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

# ==========================================
# MAIN APPLICATION ENGINE
# ==========================================
class SkincareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ GlowGuide: Premium Skincare Catalog")
        self.root.geometry("1100x850") 
        
        # --- Application State ---
        self.is_dark_mode = False
        self.current_screen = "onboarding"
        self.current_filter = "All"
        self.routine_generated = False
        
        # E-commerce State
        self.cart = {} # Dictionary: {name: {'product': tuple, 'quantity': int}}
        self.current_budget = 7000 
        self._filter_timer = None 
        self.image_cache = {}

        # Saved Profile Data
        self.saved_concern = "Select Concern..."
        self.saved_type = "Select Skin Type..."

        # Data Initialization
        self.all_products = self.fetch_in_stock_products()
        self.setup_ui_once()

    def fetch_in_stock_products(self):
        """Connects to the database and pulls all 5 columns including stock."""
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT name, category, suitable, price, stock FROM products WHERE stock > 0")
            items = cursor.fetchall() 
            conn.close()
            return items
        except sqlite3.OperationalError:
            print("⚠️ Database Error: Ensure vendor_dashboard.py was run.")
            return []

    # ==========================================
    # IMAGE HANDLING (HD OPTIMIZED)
    # ==========================================
    def get_product_image(self, category, product_name):
        """Standard 150x150 square thumbnail for the catalog grid."""
        if product_name in self.image_cache:
            return self.image_cache[product_name]

        safe_name = "".join([c for c in product_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        filepath = os.path.join(IMAGE_DIR, f"{safe_name}.jpg")

        if os.path.exists(filepath):
            try:
                pil_image = Image.open(filepath)
                # Crop to perfect square
                width, height = pil_image.size
                min_dim = min(width, height)
                left = (width - min_dim) / 2
                top = (height - min_dim) / 2
                pil_image = pil_image.crop((left, top, left + min_dim, top + min_dim))
                
                pil_image = pil_image.resize((150, 150), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=pil_image, size=(150, 150))
                self.image_cache[product_name] = ctk_img
                return ctk_img
            except Exception as e:
                print(f"Error loading thumbnail {filepath}: {e}")
        
        # Fallback colored box
        colors = {
            "Cleanser": "#A2D2FF", "Moisturizer": "#BDE0FE", 
            "Sunscreen": "#FFC8DD", "Serum": "#FFAFCC", 
            "Exfoliant": "#CDB4DB", "Toner": "#b9fbc0", 
            "Essence": "#fbf8cc", "Treatment": "#ffcfd2"
        }
        hex_color = colors.get(category, "#e0e0e0")
        pil_image = Image.new('RGB', (150, 150), color=hex_color)
        ctk_img = ctk.CTkImage(light_image=pil_image, size=(150, 150))
        return ctk_img

    def get_raw_image(self, category, product_name, img_type="main"):
        """Loads the high-resolution original file for the magnifier engine."""
        safe_name = "".join([c for c in product_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        suffix = "_ad" if img_type == "ad" else ""
        filepath = os.path.join(IMAGE_DIR, f"{safe_name}{suffix}.jpg")

        if os.path.exists(filepath):
            try:
                return Image.open(filepath)
            except Exception:
                pass
        
        # HD Fallback color for missing ads/main images
        colors = {"Cleanser": "#A2D2FF", "Moisturizer": "#BDE0FE", "Sunscreen": "#FFC8DD", "Serum": "#FFAFCC"}
        hex_color = colors.get(category, "#e0e0e0") if img_type == "main" else "#d3d3d3"
        return Image.new('RGB', (1200, 1200), color=hex_color)

    def parse_price(self, price_str):
        clean_string = "".join(filter(str.isdigit, price_str))
        return int(clean_string) if clean_string else 0

    def toggle_theme(self):
        if self.is_dark_mode:
            ctk.set_appearance_mode("Light")
            self.is_dark_mode = False
            self.theme_btn.configure(text="🌙 Dark Mode")
        else:
            ctk.set_appearance_mode("Dark")
            self.is_dark_mode = True
            self.theme_btn.configure(text="☀️ Light Mode")

    # ==========================================
    # NAVIGATION LOGIC
    # ==========================================
    def setup_ui_once(self):
        self.build_header()
        
        # Create Main Containers
        self.onboard_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        self.product_detail_container = ctk.CTkFrame(self.root, fg_color="transparent")
        
        self.build_onboarding_ui(self.onboard_container)
        self.build_main_ui(self.main_container)
        
        footer_label = ctk.CTkLabel(self.root, text="© 2026 GlowGuide. All rights reserved.", 
                                    font=ctk.CTkFont(family="Segoe UI", size=10), text_color="gray")
        footer_label.pack(side="bottom", pady=10)

        self.go_to_onboarding()

    def build_header(self):
        header_frame = ctk.CTkFrame(self.root, corner_radius=0, fg_color="transparent")
        header_frame.pack(fill="x", side="top", pady=(10, 0))

        self.back_btn = ctk.CTkButton(header_frame, text="🔙 My Routine", command=self.go_to_onboarding,
                                     width=120, height=35, corner_radius=8, fg_color="transparent", 
                                     border_width=1, text_color=("black", "white"))
        
        btn_text = "☀️ Light Mode" if self.is_dark_mode else "🌙 Dark Mode"
        self.theme_btn = ctk.CTkButton(header_frame, text=btn_text, command=self.toggle_theme,
                                  width=120, height=35, corner_radius=8, fg_color="transparent", 
                                  border_width=1, text_color=("black", "white"))
        self.theme_btn.pack(side="right", padx=20)

        ctk.CTkLabel(header_frame, text="✨ GlowGuide ✨", font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold")).pack()
        ctk.CTkLabel(header_frame, text="Your personal dermatology & product companion", 
                     font=ctk.CTkFont(family="Segoe UI", size=14, slant="italic"), text_color="gray").pack()
        ctk.CTkFrame(self.root, height=2, corner_radius=0).pack(fill="x", padx=20, pady=15)

    def go_to_main_screen(self):
        self.current_screen = "main"
        self.onboard_container.pack_forget() 
        self.product_detail_container.pack_forget()
        self.main_container.pack(fill="both", expand=True) 
        self.back_btn.pack(side="left", padx=20) 
        
        if self.type_var.get() != "Select Skin Type...": 
            self.current_filter = self.type_var.get()
            self.filter_var.set(self.current_filter)
            self.filter_products()

    def go_to_onboarding(self):
        self.current_screen = "onboarding"
        self.main_container.pack_forget() 
        self.product_detail_container.pack_forget()
        self.onboard_container.pack(fill="both", expand=True) 
        self.back_btn.pack_forget() 

    def go_to_shop_from_product(self):
        self.product_detail_container.pack_forget()
        self.main_container.pack(fill="both", expand=True)

    # ==========================================
    # CART LOGIC (INTERACTIVE STACKING)
    # ==========================================
    def add_to_cart_direct(self, product):
        name = product[0]
        stock_available = product[4]

        if name in self.cart:
            if self.cart[name]['quantity'] < stock_available:
                self.cart[name]['quantity'] += 1
                messagebox.showinfo("Cart Update", f"Quantity increased for {name}.")
            else:
                messagebox.showwarning("Stock Limit", f"Only {stock_available} units available.")
        else:
            self.cart[name] = {'product': product, 'quantity': 1}
            messagebox.showinfo("Success", f"{name} added to cart!")
            
        self.refresh_cart_tab()

    def increment_cart_item(self, product_name):
        if product_name in self.cart:
            self.add_to_cart_direct(self.cart[product_name]['product'])

    def decrement_cart_item(self, product_name):
        if product_name in self.cart:
            if self.cart[product_name]['quantity'] > 1:
                self.cart[product_name]['quantity'] -= 1
            else:
                del self.cart[product_name]
            self.refresh_cart_tab()

    def remove_from_cart(self, product_name):
        if product_name in self.cart:
            del self.cart[product_name] 
        self.refresh_cart_tab() 

    def process_checkout(self):
        if not self.cart:
            messagebox.showwarning("Empty Cart", "Add some products before checking out!")
            return
            
        total = sum(self.parse_price(item['product'][3]) * item['quantity'] for item in self.cart.values())
        messagebox.showinfo("Checkout", f"Payment of ₹ {total} processed!\n\nDelivery is on its way. 🚚")
        self.cart.clear() 
        self.refresh_cart_tab() 

    def refresh_cart_tab(self):
        tab = self.tabview.tab("🛒 My Cart")
        for widget in tab.winfo_children(): widget.destroy()
            
        ctk.CTkLabel(tab, text="Your Shopping Cart", font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold")).pack(pady=(15, 20))
        
        if not self.cart:
            ctk.CTkLabel(tab, text="Your cart is currently empty. Start shopping!", 
                         font=ctk.CTkFont(family="Segoe UI", size=15, slant="italic"), text_color="gray").pack(pady=60)
            return

        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=25, pady=10)
        
        total_price = 0
        for name, data in self.cart.items():
            product = data['product']
            qty = data['quantity']
            row_price = self.parse_price(product[3]) * qty
            total_price += row_price
            
            row = ctk.CTkFrame(scroll_frame, corner_radius=10, border_width=1)
            row.pack(fill="x", pady=6)
            
            ctk.CTkLabel(row, text=name, font=ctk.CTkFont(weight="bold", size=13), width=350, anchor="w").pack(side="left", padx=20, pady=20)
            ctk.CTkLabel(row, text=f"₹ {row_price}", font=ctk.CTkFont(size=14, weight="bold"), width=100).pack(side="left")
            
            # Interactive Controls frame
            ctrl = ctk.CTkFrame(row, fg_color="transparent")
            ctrl.pack(side="right", padx=20)
            
            ctk.CTkButton(ctrl, text="🗑️", width=35, fg_color="#c0392b", hover_color="#e74c3c",
                          command=lambda n=name: self.remove_from_cart(n)).pack(side="right", padx=(10, 0))
            
            ctk.CTkButton(ctrl, text="+", width=35, font=ctk.CTkFont(weight="bold"),
                          command=lambda n=name: self.increment_cart_item(n)).pack(side="right", padx=4)
            
            ctk.CTkLabel(ctrl, text=str(qty), font=ctk.CTkFont(weight="bold", size=15), width=25).pack(side="right", padx=4)
            
            ctk.CTkButton(ctrl, text="-", width=35, font=ctk.CTkFont(weight="bold"),
                          command=lambda n=name: self.decrement_cart_item(n)).pack(side="right", padx=4)

        footer = ctk.CTkFrame(tab, corner_radius=15, fg_color=("gray85", "gray20"))
        footer.pack(fill="x", padx=25, pady=25)
        ctk.CTkLabel(footer, text=f"Subtotal: ₹ {total_price}", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")).pack(side="left", padx=25, pady=25)
        ctk.CTkButton(footer, text="Confirm Order 💳", font=ctk.CTkFont(weight="bold", size=15), height=45,
                      command=self.process_checkout).pack(side="right", padx=25)

    # ==========================================
    # ONBOARDING & RECOMMENDATION ENGINE
    # ==========================================
    def update_progress_bar(self, choice=None):
        steps = sum(1 for v in [self.concern_var, self.type_var] if v.get() not in ["Select Concern...", "Select Skin Type..."])
        self.progress_bar.set({0: 0.05, 1: 0.50, 2: 1.0}[steps])
        self.progress_label.configure(text=f"Profile Completion: {steps}/2")

    def build_onboarding_ui(self, parent):
        scroll_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=25, pady=15)

        self.progress_label = ctk.CTkLabel(scroll_frame, text="Profile Completion: 0/2", font=ctk.CTkFont(weight="bold"), text_color="gray")
        self.progress_label.pack(pady=(10, 5))
        self.progress_bar = ctk.CTkProgressBar(scroll_frame, width=400, height=12, corner_radius=6)
        self.progress_bar.pack(pady=(0, 25))
        self.progress_bar.set(0.05)

        ctk.CTkLabel(scroll_frame, text="Let's build your perfect morning & night routine! 🧴", 
                     font=ctk.CTkFont(size=24, weight="bold")).pack(pady=(0, 25))

        self.concern_var = ctk.StringVar(value=self.saved_concern)
        ctk.CTkOptionMenu(scroll_frame, variable=self.concern_var, width=300, height=40, command=self.update_progress_bar,
                          values=["None", "Acne & Breakouts", "Eczema / Severe Dryness", "Rosacea / Redness", "Hyperpigmentation"]).pack(pady=10)

        self.type_var = ctk.StringVar(value=self.saved_type)
        ctk.CTkOptionMenu(scroll_frame, variable=self.type_var, width=300, height=40, command=self.update_progress_bar,
                          values=["Normal", "Dry", "Oily", "Combination", "Sensitive"]).pack(pady=10)

        ctk.CTkButton(scroll_frame, text="Generate Personalized Routine", font=ctk.CTkFont(weight="bold", size=14), 
                      height=45, command=self.show_recommendations).pack(pady=30)

        self.recs_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        self.recs_frame.pack(fill="both", expand=True, pady=10)
        self.update_progress_bar()

    def get_best_match(self, category, user_type, user_concern):
        prods = [p for p in self.all_products if p[1] == category]
        if not prods: return None
        best, highest_score = None, -999

        for prod in prods:
            name, cat, suitable, price, stock = prod
            score = 0
            if user_type in suitable: score += 3
            elif "All" in suitable: score += 1
            else: score -= 3

            if user_concern == "Acne & Breakouts":
                if "Acne" in suitable or "Salicylic" in name or "BHA" in name: score += 5
            elif user_concern == "Eczema / Severe Dryness":
                if "Dry" in suitable or "Ceramide" in name or "Baume" in name: score += 5
                if "Acid" in name and "Hyaluronic" not in name: score -= 5
            elif user_concern == "Rosacea / Redness":
                if "Sensitive" in suitable or "Snail" in name or "Soothing" in name: score += 5
            elif user_concern == "Hyperpigmentation":
                if "Vitamin C" in name or "Niacinamide" in name or "Arbutin" in name: score += 5

            if score > highest_score:
                highest_score = score
                best = prod

        return best if best else (prods[0] if prods else None)

    def show_recommendations(self):
        for widget in self.recs_frame.winfo_children(): widget.destroy()
        self.routine_generated = True
        self.saved_type = self.type_var.get() if self.type_var.get() != "Select Skin Type..." else "Normal"
        self.saved_concern = self.concern_var.get()

        ctk.CTkLabel(self.recs_frame, text=f"Curated {self.saved_type} Routine", 
                     font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")).pack(pady=(0, 5))
        
        if self.saved_concern not in ["None", "Select Concern..."]:
            ctk.CTkLabel(self.recs_frame, text=f"Targeting: {self.saved_concern}", 
                         font=ctk.CTkFont(family="Segoe UI", size=15, slant="italic"), text_color="gray").pack(pady=(0, 20))

        routine_steps = ["Cleanser", "Toner", "Serum", "Moisturizer", "Sunscreen"]
        routine_data = []
        
        for step in routine_steps:
            match = self.get_best_match(step, self.saved_type, self.saved_concern)
            if match:
                routine_data.append((step, match))
                card = ctk.CTkFrame(self.recs_frame, corner_radius=12, border_width=1)
                card.pack(fill="x", padx=50, pady=6)
                ctk.CTkLabel(card, text=f"Step: {step}", font=ctk.CTkFont(weight="bold", size=13), text_color="gray", width=140, anchor="w").pack(side="left", padx=20, pady=15)
                ctk.CTkLabel(card, text=f"✨ {match[0]}", font=ctk.CTkFont(weight="bold", size=14)).pack(side="left", padx=5)

        btn_f = ctk.CTkFrame(self.recs_frame, fg_color="transparent")
        btn_f.pack(pady=30)
        
        ctk.CTkButton(btn_f, text="📥 Download Routine", font=ctk.CTkFont(weight="bold"), 
                      height=45, fg_color="transparent", border_width=2, text_color=("black", "white"),
                      command=lambda: self.export_routine(routine_data)).pack(side="left", padx=15)
        
        ctk.CTkButton(btn_f, text="Go to Full Catalog ➡️", font=ctk.CTkFont(weight="bold"), 
                      height=45, command=self.go_to_main_screen).pack(side="left", padx=15)

    def export_routine(self, data):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", title="Save Skincare Routine")
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("✨ MY GLOWGUIDE SKINCARE ROUTINE ✨\n")
                f.write("="*40 + "\n")
                f.write(f"Skin Profile: {self.saved_type}\nConcern: {self.saved_concern}\n\n")
                for step, prod in data:
                    f.write(f"{step}: {prod[0]} | {prod[3]}\n")
            messagebox.showinfo("Export Success", "Routine has been saved to your PC.")

    # ==========================================
    # SHOP INTERFACE (GRID & FILTERING)
    # ==========================================
    def build_main_ui(self, parent):
        self.tabview = ctk.CTkTabview(parent, corner_radius=12)
        self.tabview.pack(fill='both', expand=True, padx=20, pady=10)

        self.tabview.add("🛍️ Shop")          
        self.tabview.add("🛒 My Cart")
        self.tabview.add("📖 Skin Types Guide")
        self.tabview.add("🩺 Skin Conditions")

        self.setup_products_tab()
        self.refresh_cart_tab()
        self.setup_skin_types_tab()
        self.setup_conditions_tab()

    def setup_products_tab(self):
        tab = self.tabview.tab("🛍️ Shop")
        search_frame = ctk.CTkFrame(tab, fg_color="transparent")
        search_frame.pack(fill="x", padx=15, pady=15)

        ctk.CTkLabel(search_frame, text="Search:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(10, 5))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.debounce_filter())
        ctk.CTkEntry(search_frame, textvariable=self.search_var, placeholder_text="Brand or product...", width=200).pack(side="left", padx=(0, 15))

        ctk.CTkLabel(search_frame, text="Filter Skin Type:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(10, 5))
        self.filter_var = ctk.StringVar(value="All")
        ctk.CTkOptionMenu(search_frame, variable=self.filter_var, command=lambda _: self.filter_products(), 
                          values=["All", "Normal", "Dry", "Oily", "Combination", "Sensitive"]).pack(side="left", padx=5)
        
        self.grid_scroll = ctk.CTkScrollableFrame(tab)
        self.grid_scroll.pack(fill="both", expand=True, padx=15, pady=5)
        self.grid_scroll.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.filter_products()

    def debounce_filter(self):
        if self._filter_timer is not None:
            self.root.after_cancel(self._filter_timer)
        self._filter_timer = self.root.after(200, self.filter_products)

    def filter_products(self):
        query = self.search_var.get().lower()
        sel_type = self.filter_var.get()
        
        filtered = [p for p in self.all_products 
                    if (sel_type == "All" or sel_type in p[2] or "All" in p[2]) 
                    and (query in p[0].lower() or query in p[1].lower())]
        
        self.load_grid_data(filtered)

    def load_grid_data(self, data):
        for widget in self.grid_scroll.winfo_children(): widget.destroy()
        if not data:
            ctk.CTkLabel(self.grid_scroll, text="No matches found.", font=ctk.CTkFont(slant="italic")).grid(row=0, column=0, pady=50)
            return

        r, c = 0, 0
        for item in data:
            card = ctk.CTkFrame(self.grid_scroll, corner_radius=12, border_width=1, cursor="hand2")
            card.grid(row=r, column=c, padx=12, pady=12, sticky="nsew")
            
            img_data = self.get_product_image(item[1], item[0])
            img_lbl = ctk.CTkLabel(card, image=img_data, text="")
            img_lbl.pack(pady=(15, 10))
            
            title = ctk.CTkLabel(card, text=item[0], font=ctk.CTkFont(weight="bold", size=13), wraplength=160, justify="center")
            title.pack(padx=12, pady=(0, 5))
            
            ctk.CTkLabel(card, text=item[1].upper(), font=ctk.CTkFont(size=10, weight="bold"), text_color="gray").pack()
            ctk.CTkLabel(card, text=item[3], font=ctk.CTkFont(weight="bold", size=18), text_color="#2ecc71").pack(pady=10)
            
            # Click events for navigation
            for widget in (card, img_lbl, title):
                widget.bind("<Button-1>", lambda e, i=item: self.show_product_page(i))
            
            c += 1
            if c > 3:
                c = 0
                r += 1

    # ==========================================
    # PRODUCT PAGE (3-COLUMN HD ZOOM)
    # ==========================================
    def show_product_page(self, product):
        name, category, suitable, price, stock = product
        self.main_container.pack_forget()
        self.product_detail_container.pack(fill="both", expand=True)
        for w in self.product_detail_container.winfo_children(): w.destroy()

        # Top Bar
        nav = ctk.CTkFrame(self.product_detail_container, fg_color="transparent")
        nav.pack(fill="x", padx=35, pady=20)
        ctk.CTkButton(nav, text="🔙 Back to Shop", command=self.go_to_shop_from_product, width=150).pack(side="left")

        # Layout Container
        body = ctk.CTkFrame(self.product_detail_container, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=45)

        # 1. Thumbnails Column
        thumb_f = ctk.CTkFrame(body, fg_color="transparent", width=90)
        thumb_f.pack(side="left", fill="y", padx=(0, 25))

        # 2. Main High-Res View
        mid_f = ctk.CTkFrame(body, fg_color="transparent")
        mid_f.pack(side="left", padx=25)
        main_view_lbl = ctk.CTkLabel(mid_f, text="", cursor="crosshair", corner_radius=15, fg_color=("gray90", "gray16"))
        main_view_lbl.pack()
        ctk.CTkLabel(mid_f, text="🔍 Hover label to magnify text", font=("Segoe UI", 12, "italic"), text_color="gray").pack(pady=12)

        # 3. Text & Zoom Overlay Column
        right_f = ctk.CTkFrame(body, fg_color="transparent")
        right_f.pack(side="left", fill="both", expand=True)
        
        info_f = ctk.CTkFrame(right_f, fg_color="transparent")
        info_f.pack(fill="both", expand=True)
        zoom_overlay = ctk.CTkLabel(right_f, text="", corner_radius=12, fg_color=("white", "gray15"))

        ctk.CTkLabel(info_f, text=category.upper(), font=("Segoe UI", 14, "bold"), text_color="gray").pack(anchor="w")
        ctk.CTkLabel(info_f, text=name, font=("Segoe UI", 30, "bold"), wraplength=480, justify="left").pack(anchor="w", pady=12)
        ctk.CTkLabel(info_f, text=price, font=("Segoe UI", 36, "bold"), text_color="#2ecc71").pack(anchor="w")
        
        stock_msg = f"📦 {stock} items in stock ready to ship"
        ctk.CTkLabel(info_f, text=stock_msg, font=("Segoe UI", 14, "bold"), text_color="#2ecc71" if stock > 10 else "orange").pack(anchor="w", pady=8)
        
        ctk.CTkLabel(info_f, text="Top Highlights", font=("Segoe UI", 19, "bold")).pack(anchor="w", pady=(20, 8))
        highlights = [
            f"Dermatologist tested for {suitable} skin.",
            "Formulated with high-potency ingredients.",
            "Cruelty-free and sustainably sourced.",
            "Fast-absorbing formula with long-lasting hydration."
        ]
        for h in highlights:
            ctk.CTkLabel(info_f, text=f"• {h}", font=("Segoe UI", 15), wraplength=450, justify="left").pack(anchor="w", padx=10, pady=3)
            
        ctk.CTkButton(info_f, text="Add to Shopping Cart 🛒", height=55, width=300, font=("Segoe UI", 16, "bold"),
                      command=lambda: self.add_to_cart_direct(product)).pack(anchor="w", pady=40)

        # MAGNIFIER ENGINE (ORIGINAL BICUBIC QUALITY)
        self.thumb_btns = []
        def switch_main_view(itype, btn_idx):
            for i, b in enumerate(self.thumb_btns):
                b.configure(border_width=2 if i == btn_idx else 0, border_color="#2ecc71")
            
            raw_pil = self.get_raw_image(category, name, itype)
            
            # Display Layer
            disp_pil = raw_pil.resize((400, 400), Image.Resampling.LANCZOS)
            main_view_lbl.configure(image=ctk.CTkImage(light_image=disp_pil, size=(400, 400)))
            
            # Virtual HD Layer
            zoom_res = 1200
            hd_layer = raw_pil.resize((zoom_res, zoom_res), Image.Resampling.BICUBIC)

            def trigger_zoom(e):
                if 0 <= e.x <= 400 and 0 <= e.y <= 400:
                    zoom_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
                    zoom_overlay.lift()
                    
                    # Mapping 400px mouse to 1200px HD layer
                    xh, yh = int((e.x / 400) * zoom_res), int((e.y / 400) * zoom_res)
                    box = 280 # Lens window size
                    
                    l = max(0, min(xh - box // 2, zoom_res - box))
                    t = max(0, min(yh - box // 2, zoom_res - box))
                    
                    cropped = hd_layer.crop((l, t, l + box, t + box))
                    # Scale to 500x500 for a crisp 2.5x effect
                    zoom_overlay.configure(image=ctk.CTkImage(light_image=cropped.resize((500,500), Image.Resampling.BICUBIC), size=(500,500)))

            main_view_lbl.bind("<Motion>", trigger_zoom)
            main_view_lbl.bind("<Leave>", lambda e: zoom_overlay.place_forget())

        # Build Thumbnails
        for idx, itype in enumerate(["main", "ad"]):
            p_img = self.get_raw_image(category, name, itype)
            ctk_t = ctk.CTkImage(light_image=p_img.resize((80, 80), Image.Resampling.LANCZOS), size=(80, 80))
            btn = ctk.CTkButton(thumb_f, image=ctk_t, text="", width=80, height=80, fg_color="transparent", 
                                hover_color="#2ecc71", command=lambda t=itype, i=idx: switch_main_view(t, i))
            btn.pack(pady=8)
            self.thumb_btns.append(btn)
        
        switch_main_view("main", 0)

    # ==========================================
    # KNOWLEDGE BASE CONTENT
    # ==========================================
    def setup_skin_types_tab(self):
        tab = self.tabview.tab("📖 Skin Types Guide")
        ctk.CTkLabel(tab, text="Understanding Your Skin Profile", font=("Segoe UI", 20, "bold")).pack(pady=20)
        types = {
            "🌿 Normal": "Balanced skin. Not too oily and not too dry. Pores are small and skin is not sensitive.",
            "💧 Dry": "Skin produces less sebum. Can feel tight, look dull, and be prone to fine lines or flaking.",
            "✨ Oily": "Produces excess sebum. Skin appears shiny, with enlarged pores and a tendency for breakouts.",
            "🌗 Combination": "Skin is oily in the T-zone (forehead, nose, chin) and normal or dry on the cheeks.",
            "🌸 Sensitive": "Skin is easily irritated and reacts to products or the environment with redness or itching."
        }
        for stype, desc in types.items():
            f = ctk.CTkFrame(tab, corner_radius=10, border_width=1)
            f.pack(fill="x", padx=30, pady=6)
            ctk.CTkLabel(f, text=stype, font=("Segoe UI", 13, "bold"), width=180, anchor="w").pack(side="left", padx=20, pady=15)
            ctk.CTkLabel(f, text=desc, wraplength=600, justify="left").pack(side="left", padx=15)

    def setup_conditions_tab(self):
        tab = ctk.CTkScrollableFrame(self.tabview.tab("🩺 Skin Conditions"), fg_color="transparent")
        tab.pack(fill="both", expand=True)
        ctk.CTkLabel(tab, text="Common Conditions & Key Ingredients", font=("Segoe UI", 20, "bold")).pack(pady=20)
        
        conditions_data = [
            {"t": "🔴 Acne & Clogged Pores", "d": "Result of excess oil and bacteria. Best treated with chemical exfoliants.",
             "i": [("Salicylic Acid (BHA)", "Cleanses deep inside the pores."), ("Benzoyl Peroxide", "Kills acne-causing bacteria.")]},
            {"t": "🏜️ Eczema & Dehydration", "d": "Occurs when the skin barrier is damaged. Needs lipids and humectants.",
             "i": [("Ceramides", "Repairs the moisture barrier."), ("Hyaluronic Acid", "Attracts water into the skin.")]},
            {"t": "🔥 Rosacea & Redness", "d": "Chronic inflammation. Needs soothing ingredients and barrier support.",
             "i": [("Azelaic Acid", "Reduces redness significantly."), ("Centella Asiatica", "Calms and repairs irritated skin.")]},
            {"t": "🌑 Hyperpigmentation", "d": "Dark spots from sun or acne. Requires melanin-inhibiting ingredients.",
             "i": [("Vitamin C", "Brightens and provides antioxidant care."), ("Alpha Arbutin", "Safely fades dark patches.")]}
        ]

        for item in conditions_data:
            f = ctk.CTkFrame(tab, corner_radius=12, border_width=1)
            f.pack(fill="x", padx=30, pady=8)
            
            ctk.CTkLabel(f, text=item["t"], font=("Segoe UI", 16, "bold"), width=220, anchor="w").pack(side="left", padx=20, pady=20)
            ctk.CTkLabel(f, text=item["d"], wraplength=400, justify="left").pack(side="left", padx=10)
            
            badge_frame = ctk.CTkFrame(f, fg_color="transparent")
            badge_frame.pack(side="right", padx=20)
            for name, tooltip in item["i"]:
                b = ctk.CTkLabel(badge_frame, text=name, fg_color=("gray85", "gray25"), corner_radius=6, padx=10, pady=4, cursor="hand2")
                b.pack(side="left", padx=4)
                ToolTip(b, tooltip)

# ==========================================
# APP LAUNCHER
# ==========================================
if __name__ == "__main__":
    root = ctk.CTk()
    app = SkincareApp(root)
    root.mainloop()
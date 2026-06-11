import os
import sqlite3
import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image

# Set the theme and color tone
ctk.set_appearance_mode("System")  
ctk.set_default_color_theme("green")  

# Get the exact folder this script is saved in
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
        if self.tooltip_window:  # Prevent duplicate tooltips
            self.hide_tooltip()
            
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
        self.cart = {} # Dictionary for stacking quantities
        self.current_budget = 7000 
        self._filter_timer = None 
        self.image_cache = {}

        self.saved_concern = "Select Concern..."
        self.saved_type = "Select Skin Type..."
        
        # Centralized Category Colors (DRY Principle)
        self.category_colors = {
            "Cleanser": "#A2D2FF", "Moisturizer": "#BDE0FE", 
            "Sunscreen": "#FFC8DD", "Serum": "#FFAFCC", 
            "Exfoliant": "#CDB4DB", "Toner": "#b9fbc0", 
            "Essence": "#fbf8cc", "Treatment": "#ffcfd2"
        }

        self.all_products = self.fetch_in_stock_products()
        
        # Dynamic Budget Limit
        if self.all_products:
            max_price = max(self.parse_price(prod[3]) for prod in self.all_products)
            self.max_slider_value = max_price + 500 
        else:
            self.max_slider_value = 8000 

        self.setup_ui_once()

    def fetch_in_stock_products(self):
        try:
            # Safer Database Connection (Context Manager)
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name, category, suitable, price, stock FROM products WHERE stock > 0")
                return cursor.fetchall()
        except sqlite3.OperationalError:
            print("⚠️ Database not found! Make sure to run vendor_dashboard.py first.")
            return []

    # ==========================================
    # IMAGE HANDLING
    # ==========================================
    def get_product_image(self, category, product_name):
        """Fetches the 150x150 image for the main shop grid."""
        if product_name in self.image_cache:
            return self.image_cache[product_name]

        safe_name = "".join([c for c in product_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        filepath = os.path.join(IMAGE_DIR, f"{safe_name}.jpg")

        if os.path.exists(filepath):
            try:
                pil_image = Image.open(filepath)
                width, height = pil_image.size
                min_dim = min(width, height)
                left = (width - min_dim) / 2
                top = (height - min_dim) / 2
                right = (width + min_dim) / 2
                bottom = (height + min_dim) / 2
                pil_image = pil_image.crop((left, top, right, bottom))
                pil_image = pil_image.resize((150, 150), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(150, 150))
                self.image_cache[product_name] = ctk_img
                return ctk_img
            except (OSError, IOError) as e:
                print(f"Error loading {filepath}: {e}")
        
        hex_color = self.category_colors.get(category, "#e0e0e0")
        pil_image = Image.new('RGB', (150, 150), color=hex_color)
        ctk_img = ctk.CTkImage(light_image=pil_image, dark_image=pil_image, size=(150, 150))
        self.image_cache[product_name] = ctk_img
        return ctk_img

    def get_raw_image(self, category, product_name, img_type="main"):
        """Fetches the high-res PIL image without pre-shrinking it to maintain text clarity."""
        safe_name = "".join([c for c in product_name if c.isalpha() or c.isdigit() or c==' ']).rstrip()
        suffix = "_ad" if img_type == "ad" else ""
        filepath = os.path.join(IMAGE_DIR, f"{safe_name}{suffix}.jpg")

        if os.path.exists(filepath):
            try:
                pil_image = Image.open(filepath)
                return pil_image
            except (OSError, IOError) as e:
                print(f"Error loading high-res {filepath}: {e}")
        
        # Fallback
        hex_color = self.category_colors.get(category, "#e0e0e0") if img_type == "main" else "#d3d3d3"
        return Image.new('RGB', (800, 800), color=hex_color)

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

    def setup_ui_once(self):
        self.build_header()
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

    # ==========================================
    # CART LOGIC (Stackable & Interactive)
    # ==========================================
    def add_to_cart_direct(self, product):
        name = product[0]
        stock_available = product[4]

        if name in self.cart:
            if self.cart[name]['quantity'] < stock_available:
                self.cart[name]['quantity'] += 1
                messagebox.showinfo("Added to Cart 🛒", f"Another {name} has been added to your cart!")
            else:
                messagebox.showwarning("Out of Stock", f"You cannot add more of this item. Only {stock_available} in stock.")
        else:
            self.cart[name] = {'product': product, 'quantity': 1}
            messagebox.showinfo("Added to Cart 🛒", f"{name} has been added to your cart!")
            
        self.refresh_cart_tab()

    def increment_cart_item(self, product_name):
        if product_name in self.cart:
            stock_available = self.cart[product_name]['product'][4]
            if self.cart[product_name]['quantity'] < stock_available:
                self.cart[product_name]['quantity'] += 1
            else:
                messagebox.showwarning("Stock Limit", f"Only {stock_available} units of {product_name} available.")
            self.refresh_cart_tab()

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
            messagebox.showwarning("Empty Cart", "Your cart is empty. Add some products first!")
            return
            
        total = sum(self.parse_price(item['product'][3]) * item['quantity'] for item in self.cart.values())
        messagebox.showinfo("Checkout Successful", f"Payment of ₹ {total} processed!\n\nYour skincare goodies are on their way. 🚚✨")
        self.cart.clear() 
        self.refresh_cart_tab() 

    def refresh_cart_tab(self):
        tab = self.tabview.tab("🛒 My Cart")
        for widget in tab.winfo_children(): widget.destroy()
            
        ctk.CTkLabel(tab, text="Your Shopping Cart", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")).pack(pady=(10, 15))
        
        if not self.cart:
            ctk.CTkLabel(tab, text="Your cart is empty. Explore the catalog to find products!", 
                         font=ctk.CTkFont(family="Segoe UI", size=14, slant="italic"), text_color="gray").pack(pady=40)
            return

        scroll_frame = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        total_price = 0
        
        for name, item_data in self.cart.items():
            product = item_data['product']
            qty = item_data['quantity']
            category, suitable, price_str, stock = product[1], product[2], product[3], product[4]
            
            unit_price = self.parse_price(price_str)
            row_total = unit_price * qty
            total_price += row_total
            
            row = ctk.CTkFrame(scroll_frame, corner_radius=8, border_width=1)
            row.pack(fill="x", pady=5)
            
            ctk.CTkLabel(row, text=name, font=ctk.CTkFont(weight="bold"), width=300, anchor="w").pack(side="left", padx=15, pady=15)
            ctk.CTkLabel(row, text=category, text_color="gray", width=100, anchor="w").pack(side="left", padx=5)
            ctk.CTkLabel(row, text=f"₹ {row_total}", font=ctk.CTkFont(weight="bold", size=14), width=80, anchor="e").pack(side="left", padx=15)
            
            control_frame = ctk.CTkFrame(row, fg_color="transparent")
            control_frame.pack(side="right", padx=15)

            ctk.CTkButton(control_frame, text="🗑️", width=30, fg_color="#c0392b", hover_color="#e74c3c",
                          command=lambda n=name: self.remove_from_cart(n)).pack(side="right", padx=(10, 0))

            ctk.CTkButton(control_frame, text="+", width=30, font=ctk.CTkFont(weight="bold"),
                          command=lambda n=name: self.increment_cart_item(n)).pack(side="right", padx=5)
            
            ctk.CTkLabel(control_frame, text=str(qty), font=ctk.CTkFont(weight="bold", size=14), width=20).pack(side="right", padx=5)
            
            ctk.CTkButton(control_frame, text="-", width=30, font=ctk.CTkFont(weight="bold"),
                          command=lambda n=name: self.decrement_cart_item(n)).pack(side="right", padx=5)

        checkout_frame = ctk.CTkFrame(tab, corner_radius=10, fg_color=("gray85", "gray20"))
        checkout_frame.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(checkout_frame, text=f"Subtotal: ₹ {total_price}", font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold")).pack(side="left", padx=20, pady=20)
        ctk.CTkButton(checkout_frame, text="Secure Checkout 💳", font=ctk.CTkFont(weight="bold", size=14), height=40,
                      command=self.process_checkout).pack(side="right", padx=20)

    # ==========================================
    # ONBOARDING & RECOMMENDATIONS
    # ==========================================
    def update_progress_bar(self, choice=None):
        steps_completed = sum(1 for var in [self.concern_var, self.type_var] if var.get() not in ["Select Concern...", "Select Skin Type..."])
        self.progress_bar.set({0: 0.05, 1: 0.50, 2: 1.0}[steps_completed])
        self.progress_label.configure(text=f"Profile Completion: {steps_completed}/2")

    def build_onboarding_ui(self, parent):
        scroll_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.progress_label = ctk.CTkLabel(scroll_frame, text="Profile Completion: 0/2", font=ctk.CTkFont(weight="bold"), text_color="gray")
        self.progress_label.pack(pady=(0, 5))
        self.progress_bar = ctk.CTkProgressBar(scroll_frame, width=300, height=10, corner_radius=5)
        self.progress_bar.pack(pady=(0, 20))
        self.progress_bar.set(0.05)

        ctk.CTkLabel(scroll_frame, text="Let's find your perfect routine! 🧴", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(0, 20))

        self.concern_var = ctk.StringVar(value=self.saved_concern)
        ctk.CTkOptionMenu(scroll_frame, variable=self.concern_var, width=250, height=35, command=self.update_progress_bar,
                          values=["None", "Acne & Breakouts", "Eczema / Severe Dryness", "Rosacea / Redness", "Hyperpigmentation"]).pack(pady=(5, 15))

        self.type_var = ctk.StringVar(value=self.saved_type)
        ctk.CTkOptionMenu(scroll_frame, variable=self.type_var, width=250, height=35, command=self.update_progress_bar,
                          values=["Normal", "Dry", "Oily", "Combination", "Sensitive"]).pack(pady=(5, 25))

        ctk.CTkButton(scroll_frame, text="Build My Routine", font=ctk.CTkFont(weight="bold"), height=40, command=self.show_recommendations).pack()

        self.recs_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        self.recs_frame.pack(fill="both", expand=True, pady=20)
        self.update_progress_bar()

    def get_best_match(self, category, user_type, user_concern):
        category_prods = [p for p in self.all_products if p[1] == category]
        if not category_prods: return None
        best_match, highest_score = None, -999

        for prod in category_prods:
            name, cat, suitable_for, price, stock = prod
            score = 0
            if user_type in suitable_for: score += 3
            elif "All" in suitable_for: score += 1
            else: score -= 3

            if user_concern == "Acne & Breakouts":
                if "Acne" in suitable_for or "Salicylic" in name or "BHA" in name: score += 4
            elif user_concern == "Eczema / Severe Dryness":
                if "Dry" in suitable_for or "Ceramide" in name or "Baume" in name: score += 4
                if "Glycolic" in name or "BHA" in name: score -= 5
            elif user_concern == "Rosacea / Redness":
                if "Sensitive" in suitable_for or "Sensibio" in name or "Snail" in name: score += 4
                if "Acid" in name and "Hyaluronic" not in name: score -= 5
            elif user_concern == "Hyperpigmentation":
                if "Vitamin C" in name or "Glycolic" in name or "Niacinamide" in name: score += 4

            if score > highest_score:
                highest_score = score
                best_match = prod

        if highest_score < 0 and category_prods:
            for p in category_prods:
                if "All" in p[2]: return p
            return category_prods[0]
        return best_match

    def export_routine(self, routine_data, am, pm):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt", 
            filetypes=[("Text file", "*.txt")],
            title="Save Your Routine"
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("✨ MY GLOWGUIDE SKINCARE ROUTINE ✨\n")
                f.write("="*40 + "\n\n")
                f.write(f"Target Skin Type: {self.saved_type}\n")
                f.write(f"Primary Concern: {self.saved_concern}\n")
                f.write("-" * 40 + "\n\n")
                f.write("🧴 YOUR PRODUCTS:\n")
                for step, prod in routine_data:
                    f.write(f"{step}:\n  - {prod[0]}\n  - Price: {prod[3]}\n\n")
                f.write("-" * 40 + "\n")
                f.write("📖 HOW TO USE:\n")
                f.write(f"🌞 AM: {am}\n")
                f.write(f"🌙 PM: {pm}\n")

    def show_recommendations(self):
        for widget in self.recs_frame.winfo_children(): widget.destroy()

        self.routine_generated = True
        self.saved_type = self.type_var.get() if self.type_var.get() != "Select Skin Type..." else "Normal"
        self.saved_concern = self.concern_var.get()

        ctk.CTkLabel(self.recs_frame, text=f"Curated Routine for {self.saved_type} skin", 
                     font=ctk.CTkFont(family="Segoe UI", size=18, weight="bold")).pack(pady=(0, 2))
        
        if self.saved_concern not in ["None", "Select Concern..."]:
            ctk.CTkLabel(self.recs_frame, text=f"Targeting: {self.saved_concern}", 
                         font=ctk.CTkFont(family="Segoe UI", size=14, slant="italic"), text_color="gray").pack(pady=(0, 15))

        routine = []
        if (c := self.get_best_match("Cleanser", self.saved_type, self.saved_concern)): routine.append(("Step 1: Cleanser", c))
        
        has_toner = False
        if self.saved_type in ["Oily", "Combination", "Normal"] or self.saved_concern == "Acne & Breakouts":
            if (t := self.get_best_match("Toner", self.saved_type, self.saved_concern)):
                routine.append(("Step 2: Toner", t))
                has_toner = True

        has_exfoliant = False
        if self.saved_concern in ["Acne & Breakouts", "Hyperpigmentation"] and self.saved_concern not in ["Eczema / Severe Dryness", "Rosacea / Redness"]:
            if (e := self.get_best_match("Exfoliant", self.saved_type, self.saved_concern)):
                routine.append(("Step 3: Exfoliant (PM)", e))
                has_exfoliant = True

        if (s := self.get_best_match("Serum", self.saved_type, self.saved_concern)): routine.append(("Step 4: Serum", s))
        if (m := self.get_best_match("Moisturizer", self.saved_type, self.saved_concern)): routine.append(("Step 5: Moisturizer", m))
        if (sun := self.get_best_match("Sunscreen", self.saved_type, self.saved_concern)): routine.append(("Step 6: Sunscreen (AM)", sun))

        for step_name, prod in routine:
            card = ctk.CTkFrame(self.recs_frame, corner_radius=10, border_width=1)
            card.pack(fill="x", padx=40, pady=5)
            ctk.CTkLabel(card, text=step_name, font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"), text_color="gray", width=160, anchor="w").pack(side="left", padx=(15, 0), pady=12)
            ctk.CTkLabel(card, text=f"✨ {prod[0]}", font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold")).pack(side="left", padx=5, pady=12)

        guide_frame = ctk.CTkFrame(self.recs_frame, corner_radius=10)
        guide_frame.pack(fill="x", padx=40, pady=(20, 15))

        am_steps = "Cleanser ➔ " + ("Toner ➔ " if has_toner else "") + "Serum ➔ Moisturizer ➔ Sunscreen"
        pm_steps = "Cleanser ➔ " + ("Exfoliant (2x/week) ➔ " if has_exfoliant else ("Toner ➔ " if has_toner else "")) + "Serum ➔ Moisturizer"

        ctk.CTkLabel(guide_frame, text="📖 How to use your routine:", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold")).pack(pady=(12, 5))
        ctk.CTkLabel(guide_frame, text=f"🌞 AM: {am_steps}", font=ctk.CTkFont(family="Segoe UI", size=12)).pack(pady=2)
        ctk.CTkLabel(guide_frame, text=f"🌙 PM: {pm_steps}", font=ctk.CTkFont(family="Segoe UI", size=12)).pack(pady=(2, 12))

        btn_frame = ctk.CTkFrame(self.recs_frame, fg_color="transparent")
        btn_frame.pack(pady=(10, 20))

        ctk.CTkButton(btn_frame, text="📥 Save Routine", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                      height=45, corner_radius=8, fg_color="transparent", border_width=2, text_color=("black", "white"),
                      command=lambda: self.export_routine(routine, am_steps, pm_steps)).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="Explore Full Catalog ➡️", font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
                      height=45, corner_radius=8, command=self.go_to_main_screen).pack(side="left", padx=10)

    # ==========================================
    # MAIN TABS & AMAZON-STYLE GRID CATALOG
    # ==========================================
    def build_main_ui(self, parent):
        self.tabview = ctk.CTkTabview(parent, corner_radius=10)
        self.tabview.pack(fill='both', expand=True, padx=20, pady=(5, 15))

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
        search_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(search_frame, text="Search:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(10, 5))
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.debounce_filter())
        ctk.CTkEntry(search_frame, textvariable=self.search_var, placeholder_text="Brand or product...", width=160).pack(side="left", padx=(0, 10))

        ctk.CTkLabel(search_frame, text="Type:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(10, 5))
        self.filter_var = ctk.StringVar(value=self.current_filter)
        ctk.CTkOptionMenu(search_frame, variable=self.filter_var, command=lambda _: self.debounce_filter(), width=100,
                          values=["All", "Normal", "Dry", "Oily", "Combination", "Sensitive", "Acne"]).pack(side="left", padx=5)
        
        # --- NEW CATEGORY FILTER ---
        ctk.CTkLabel(search_frame, text="Category:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(10, 5))
        self.category_var = ctk.StringVar(value="All Categories")
        ctk.CTkOptionMenu(search_frame, variable=self.category_var, command=lambda _: self.debounce_filter(), width=120,
                          values=["All Categories", "Cleanser", "Moisturizer", "Sunscreen", "Serum", "Exfoliant", "Toner", "Essence", "Treatment"]).pack(side="left", padx=5)
        
        ctk.CTkLabel(search_frame, text="Max Budget:", font=ctk.CTkFont(weight="bold")).pack(side="left", padx=(15, 5))
        self.budget_label_var = ctk.StringVar(value=f"₹ {self.current_budget}")
        ctk.CTkLabel(search_frame, textvariable=self.budget_label_var).pack(side="left", padx=5)
        
        # Dynamic Budget Slider Limit Applied Here
        self.budget_slider = ctk.CTkSlider(search_frame, from_=200, to=self.max_slider_value, command=self.update_budget, width=120)
        self.budget_slider.set(self.current_budget)
        self.budget_slider.pack(side="left", padx=10)

        self.catalog_scroll_frame = ctk.CTkScrollableFrame(tab)
        self.catalog_scroll_frame.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        self.catalog_scroll_frame.grid_columnconfigure((0, 1, 2, 3), weight=1)

        self.filter_products()

    def debounce_filter(self):
        if self._filter_timer is not None:
            self.root.after_cancel(self._filter_timer)
        self._filter_timer = self.root.after(200, self.filter_products)

    def update_budget(self, value):
        self.current_budget = int(value)
        self.budget_label_var.set(f"₹ {self.current_budget}") 
        self.debounce_filter()

    def filter_products(self, event=None):
        selected_type = self.filter_var.get()
        search_query = self.search_var.get().lower()
        
        # Safely fetch category
        selected_category = getattr(self, "category_var", ctk.StringVar(value="All Categories")).get()

        filtered_data = [
            prod for prod in self.all_products 
            # Match Skin Type
            if (selected_type in prod[2] or "All" in prod[2] or selected_type == "All") 
            # Match Category
            and (selected_category == "All Categories" or selected_category == prod[1])
            # Match Budget
            and self.parse_price(prod[3]) <= self.current_budget
            # Match Search
            and (search_query in prod[0].lower() or search_query in prod[1].lower() or search_query in prod[2].lower())
        ]
        self.load_product_data(filtered_data)

    def load_product_data(self, data):
        for widget in self.catalog_scroll_frame.winfo_children(): widget.destroy()

        if not data:
            ctk.CTkLabel(self.catalog_scroll_frame, text="No products found matching your criteria.", 
                         font=ctk.CTkFont(family="Segoe UI", size=14, slant="italic"), text_color="gray").grid(row=0, column=0, columnspan=4, pady=40)
            return

        row_idx = 0
        col_idx = 0
        MAX_COLS = 4 

        for item in data:
            name, category, suitable, price, stock = item
            
            card = ctk.CTkFrame(self.catalog_scroll_frame, corner_radius=10, border_width=1, cursor="hand2")
            card.grid(row=row_idx, column=col_idx, padx=10, pady=10, sticky="nsew")
            
            img = self.get_product_image(category, name)
            img_lbl = ctk.CTkLabel(card, image=img, text="", cursor="hand2")
            img_lbl.pack(pady=(15, 5))
            
            title_lbl = ctk.CTkLabel(card, text=name, font=ctk.CTkFont(weight="bold", size=13), wraplength=170, justify="center", cursor="hand2")
            title_lbl.pack(padx=10, pady=(5, 0), fill="x")
            
            cat_lbl = ctk.CTkLabel(card, text=category.upper(), font=ctk.CTkFont(size=10, weight="bold"), text_color="gray", cursor="hand2")
            cat_lbl.pack(pady=(0, 5))
            
            price_lbl = ctk.CTkLabel(card, text=price, font=ctk.CTkFont(weight="bold", size=18), text_color="#2ecc71", cursor="hand2")
            price_lbl.pack(pady=(5, 10))
            
            btn_frame = ctk.CTkFrame(card, fg_color="transparent")
            btn_frame.pack(fill="x", padx=15, pady=(0, 15))
            
            info_btn = ctk.CTkButton(btn_frame, text="ℹ️", width=30, fg_color="gray", command=lambda p=item: self.show_product_page(None, p))
            info_btn.pack(side="left", padx=(0, 5))
            
            cart_btn = ctk.CTkButton(btn_frame, text="Add to Cart", command=lambda p=item: self.add_to_cart_direct(p))
            cart_btn.pack(side="right", expand=True, fill="x")
            
            for w in (card, img_lbl, title_lbl, cat_lbl, price_lbl):
                w.bind("<Button-1>", lambda e, p=item: self.show_product_page(e, p))
            
            col_idx += 1
            if col_idx >= MAX_COLS:
                col_idx = 0
                row_idx += 1

    # ==========================================
    # FULL PRODUCT PAGE WITH HOVER ZOOM
    # ==========================================
    def go_to_shop_from_product(self):
        self.product_detail_container.pack_forget()
        self.main_container.pack(fill="both", expand=True)

    def show_product_page(self, event, product):
        name, category, suitable, price, stock = product 
        
        self.main_container.pack_forget()
        self.product_detail_container.pack(fill="both", expand=True)
        
        for widget in self.product_detail_container.winfo_children():
            widget.destroy()

        top_bar = ctk.CTkFrame(self.product_detail_container, fg_color="transparent")
        top_bar.pack(fill="x", padx=30, pady=(10, 20))
        
        ctk.CTkButton(top_bar, text="🔙 Back to Catalog", command=self.go_to_shop_from_product, 
                      width=150, height=35, corner_radius=8, fg_color="transparent", border_width=1, 
                      text_color=("black", "white")).pack(side="left")
        
        content_frame = ctk.CTkFrame(self.product_detail_container, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=40, pady=10)
        
        # 1. THUMBNAILS COLUMN
        thumb_col = ctk.CTkFrame(content_frame, fg_color="transparent", width=100)
        thumb_col.pack(side="left", fill="y", padx=(0, 20))
        
        # 2. MAIN IMAGE COLUMN
        main_img_col = ctk.CTkFrame(content_frame, fg_color="transparent", width=400)
        main_img_col.pack(side="left", fill="y", padx=(0, 40))

        main_img_label = ctk.CTkLabel(main_img_col, text="", corner_radius=10, fg_color=("gray90", "gray16"), cursor="crosshair")
        main_img_label.pack(pady=(0, 10))
        
        ctk.CTkLabel(main_img_col, text="🔍 Hover over image to zoom", text_color="gray", font=ctk.CTkFont(size=12, slant="italic")).pack()

        # 3. TEXT & HIGHLIGHTS COLUMN
        right_col = ctk.CTkFrame(content_frame, fg_color="transparent")
        right_col.pack(side="left", fill="both", expand=True)

        info_container = ctk.CTkFrame(right_col, fg_color="transparent")
        info_container.pack(fill="both", expand=True)

        zoom_overlay = ctk.CTkLabel(right_col, text="", corner_radius=10, fg_color=("white", "gray15"))

        ctk.CTkLabel(info_container, text=category.upper(), font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"), text_color="gray").pack(anchor="w")
        ctk.CTkLabel(info_container, text=name, font=ctk.CTkFont(family="Segoe UI", size=28, weight="bold"), wraplength=450, justify="left").pack(anchor="w", pady=(0, 15))
        ctk.CTkFrame(info_container, height=2, corner_radius=0).pack(fill="x", pady=5)
        
        stats_frame = ctk.CTkFrame(info_container, fg_color="transparent")
        stats_frame.pack(fill="x", pady=(10, 15))
        ctk.CTkLabel(stats_frame, text=f"{price}", font=ctk.CTkFont(size=32, weight="bold"), text_color="#2ecc71").pack(side="left")
        stock_color = "orange" if stock < 10 else "green"
        ctk.CTkLabel(stats_frame, text=f"📦 {stock} in stock ready to ship", font=ctk.CTkFont(size=14, weight="bold"), text_color=stock_color).pack(side="left", padx=20)
        
        ctk.CTkLabel(info_container, text="Top Highlights", font=ctk.CTkFont(size=18, weight="bold")).pack(anchor="w", pady=(10, 5))
        highlights = [
            f"Formulated for skin types including {suitable}.",
            "Dermatologist tested and recommended.",
            "Premium quality ingredients for daily use.",
            "Fast-absorbing and highly effective."
        ]
        for h in highlights:
            ctk.CTkLabel(info_container, text=f"•  {h}", font=ctk.CTkFont(size=14), wraplength=450, justify="left").pack(anchor="w", padx=10, pady=2)
        
        advice = "Apply gently avoiding the eye area."
        if category == "Sunscreen": advice = "Apply generously 15 minutes before sun exposure. Reapply every 2 hours."
        elif category == "Cleanser": advice = "Massage onto damp skin, then rinse thoroughly."
        elif "Acid" in name or "BHA" in name: advice = "Use carefully 2-3 times a week. Always follow with sunscreen the next morning."
        elif category == "Moisturizer": advice = "Apply an even layer to seal in hydration."
        
        ctk.CTkLabel(info_container, text=f"💡 Usage Tip:", font=ctk.CTkFont(size=16, weight="bold")).pack(anchor="w", pady=(15, 0))
        ctk.CTkLabel(info_container, text=advice, font=ctk.CTkFont(size=14), wraplength=450, justify="left").pack(anchor="w", pady=(0, 25))
        
        ctk.CTkButton(info_container, text="Add to Cart 🛒", font=ctk.CTkFont(size=16, weight="bold"), height=50, width=250, 
                      command=lambda: self.add_to_cart_direct(product)).pack(anchor="w")

        # HOVER ZOOM LOGIC
        self.thumb_buttons = []
        def update_main_image(img_type, btn_index):
            for i, btn in enumerate(self.thumb_buttons):
                btn.configure(border_color="#2ecc71" if i == btn_index else "gray")
                
            pil_img = self.get_raw_image(category, name, img_type)
            
            display_size = 350
            base_img = pil_img.resize((display_size, display_size), Image.Resampling.LANCZOS)
            ctk_base = ctk.CTkImage(light_image=base_img, size=(display_size, display_size))
            main_img_label.configure(image=ctk_base)

            zoom_res = 800 
            high_res_img = pil_img.resize((zoom_res, zoom_res), Image.Resampling.LANCZOS)

            def on_hover(e):
                zoom_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
                zoom_overlay.lift()
                update_zoom(e)

            def on_leave(e):
                zoom_overlay.place_forget()

            def update_zoom(e):
                if e.x < 0 or e.y < 0 or e.x > display_size or e.y > display_size:
                    return

                x_hr = int((e.x / display_size) * zoom_res)
                y_hr = int((e.y / display_size) * zoom_res)

                box_size = 250
                half = box_size // 2
                left, top = x_hr - half, y_hr - half
                right, bottom = x_hr + half, y_hr + half

                if left < 0: left, right = 0, box_size
                if top < 0: top, bottom = 0, box_size
                if right > zoom_res: right, left = zoom_res, zoom_res - box_size
                if bottom > zoom_res: bottom, top = zoom_res, zoom_res - box_size

                cropped = high_res_img.crop((left, top, right, bottom))
                zoomed_ctk = ctk.CTkImage(light_image=cropped.resize((500, 500), Image.Resampling.LANCZOS), size=(500, 500))
                zoom_overlay.configure(image=zoomed_ctk)

            main_img_label.unbind("<Enter>")
            main_img_label.unbind("<Leave>")
            main_img_label.unbind("<Motion>")

            main_img_label.bind("<Enter>", on_hover)
            main_img_label.bind("<Leave>", on_leave)
            main_img_label.bind("<Motion>", update_zoom)

        main_raw = self.get_raw_image(category, name, "main")
        ad_raw = self.get_raw_image(category, name, "ad")

        if main_raw:
            t1 = main_raw.resize((80, 80), Image.Resampling.LANCZOS)
            ctk_t1 = ctk.CTkImage(light_image=t1, size=(80, 80))
            btn1 = ctk.CTkButton(thumb_col, image=ctk_t1, text="", width=80, height=80, fg_color="transparent", 
                                 border_width=2, cursor="hand2", command=lambda: update_main_image("main", 0))
            btn1.pack(pady=(0, 10))
            self.thumb_buttons.append(btn1)
            
        if ad_raw:
            t2 = ad_raw.resize((80, 80), Image.Resampling.LANCZOS)
            ctk_t2 = ctk.CTkImage(light_image=t2, size=(80, 80))
            btn2 = ctk.CTkButton(thumb_col, image=ctk_t2, text="", width=80, height=80, fg_color="transparent", 
                                 border_width=2, cursor="hand2", command=lambda: update_main_image("ad", 1))
            btn2.pack(pady=10)
            self.thumb_buttons.append(btn2)

        if self.thumb_buttons:
            update_main_image("main", 0)

    def setup_skin_types_tab(self):
        tab = self.tabview.tab("📖 Skin Types Guide")
        ctk.CTkLabel(tab, text="Identify Your Skin Profile", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")).pack(pady=(10, 15))
        skin_types = {
            "🌿 Normal": "Well-balanced skin. Not too oily, not too dry.",
            "💧 Dry": "Produces less sebum. Can feel tight or look flaky.",
            "✨ Oily": "Produces excess sebum. Prone to enlarged pores.",
            "🌗 Combination": "Features both oily and dry areas.",
            "🌸 Sensitive": "Easily irritated by products or environment."
        }
        for stype, desc in skin_types.items():
            card = ctk.CTkFrame(tab, corner_radius=8)
            card.pack(fill="x", padx=20, pady=6)
            ctk.CTkLabel(card, text=stype, font=ctk.CTkFont(weight="bold"), width=150, anchor="w").pack(side="left", padx=15, pady=15)
            ctk.CTkLabel(card, text=desc).pack(side="left", padx=10, pady=15)

    def setup_conditions_tab(self):
        tab = ctk.CTkScrollableFrame(self.tabview.tab("🩺 Skin Conditions"), fg_color="transparent")
        tab.pack(fill="both", expand=True)
        ctk.CTkLabel(tab, text="Common Skin Conditions & Ingredients", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold")).pack(pady=(10, 5))
        ctk.CTkLabel(tab, text="Hover over an ingredient badge to see what it does!", font=ctk.CTkFont(family="Segoe UI", size=12, slant="italic"), text_color="gray").pack(pady=(0, 15))
                     
        conditions_data = [
            {"title": "🔴 Acne & Breakouts", "desc": "Caused by clogged pores, bacteria, and excess sebum production.",
             "ingredients": [("Salicylic Acid (BHA)", "Exfoliates deep inside pores."), ("Benzoyl Peroxide", "Kills acne-causing bacteria."), ("Niacinamide", "Reduces inflammation and oil.")]},
            {"title": "🏜️ Eczema / Dryness", "desc": "A damaged skin barrier leading to severe flaking, itching, and redness.",
             "ingredients": [("Ceramides", "Rebuilds the skin's barrier."), ("Hyaluronic Acid", "Draws water into the skin."), ("Colloidal Oatmeal", "Relieves itching and irritation.")]},
            {"title": "🔥 Rosacea", "desc": "Chronic condition causing redness, visible blood vessels, and sometimes bumps.",
             "ingredients": [("Azelaic Acid", "Reduces redness and inflammation."), ("Centella Asiatica", "Repairs and soothes irritated skin."), ("Sulfur", "Clears bumps without severe irritation.")]},
            {"title": "🌑 Hyperpigmentation", "desc": "Dark patches caused by excess melanin production.",
             "ingredients": [("Vitamin C", "Brightens skin and inhibits melanin."), ("Alpha Arbutin", "Targets dark spots directly."), ("Glycolic Acid (AHA)", "Sweeps away dark surface skin cells.")]}
        ]

        for item in conditions_data:
            card = ctk.CTkFrame(tab, corner_radius=8)
            card.pack(fill="x", padx=20, pady=8)
            top_frame = ctk.CTkFrame(card, fg_color="transparent")
            top_frame.pack(fill="x", padx=15, pady=(15, 5))
            ctk.CTkLabel(top_frame, text=item["title"], font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"), width=200, anchor="w").pack(side="left")
            ctk.CTkLabel(top_frame, text=item["desc"], font=ctk.CTkFont(family="Segoe UI", size=13), wraplength=450, justify="left").pack(side="left", padx=10)
            badge_frame = ctk.CTkFrame(card, fg_color="transparent")
            badge_frame.pack(fill="x", padx=215, pady=(0, 15))
            ctk.CTkLabel(badge_frame, text="Key Ingredients:", font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"), text_color="gray").pack(side="left", padx=(0, 10))
            for ing_name, ing_desc in item["ingredients"]:
                badge = ctk.CTkLabel(badge_frame, text=ing_name, font=ctk.CTkFont(family="Segoe UI", size=11), fg_color=("gray85", "gray25"), corner_radius=5, padx=8, pady=2, cursor="hand2")
                badge.pack(side="left", padx=5)
                ToolTip(badge, text=ing_desc)

if __name__ == "__main__":
    root = ctk.CTk()
    app = SkincareApp(root)
    root.mainloop()
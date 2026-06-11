import tkinter as tk
from tkinter import ttk


class SkincareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ GlowGuide: Premium Skincare Catalog")
        self.root.geometry("950x850")

        # --- Application State ---
        self.is_dark_mode = False
        self.current_screen = "onboarding"
        self.current_filter = "All"
        self.routine_generated = False

        # Saved quiz states so going back remembers your choices
        self.saved_concern = "None"
        self.saved_type = "Normal"

        # Mega Database with approximate Amazon India Pricing
        self.all_products = [
            # Cleansers
            ("Cetaphil Gentle Skin Cleanser (125ml)", "Cleanser", "All, Sensitive", "₹ 333"),
            ("CeraVe Hydrating Cleanser (236ml)", "Cleanser", "Dry, Normal", "₹ 990"),
            ("Minimalist 2% Salicylic Acid Face Wash", "Cleanser", "Oily, Acne", "₹ 299"),
            ("Plum Green Tea Pore Cleansing Face Wash", "Cleanser", "Oily, Combination", "₹ 345"),
            ("Bioderma Sensibio Gel Moussant (200ml)", "Cleanser", "Sensitive, All", "₹ 1,079"),
            ("Himalaya Purifying Neem Face Wash (150ml)", "Cleanser", "Oily, Acne", "₹ 180"),
            ("Simple Kind to Skin Refreshing Face Wash", "Cleanser", "All, Sensitive", "₹ 325"),
            ("La Roche-Posay Effaclar Purifying Foaming Gel", "Cleanser", "Oily, Combination", "₹ 2,999"),

            # Moisturizers
            ("Neutrogena Hydro Boost Water Gel (50g)", "Moisturizer", "All, Oily", "₹ 1,050"),
            ("Pond's Super Light Gel Oil Free Moisturiser", "Moisturizer", "Oily, Combination", "₹ 200"),
            ("CeraVe Moisturizing Cream (50g)", "Moisturizer", "Dry, Normal", "₹ 550"),
            ("Emolene Cream (100g)", "Moisturizer", "Dry, Sensitive", "₹ 350"),
            ("Dot & Key Ceramide & Hyaluronic Face Cream", "Moisturizer", "Dry, Normal", "₹ 395"),
            ("Re'equil Oil Free Moisturiser", "Moisturizer", "Oily, Acne", "₹ 350"),
            ("Sebamed Clear Face Care Gel (50g)", "Moisturizer", "Oily, Sensitive", "₹ 476"),
            ("Bioderma Atoderm Intensive Baume (75ml)", "Moisturizer", "Dry, Sensitive", "₹ 1,199"),
            ("Vanicream Daily Facial Moisturizer", "Moisturizer", "Sensitive, Dry", "₹ 1,120"),

            # Sunscreens
            ("Aqualogica Radiance+ Dewy Sunscreen", "Sunscreen", "All", "₹ 399"),
            ("The Derma Co 1% Hyaluronic Sunscreen Aqua Gel", "Sunscreen", "All", "₹ 499"),
            ("Minimalist Sunscreen SPF 50 PA++++", "Sunscreen", "All", "₹ 399"),
            ("Re'equil Ultra Matte Dry Touch Sunscreen", "Sunscreen", "Oily, Combination", "₹ 695"),
            ("Neutrogena Ultra Sheer Dry-Touch SPF 50+", "Sunscreen", "All", "₹ 260"),
            ("UV Doux Silicone Sunscreen Gel", "Sunscreen", "Oily, Acne", "₹ 650"),
            ("EltaMD UV Clear SPF 46 (48g)", "Sunscreen", "Sensitive, Oily", "₹ 6,289"),
            ("Blynds Emulgel SPF 40+ (50g)", "Sunscreen", "All, Sensitive", "₹ 445"),

            # Serums
            ("The Ordinary Niacinamide 10% + Zinc 1%", "Serum", "Oily, All", "₹ 550"),
            ("Minimalist 10% Vitamin C Face Serum", "Serum", "All", "₹ 699"),
            ("Plum 15% Vitamin C Face Serum", "Serum", "All", "₹ 550"),
            ("The Derma Co 2% Salicylic Acid Face Serum", "Serum", "Oily, Acne", "₹ 499"),
            ("L'Oreal Paris Revitalift Hyaluronic Acid", "Serum", "All", "₹ 499"),
            ("COSRX The Vitamin C 23 Serum", "Serum", "All", "₹ 1,200"),
            ("Estee Lauder Advanced Night Repair (30ml)", "Serum", "All", "₹ 6,500"),

            # Exfoliants & Toners
            ("Paula's Choice 2% BHA Liquid Exfoliant (30ml)", "Exfoliant", "Oily, Combination", "₹ 1,200"),
            ("Minimalist 8% Glycolic Acid Toner", "Toner", "Normal, Oily", "₹ 499"),
            ("Pixi Glow Tonic (100ml)", "Toner", "All", "₹ 1,400"),
            ("The Ordinary AHA 30% + BHA 2% Peeling Solution", "Exfoliant", "All", "₹ 950"),
            ("COSRX AHA/BHA Clarifying Treatment Toner", "Toner", "Oily, Acne", "₹ 1,090"),

            # Essence & Treatments
            ("COSRX Advanced Snail 96 Mucin Power Essence", "Essence", "Dry, Sensitive", "₹ 999"),
            ("Laneige Lip Sleeping Mask (20g)", "Treatment", "All", "₹ 1,300"),
            ("Sebamed Clear Face Anti-Pimple Gel", "Treatment", "Acne", "₹ 450"),
            ("Mario Badescu Drying Lotion", "Treatment", "Acne", "₹ 1,650")
        ]

        # Initialize the UI with the default theme
        self.apply_theme()

    def toggle_theme(self):
        if hasattr(self, 'filter_var') and self.current_screen == "main":
            self.current_filter = self.filter_var.get()
        self.is_dark_mode = not self.is_dark_mode
        self.apply_theme()

    def apply_theme(self):
        if self.is_dark_mode:
            self.bg_color = "#121212"
            self.text_color = "#E0E0E0"
            self.header_bg = "#1A2421"
            self.card_bg = "#1E1E1E"
            self.tab_bg = "#2D2D2D"
            self.tab_text = "#FFFFFF"
            self.sub_text = "#AAAAAA"
            self.btn_text = "☀️ Light Mode"
            self.border_color = "#333333"
            self.accent_bg = "#3A5048"
        else:
            self.bg_color = "#FAF7F2"
            self.text_color = "#3E363F"
            self.header_bg = "#D4E0D9"
            self.card_bg = "#FFFFFF"
            self.tab_bg = "#E8D5C4"
            self.tab_text = "#3E363F"
            self.sub_text = "#555555"
            self.btn_text = "🌙 Dark Mode"
            self.border_color = "#E8D5C4"
            self.accent_bg = "#C6D5CB"

        self.root.configure(bg=self.bg_color)

        for widget in self.root.winfo_children():
            widget.destroy()

        style = ttk.Style()
        style.theme_use('clam')

        style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 12, "bold"), padding=[15, 8], background=self.tab_bg,
                        foreground=self.tab_text)
        style.map("TNotebook.Tab", background=[("selected", self.header_bg)],
                  foreground=[("selected", self.text_color)])
        style.configure("TFrame", background=self.bg_color)

        self.build_header()

        if self.current_screen == "onboarding":
            self.build_onboarding_ui()
        else:
            self.build_main_ui()

        footer_label = tk.Label(self.root, text="© 2026 GlowGuide. All rights reserved.", font=("Segoe UI", 9),
                                bg=self.bg_color, fg=self.sub_text)
        footer_label.pack(side="bottom", pady=5)

    def build_header(self):
        header_frame = tk.Frame(self.root, bg=self.header_bg, pady=15)
        header_frame.pack(fill="x", side="top")

        # BACK BUTTON (Only visible in Main Catalog)
        if self.current_screen == "main":
            back_btn = tk.Button(header_frame, text="🔙 My Routine", command=self.go_to_onboarding,
                                 bg=self.bg_color, fg=self.text_color, relief="flat", font=("Segoe UI", 10, "bold"),
                                 cursor="hand2")
            back_btn.pack(side="left", padx=20)

        # THEME BUTTON
        theme_btn = tk.Button(header_frame, text=self.btn_text, command=self.toggle_theme,
                              bg=self.bg_color, fg=self.text_color, relief="flat", font=("Segoe UI", 10, "bold"),
                              cursor="hand2")
        theme_btn.pack(side="right", padx=20)

        tk.Label(header_frame, text="✨ GlowGuide ✨", font=("Segoe UI", 24, "bold"), bg=self.header_bg,
                 fg=self.text_color).pack()
        tk.Label(header_frame, text="Your personal dermatology & product companion", font=("Segoe UI", 12, "italic"),
                 bg=self.header_bg, fg=self.text_color).pack()

    # ==========================================
    # SCROLL WHEEL EVENT HANDLER
    # ==========================================
    def _on_mousewheel(self, event):
        if self.current_screen != "onboarding":
            return

        # Prevent scrolling if the content is smaller than the canvas window
        if self.onboard_canvas.bbox("all")[3] <= self.onboard_canvas.winfo_height():
            return

        # Cross-platform handling (Windows/Mac use delta, Linux uses num 4 & 5)
        if event.num == 4 or getattr(event, 'delta', 0) > 0:
            self.onboard_canvas.yview_scroll(-1, "units")
        elif event.num == 5 or getattr(event, 'delta', 0) < 0:
            self.onboard_canvas.yview_scroll(1, "units")

    # ==========================================
    # ONBOARDING SCREEN & RECOMMENDATION ALGORITHM
    # ==========================================
    def build_onboarding_ui(self):
        # Outer frame to hold canvas and scrollbar
        self.onboard_outer_frame = tk.Frame(self.root, bg=self.bg_color)
        self.onboard_outer_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Canvas for scrolling
        self.onboard_canvas = tk.Canvas(self.onboard_outer_frame, bg=self.bg_color, highlightthickness=0)
        self.onboard_canvas.pack(side="left", fill="both", expand=True)

        # Scrollbar linked to Canvas
        self.onboard_scrollbar = ttk.Scrollbar(self.onboard_outer_frame, orient="vertical",
                                               command=self.onboard_canvas.yview)
        self.onboard_scrollbar.pack(side="right", fill="y")
        self.onboard_canvas.configure(yscrollcommand=self.onboard_scrollbar.set)

        # The actual frame that contains the UI, placed inside the canvas
        self.onboard_frame = tk.Frame(self.onboard_canvas, bg=self.bg_color)
        self.canvas_window = self.onboard_canvas.create_window((0, 0), window=self.onboard_frame, anchor="nw")

        # Ensure the canvas scrollregion updates when the inner frame changes size
        self.onboard_frame.bind("<Configure>",
                                lambda e: self.onboard_canvas.configure(scrollregion=self.onboard_canvas.bbox("all")))
        # Ensure the inner frame stretches to the canvas width
        self.onboard_canvas.bind('<Configure>',
                                 lambda e: self.onboard_canvas.itemconfig(self.canvas_window, width=e.width))

        # --- Bind the mouse scroll wheel globally while on this screen ---
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self.root.bind_all("<Button-4>", self._on_mousewheel)
        self.root.bind_all("<Button-5>", self._on_mousewheel)

        # --- UI Elements (placed inside self.onboard_frame) ---
        tk.Label(self.onboard_frame, text="Let's find your perfect routine! 🧴", font=("Segoe UI", 18, "bold"),
                 bg=self.bg_color, fg=self.text_color).pack(pady=(0, 10))

        tk.Label(self.onboard_frame, text="Do you have any specific skin conditions?", font=("Segoe UI", 12),
                 bg=self.bg_color, fg=self.text_color).pack()
        self.concern_var = tk.StringVar(value=self.saved_concern)
        concern_dropdown = ttk.Combobox(self.onboard_frame, textvariable=self.concern_var, state="readonly", width=30,
                                        font=("Segoe UI", 11))
        concern_dropdown['values'] = ("None", "Acne & Breakouts", "Eczema / Severe Dryness", "Rosacea / Redness",
                                      "Hyperpigmentation")
        concern_dropdown.pack(pady=(5, 10))

        tk.Label(self.onboard_frame, text="What is your primary skin type?", font=("Segoe UI", 12), bg=self.bg_color,
                 fg=self.text_color).pack()
        self.type_var = tk.StringVar(value=self.saved_type)
        type_dropdown = ttk.Combobox(self.onboard_frame, textvariable=self.type_var, state="readonly", width=30,
                                     font=("Segoe UI", 11))
        type_dropdown['values'] = ("Normal", "Dry", "Oily", "Combination", "Sensitive")
        type_dropdown.pack(pady=(5, 15))

        btn = tk.Button(self.onboard_frame, text="Build My Routine", font=("Segoe UI", 12, "bold"),
                        bg=self.tab_bg, fg=self.tab_text, relief="flat", padx=20, pady=8, cursor="hand2",
                        command=self.show_recommendations)
        btn.pack()

        self.recs_frame = tk.Frame(self.onboard_frame, bg=self.bg_color)
        self.recs_frame.pack(fill="both", expand=True, pady=10)

        # Auto-display if coming "Back" from the catalog
        if self.routine_generated:
            self.show_recommendations()

    def get_best_match(self, category, user_type, user_concern):
        category_prods = [p for p in self.all_products if p[1] == category]
        if not category_prods: return None

        best_match = None
        highest_score = -999

        for prod in category_prods:
            name, cat, suitable_for, price = prod
            score = 0

            # 1. Base Match: Skin Type
            if user_type in suitable_for:
                score += 3
            elif "All" in suitable_for:
                score += 1
            else:
                score -= 3

                # 2. Advanced Match: Skin Concern & Active Ingredients
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

    def show_recommendations(self):
        for widget in self.recs_frame.winfo_children():
            widget.destroy()

        self.routine_generated = True
        self.saved_type = self.type_var.get()
        self.saved_concern = self.concern_var.get()
        user_type = self.saved_type
        user_concern = self.saved_concern

        tk.Label(self.recs_frame, text=f"Curated Routine for {user_type} skin", font=("Segoe UI", 14, "bold"),
                 bg=self.bg_color, fg=self.text_color).pack(pady=(0, 2))
        if user_concern != "None":
            tk.Label(self.recs_frame, text=f"Targeting: {user_concern}", font=("Segoe UI", 11, "italic"),
                     bg=self.bg_color, fg=self.sub_text).pack(pady=(0, 10))

        routine = []

        # Build Products
        cleanser = self.get_best_match("Cleanser", user_type, user_concern)
        if cleanser: routine.append(("Step 1: Cleanser", cleanser))

        has_toner = False
        if user_type in ["Oily", "Combination", "Normal"] or user_concern == "Acne & Breakouts":
            toner = self.get_best_match("Toner", user_type, user_concern)
            if toner:
                routine.append(("Step 2: Toner", toner))
                has_toner = True

        has_exfoliant = False
        if user_concern in ["Acne & Breakouts", "Hyperpigmentation"] and user_concern not in ["Eczema / Severe Dryness",
                                                                                              "Rosacea / Redness"]:
            exfoliant = self.get_best_match("Exfoliant", user_type, user_concern)
            if exfoliant:
                routine.append(("Step 3: Exfoliant (PM)", exfoliant))
                has_exfoliant = True

        serum = self.get_best_match("Serum", user_type, user_concern)
        if serum: routine.append(("Step 4: Serum", serum))

        moisturizer = self.get_best_match("Moisturizer", user_type, user_concern)
        if moisturizer: routine.append(("Step 5: Moisturizer", moisturizer))

        sunscreen = self.get_best_match("Sunscreen", user_type, user_concern)
        if sunscreen: routine.append(("Step 6: Sunscreen (AM)", sunscreen))

        # Render the Product Cards
        for step_name, prod in routine:
            card = tk.Frame(self.recs_frame, bg=self.card_bg, bd=0, highlightbackground=self.border_color,
                            highlightthickness=1)
            card.pack(fill="x", padx=40, pady=2)
            tk.Label(card, text=step_name, font=("Segoe UI", 10, "bold"), bg=self.card_bg, fg=self.sub_text, width=22,
                     anchor="w").pack(side="left", padx=(15, 0), pady=6)
            tk.Label(card, text=f"✨ {prod[0]}", font=("Segoe UI", 11, "bold"), bg=self.card_bg,
                     fg=self.text_color).pack(side="left", padx=5, pady=6)

        # Render the AM / PM Guide
        guide_frame = tk.Frame(self.recs_frame, bg=self.header_bg, bd=0, highlightbackground=self.border_color,
                               highlightthickness=1)
        guide_frame.pack(fill="x", padx=40, pady=(15, 10))

        am_steps = "Cleanser ➔ " + ("Toner ➔ " if has_toner else "") + "Serum ➔ Moisturizer ➔ Sunscreen"
        pm_steps = "Cleanser ➔ " + (
            "Exfoliant (2x/week) ➔ " if has_exfoliant else ("Toner ➔ " if has_toner else "")) + "Serum ➔ Moisturizer"

        tk.Label(guide_frame, text="📖 How to use your routine:", font=("Segoe UI", 11, "bold"), bg=self.header_bg,
                 fg=self.text_color).pack(pady=(8, 2))
        tk.Label(guide_frame, text=f"🌞 AM: {am_steps}", font=("Segoe UI", 10), bg=self.header_bg,
                 fg=self.text_color).pack(pady=2)
        tk.Label(guide_frame, text=f"🌙 PM: {pm_steps}", font=("Segoe UI", 10), bg=self.header_bg,
                 fg=self.text_color).pack(pady=(2, 8))

        continue_btn = tk.Button(self.recs_frame, text="Explore Full Catalog ➡️", font=("Segoe UI", 13, "bold"),
                                 bg=self.accent_bg, fg=self.text_color, relief="ridge", bd=2, padx=25, pady=8,
                                 cursor="hand2", command=self.go_to_main_screen)
        continue_btn.pack(pady=(5, 20))

        # ==========================================

    # NAVIGATION METHODS
    # ==========================================
    def go_to_main_screen(self):
        # Unbind the canvas scroll wheel when leaving the onboarding screen
        self.root.unbind_all("<MouseWheel>")
        self.root.unbind_all("<Button-4>")
        self.root.unbind_all("<Button-5>")

        self.current_screen = "main"
        self.current_filter = self.type_var.get()
        self.apply_theme()

    def go_to_onboarding(self):
        self.current_screen = "onboarding"
        self.apply_theme()

    # ==========================================
    # MAIN CATALOG SCREEN LOGIC
    # ==========================================
    def build_main_ui(self):
        style = ttk.Style()
        style.configure("Treeview", font=("Segoe UI", 10), rowheight=35, background=self.card_bg,
                        fieldbackground=self.card_bg, foreground=self.text_color, borderwidth=0)
        style.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), background=self.header_bg,
                        foreground=self.text_color, relief="flat")
        style.map('Treeview', background=[('selected', self.header_bg)])

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=(15, 5))

        self.tab_skin_types = ttk.Frame(self.notebook)
        self.tab_conditions = ttk.Frame(self.notebook)
        self.tab_products = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_skin_types, text=" 📖 Skin Types Guide ")
        self.notebook.add(self.tab_conditions, text=" 🩺 Skin Conditions ")
        self.notebook.add(self.tab_products, text=" 🛍️ Product Catalog ")

        self.setup_skin_types_tab()
        self.setup_conditions_tab()
        self.setup_products_tab()

    def setup_skin_types_tab(self):
        tk.Label(self.tab_skin_types, text="Identify Your Skin Profile", font=("Segoe UI", 16, "bold"),
                 bg=self.bg_color, fg=self.text_color).pack(pady=(20, 10))
        skin_types = {
            "🌿 Normal": "Well-balanced skin. Not too oily, not too dry. Few imperfections and no severe sensitivity.",
            "💧 Dry": "Produces less sebum. Can feel tight, rough, or look flaky. Needs heavy hydration and ceramides.",
            "✨ Oily": "Produces excess sebum. Prone to enlarged pores and breakouts. Needs lightweight, non-comedogenic care.",
            "🌗 Combination": "Features both oily and dry areas. Usually oily in the T-zone and normal/dry on the cheeks.",
            "🌸 Sensitive": "Easily irritated by products or environmental factors. Prone to redness, itching, and burning."
        }
        for stype, desc in skin_types.items():
            card = tk.Frame(self.tab_skin_types, bg=self.card_bg, bd=0, highlightbackground=self.border_color,
                            highlightthickness=1)
            card.pack(fill="x", padx=30, pady=8)
            tk.Label(card, text=stype, font=("Segoe UI", 13, "bold"), bg=self.card_bg, fg=self.text_color, width=15,
                     anchor="w").pack(side="left", padx=15, pady=15)
            tk.Label(card, text=desc, font=("Segoe UI", 11), bg=self.card_bg, fg=self.sub_text, wraplength=500,
                     justify="left").pack(side="left", padx=10, pady=15)

    def setup_conditions_tab(self):
        tk.Label(self.tab_conditions, text="Common Skin Conditions & Ingredients", font=("Segoe UI", 16, "bold"),
                 bg=self.bg_color, fg=self.text_color).pack(pady=(20, 10))
        conditions = {
            "🔴 Acne & Breakouts": "Caused by clogged pores, bacteria, and excess sebum. \nLook for: Salicylic Acid (BHA), Benzoyl Peroxide, Niacinamide.",
            "🏜️ Eczema / Dryness": "A damaged skin barrier leading to severe flaking, itching, and redness. \nLook for: Ceramides, Colloidal Oatmeal, Hyaluronic Acid, Glycerin.",
            "🔥 Rosacea": "Chronic condition causing redness, visible blood vessels, and sometimes bumps. \nLook for: Azelaic Acid, Centella Asiatica (Cica), Sulfur. Avoid physical scrubs.",
            "🌑 Hyperpigmentation": "Dark patches caused by excess melanin production (sun damage, post-acne marks). \nLook for: Vitamin C, Alpha Arbutin, Tranexamic Acid, Glycolic Acid (AHA)."
        }
        for cond, desc in conditions.items():
            card = tk.Frame(self.tab_conditions, bg=self.card_bg, bd=0, highlightbackground=self.border_color,
                            highlightthickness=1)
            card.pack(fill="x", padx=30, pady=8)
            tk.Label(card, text=cond, font=("Segoe UI", 13, "bold"), bg=self.card_bg, fg=self.text_color, width=22,
                     anchor="w").pack(side="left", padx=15, pady=15)
            tk.Label(card, text=desc, font=("Segoe UI", 11), bg=self.card_bg, fg=self.sub_text, wraplength=450,
                     justify="left").pack(side="left", padx=10, pady=15)

    def setup_products_tab(self):
        search_frame = tk.Frame(self.tab_products, bg=self.bg_color)
        search_frame.pack(fill="x", padx=20, pady=15)

        tk.Label(search_frame, text="🔍 Filter by Skin Type:", font=("Segoe UI", 11, "bold"), bg=self.bg_color,
                 fg=self.text_color).pack(side="left")

        self.filter_var = tk.StringVar(value=self.current_filter)
        filter_dropdown = ttk.Combobox(search_frame, textvariable=self.filter_var, state="readonly", width=15,
                                       font=("Segoe UI", 10))
        filter_dropdown['values'] = ("All", "Normal", "Dry", "Oily", "Combination", "Sensitive", "Acne")
        filter_dropdown.pack(side="left", padx=10)
        filter_dropdown.bind("<<ComboboxSelected>>", self.filter_products)

        tree_frame = tk.Frame(self.tab_products, bg=self.bg_color)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        columns = ("Product Name", "Category", "Suitable For", "Price (₹)")
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.column("Product Name", width=350, anchor="w")

        self.tree.tag_configure('oddrow', background=self.card_bg, foreground=self.text_color)
        self.tree.tag_configure('evenrow', background=self.bg_color, foreground=self.text_color)

        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.filter_products()

    def load_product_data(self, data):
        for row in self.tree.get_children():
            self.tree.delete(row)

        for index, item in enumerate(data):
            if index % 2 == 0:
                self.tree.insert("", "end", values=item, tags=('evenrow',))
            else:
                self.tree.insert("", "end", values=item, tags=('oddrow',))

    def filter_products(self, event=None):
        selected_type = self.filter_var.get()
        if selected_type == "All":
            self.load_product_data(self.all_products)
        else:
            filtered_data = [prod for prod in self.all_products if selected_type in prod[2] or "All" in prod[2]]
            self.load_product_data(filtered_data)


if __name__ == "__main__":
    root = tk.Tk()
    app = SkincareApp(root)
    root.mainloop()
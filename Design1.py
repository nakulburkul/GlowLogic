import tkinter as tk
from tkinter import ttk


class SkincareApp:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ GlowGuide: Premium Skincare Catalog")
        self.root.geometry("850x600")

        # --- Premium Color Palette ---
        self.bg_color = "#FAF7F2"  # Creamy white base
        self.accent_color = "#E8D5C4"  # Soft blush/peach
        self.text_color = "#3E363F"  # Soft dark plum/grey for text
        self.header_bg = "#D4E0D9"  # Muted sage green

        self.root.configure(bg=self.bg_color)

        # --- Custom Styling ---
        style = ttk.Style()
        style.theme_use('clam')

        # Notebook (Tabs) Styling
        style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        style.configure("TNotebook.Tab", font=("Segoe UI", 12, "bold"), padding=[15, 8],
                        background=self.accent_color, foreground=self.text_color)
        style.map("TNotebook.Tab", background=[("selected", self.header_bg)])

        # Frame Styling
        style.configure("TFrame", background=self.bg_color)

        # Treeview (Table) Styling
        style.configure("Treeview",
                        font=("Segoe UI", 10),
                        rowheight=35,
                        background="white",
                        fieldbackground="white",
                        borderwidth=0)
        style.configure("Treeview.Heading",
                        font=("Segoe UI", 11, "bold"),
                        background=self.header_bg,
                        foreground=self.text_color,
                        relief="flat")
        style.map('Treeview', background=[('selected', self.accent_color)])

        # --- App Header ---
        header_frame = tk.Frame(self.root, bg=self.header_bg, pady=15)
        header_frame.pack(fill="x")

        tk.Label(header_frame, text="✨ GlowGuide ✨", font=("Segoe UI", 24, "bold"),
                 bg=self.header_bg, fg=self.text_color).pack()
        tk.Label(header_frame, text="Your personal dermatology & product companion",
                 font=("Segoe UI", 12, "italic"), bg=self.header_bg, fg=self.text_color).pack()

        # --- Notebook (Tabs) ---
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=20, pady=20)

        self.tab_skin_types = ttk.Frame(self.notebook)
        self.tab_products = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_skin_types, text=" 📖 Skin Types Guide ")
        self.notebook.add(self.tab_products, text=" 🛍️ Product Catalog ")

        self.setup_skin_types_tab()
        self.setup_products_tab()

    def setup_skin_types_tab(self):
        # Title
        tk.Label(self.tab_skin_types, text="Identify Your Skin Profile",
                 font=("Segoe UI", 16, "bold"), bg=self.bg_color, fg=self.text_color).pack(pady=(20, 10))

        skin_types = {
            "🌿 Normal": "Well-balanced skin. Not too oily, not too dry. Few imperfections and no severe sensitivity.",
            "💧 Dry": "Produces less sebum. Can feel tight, rough, or look flaky. Needs heavy hydration and ceramides.",
            "✨ Oily": "Produces excess sebum. Prone to enlarged pores and breakouts. Needs lightweight, non-comedogenic care.",
            "🌗 Combination": "Features both oily and dry areas. Usually oily in the T-zone and normal/dry on the cheeks.",
            "🌸 Sensitive": "Easily irritated by products or environmental factors. Prone to redness, itching, and burning."
        }

        # Elegant Cards for Skin Types
        for stype, desc in skin_types.items():
            card = tk.Frame(self.tab_skin_types, bg="white", bd=0, highlightbackground=self.accent_color,
                            highlightthickness=1)
            card.pack(fill="x", padx=30, pady=8)

            tk.Label(card, text=stype, font=("Segoe UI", 13, "bold"), bg="white", fg=self.text_color, width=15,
                     anchor="w").pack(side="left", padx=15, pady=15)
            tk.Label(card, text=desc, font=("Segoe UI", 11), bg="white", fg="#555555", wraplength=500,
                     justify="left").pack(side="left", padx=10, pady=15)

    def setup_products_tab(self):
        # Search/Filter Bar
        search_frame = tk.Frame(self.tab_products, bg=self.bg_color)
        search_frame.pack(fill="x", padx=20, pady=15)

        tk.Label(search_frame, text="🔍 Filter by Skin Type:", font=("Segoe UI", 11, "bold"), bg=self.bg_color,
                 fg=self.text_color).pack(side="left")

        self.filter_var = tk.StringVar(value="All")
        filter_dropdown = ttk.Combobox(search_frame, textvariable=self.filter_var, state="readonly", width=15,
                                       font=("Segoe UI", 10))
        filter_dropdown['values'] = ("All", "Normal", "Dry", "Oily", "Combination", "Sensitive")
        filter_dropdown.pack(side="left", padx=10)
        filter_dropdown.bind("<<ComboboxSelected>>", self.filter_products)

        # Treeview Configuration
        columns = ("Product Name", "Category", "Suitable For", "Price (₹)")
        self.tree = ttk.Treeview(self.tab_products, columns=columns, show="headings")

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150, anchor="center")
        self.tree.column("Product Name", width=250, anchor="w")

        # Adding striped rows colors
        self.tree.tag_configure('oddrow', background="white")
        self.tree.tag_configure('evenrow', background=self.bg_color)

        # Treeview Layout
        tree_frame = tk.Frame(self.tab_products)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # Dummy Database (Rupees)
        self.all_products = [
            ("CeraVe Hydrating Cleanser", "Cleanser", "Dry, Normal", "₹ 1,327"),
            ("La Roche-Posay Effaclar", "Cleanser", "Oily, Combination", "₹ 1,410"),
            ("Paula's Choice 2% BHA", "Exfoliant", "Oily, Combination", "₹ 2,822"),
            ("Neutrogena Hydro Boost", "Moisturizer", "Dry, Normal", "₹ 1,659"),
            ("Vanicream Daily Moisturizer", "Moisturizer", "Sensitive, Dry", "₹ 1,120"),
            ("The Ordinary Niacinamide 10%", "Serum", "Oily, All", "₹ 498"),
            ("EltaMD UV Clear SPF 46", "Sunscreen", "Sensitive, Oily", "₹ 3,237"),
            ("COSRX Snail Mucin 96", "Essence", "Dry, Sensitive", "₹ 2,075"),
            ("Cetaphil Gentle Cleanser", "Cleanser", "All", "₹ 953"),
        ]

        self.load_product_data(self.all_products)

    def load_product_data(self, data):
        # Clear existing data
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Insert new data with alternating row colors
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
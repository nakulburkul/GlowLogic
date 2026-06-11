import tkinter as tk
from tkinter import ttk


class SkincareApp:
    def __init__(self, root):
        self.root, self.screen, self.filter = root, "onboarding", "All"
        self.root.title("✨ GlowGuide: Premium Skincare Catalog")
        self.root.geometry("950x850")
        self.routine_gen, self.s_type, self.s_conc = False, "Normal", "None"

        self.db = [
            ("Cetaphil Gentle Skin Cleanser (125ml)", "Cleanser", "All, Sensitive", "₹ 333"),
            ("CeraVe Hydrating Cleanser (236ml)", "Cleanser", "Dry, Normal", "₹ 990"),
            ("Minimalist 2% Salicylic Acid Face Wash", "Cleanser", "Oily, Acne", "₹ 299"),
            ("Plum Green Tea Pore Cleansing Face Wash", "Cleanser", "Oily, Combination", "₹ 345"),
            ("Bioderma Sensibio Gel Moussant (200ml)", "Cleanser", "Sensitive, All", "₹ 1,079"),
            ("Himalaya Purifying Neem Face Wash (150ml)", "Cleanser", "Oily, Acne", "₹ 180"),
            ("Simple Kind to Skin Refreshing Face Wash", "Cleanser", "All, Sensitive", "₹ 325"),
            ("La Roche-Posay Effaclar Purifying Foaming Gel", "Cleanser", "Oily, Combination", "₹ 2,999"),
            ("Neutrogena Hydro Boost Water Gel (50g)", "Moisturizer", "All, Oily", "₹ 1,050"),
            ("Pond's Super Light Gel Oil Free", "Moisturizer", "Oily, Combination", "₹ 200"),
            ("CeraVe Moisturizing Cream (50g)", "Moisturizer", "Dry, Normal", "₹ 550"),
            ("Emolene Cream (100g)", "Moisturizer", "Dry, Sensitive", "₹ 350"),
            ("Dot & Key Ceramide & Hyaluronic Face Cream", "Moisturizer", "Dry, Normal", "₹ 395"),
            ("Re'equil Oil Free Moisturiser", "Moisturizer", "Oily, Acne", "₹ 350"),
            ("Sebamed Clear Face Care Gel (50g)", "Moisturizer", "Oily, Sensitive", "₹ 476"),
            ("Bioderma Atoderm Intensive Baume (75ml)", "Moisturizer", "Dry, Sensitive", "₹ 1,199"),
            ("Vanicream Daily Facial Moisturizer", "Moisturizer", "Sensitive, Dry", "₹ 1,120"),
            ("Aqualogica Radiance+ Dewy Sunscreen", "Sunscreen", "All", "₹ 399"),
            ("The Derma Co 1% Hyaluronic Sunscreen", "Sunscreen", "All", "₹ 499"),
            ("Minimalist Sunscreen SPF 50 PA++++", "Sunscreen", "All", "₹ 399"),
            ("Re'equil Ultra Matte Dry Touch Sunscreen", "Sunscreen", "Oily, Combination", "₹ 695"),
            ("Neutrogena Ultra Sheer Dry-Touch SPF 50+", "Sunscreen", "All", "₹ 260"),
            ("UV Doux Silicone Sunscreen Gel", "Sunscreen", "Oily, Acne", "₹ 650"),
            ("EltaMD UV Clear SPF 46 (48g)", "Sunscreen", "Sensitive, Oily", "₹ 6,289"),
            ("Blynds Emulgel SPF 40+ (50g)", "Sunscreen", "All, Sensitive", "₹ 445"),
            ("The Ordinary Niacinamide 10% + Zinc 1%", "Serum", "Oily, All", "₹ 550"),
            ("Minimalist 10% Vitamin C Face Serum", "Serum", "All", "₹ 699"),
            ("Plum 15% Vitamin C Face Serum", "Serum", "All", "₹ 550"),
            ("The Derma Co 2% Salicylic Acid Face Serum", "Serum", "Oily, Acne", "₹ 499"),
            ("L'Oreal Paris Revitalift Hyaluronic Acid", "Serum", "All", "₹ 499"),
            ("COSRX The Vitamin C 23 Serum", "Serum", "All", "₹ 1,200"),
            ("Estee Lauder Advanced Night Repair (30ml)", "Serum", "All", "₹ 6,500"),
            ("Paula's Choice 2% BHA Liquid Exfoliant (30ml)", "Exfoliant", "Oily, Combination", "₹ 1,200"),
            ("Minimalist 8% Glycolic Acid Toner", "Toner", "Normal, Oily", "₹ 499"),
            ("Pixi Glow Tonic (100ml)", "Toner", "All", "₹ 1,400"),
            ("The Ordinary AHA 30% + BHA 2% Peeling Solution", "Exfoliant", "All", "₹ 950"),
            ("COSRX AHA/BHA Clarifying Treatment Toner", "Toner", "Oily, Acne", "₹ 1,090"),
            ("COSRX Advanced Snail 96 Mucin Power Essence", "Essence", "Dry, Sensitive", "₹ 999"),
            ("Laneige Lip Sleeping Mask (20g)", "Treatment", "All", "₹ 1,300"),
            ("Sebamed Clear Face Anti-Pimple Gel", "Treatment", "Acne", "₹ 450"),
            ("Mario Badescu Drying Lotion", "Treatment", "Acne", "₹ 1,650")
        ]
        self.apply_theme()

    def add_lbl(self, p, t, f=("Segoe UI", 11), bg=None, fg=None, **k):
        pk = k.pop('pack', {});
        lbl = tk.Label(p, text=t, font=f, bg=bg or self.bg, fg=fg or self.fg, **k)
        lbl.pack(**pk);
        return lbl

    def add_frm(self, p, bg=None, **k):
        pk = k.pop('pack', {});
        frm = tk.Frame(p, bg=bg or self.bg, **k);
        frm.pack(**pk);
        return frm

    def apply_theme(self):
        self.bg, self.fg = "#FAF7F2", "#3E363F"
        self.hdr, self.crd = "#D4E0D9", "#FFFFFF"
        self.tab, self.acc = "#E8D5C4", "#C6D5CB"
        self.sub, self.brd = "#555555", "#E8D5C4"
        self.root.configure(bg=self.bg)
        for w in self.root.winfo_children(): w.destroy()

        s = ttk.Style();
        s.theme_use('clam');
        s.configure("TNotebook", background=self.bg, borderwidth=0)
        s.configure("TNotebook.Tab", font=("Segoe UI", 12, "bold"), padding=[15, 8], background=self.tab,
                    foreground=self.fg)
        s.map("TNotebook.Tab", background=[("selected", self.hdr)], foreground=[("selected", self.fg)])
        s.configure("Treeview", font=("Segoe UI", 10), rowheight=35, background=self.crd, fieldbackground=self.crd,
                    foreground=self.fg)
        s.configure("Treeview.Heading", font=("Segoe UI", 11, "bold"), background=self.hdr, foreground=self.fg)

        h = self.add_frm(self.root, bg=self.hdr, pack={'fill': 'x', 'side': 'top'}, pady=15)
        if self.screen == "main": tk.Button(h, text="🔙 My Routine", command=lambda: self.nav("onboarding"), bg=self.bg,
                                            fg=self.fg, relief="flat", font=("Segoe UI", 10, "bold")).pack(side="left",
                                                                                                           padx=20)
        self.add_lbl(h, "✨ GlowGuide ✨", ("Segoe UI", 24, "bold"), bg=self.hdr)
        self.add_lbl(h, "Your personal dermatology companion", ("Segoe UI", 12, "italic"), bg=self.hdr)

        self.build_onboard() if self.screen == "onboarding" else self.build_main()
        self.add_lbl(self.root, "© 2026 GlowGuide.", ("Segoe UI", 9), fg=self.sub, pack={'side': 'bottom', 'pady': 5})

    def scroll(self, e):
        if self.screen == "onboarding" and self.cvs.bbox("all")[3] > self.cvs.winfo_height():
            self.cvs.yview_scroll(-1 if e.num == 4 or getattr(e, 'delta', 0) > 0 else 1, "units")

    def build_onboard(self):
        out = self.add_frm(self.root, pack={'fill': 'both', 'expand': True, 'padx': 20, 'pady': 10})
        self.cvs = tk.Canvas(out, bg=self.bg, highlightthickness=0);
        sb = ttk.Scrollbar(out, orient="vertical", command=self.cvs.yview)
        self.cvs.configure(yscrollcommand=sb.set);
        sb.pack(side="right", fill="y");
        self.cvs.pack(side="left", fill="both", expand=True)
        self.frm = tk.Frame(self.cvs, bg=self.bg);
        win = self.cvs.create_window((0, 0), window=self.frm, anchor="nw")
        self.frm.bind("<Configure>", lambda e: self.cvs.configure(scrollregion=self.cvs.bbox("all")))
        self.cvs.bind("<Configure>", lambda e: self.cvs.itemconfig(win, width=e.width))
        for ev in ["<MouseWheel>", "<Button-4>", "<Button-5>"]: self.root.bind_all(ev, self.scroll)

        self.add_lbl(self.frm, "Let's find your perfect routine! 🧴", ("Segoe UI", 18, "bold"), pack={'pady': 10})
        self.add_lbl(self.frm, "Any specific skin conditions?");
        self.v_conc = tk.StringVar(value=self.s_conc)
        ttk.Combobox(self.frm, textvariable=self.v_conc,
                     values=("None", "Acne & Breakouts", "Eczema / Severe Dryness", "Rosacea / Redness",
                             "Hyperpigmentation"), state="readonly", width=30).pack(pady=5)
        self.add_lbl(self.frm, "Primary skin type?");
        self.v_type = tk.StringVar(value=self.s_type)
        ttk.Combobox(self.frm, textvariable=self.v_type, values=("Normal", "Dry", "Oily", "Combination", "Sensitive"),
                     state="readonly", width=30).pack(pady=5)
        tk.Button(self.frm, text="Build My Routine", bg=self.tab, fg=self.fg, font=("Segoe UI", 12, "bold"),
                  command=self.gen_recs).pack(pady=10)
        self.rec_frm = self.add_frm(self.frm, pack={'fill': 'both', 'expand': True, 'pady': 10})
        if self.routine_gen: self.gen_recs()

    def get_match(self, cat, t, c):
        prods = [p for p in self.db if p[1] == cat];
        best, max_s = None, -999
        if not prods: return None
        for p in prods:
            s = 3 if t in p[2] else (1 if "All" in p[2] else -3)
            if c == "Acne & Breakouts":
                s += 4 if "Acne" in p[2] or any(x in p[0] for x in ["Salicylic", "BHA"]) else 0
            elif c == "Eczema / Severe Dryness":
                s += 4 if "Dry" in p[2] or any(x in p[0] for x in ["Ceramide", "Baume"]) else (
                    -5 if any(x in p[0] for x in ["Glycolic", "BHA"]) else 0)
            elif c == "Rosacea / Redness":
                s += 4 if "Sensitive" in p[2] or any(x in p[0] for x in ["Sensibio", "Snail"]) else (
                    -5 if "Acid" in p[0] and "Hyaluronic" not in p[0] else 0)
            elif c == "Hyperpigmentation":
                s += 4 if any(x in p[0] for x in ["Vitamin C", "Glycolic", "Niacinamide"]) else 0
            if s > max_s: max_s, best = s, p
        return best if max_s >= 0 else next((p for p in prods if "All" in p[2]), prods[0])

    def gen_recs(self):
        for w in self.rec_frm.winfo_children(): w.destroy()
        self.routine_gen, t, c = True, self.v_type.get(), self.v_conc.get()
        self.s_type, self.s_conc = t, c
        self.add_lbl(self.rec_frm, f"Curated Routine for {t} skin", ("Segoe UI", 14, "bold"))
        if c != "None": self.add_lbl(self.rec_frm, f"Targeting: {c}", ("Segoe UI", 11, "italic"), fg=self.sub,
                                     pack={'pady': (0, 10)})

        steps = [("Step 1: Cleanser", self.get_match("Cleanser", t, c))]
        if t in ["Oily", "Combination", "Normal"] or c == "Acne & Breakouts": steps.append(
            ("Step 2: Toner", self.get_match("Toner", t, c)))
        if c in ["Acne & Breakouts", "Hyperpigmentation"] and c not in ["Eczema / Severe Dryness",
                                                                        "Rosacea / Redness"]: steps.append(
            ("Step 3: Exfoliant", self.get_match("Exfoliant", t, c)))
        steps += [("Step 4: Serum", self.get_match("Serum", t, c)),
                  ("Step 5: Moisturizer", self.get_match("Moisturizer", t, c)),
                  ("Step 6: Sunscreen", self.get_match("Sunscreen", t, c))]

        for name, prod in filter(lambda x: x[1], steps):
            crd = self.add_frm(self.rec_frm, bg=self.crd, highlightbackground=self.brd, highlightthickness=1,
                               pack={'fill': 'x', 'padx': 40, 'pady': 2})
            self.add_lbl(crd, name, ("Segoe UI", 10, "bold"), bg=self.crd, fg=self.sub, width=22, anchor="w",
                         pack={'side': 'left', 'padx': 15, 'pady': 6})
            self.add_lbl(crd, f"✨ {prod[0]}", ("Segoe UI", 11, "bold"), bg=self.crd, pack={'side': 'left'})

        g = self.add_frm(self.rec_frm, bg=self.hdr, highlightbackground=self.brd, highlightthickness=1,
                         pack={'fill': 'x', 'padx': 40, 'pady': 15})
        self.add_lbl(g, "📖 How to use your routine:", ("Segoe UI", 11, "bold"), bg=self.hdr, pack={'pady': 5})
        self.add_lbl(g, "🌞 AM: Cleanser ➔ Toner ➔ Serum ➔ Moisturizer ➔ Sunscreen", ("Segoe UI", 10), bg=self.hdr)
        self.add_lbl(g, "🌙 PM: Cleanser ➔ Exfoliant/Toner ➔ Serum ➔ Moisturizer", ("Segoe UI", 10), bg=self.hdr,
                     pack={'pady': (0, 8)})
        tk.Button(self.rec_frm, text="Explore Catalog ➡️", font=("Segoe UI", 13, "bold"), bg=self.acc, fg=self.fg, bd=2,
                  command=lambda: self.nav("main")).pack(pady=10)

    def build_main(self):
        nb = ttk.Notebook(self.root);
        nb.pack(fill='both', expand=True, padx=20, pady=15)
        tabs = {"📖 Skin Types": ttk.Frame(nb), "🩺 Conditions": ttk.Frame(nb), "🛍️ Catalog": ttk.Frame(nb)}
        for name, frm in tabs.items(): nb.add(frm, text=f" {name} ")

        guides = {
            tabs["📖 Skin Types"]: {
                "🌿 Normal": "Well-balanced skin. Not too oily, not too dry. Few imperfections and no severe sensitivity.",
                "💧 Dry": "Produces less sebum. Can feel tight, rough, or look flaky. Needs heavy hydration and ceramides.",
                "✨ Oily": "Produces excess sebum. Prone to enlarged pores and breakouts. Needs lightweight, non-comedogenic care.",
                "🌗 Combination": "Features both oily and dry areas. Usually oily in the T-zone and normal/dry on the cheeks.",
                "🌸 Sensitive": "Easily irritated by products or environmental factors. Prone to redness, itching, and burning."
            },
            tabs["🩺 Conditions"]: {
                "🔴 Acne & Breakouts": "Caused by clogged pores, bacteria, and excess sebum. \nLook for: Salicylic Acid (BHA), Benzoyl Peroxide, Niacinamide.",
                "🏜️ Eczema / Dryness": "A damaged skin barrier leading to severe flaking, itching, and redness. \nLook for: Ceramides, Colloidal Oatmeal, Hyaluronic Acid, Glycerin.",
                "🔥 Rosacea": "Chronic condition causing redness, visible blood vessels, and sometimes bumps. \nLook for: Azelaic Acid, Centella Asiatica (Cica), Sulfur. Avoid physical scrubs.",
                "🌑 Hyperpigmentation": "Dark patches caused by excess melanin production (sun damage, post-acne marks). \nLook for: Vitamin C, Alpha Arbutin, Tranexamic Acid, Glycolic Acid (AHA)."
            }
        }
        for tab, data in guides.items():
            self.add_lbl(tab, "Guide", ("Segoe UI", 16, "bold"), pack={'pady': 15})
            for k, v in data.items():
                crd = self.add_frm(tab, bg=self.crd, highlightbackground=self.brd, highlightthickness=1,
                                   pack={'fill': 'x', 'padx': 30, 'pady': 8})
                self.add_lbl(crd, k, ("Segoe UI", 13, "bold"), bg=self.crd, width=22, anchor="w",
                             pack={'side': 'left', 'padx': 15, 'pady': 15})
                self.add_lbl(crd, v, ("Segoe UI", 11), bg=self.crd, fg=self.sub, wraplength=500, justify="left",
                             pack={'side': 'left', 'padx': 10, 'pady': 15})

        top = self.add_frm(tabs["🛍️ Catalog"], pack={'fill': 'x', 'padx': 20, 'pady': 15})
        self.add_lbl(top, "🔍 Filter:", ("Segoe UI", 11, "bold"), pack={'side': 'left'})
        self.v_filt = tk.StringVar(value=self.filter)
        cb = ttk.Combobox(top, textvariable=self.v_filt,
                          values=("All", "Normal", "Dry", "Oily", "Combination", "Sensitive", "Acne"), state="readonly")
        cb.pack(side="left", padx=10);
        cb.bind("<<ComboboxSelected>>", self.do_filter)

        tf = self.add_frm(tabs["🛍️ Catalog"], pack={'fill': 'both', 'expand': True, 'padx': 20, 'pady': 20})
        cols = ("Name", "Category", "Suitable For", "Price")
        self.tree = ttk.Treeview(tf, columns=cols, show="headings")
        for c in cols: self.tree.heading(c, text=c); self.tree.column(c, width=350 if c == "Name" else 150)
        self.tree.tag_configure('odd', background=self.crd);
        self.tree.tag_configure('even', background=self.bg)

        sb = ttk.Scrollbar(tf, orient="vertical", command=self.tree.yview)
        sb.pack(side="right", fill="y");
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.configure(yscrollcommand=sb.set);
        self.do_filter()

    def do_filter(self, e=None):
        f = self.v_filt.get();
        self.filter = f
        self.tree.delete(*self.tree.get_children())
        for i, p in enumerate([p for p in self.db if f == "All" or f in p[2]]):
            self.tree.insert("", "end", values=p, tags=('even' if i % 2 == 0 else 'odd',))

    def nav(self, s):
        for ev in ["<MouseWheel>", "<Button-4>", "<Button-5>"]: self.root.unbind_all(ev)
        self.screen = s;
        self.apply_theme()


if __name__ == "__main__":
    root = tk.Tk()
    app = SkincareApp(root)
    root.mainloop()
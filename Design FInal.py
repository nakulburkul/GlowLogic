import tkinter as tk
from tkinter import ttk

class SkincareApp:
    def __init__(self, R):
        self.R, self.scr, self.f, self.t, self.c = R, "ob", "All", "Normal", "None"
        R.title("✨ GlowGuide: Premium Skincare Catalog"); R.geometry("950x850")
        self.db = [
            ("Cetaphil Gentle Skin Cleanser (125ml)","Cleanser","All, Sensitive","₹ 333"), ("CeraVe Hydrating Cleanser (236ml)","Cleanser","Dry, Normal","₹ 990"),
            ("Minimalist 2% Salicylic Acid Face Wash","Cleanser","Oily, Acne","₹ 299"), ("Plum Green Tea Pore Cleansing Face Wash","Cleanser","Oily, Combination","₹ 345"),
            ("Bioderma Sensibio Gel Moussant (200ml)","Cleanser","Sensitive, All","₹ 1,079"), ("Himalaya Purifying Neem Face Wash (150ml)","Cleanser","Oily, Acne","₹ 180"),
            ("Simple Kind to Skin Refreshing Face Wash","Cleanser","All, Sensitive","₹ 325"), ("La Roche-Posay Effaclar Purifying Foaming Gel","Cleanser","Oily, Combination","₹ 2,999"),
            ("Neutrogena Hydro Boost Water Gel (50g)","Moisturizer","All, Oily","₹ 1,050"), ("Pond's Super Light Gel Oil Free","Moisturizer","Oily, Combination","₹ 200"),
            ("CeraVe Moisturizing Cream (50g)","Moisturizer","Dry, Normal","₹ 550"), ("Emolene Cream (100g)","Moisturizer","Dry, Sensitive","₹ 350"),
            ("Dot & Key Ceramide & Hyaluronic Face Cream","Moisturizer","Dry, Normal","₹ 395"), ("Re'equil Oil Free Moisturiser","Moisturizer","Oily, Acne","₹ 350"),
            ("Sebamed Clear Face Care Gel (50g)","Moisturizer","Oily, Sensitive","₹ 476"), ("Bioderma Atoderm Intensive Baume (75ml)","Moisturizer","Dry, Sensitive","₹ 1,199"),
            ("Vanicream Daily Facial Moisturizer","Moisturizer","Sensitive, Dry","₹ 1,120"), ("Aqualogica Radiance+ Dewy Sunscreen","Sunscreen","All","₹ 399"),
            ("The Derma Co 1% Hyaluronic Sunscreen","Sunscreen","All","₹ 499"), ("Minimalist Sunscreen SPF 50 PA++++","Sunscreen","All","₹ 399"),
            ("Re'equil Ultra Matte Dry Touch Sunscreen","Sunscreen","Oily, Combination","₹ 695"), ("Neutrogena Ultra Sheer Dry-Touch SPF 50+","Sunscreen","All","₹ 260"),
            ("UV Doux Silicone Sunscreen Gel","Sunscreen","Oily, Acne","₹ 650"), ("EltaMD UV Clear SPF 46 (48g)","Sunscreen","Sensitive, Oily","₹ 6,289"),
            ("Blynds Emulgel SPF 40+ (50g)","Sunscreen","All, Sensitive","₹ 445"), ("The Ordinary Niacinamide 10% + Zinc 1%","Serum","Oily, All","₹ 550"),
            ("Minimalist 10% Vitamin C Face Serum","Serum","All","₹ 699"), ("Plum 15% Vitamin C Face Serum","Serum","All","₹ 550"),
            ("The Derma Co 2% Salicylic Acid Face Serum","Serum","Oily, Acne","₹ 499"), ("L'Oreal Paris Revitalift Hyaluronic Acid","Serum","All","₹ 499"),
            ("COSRX The Vitamin C 23 Serum","Serum","All","₹ 1,200"), ("Estee Lauder Advanced Night Repair (30ml)","Serum","All","₹ 6,500"),
            ("Paula's Choice 2% BHA Liquid Exfoliant (30ml)","Exfoliant","Oily, Combination","₹ 1,200"), ("Minimalist 8% Glycolic Acid Toner","Toner","Normal, Oily","₹ 499"),
            ("Pixi Glow Tonic (100ml)","Toner","All","₹ 1,400"), ("The Ordinary AHA 30% + BHA 2% Peeling Solution","Exfoliant","All","₹ 950"),
            ("COSRX AHA/BHA Clarifying Treatment Toner","Toner","Oily, Acne","₹ 1,090"), ("COSRX Advanced Snail 96 Mucin Power Essence","Essence","Dry, Sensitive","₹ 999"),
            ("Laneige Lip Sleeping Mask (20g)","Treatment","All","₹ 1,300"), ("Sebamed Clear Face Anti-Pimple Gel","Treatment","Acne","₹ 450"),
            ("Mario Badescu Drying Lotion","Treatment","Acne","₹ 1,650")
        ]
        self.draw()

    def L(self, P, t, f=("Segoe UI",11), b="#FAF7F2", c="#3E363F", pk={}, **k):
        l=tk.Label(P, text=t, font=f, bg=b, fg=c, **k); l.pack(**pk); return l

    def F(self, P, b="#FAF7F2", pk={}, **k):
        f=tk.Frame(P, bg=b, **k); f.pack(**pk); return f

    def draw(self):
        for w in self.R.winfo_children(): w.destroy()
        self.R.configure(bg="#FAF7F2")
        s=ttk.Style(); s.theme_use('clam'); s.configure("TNotebook", background="#FAF7F2", borderwidth=0)
        s.configure("TNotebook.Tab", font=("Segoe UI",12,"bold"), padding=[15,8], background="#E8D5C4", foreground="#3E363F")
        s.map("TNotebook.Tab", background=[("selected","#D4E0D9")])
        s.configure("Treeview", font=("Segoe UI",10), rowheight=35, background="#FFF", fieldbackground="#FFF", foreground="#3E363F")
        s.configure("Treeview.Heading", font=("Segoe UI",11,"bold"), background="#D4E0D9", foreground="#3E363F")

        h=self.F(self.R, "#D4E0D9", {'fill':'x','side':'top'}, pady=15)
        if self.scr=="main": tk.Button(h, text="🔙 My Routine", command=lambda: self.nav("ob"), bg="#FAF7F2", fg="#3E363F", relief="flat", font=("Segoe UI",10,"bold")).pack(side="left", padx=20)
        self.L(h, "✨ GlowGuide ✨", ("Segoe UI",24,"bold"), "#D4E0D9")
        self.L(h, "Your personal dermatology companion", ("Segoe UI",12,"italic"), "#D4E0D9")
        self.build_ob() if self.scr=="ob" else self.build_main()
        self.L(self.R, "© 2026 GlowGuide.", ("Segoe UI",9), c="#555", pk={'side':'bottom','pady':5})

    def scroll(self, e):
        if self.scr=="ob" and self.cv.bbox("all")[3]>self.cv.winfo_height(): self.cv.yview_scroll(-1 if e.num==4 or getattr(e,'delta',0)>0 else 1, "units")

    def build_ob(self):
        o=self.F(self.R, pk={'fill':'both','expand':True,'padx':20,'pady':10})
        self.cv=tk.Canvas(o, bg="#FAF7F2", highlightthickness=0); sb=ttk.Scrollbar(o, command=self.cv.yview)
        self.cv.configure(yscrollcommand=sb.set); sb.pack(side="right", fill="y"); self.cv.pack(side="left", fill="both", expand=True)
        frm=tk.Frame(self.cv, bg="#FAF7F2"); win=self.cv.create_window((0,0), window=frm, anchor="nw")
        frm.bind("<Configure>", lambda e: self.cv.configure(scrollregion=self.cv.bbox("all")))
        self.cv.bind("<Configure>", lambda e: self.cv.itemconfig(win, width=e.width))
        for e in ["<MouseWheel>","<Button-4>","<Button-5>"]: self.R.bind_all(e, self.scroll)

        self.L(frm, "Let's find your perfect routine! 🧴", ("Segoe UI",18,"bold"), pk={'pady':10})
        self.L(frm, "Any specific skin conditions?"); self.vc=tk.StringVar(value=self.c)
        ttk.Combobox(frm, textvariable=self.vc, values=("None","Acne & Breakouts","Eczema / Severe Dryness","Rosacea / Redness","Hyperpigmentation"), state="readonly", width=30).pack(pady=5)
        self.L(frm, "Primary skin type?"); self.vt=tk.StringVar(value=self.t)
        ttk.Combobox(frm, textvariable=self.vt, values=("Normal","Dry","Oily","Combination","Sensitive"), state="readonly", width=30).pack(pady=5)
        tk.Button(frm, text="Build My Routine", bg="#E8D5C4", fg="#3E363F", font=("Segoe UI",12,"bold"), command=self.gen).pack(pady=10)
        self.rf = self.F(frm, pk={'fill':'both','expand':True,'pady':10})
        if hasattr(self, 'rg') and self.rg: self.gen()

    def match(self, cat, t, c):
        P=[p for p in self.db if p[1]==cat]; b, ms = None, -99
        if not P: return None
        for p in P:
            s = 3 if t in p[2] else (1 if "All" in p[2] else -3)
            a = p[0]
            if c=="Acne & Breakouts": s += 4 if "Acne" in p[2] or "Salicylic" in a or "BHA" in a else 0
            elif c=="Eczema / Severe Dryness": s += 4 if "Dry" in p[2] or "Ceramide" in a or "Baume" in a else (-5 if "Glycolic" in a or "BHA" in a else 0)
            elif c=="Rosacea / Redness": s += 4 if "Sensitive" in p[2] or "Sensibio" in a or "Snail" in a else (-5 if "Acid" in a and "Hyaluronic" not in a else 0)
            elif c=="Hyperpigmentation": s += 4 if "Vitamin C" in a or "Glycolic" in a or "Niacinamide" in a else 0
            if s>ms: ms, b = s, p
        return b if ms>=0 else next((p for p in P if "All" in p[2]), P[0])

    def gen(self):
        for w in self.rf.winfo_children(): w.destroy()
        self.rg, self.t, self.c = True, self.vt.get(), self.vc.get()
        t, c = self.t, self.c
        self.L(self.rf, f"Curated Routine for {t} skin", ("Segoe UI",14,"bold"))
        if c!="None": self.L(self.rf, f"Targeting: {c}", ("Segoe UI",11,"italic"), c="#555", pk={'pady':(0,10)})

        S = [("Step 1: Cleanser", self.match("Cleanser",t,c))]
        if t in ["Oily","Combination","Normal"] or c=="Acne & Breakouts": S.append(("Step 2: Toner", self.match("Toner",t,c)))
        if c in ["Acne & Breakouts","Hyperpigmentation"] and c not in ["Eczema / Severe Dryness","Rosacea / Redness"]: S.append(("Step 3: Exfoliant", self.match("Exfoliant",t,c)))
        S += [("Step 4: Serum", self.match("Serum",t,c)), ("Step 5: Moisturizer", self.match("Moisturizer",t,c)), ("Step 6: Sunscreen", self.match("Sunscreen",t,c))]

        for n, p in filter(lambda x: x[1], S):
            crd = self.F(self.rf, "#FFF", highlightbackground="#E8D5C4", highlightthickness=1, pk={'fill':'x','padx':40,'pady':2})
            self.L(crd, n, ("Segoe UI",10,"bold"), "#FFF", "#555", pk={'side':'left','padx':15,'pady':6}, width=22, anchor="w")
            self.L(crd, f"✨ {p[0]}", ("Segoe UI",11,"bold"), "#FFF", pk={'side':'left'})

        g = self.F(self.rf, "#D4E0D9", highlightbackground="#E8D5C4", highlightthickness=1, pk={'fill':'x','padx':40,'pady':15})
        self.L(g, "📖 How to use:", ("Segoe UI",11,"bold"), "#D4E0D9", pk={'pady':5})
        self.L(g, "🌞 AM: Cleanser ➔ Toner ➔ Serum ➔ Moisturizer ➔ Sunscreen\n🌙 PM: Cleanser ➔ Exfoliant/Toner ➔ Serum ➔ Moisturizer", ("Segoe UI",10), "#D4E0D9", pk={'pady':(0,8)})
        tk.Button(self.rf, text="Explore Catalog ➡️", font=("Segoe UI",13,"bold"), bg="#C6D5CB", fg="#3E363F", bd=2, command=lambda: self.nav("main")).pack(pady=10)

    def build_main(self):
        nb=ttk.Notebook(self.R); nb.pack(fill='both', expand=True, padx=20, pady=15)
        T={"📖 Skin Types":ttk.Frame(nb), "🩺 Conditions":ttk.Frame(nb), "🛍️ Catalog":ttk.Frame(nb)}
        for n, f in T.items(): nb.add(f, text=f" {n} ")

        G = {
            T["📖 Skin Types"]: {"🌿 Normal":"Well-balanced skin. Not too oily, not too dry. Few imperfections and no severe sensitivity.", "💧 Dry":"Produces less sebum. Can feel tight, rough, or look flaky. Needs heavy hydration and ceramides.", "✨ Oily":"Produces excess sebum. Prone to enlarged pores and breakouts. Needs lightweight, non-comedogenic care.", "🌗 Combination":"Features both oily and dry areas. Usually oily in the T-zone and normal/dry on the cheeks.", "🌸 Sensitive":"Easily irritated by products or environmental factors. Prone to redness, itching, and burning."},
            T["🩺 Conditions"]: {"🔴 Acne & Breakouts":"Caused by clogged pores, bacteria, and excess sebum. \nLook for: Salicylic Acid (BHA), Benzoyl Peroxide, Niacinamide.", "🏜️ Eczema / Dryness":"A damaged skin barrier leading to severe flaking, itching, and redness. \nLook for: Ceramides, Colloidal Oatmeal, Hyaluronic Acid, Glycerin.", "🔥 Rosacea":"Chronic condition causing redness, visible blood vessels, and sometimes bumps. \nLook for: Azelaic Acid, Centella Asiatica (Cica), Sulfur. Avoid physical scrubs.", "🌑 Hyperpigmentation":"Dark patches caused by excess melanin production (sun damage, post-acne marks). \nLook for: Vitamin C, Alpha Arbutin, Tranexamic Acid, Glycolic Acid (AHA)."}
        }
        for t, d in G.items():
            self.L(t, "Guide", ("Segoe UI",16,"bold"), pk={'pady':15})
            for k, v in d.items():
                c = self.F(t, "#FFF", highlightbackground="#E8D5C4", highlightthickness=1, pk={'fill':'x','padx':30,'pady':8})
                self.L(c, k, ("Segoe UI",13,"bold"), "#FFF", pk={'side':'left','padx':15,'pady':15}, width=22, anchor="w")
                self.L(c, v, ("Segoe UI",11), "#FFF", "#555", pk={'side':'left','padx':10,'pady':15}, wraplength=500, justify="left")

        top=self.F(T["🛍️ Catalog"], pk={'fill':'x','padx':20,'pady':15})
        self.L(top, "🔍 Filter:", ("Segoe UI",11,"bold"), pk={'side':'left'})
        self.vf=tk.StringVar(value=self.f); cb=ttk.Combobox(top, textvariable=self.vf, values=("All","Normal","Dry","Oily","Combination","Sensitive","Acne"), state="readonly")
        cb.pack(side="left", padx=10); cb.bind("<<ComboboxSelected>>", self.filt_t)

        tf=self.F(T["🛍️ Catalog"], pk={'fill':'both','expand':True,'padx':20,'pady':20}); C=("Name","Category","Suitable For","Price")
        self.tv=ttk.Treeview(tf, columns=C, show="headings")
        for c in C: self.tv.heading(c, text=c); self.tv.column(c, width=350 if c=="Name" else 150)
        self.tv.tag_configure('o', background="#FFF"); self.tv.tag_configure('e', background="#FAF7F2")
        sb=ttk.Scrollbar(tf, command=self.tv.yview); sb.pack(side="right", fill="y")
        self.tv.pack(side="left", fill="both", expand=True); self.tv.configure(yscrollcommand=sb.set); self.filt_t()

    def filt_t(self, e=None):
        self.f = self.vf.get(); self.tv.delete(*self.tv.get_children())
        for i, p in enumerate([p for p in self.db if self.f=="All" or self.f in p[2]]): self.tv.insert("", "end", values=p, tags=('e' if i%2==0 else 'o',))

    def nav(self, s):
        for e in ["<MouseWheel>","<Button-4>","<Button-5>"]: self.R.unbind_all(e)
        self.scr=s; self.draw()

if __name__=="__main__": root=tk.Tk(); app=SkincareApp(root); root.mainloop()
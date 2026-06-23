#!/usr/bin/env python3
"""
KernelCTC — India Salary Calculator (FY 2025-26)
Desktop GUI · Built with tkinter (zero install needed)

Run:  python3 kernelctc.py
"""

import tkinter as tk
from tkinter import font as tkfont
import math

# ─── Tax / Salary Constants ────────────────────────────────────────────────────

PF_CAP_BASIC      = 15_000          # Statutory PF cap on basic/month
EMPLOYER_PF_RATE  = 0.12
GRATUITY_RATE     = 4.81 / 100
STANDARD_DED_NEW  = 75_000
STANDARD_DED_OLD  = 50_000
PROFESSIONAL_TAX  = 2_400

NEW_REGIME_SLABS = [
    (400_000, 0.00), (400_000, 0.05), (400_000, 0.10),
    (400_000, 0.15), (400_000, 0.20), (float("inf"), 0.30),
]
NEW_REBATE_LIMIT, NEW_REBATE = 1_200_000, 60_000

OLD_REGIME_SLABS = [
    (250_000, 0.00), (250_000, 0.05),
    (500_000, 0.20), (float("inf"), 0.30),
]
OLD_REBATE_LIMIT, OLD_REBATE = 500_000, 12_500


# ─── Calculation ───────────────────────────────────────────────────────────────

def calculate_tax(taxable, slabs, rebate_limit, rebate):
    tax, rem = 0.0, taxable
    for size, rate in slabs:
        if rem <= 0: break
        tax += min(rem, size) * rate
        rem -= size
    if taxable <= rebate_limit:
        tax = max(0, tax - rebate)
    if taxable > 5_000_000:
        r = 0.10
        if taxable > 10_000_000: r = 0.15
        if taxable > 20_000_000: r = 0.25
        if taxable > 50_000_000: r = 0.37
        tax += tax * r
    return round(tax * 1.04)


def calculate(ctc, is_metro, sec80c_extra=0, nps=50_000):
    basic        = round(ctc * 0.40)
    # PF capped at statutory basic of ₹15,000/month
    pf_basic     = min(basic, PF_CAP_BASIC * 12)
    emp_pf_cost  = round(pf_basic * EMPLOYER_PF_RATE)
    gratuity     = round(basic * GRATUITY_RATE)
    hra          = round(basic * (0.50 if is_metro else 0.40))
    special      = max(0, ctc - basic - hra - emp_pf_cost - gratuity)
    gross        = basic + hra + special

    emp_pf       = round(pf_basic * 0.12)
    pt           = PROFESSIONAL_TAX

    # Old Regime
    total_80c    = min(emp_pf + sec80c_extra, 150_000)
    old_ded      = STANDARD_DED_OLD + total_80c + hra + pt + nps
    old_taxable  = max(0, gross - old_ded)
    old_tax      = calculate_tax(old_taxable, OLD_REGIME_SLABS, OLD_REBATE_LIMIT, OLD_REBATE)
    old_inhand   = round((gross - emp_pf * 12 - pt - old_tax) / 12)

    # New Regime
    new_taxable  = max(0, gross - STANDARD_DED_NEW)
    new_tax      = calculate_tax(new_taxable, NEW_REGIME_SLABS, NEW_REBATE_LIMIT, NEW_REBATE)
    new_inhand   = round((gross - emp_pf * 12 - pt - new_tax) / 12)

    return dict(
        ctc=ctc, basic=basic, hra=hra, special=special,
        emp_pf_cost=emp_pf_cost, gratuity=gratuity, gross=gross,
        emp_pf=emp_pf, pt=pt, total_ded=emp_pf + pt,
        total_80c=total_80c, nps=nps,
        old_taxable=old_taxable, old_tax=old_tax, old_inhand=old_inhand,
        old_eff=round(old_tax / gross * 100, 1) if gross else 0,
        new_taxable=new_taxable, new_tax=new_tax, new_inhand=new_inhand,
        new_eff=round(new_tax / gross * 100, 1) if gross else 0,
        better="Old Regime" if old_inhand > new_inhand else "New Regime",
        diff=abs(old_inhand - new_inhand),
    )


def parse_ctc(raw):
    raw = raw.strip().replace(",", "").upper()
    if raw.endswith("CR"): return float(raw[:-2]) * 10_000_000
    if raw.endswith("L"):  return float(raw[:-1]) * 100_000
    if raw.endswith("K"):  return float(raw[:-1]) * 1_000
    return float(raw)


def inr(n):  return f"₹ {int(n):,}"
def inr_s(n):
    n = int(n)
    if n >= 10_000_000: return f"₹ {n/10_000_000:.2f} Cr"
    if n >= 100_000:    return f"₹ {n/100_000:.2f} L"
    return f"₹ {n:,}"


# ─── Colours ───────────────────────────────────────────────────────────────────

C = dict(
    bg       = "#0d0f17",
    panel    = "#161824",
    panel2   = "#1c1f2e",
    border   = "#2a2d42",
    accent   = "#63b3ed",
    green    = "#48c78e",
    yellow   = "#f6ad55",
    red      = "#fc8181",
    blue     = "#76a9fa",
    muted    = "#8892a4",
    white    = "#e6ebf5",
    card_new = "#0d2a1f",
    card_old = "#2a1f0d",
    card_rec = "#0d1a2a",
    btn_calc = "#d4a017",   # amber/gold for Calculate
)


# ─── Colour helpers ────────────────────────────────────────────────────────────

def _hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _rgb_to_hex(r, g, b):
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

def _lerp_color(c1, c2, t):
    r1, g1, b1 = _hex_to_rgb(c1)
    r2, g2, b2 = _hex_to_rgb(c2)
    return _rgb_to_hex(r1 + (r2-r1)*t, g1 + (g2-g1)*t, b1 + (b2-b1)*t)


# ─── Splash Screen ─────────────────────────────────────────────────────────────

class SplashFrame:
    """
    Animated splash with:
      - Subtle dot-grid background
      - Three expanding ripple rings (cyan) that loop
      - KernelCTC wordmark + tagline
      - Pill-shaped "Open Calculator" button
    Uses composition (not subclassing) for Python 3.14 compatibility.
    """
    RING_COLORS = ["#0e7490", "#0891b2", "#22d3ee"]
    RING_PERIOD = 120
    FPS         = 16

    def __init__(self, master, on_start):
        self.master   = master
        self.on_start = on_start
        self._frame   = 0
        self._running = True
        self._ready   = False
        self._w = self._h = 0
        # Root frame — composition, not inheritance
        self.frame = tk.Frame(master, bg=C["bg"])
        self._build()

    def pack(self, **kw):
        self.frame.pack(**kw)

    def destroy(self):
        self._running = False
        self.frame.destroy()

    def _build(self):
        self.canvas = tk.Canvas(self.frame, bg=C["bg"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        self._ready = True
        if self._frame == 0:
            self._w, self._h = event.width, event.height
            self._draw_static()
            self._animate()

    # ── Static background layer ───────────────────────────────────────────────

    def _draw_static(self):
        c = self.canvas
        w, h = self._w, self._h
        c.delete("all")

        # Dot grid
        gap = 32
        for x in range(0, w + gap, gap):
            for y in range(0, h + gap, gap):
                c.create_oval(x-1, y-1, x+1, y+1, fill="#1e2235", outline="")

        # Diagonal accent lines (top-left corner decoration)
        for i in range(6):
            off = 40 + i * 22
            c.create_line(0, off, off, 0, fill="#1a2040", width=1)

        # Same bottom-right
        for i in range(6):
            off = 40 + i * 22
            c.create_line(w, h - off, w - off, h, fill="#1a2040", width=1)

    # ── Animation loop ────────────────────────────────────────────────────────

    def _animate(self):
        if not self._running or not self._ready:
            return
        c = self.canvas

        # Always read live canvas size so resizing recentres everything
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 2 or h < 2:
            self.canvas.after(self.FPS, self._animate)
            return

        # If canvas grew, redraw static layer to fill new area
        if w != self._w or h != self._h:
            self._w, self._h = w, h
            self._draw_static()

        cx, cy = w // 2, h // 2

        # Remove previous animated items only
        c.delete("anim")

        f = self._frame
        P = self.RING_PERIOD

        # Three rings staggered by P/3 each
        for i, col in enumerate(self.RING_COLORS):
            phase   = (f + i * P // 3) % P
            t       = phase / P                    # 0→1
            radius  = 60 + t * min(w, h) * 0.38
            alpha_t = 1 - t                        # fade as it expands
            ring_col = _lerp_color(col, C["bg"], 1 - alpha_t * 0.7)
            c.create_oval(cx - radius, cy - radius,
                          cx + radius, cy + radius,
                          outline=ring_col, width=max(1, int(2 * alpha_t + 0.5)),
                          tags="anim")

        # Wordmark — redrawn each frame so it stays on top
        c.create_text(cx, cy - 55,
                      text="KernelCTC",
                      font=("SF Pro Display", 54, "bold"),
                      fill="#ffffff", tags="anim")

        # Thin cyan underline accent
        uw = 130
        c.create_rectangle(cx - uw//2, cy - 18,
                           cx + uw//2, cy - 15,
                           fill="#22d3ee", outline="", tags="anim")

        # Tagline
        c.create_text(cx, cy + 10,
                      text="India Salary Calculator  ·  FY 2025-26",
                      font=("SF Pro Text", 15),
                      fill="#94a3b8", tags="anim")

        # Sub-tagline
        c.create_text(cx, cy + 38,
                      text="CTC  ·  In-Hand  ·  PF  ·  HRA  ·  Tax  ·  Both Regimes",
                      font=("SF Pro Text", 11),
                      fill="#475569", tags="anim")

        # Pill button
        bx, by, bw, bh = cx, cy + 108, 210, 44
        r = bh // 2
        # Draw pill via overlapping rect + two circles
        c.create_rectangle(bx - bw//2 + r, by - r,
                           bx + bw//2 - r, by + r,
                           fill="#0891b2", outline="", tags=("anim", "btn"))
        c.create_oval(bx - bw//2, by - r, bx - bw//2 + 2*r, by + r,
                      fill="#0891b2", outline="", tags=("anim", "btn"))
        c.create_oval(bx + bw//2 - 2*r, by - r, bx + bw//2, by + r,
                      fill="#0891b2", outline="", tags=("anim", "btn"))
        c.create_text(bx, by,
                      text="Open Calculator  →",
                      font=("SF Pro Text", 13, "bold"),
                      fill="#ffffff", tags=("anim", "btn"))

        c.tag_bind("btn", "<Enter>",  lambda e: c.itemconfig("btn", fill="#0e7490"))
        c.tag_bind("btn", "<Leave>",  lambda e: c.itemconfig("btn", fill="#0891b2"))
        c.tag_bind("btn", "<Button-1>", lambda e: self._go())

        # FY badge — top-right
        c.create_text(w - 16, 16,
                      text="FY 2025-26", anchor="ne",
                      font=("SF Pro Text", 10),
                      fill="#334155", tags="anim")

        self._frame = (self._frame + 1) % P
        self.canvas.after(self.FPS, self._animate)

    def _go(self):
        self._running = False
        self.on_start()


# ─── Main App ──────────────────────────────────────────────────────────────────

class KernelCTC(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("KernelCTC — India Salary Calculator")
        self.geometry("1040x760")
        self.minsize(920, 680)
        self.configure(bg=C["bg"])

        self.f_title = tkfont.Font(family="SF Pro Display", size=17, weight="bold")
        self.f_head  = tkfont.Font(family="SF Pro Text",    size=11, weight="bold")
        self.f_body  = tkfont.Font(family="SF Pro Text",    size=11)
        self.f_small = tkfont.Font(family="SF Pro Text",    size=9)
        self.f_card  = tkfont.Font(family="SF Pro Display", size=15, weight="bold")
        self.f_mono  = tkfont.Font(family="Menlo",          size=11)
        self.v = {}

        self._show_splash()

    # ── Splash ────────────────────────────────────────────────────────────────

    def _show_splash(self):
        self._splash = SplashFrame(self, self._launch_app)
        self._splash.pack(fill="both", expand=True)

    def _launch_app(self):
        self._splash.destroy()
        self._build_app()

    # ── App layout ────────────────────────────────────────────────────────────

    def _build_app(self):
        root = tk.Frame(self, bg=C["bg"])
        root.pack(fill="both", expand=True, padx=16, pady=16)

        left = tk.Frame(root, bg=C["panel"], width=290)
        left.pack(side="left", fill="y", padx=(0, 14))
        left.pack_propagate(False)
        self._build_sidebar(left)

        right = tk.Frame(root, bg=C["bg"])
        right.pack(side="left", fill="both", expand=True)
        self._build_results(right)

    # ── Sidebar ───────────────────────────────────────────────────────────────

    def _build_sidebar(self, p):
        def pad_label(text, color, top=8):
            tk.Label(p, text=text, font=self.f_head, fg=color,
                     bg=C["panel"]).pack(anchor="w", padx=16, pady=(top, 2))

        def sep():
            tk.Frame(p, bg=C["border"], height=1).pack(fill="x", padx=16, pady=6)

        tk.Label(p, text="KernelCTC", font=self.f_title,
                 fg=C["accent"], bg=C["panel"]).pack(anchor="w", padx=16, pady=(16, 0))
        tk.Label(p, text="India Salary Calculator · FY 2025-26",
                 font=self.f_small, fg=C["muted"], bg=C["panel"]).pack(anchor="w", padx=16)

        sep()

        # ── CTC input ────────────────────────────────────────────────────────
        pad_label("Annual CTC", C["accent"])
        tk.Label(p, text="e.g.  15L  ·  1.5Cr  ·  1500000",
                 font=self.f_small, fg=C["muted"], bg=C["panel"]).pack(anchor="w", padx=16)
        self.ctc_var = tk.StringVar()
        e = tk.Entry(p, textvariable=self.ctc_var, font=self.f_body,
                     bg=C["panel2"], fg=C["white"], insertbackground=C["white"],
                     relief="flat", highlightthickness=1,
                     highlightbackground=C["border"], highlightcolor=C["accent"])
        e.pack(fill="x", padx=16, pady=(4, 0), ipady=7)
        e.bind("<Return>", lambda _: self._calculate())

        sep()

        # ── Location ─────────────────────────────────────────────────────────
        pad_label("Location", C["accent"], top=2)
        self.metro_var = tk.BooleanVar(value=True)

        for label, val in [("Metro city", True), ("Non-metro city", False)]:
            row = tk.Frame(p, bg=C["panel"])
            row.pack(anchor="w", padx=16, pady=2, fill="x")
            rb = tk.Radiobutton(row, variable=self.metro_var, value=val,
                                bg=C["panel"], activebackground=C["panel"],
                                selectcolor=C["panel2"], relief="flat",
                                highlightthickness=0, cursor="hand2")
            rb.pack(side="left")
            tk.Label(row, text=label, font=self.f_body,
                     fg=C["white"], bg=C["panel"]).pack(side="left")

        tk.Label(p, text="Metro: Delhi · Mumbai · Chennai · Kolkata",
                 font=self.f_small, fg=C["muted"], bg=C["panel"]
                 ).pack(anchor="w", padx=16, pady=(2, 0))

        sep()

        # ── Sliders ──────────────────────────────────────────────────────────
        pad_label("Old Regime Investments", C["accent"], top=2)

        # 80C slider
        row80 = tk.Frame(p, bg=C["panel"])
        row80.pack(fill="x", padx=16, pady=(2, 0))
        tk.Label(row80, text="80C extras (beyond PF)", font=self.f_small,
                 fg=C["muted"], bg=C["panel"]).pack(side="left")
        self.s80c_lbl = tk.Label(row80, text="₹ 0", font=self.f_small,
                                  fg=C["yellow"], bg=C["panel"])
        self.s80c_lbl.pack(side="right")
        self.s80c_var = tk.IntVar(value=0)
        tk.Scale(p, variable=self.s80c_var, from_=0, to=150_000,
                 orient="horizontal", bg=C["panel"], fg=C["white"],
                 troughcolor=C["border"], highlightthickness=0,
                 activebackground=C["accent"], resolution=1000, showvalue=False,
                 command=lambda v: self.s80c_lbl.config(text=inr(int(float(v))))
                 ).pack(fill="x", padx=16)

        # NPS slider
        row_nps = tk.Frame(p, bg=C["panel"])
        row_nps.pack(fill="x", padx=16, pady=(6, 0))
        tk.Label(row_nps, text="NPS 80CCD(1B)  (max ₹50K)", font=self.f_small,
                 fg=C["muted"], bg=C["panel"]).pack(side="left")
        self.nps_lbl = tk.Label(row_nps, text="₹ 50,000", font=self.f_small,
                                 fg=C["yellow"], bg=C["panel"])
        self.nps_lbl.pack(side="right")
        self.nps_var = tk.IntVar(value=50_000)
        tk.Scale(p, variable=self.nps_var, from_=0, to=50_000,
                 orient="horizontal", bg=C["panel"], fg=C["white"],
                 troughcolor=C["border"], highlightthickness=0,
                 activebackground=C["accent"], resolution=1000, showvalue=False,
                 command=lambda v: self.nps_lbl.config(text=inr(int(float(v))))
                 ).pack(fill="x", padx=16)

        sep()

        # ── Calculate button ──────────────────────────────────────────────────
        tk.Button(p, text="Calculate", font=self.f_head,
                  bg=C["btn_calc"], fg="#1a1200",
                  activebackground="#e8b820", activeforeground="#1a1200",
                  relief="flat", cursor="hand2", bd=0,
                  command=self._calculate
                  ).pack(fill="x", padx=16, pady=(4, 6), ipady=9)

        self.err_lbl = tk.Label(p, text="", font=self.f_small,
                                 fg=C["red"], bg=C["panel"], wraplength=258)
        self.err_lbl.pack(anchor="w", padx=16)

    # ── Results ───────────────────────────────────────────────────────────────

    def _build_results(self, parent):
        # Stat cards
        cards = tk.Frame(parent, bg=C["bg"])
        cards.pack(fill="x", pady=(0, 12))
        self.card_new = self._stat_card(cards, "New Regime · Monthly Take-Home", "—", C["card_new"], C["green"])
        self.card_old = self._stat_card(cards, "Old Regime · Monthly Take-Home",  "—", C["card_old"], C["yellow"])
        self.card_rec = self._stat_card(cards, "Recommended Regime",              "—", C["card_rec"], C["blue"])

        # Scrollable area
        canvas = tk.Canvas(parent, bg=C["bg"], highlightthickness=0)
        vbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vbar.set)
        vbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=C["bg"])
        win_id = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(win_id, width=e.width))
        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind_all("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        self._build_detail(inner)

    def _build_detail(self, p):
        # CTC Breakdown
        sec = self._section(p, "CTC Breakdown  (Annual)")
        cols = tk.Frame(sec, bg=C["panel2"]); cols.pack(fill="x", padx=12, pady=(0, 10))
        L = tk.Frame(cols, bg=C["panel2"]); L.pack(side="left", fill="both", expand=True)
        R = tk.Frame(cols, bg=C["panel2"]); R.pack(side="left", fill="both", expand=True)
        self._kv(L, "Total CTC",          "ctc",         C["white"])
        self._kv(L, "Basic Salary  (40%)", "basic",      C["white"])
        self._kv(L, "HRA",                "hra",         C["white"])
        self._kv(L, "Special Allowance",  "special",     C["white"])
        self._kv(R, "Gross Salary",       "gross",       C["green"])
        self._kv(R, "Employer PF  (12%)", "emp_pf_cost", C["muted"])
        self._kv(R, "Gratuity  (4.81%)",  "gratuity",    C["muted"])

        # Deductions
        sec2 = self._section(p, "Your Deductions  (Annual)")
        c2 = tk.Frame(sec2, bg=C["panel2"]); c2.pack(fill="x", padx=12, pady=(0, 10))
        L2 = tk.Frame(c2, bg=C["panel2"]); L2.pack(side="left", fill="both", expand=True)
        R2 = tk.Frame(c2, bg=C["panel2"]); R2.pack(side="left", fill="both", expand=True)
        self._kv(L2, "Employee PF  (12%)", "emp_pf",   C["yellow"])
        self._kv(L2, "Professional Tax",   "pt",        C["yellow"])
        self._kv(R2, "Total Deductions",   "total_ded", C["red"])

        # Tax regimes side by side
        reg = tk.Frame(p, bg=C["bg"]); reg.pack(fill="x", pady=(0, 10))
        old_s = self._section(reg, "Old Tax Regime",          color=C["yellow"], side="left", expand=True)
        new_s = self._section(reg, "New Tax Regime  (Default)", color=C["blue"], side="left", expand=True, padleft=8)

        oF = tk.Frame(old_s, bg=C["panel2"]); oF.pack(fill="x", padx=12, pady=(0, 10))
        self._kv(oF, "Gross Salary",   "ov_gross",   C["white"])
        self._kv(oF, "Standard Ded.",  "ov_std",     C["muted"])
        self._kv(oF, "HRA Exemption",  "ov_hra",     C["muted"])
        self._kv(oF, "80C Deduction",  "ov_80c",     C["muted"])
        self._kv(oF, "NPS 80CCD(1B)",  "ov_nps",     C["muted"])
        self._kv(oF, "Taxable Income", "ov_taxable", C["yellow"])
        self._kv(oF, "Tax + Cess",     "ov_tax",     C["red"])
        self._kv(oF, "Effective Rate", "ov_eff",     C["red"])

        nF = tk.Frame(new_s, bg=C["panel2"]); nF.pack(fill="x", padx=12, pady=(0, 10))
        self._kv(nF, "Gross Salary",   "nv_gross",   C["white"])
        self._kv(nF, "Standard Ded.",  "nv_std",     C["muted"])
        self._kv(nF, "Taxable Income", "nv_taxable", C["blue"])
        self._kv(nF, "Tax + Cess",     "nv_tax",     C["red"])
        self._kv(nF, "Effective Rate", "nv_eff",     C["red"])

        # Monthly Payslip
        sec4 = self._section(p, "Monthly Payslip Snapshot  (New Regime)", color=C["green"])
        c4 = tk.Frame(sec4, bg=C["panel2"]); c4.pack(fill="x", padx=12, pady=(0, 10))
        L4 = tk.Frame(c4, bg=C["panel2"]); L4.pack(side="left", fill="both", expand=True)
        R4 = tk.Frame(c4, bg=C["panel2"]); R4.pack(side="left", fill="both", expand=True)
        self._kv(L4, "Gross Monthly",        "pm_gross",  C["white"])
        self._kv(L4, "  – Employee PF",      "pm_pf",     C["muted"])
        self._kv(L4, "  – Professional Tax", "pm_pt",     C["muted"])
        self._kv(L4, "  – TDS (Tax ÷ 12)",   "pm_tds",    C["muted"])
        self._kv(R4, "Net Take-Home",        "pm_net",    C["green"])
        self._kv(R4, "Annual Take-Home",     "pm_annual", C["green"])
        self._kv(R4, "Savings (20% rule)",   "pm_save",   C["blue"])

        tk.Label(p,
                 text="* Basic=40% CTC · PF capped at statutory ₹15K/mo basic · "
                      "Old regime uses max 80C (₹1.5L) + NPS · Gratuity & Employer PF are CTC cost, not in-hand",
                 font=self.f_small, fg=C["muted"], bg=C["bg"],
                 wraplength=680, justify="left"
                 ).pack(anchor="w", padx=4, pady=(0, 12))

    # ── Calculate ─────────────────────────────────────────────────────────────

    def _calculate(self):
        raw = self.ctc_var.get().strip()
        if not raw:
            self.err_lbl.config(text="Please enter your CTC.")
            return
        try:
            ctc = parse_ctc(raw)
        except Exception:
            self.err_lbl.config(text=f'Cannot parse "{raw}". Try: 15L, 1.5Cr, 1500000')
            return
        if ctc < 100_000:
            self.err_lbl.config(text="Enter annual CTC (e.g. 5L for ₹5 lakh).")
            return
        self.err_lbl.config(text="")

        d = calculate(ctc, self.metro_var.get(), self.s80c_var.get(), self.nps_var.get())

        self.card_new.config(text=inr(d["new_inhand"]) + " / mo")
        self.card_old.config(text=inr(d["old_inhand"]) + " / mo")
        better_col = C["green"] if d["better"] == "New Regime" else C["yellow"]
        self.card_rec.config(text=f"{d['better']}\n+{inr(d['diff'])} / mo", fg=better_col)

        sets = {
            "ctc": inr(d["ctc"]),         "basic": inr(d["basic"]),
            "hra": inr(d["hra"]),          "special": inr(d["special"]),
            "gross": inr(d["gross"]),      "emp_pf_cost": inr(d["emp_pf_cost"]),
            "gratuity": inr(d["gratuity"]),"emp_pf": inr(d["emp_pf"]),
            "pt": inr(d["pt"]),            "total_ded": inr(d["total_ded"]),
            "ov_gross": inr(d["gross"]),   "ov_std": f"– {inr(STANDARD_DED_OLD)}",
            "ov_hra": f"– {inr(d['hra'])}", "ov_80c": f"– {inr(d['total_80c'])}",
            "ov_nps": f"– {inr(d['nps'])}","ov_taxable": inr(d["old_taxable"]),
            "ov_tax": inr(d["old_tax"]),   "ov_eff": f"{d['old_eff']}%",
            "nv_gross": inr(d["gross"]),   "nv_std": f"– {inr(STANDARD_DED_NEW)}",
            "nv_taxable": inr(d["new_taxable"]), "nv_tax": inr(d["new_tax"]),
            "nv_eff": f"{d['new_eff']}%",  "pm_gross": inr(round(d["gross"]/12)),
            "pm_pf": f"– {inr(round(d['emp_pf']/12))}",
            "pm_pt": f"– {inr(round(d['pt']/12))}",
            "pm_tds": f"– {inr(round(d['new_tax']/12))}",
            "pm_net": inr(d["new_inhand"]),
            "pm_annual": inr_s(d["new_inhand"] * 12),
            "pm_save": inr_s(round(d["new_inhand"] * 12 * 0.20)),
        }
        for k, v in sets.items():
            self.v[k].config(text=v)

    # ── Widget helpers ────────────────────────────────────────────────────────

    def _stat_card(self, parent, title, value, bg, fg):
        f = tk.Frame(parent, bg=bg, highlightthickness=1,
                     highlightbackground=C["border"])
        f.pack(side="left", fill="both", expand=True, padx=(0, 8), ipady=6, ipadx=8)
        tk.Label(f, text=title, font=self.f_small, fg=C["muted"], bg=bg
                 ).pack(anchor="w", padx=10, pady=(8, 0))
        lbl = tk.Label(f, text=value, font=self.f_card, fg=fg, bg=bg, justify="left")
        lbl.pack(anchor="w", padx=10, pady=(2, 8))
        return lbl

    def _section(self, parent, title, color=None, side=None, expand=False, padleft=0):
        color = color or C["accent"]
        outer = tk.Frame(parent, bg=C["bg"])
        if side:
            outer.pack(side=side, fill="both", expand=expand, padx=(padleft, 0))
        else:
            outer.pack(fill="x", pady=(0, 10))

        tk.Frame(outer, bg=C["panel2"], highlightthickness=1,
                 highlightbackground=C["border"]).pack(fill="x")  # spacer top border
        hdr = tk.Frame(outer, bg=C["panel2"])
        hdr.pack(fill="x")
        tk.Label(hdr, text=f"  {title}", font=self.f_head, fg=color,
                 bg=C["panel2"], anchor="w").pack(fill="x", ipady=6)

        body = tk.Frame(outer, bg=C["panel2"], highlightthickness=1,
                        highlightbackground=C["border"])
        body.pack(fill="x")
        return body

    def _kv(self, parent, label, key, color):
        row = tk.Frame(parent, bg=C["panel2"])
        row.pack(fill="x", padx=10, pady=2)
        tk.Label(row, text=label, font=self.f_body, fg=C["muted"],
                 bg=C["panel2"], anchor="w", width=22).pack(side="left")
        lbl = tk.Label(row, text="—", font=self.f_mono, fg=color,
                        bg=C["panel2"], anchor="e")
        lbl.pack(side="right")
        self.v[key] = lbl


# ─── Run ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = KernelCTC()
    app.mainloop()

#!/usr/bin/env python3
"""
India Salary Calculator
Enter your CTC and get a full breakdown: in-hand salary, PF, gratuity,
HRA, and tax liability under both Old and New tax regimes.
"""

from dataclasses import dataclass


# ─── Constants ────────────────────────────────────────────────────────────────

PF_RATE = 0.12          # Employee PF: 12% of Basic
EMPLOYER_PF_RATE = 0.12 # Employer PF: 12% of Basic (part of CTC)
GRATUITY_RATE = 4.81 / 100  # Gratuity: 4.81% of Basic (15/26 * 1/12)
STANDARD_DEDUCTION = 75_000  # FY 2025-26 (New regime) / 50,000 (Old)
STANDARD_DEDUCTION_OLD = 50_000
PROFESSIONAL_TAX_ANNUAL = 2_400  # Typical PT (₹200/month)
HRA_METRO_RATE = 0.50   # 50% of Basic for metro cities
HRA_NON_METRO_RATE = 0.40


# ─── Tax Slabs ────────────────────────────────────────────────────────────────

# New Regime (FY 2025-26, post Budget 2025)
NEW_REGIME_SLABS = [
    (400_000, 0.00),
    (400_000, 0.05),
    (400_000, 0.10),
    (400_000, 0.15),
    (400_000, 0.20),
    (float("inf"), 0.30),
]
NEW_REGIME_REBATE_LIMIT = 1_200_000  # No tax up to ₹12L (rebate u/s 87A)
NEW_REGIME_REBATE = 60_000

# Old Regime
OLD_REGIME_SLABS = [
    (250_000, 0.00),
    (250_000, 0.05),
    (500_000, 0.20),
    (float("inf"), 0.30),
]
OLD_REGIME_REBATE_LIMIT = 500_000
OLD_REGIME_REBATE = 12_500


# ─── Helpers ──────────────────────────────────────────────────────────────────

def fmt(amount: float) -> str:
    """Format as Indian currency string."""
    return f"₹{amount:>13,.0f}"


def fmt_pct(pct: float) -> str:
    return f"{pct * 100:.1f}%"


def indian_number(n: float) -> str:
    """Format number in Indian numbering system (lakhs/crores)."""
    n = int(round(n))
    if n >= 10_000_000:
        return f"₹{n/10_000_000:.2f} Cr"
    elif n >= 100_000:
        return f"₹{n/100_000:.2f} L"
    else:
        return f"₹{n:,}"


def calculate_tax(taxable_income: float, slabs, rebate_limit: float, rebate: float) -> float:
    """Calculate income tax from slabs with rebate u/s 87A."""
    tax = 0.0
    remaining = taxable_income
    lower = 0
    for (slab_size, rate) in slabs:
        if remaining <= 0:
            break
        chunk = min(remaining, slab_size)
        tax += chunk * rate
        remaining -= chunk
        lower += slab_size

    # Rebate u/s 87A
    if taxable_income <= rebate_limit:
        tax = max(0, tax - rebate)

    # Surcharge (simplified)
    if taxable_income > 5_000_000:
        surcharge_rate = 0.10
        if taxable_income > 10_000_000:
            surcharge_rate = 0.15
        if taxable_income > 20_000_000:
            surcharge_rate = 0.25
        if taxable_income > 50_000_000:
            surcharge_rate = 0.37
        tax += tax * surcharge_rate

    # Health & Education Cess: 4%
    tax += tax * 0.04

    return round(tax)


# ─── Core Calculation ─────────────────────────────────────────────────────────

@dataclass
class SalaryBreakdown:
    ctc: float
    basic: float
    hra: float
    special_allowance: float
    employer_pf: float
    gratuity_annual: float
    employee_pf: float
    professional_tax: float
    gross_salary: float
    # Old regime
    old_taxable: float
    old_tax: float
    old_inhand_monthly: float
    # New regime
    new_taxable: float
    new_tax: float
    new_inhand_monthly: float
    # Deductions old regime
    sec80c: float
    hra_exemption: float
    is_metro: bool


def calculate(ctc: float, is_metro: bool = True,
              sec80c: float = 150_000,
              nps_80ccd: float = 50_000) -> SalaryBreakdown:

    # ── CTC Structure ────────────────────────────────────────────────────────
    # Basic = 40% of CTC (common structure)
    # Employer PF and Gratuity are part of CTC
    # We need to back-calculate Basic from CTC

    # Let B = Basic
    # CTC = Gross + Employer_PF + Gratuity
    # Gross = Basic + HRA + Special Allowance
    # Employer_PF = 12% of B, Gratuity = 4.81% of B
    # HRA = 50% of B (metro)
    # We set Basic = 40% of CTC as starting point, then adjust

    # Solve: CTC = Gross + 0.12B + 0.0481B
    #        CTC = (B + HRA + SA) + 0.1681B
    # Typical: Basic = 40% CTC, HRA = 50% Basic
    # SA = CTC - Basic - HRA - Employer_PF - Gratuity

    basic = round(ctc * 0.40)
    employer_pf = round(basic * EMPLOYER_PF_RATE)
    gratuity_annual = round(basic * GRATUITY_RATE)
    hra = round(basic * (HRA_METRO_RATE if is_metro else HRA_NON_METRO_RATE))

    special_allowance = ctc - basic - hra - employer_pf - gratuity_annual
    if special_allowance < 0:
        special_allowance = 0

    gross_salary = basic + hra + special_allowance  # What employee receives before deductions

    # ── Employee Deductions ───────────────────────────────────────────────────
    employee_pf = round(basic * PF_RATE)
    professional_tax = PROFESSIONAL_TAX_ANNUAL

    # ── HRA Exemption (Old Regime) ────────────────────────────────────────────
    # Least of: (a) actual HRA, (b) 50/40% of Basic, (c) Rent paid - 10% Basic
    # Assume rent paid = HRA (max exemption scenario)
    hra_exemption = min(hra, basic * (HRA_METRO_RATE if is_metro else HRA_NON_METRO_RATE))

    # ── Old Regime ────────────────────────────────────────────────────────────
    total_80c = min(sec80c + employee_pf, 150_000)  # 80C cap ₹1.5L
    old_deductions = (STANDARD_DEDUCTION_OLD + total_80c + hra_exemption +
                      professional_tax + nps_80ccd)
    old_taxable = max(0, gross_salary - old_deductions)
    old_tax = calculate_tax(old_taxable, OLD_REGIME_SLABS,
                             OLD_REGIME_REBATE_LIMIT, OLD_REGIME_REBATE)
    old_monthly_deductions = (employee_pf + professional_tax / 12 + old_tax / 12)
    old_inhand_monthly = round((gross_salary - old_monthly_deductions * 12) / 12
                               if False else (gross_salary - employee_pf * 12 -
                               professional_tax - old_tax) / 12)

    # ── New Regime ────────────────────────────────────────────────────────────
    new_deductions = STANDARD_DEDUCTION  # Only standard deduction allowed
    new_taxable = max(0, gross_salary - new_deductions)
    new_tax = calculate_tax(new_taxable, NEW_REGIME_SLABS,
                             NEW_REGIME_REBATE_LIMIT, NEW_REGIME_REBATE)
    new_inhand_monthly = round((gross_salary - employee_pf * 12 -
                                professional_tax - new_tax) / 12)

    return SalaryBreakdown(
        ctc=ctc,
        basic=basic,
        hra=hra,
        special_allowance=special_allowance,
        employer_pf=employer_pf,
        gratuity_annual=gratuity_annual,
        employee_pf=employee_pf,
        professional_tax=professional_tax,
        gross_salary=gross_salary,
        old_taxable=old_taxable,
        old_tax=old_tax,
        old_inhand_monthly=old_inhand_monthly,
        new_taxable=new_taxable,
        new_tax=new_tax,
        new_inhand_monthly=new_inhand_monthly,
        sec80c=total_80c,
        hra_exemption=hra_exemption,
        is_metro=is_metro,
    )


# ─── Display ──────────────────────────────────────────────────────────────────

RESET  = "\033[0m"
BOLD   = "\033[1m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BLUE   = "\033[94m"
DIM    = "\033[2m"
WHITE  = "\033[97m"


def line(char="─", width=62):
    return char * width


def header(text: str, color=CYAN):
    w = 62
    pad = (w - len(text) - 2) // 2
    return f"{color}{BOLD}{'─' * pad} {text} {'─' * (w - pad - len(text) - 2)}{RESET}"


def row(label: str, value: str, color=WHITE, indent=0):
    prefix = "  " * indent
    label_col = 36 - len(prefix)
    return f"  {prefix}{color}{label:<{label_col}}{RESET}{value:>20}"


def print_report(b: SalaryBreakdown):
    W = 64

    print()
    print(f"{CYAN}{BOLD}{'═' * W}{RESET}")
    print(f"{CYAN}{BOLD}{'  INDIA SALARY CALCULATOR — FY 2025-26':^{W}}{RESET}")
    print(f"{CYAN}{BOLD}{'═' * W}{RESET}")

    # ── CTC & Structure ──────────────────────────────────────────────────────
    print(f"\n{header('CTC BREAKDOWN (Annual)')}")
    print(row("Total CTC",            fmt(b.ctc),            BOLD))
    print(row("  Basic Salary (40%)", fmt(b.basic),          WHITE, 0))
    print(row("  HRA", fmt(b.hra),                           WHITE))
    print(row("  Special Allowance",  fmt(b.special_allowance), WHITE))
    print(row("  Employer PF (12%)",  fmt(b.employer_pf),    DIM))
    print(row("  Gratuity (4.81%)",   fmt(b.gratuity_annual),DIM))
    print(row("Gross Salary",         fmt(b.gross_salary),   GREEN + BOLD))

    # ── Employee Deductions ──────────────────────────────────────────────────
    print(f"\n{header('EMPLOYEE DEDUCTIONS (Annual)')}")
    print(row("Employee PF (12% of Basic)", fmt(b.employee_pf),       YELLOW))
    print(row("Professional Tax",           fmt(b.professional_tax),  YELLOW))
    print(row("Total Statutory Deductions",
              fmt(b.employee_pf + b.professional_tax),                RED + BOLD))

    # ── Old Regime ───────────────────────────────────────────────────────────
    print(f"\n{header('OLD TAX REGIME', YELLOW)}")
    print(row("Gross Salary",              fmt(b.gross_salary),        WHITE))
    print(row("  Standard Deduction",      fmt(-STANDARD_DEDUCTION_OLD), DIM))
    print(row("  HRA Exemption",           fmt(-b.hra_exemption),      DIM))
    print(row("  80C (PF + investments)",  fmt(-b.sec80c),             DIM))
    print(row("  80CCD(1B) NPS",           fmt(-50_000),               DIM))
    print(row("  Professional Tax",        fmt(-b.professional_tax),   DIM))
    print(row("Taxable Income",            fmt(b.old_taxable),         YELLOW + BOLD))
    print(row("Income Tax + Cess",         fmt(b.old_tax),             RED + BOLD))
    eff_old = (b.old_tax / b.gross_salary * 100) if b.gross_salary else 0
    print(row("Effective Tax Rate",        f"{eff_old:.1f}%",          RED))
    print(row("Monthly In-Hand",           fmt(b.old_inhand_monthly),  GREEN + BOLD))

    # ── New Regime ───────────────────────────────────────────────────────────
    print(f"\n{header('NEW TAX REGIME (Default)', BLUE)}")
    print(row("Gross Salary",              fmt(b.gross_salary),        WHITE))
    print(row("  Standard Deduction",      fmt(-STANDARD_DEDUCTION),   DIM))
    print(row("Taxable Income",            fmt(b.new_taxable),         BLUE + BOLD))
    print(row("Income Tax + Cess",         fmt(b.new_tax),             RED + BOLD))
    eff_new = (b.new_tax / b.gross_salary * 100) if b.gross_salary else 0
    print(row("Effective Tax Rate",        f"{eff_new:.1f}%",          RED))
    print(row("Monthly In-Hand",           fmt(b.new_inhand_monthly),  GREEN + BOLD))

    # ── Comparison ───────────────────────────────────────────────────────────
    print(f"\n{header('REGIME COMPARISON')}")
    diff = b.old_inhand_monthly - b.new_inhand_monthly
    better = "Old Regime" if diff > 0 else "New Regime"
    better_color = YELLOW if diff > 0 else BLUE
    print(row("Old Regime monthly in-hand", fmt(b.old_inhand_monthly), YELLOW + BOLD))
    print(row("New Regime monthly in-hand", fmt(b.new_inhand_monthly), BLUE + BOLD))
    print(row("Difference (monthly)",       fmt(abs(diff)),            better_color))
    print(row("Recommended Regime",         better,                    better_color + BOLD))

    # ── Monthly Snapshot ─────────────────────────────────────────────────────
    print(f"\n{header('MONTHLY PAYSLIP SNAPSHOT (New Regime)')}")
    gross_m = round(b.gross_salary / 12)
    pf_m    = round(b.employee_pf / 12)
    pt_m    = round(b.professional_tax / 12)
    tax_m   = round(b.new_tax / 12)
    print(row("Gross Monthly",              fmt(gross_m),              WHITE))
    print(row("  – Employee PF",            fmt(-pf_m),                DIM))
    print(row("  – Professional Tax",       fmt(-pt_m),                DIM))
    print(row("  – TDS (Income Tax/12)",    fmt(-tax_m),               DIM))
    print(row("Net Take-Home",              fmt(b.new_inhand_monthly), GREEN + BOLD))

    print(f"\n{CYAN}{BOLD}{'═' * W}{RESET}")
    print(f"{DIM}  Note: Assumes Basic=40% CTC, HRA={'Metro (50%)' if b.is_metro else 'Non-Metro (40%)'}.{RESET}")
    print(f"{DIM}  Old regime assumes max 80C (₹1.5L) + NPS 80CCD(1B) (₹50K).{RESET}")
    print(f"{DIM}  Gratuity and Employer PF are cost-to-company, not in-hand.{RESET}")
    print(f"{CYAN}{BOLD}{'═' * W}{RESET}\n")


# ─── Input Helpers ────────────────────────────────────────────────────────────

def parse_ctc(raw: str) -> float:
    """Parse inputs like '15L', '1.5Cr', '1500000', '15,00,000'."""
    raw = raw.strip().replace(",", "").upper()
    try:
        if raw.endswith("CR"):
            return float(raw[:-2]) * 10_000_000
        elif raw.endswith("L"):
            return float(raw[:-1]) * 100_000
        elif raw.endswith("K"):
            return float(raw[:-1]) * 1_000
        else:
            return float(raw)
    except ValueError:
        raise ValueError(f"Cannot parse '{raw}' as a number.")


def prompt_yesno(question: str, default: bool = True) -> bool:
    hint = "[Y/n]" if default else "[y/N]"
    ans = input(f"  {question} {hint}: ").strip().lower()
    if not ans:
        return default
    return ans.startswith("y")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print(f"\n{CYAN}{BOLD}  India Salary Calculator — FY 2025-26{RESET}")
    print(f"{DIM}  Supports shorthand: 15L, 1.5Cr, 1500000{RESET}\n")

    while True:
        raw = input(f"  {BOLD}Enter your annual CTC:{RESET} ").strip()
        if not raw:
            print(f"  {RED}Please enter a value.{RESET}")
            continue
        try:
            ctc = parse_ctc(raw)
            if ctc < 100_000:
                print(f"  {RED}CTC seems too low. Enter annual CTC (e.g., 8L for ₹8 lakh).{RESET}")
                continue
            break
        except ValueError as e:
            print(f"  {RED}{e}{RESET}")

    is_metro = prompt_yesno("Are you in a metro city (Delhi/Mumbai/Chennai/Kolkata)?", default=True)

    print()
    b = calculate(ctc, is_metro=is_metro)
    print_report(b)


if __name__ == "__main__":
    main()

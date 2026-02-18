#!/usr/bin/env python3
"""
OpenVibe Market Sub-Segment Ranker

Scores ~80 professional service micro-niches on 5 dimensions:

  flywheel  — community density + referral velocity (30%)
  ai_rate   — % of core work AI can deliver today    (25%)
  pain      — urgency × budget availability          (20%)
  gap       — absence of AI-native competitors       (15%)
  access    — ease of reaching via Vibe / channels   (10%)

Usage:
  python market_ranker.py                              # top 20, default weights
  python market_ranker.py --top 50                     # top 50
  python market_ranker.py --industry education         # filter by industry
  python market_ranker.py --csv output.csv             # export all to CSV
  python market_ranker.py --sensitivity                # show top 10 under 3 scenarios
  python market_ranker.py --weights 0.4 0.2 0.2 0.1 0.1  # custom weights
"""

import argparse
import csv
import sys
from dataclasses import dataclass
from typing import List, Optional


# ─────────────────────────────────────────────────────────────────────────────
# Data model
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class Segment:
    industry: str
    name: str
    size: str          # micro / small / medium / large
    market_us: int     # estimated total addressable count in US
    monthly_fee: int   # realistic monthly fee in USD

    # Dimension scores: 1.0 (weak) → 5.0 (strong)
    flywheel: float    # community density, referral velocity
    ai_rate: float     # % of core work AI can deliver today
    pain: float        # urgency + budget availability
    gap: float         # absence of well-funded AI-native competitors
    access: float      # ease of reaching (Vibe channel or clear path)

    notes: str = ""

    def weighted_score(self, w: dict) -> float:
        return round(
            self.flywheel * w["flywheel"]
            + self.ai_rate * w["ai"]
            + self.pain    * w["pain"]
            + self.gap     * w["gap"]
            + self.access  * w["access"],
            3,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Segment database  (~80 segments across 10 industries)
# ─────────────────────────────────────────────────────────────────────────────

SEGMENTS: List[Segment] = [

    # ── EDUCATION: PRIVATE SCHOOLS ───────────────────────────────────────────
    Segment("Education", "Catholic K-12, small (100–300 students)", "small", 4500, 2500,
            flywheel=4.5, ai_rate=4.8, pain=4.2, gap=4.9, access=5.0,
            notes="Vibe K-12 channel; NCEA network; enrollment + development AI-ready"),
    Segment("Education", "Catholic K-12, medium (300–600 students)", "medium", 2000, 3500,
            flywheel=4.5, ai_rate=4.8, pain=4.0, gap=4.9, access=4.5),
    Segment("Education", "Secular college-prep, small", "small", 2200, 2800,
            flywheel=4.0, ai_rate=4.8, pain=4.5, gap=4.8, access=4.5,
            notes="Enrollment competition intense; AI content + admissions funnel"),
    Segment("Education", "Secular college-prep, medium", "medium", 1200, 4000,
            flywheel=4.0, ai_rate=4.8, pain=4.3, gap=4.8, access=4.0),
    Segment("Education", "Independent boarding schools", "medium", 320, 6000,
            flywheel=4.8, ai_rate=4.5, pain=3.8, gap=4.9, access=3.5,
            notes="TABS network; very tight community; development budgets large"),
    Segment("Education", "Jewish day schools, small", "small", 700, 3000,
            flywheel=5.0, ai_rate=4.8, pain=4.0, gap=4.9, access=3.5,
            notes="PRIZMAH network; extremely tight referral culture"),
    Segment("Education", "Jewish day schools, medium", "medium", 350, 4500,
            flywheel=5.0, ai_rate=4.8, pain=3.8, gap=4.9, access=3.0),
    Segment("Education", "Evangelical Christian schools", "small", 5000, 2000,
            flywheel=4.5, ai_rate=4.5, pain=4.2, gap=4.8, access=3.5,
            notes="ACSI network; strong referral culture; enrollment pressure"),
    Segment("Education", "Montessori schools, small", "micro", 3000, 2000,
            flywheel=4.2, ai_rate=4.5, pain=3.8, gap=4.9, access=3.5),
    Segment("Education", "IB schools (private)", "medium", 400, 4000,
            flywheel=3.8, ai_rate=4.5, pain=3.5, gap=4.8, access=3.5),
    Segment("Education", "Special needs private schools", "small", 1200, 3500,
            flywheel=4.0, ai_rate=3.5, pain=4.5, gap=4.9, access=3.0,
            notes="NAPSEC; fundraising + family communication strong AI use"),
    Segment("Education", "Private high schools (9–12 only)", "small", 1800, 3000,
            flywheel=4.2, ai_rate=4.8, pain=4.5, gap=4.8, access=4.0),
    Segment("Education", "Elite prep schools (>$35K tuition)", "large", 250, 8000,
            flywheel=4.5, ai_rate=4.5, pain=3.5, gap=4.8, access=3.0),
    Segment("Education", "Waldorf schools", "micro", 400, 2000,
            flywheel=4.2, ai_rate=4.2, pain=3.8, gap=5.0, access=3.0),
    Segment("Education", "International schools (US-based)", "medium", 200, 5000,
            flywheel=3.5, ai_rate=4.5, pain=3.5, gap=4.5, access=3.0),

    # ── CONSTRUCTION / AEC ───────────────────────────────────────────────────
    Segment("Construction", "Commercial GC, small ($2–10M revenue)", "small", 25000, 3000,
            flywheel=4.5, ai_rate=4.0, pain=4.5, gap=4.5, access=3.5,
            notes="AGC/ABC chapters; tight regional networks; bid writing AI-ready"),
    Segment("Construction", "Commercial GC, medium ($10–50M)", "medium", 8000, 4500,
            flywheel=4.0, ai_rate=3.8, pain=4.0, gap=4.5, access=3.0),
    Segment("Construction", "Residential custom builders, small", "small", 15000, 2500,
            flywheel=4.5, ai_rate=3.8, pain=4.3, gap=4.3, access=3.5),
    Segment("Construction", "Specialty: roofing contractors", "small", 30000, 2000,
            flywheel=4.0, ai_rate=4.0, pain=4.5, gap=3.5, access=3.0,
            notes="NRCA; competitive; storm-season urgency"),
    Segment("Construction", "Specialty: HVAC contractors", "small", 40000, 2000,
            flywheel=4.0, ai_rate=4.0, pain=4.3, gap=3.5, access=3.0),
    Segment("Construction", "Specialty: concrete/structural", "small", 12000, 2500,
            flywheel=4.2, ai_rate=4.2, pain=4.2, gap=4.5, access=3.5),
    Segment("Construction", "Architecture firms, small (5–20 staff)", "small", 8000, 3500,
            flywheel=3.5, ai_rate=4.2, pain=3.8, gap=3.8, access=3.0),
    Segment("Construction", "Civil engineering firms, small", "small", 6000, 4000,
            flywheel=3.8, ai_rate=4.0, pain=3.8, gap=4.2, access=3.0),

    # ── HEALTHCARE ───────────────────────────────────────────────────────────
    Segment("Healthcare", "Independent dental (1–3 dentists)", "micro", 80000, 2500,
            flywheel=4.0, ai_rate=3.5, pain=4.5, gap=2.5, access=3.0,
            notes="PatientPop/Weave dominant; HIPAA friction"),
    Segment("Healthcare", "Orthodontic practices", "small", 12000, 3500,
            flywheel=4.2, ai_rate=3.8, pain=4.5, gap=2.8, access=3.0),
    Segment("Healthcare", "Chiropractic practices", "micro", 35000, 2000,
            flywheel=4.0, ai_rate=4.0, pain=4.5, gap=3.0, access=3.0),
    Segment("Healthcare", "Plastic surgery / aesthetics", "small", 8000, 5000,
            flywheel=4.2, ai_rate=4.5, pain=4.8, gap=2.5, access=3.0,
            notes="High WTP; results very visible; before/after content AI-ready"),
    Segment("Healthcare", "Veterinary practices (independent)", "micro", 20000, 2500,
            flywheel=4.0, ai_rate=4.0, pain=4.2, gap=3.5, access=3.0),
    Segment("Healthcare", "Concierge / DPC primary care", "micro", 3000, 4000,
            flywheel=4.2, ai_rate=4.0, pain=4.5, gap=4.2, access=3.0,
            notes="Fast-growing segment; membership model; AI-friendly content"),
    Segment("Healthcare", "Physical therapy practices", "micro", 25000, 2000,
            flywheel=3.8, ai_rate=3.8, pain=4.2, gap=3.0, access=3.0),
    Segment("Healthcare", "Mental health group practices", "small", 15000, 2500,
            flywheel=3.5, ai_rate=3.5, pain=4.5, gap=3.8, access=3.0),

    # ── LEGAL ────────────────────────────────────────────────────────────────
    Segment("Legal", "Estate planning / elder law", "small", 15000, 3000,
            flywheel=4.0, ai_rate=4.5, pain=4.2, gap=4.0, access=3.0,
            notes="Aging population tailwind; doc generation very AI-ready"),
    Segment("Legal", "Immigration law", "small", 8000, 3000,
            flywheel=4.2, ai_rate=4.2, pain=4.8, gap=3.8, access=3.0,
            notes="Referral-dense immigrant communities; AILA network"),
    Segment("Legal", "Personal injury, small (1–5 attys)", "small", 20000, 3500,
            flywheel=3.5, ai_rate=4.0, pain=4.8, gap=2.0, access=2.5,
            notes="Very competitive; Martindale crowded; contingency model"),
    Segment("Legal", "Family law", "small", 18000, 2500,
            flywheel=3.5, ai_rate=4.0, pain=4.5, gap=3.5, access=2.8),
    Segment("Legal", "Real estate law (transaction)", "small", 12000, 3000,
            flywheel=3.8, ai_rate=4.5, pain=4.0, gap=4.0, access=3.0),
    Segment("Legal", "Business / transactional law", "small", 10000, 4000,
            flywheel=3.5, ai_rate=4.2, pain=3.8, gap=3.8, access=3.0),

    # ── ACCOUNTING / FINANCIAL ───────────────────────────────────────────────
    Segment("Finance", "Regional CPA firms (2–10 CPAs)", "small", 30000, 3000,
            flywheel=4.2, ai_rate=4.2, pain=4.0, gap=4.2, access=3.0,
            notes="AICPA / state societies; BD underdeveloped; content AI-ready"),
    Segment("Finance", "Tax boutiques (specialised)", "small", 12000, 3500,
            flywheel=3.8, ai_rate=4.5, pain=4.5, gap=3.8, access=3.0),
    Segment("Finance", "RIA, small (<$100M AUM)", "small", 8000, 3500,
            flywheel=4.0, ai_rate=4.2, pain=4.5, gap=4.0, access=3.0,
            notes="Compliance-heavy but content + prospecting AI-ready"),
    Segment("Finance", "CFO advisory / fractional CFO", "small", 4000, 4500,
            flywheel=3.8, ai_rate=4.0, pain=4.5, gap=4.2, access=3.0),
    Segment("Finance", "Business valuation firms", "micro", 3000, 4000,
            flywheel=3.5, ai_rate=4.5, pain=4.0, gap=4.5, access=2.8),

    # ── INSURANCE ────────────────────────────────────────────────────────────
    Segment("Insurance", "Independent agencies (commercial lines)", "small", 20000, 3000,
            flywheel=4.5, ai_rate=4.2, pain=4.5, gap=4.0, access=3.0,
            notes="IIABA network; proposal generation + client comms AI-ready"),
    Segment("Insurance", "Independent agencies (personal lines)", "micro", 25000, 2000,
            flywheel=4.2, ai_rate=4.2, pain=4.3, gap=3.5, access=3.0),
    Segment("Insurance", "Specialty insurance (E&O / D&O)", "small", 5000, 4000,
            flywheel=4.5, ai_rate=4.2, pain=4.0, gap=4.5, access=2.8),
    Segment("Insurance", "Employee benefits brokers", "small", 8000, 4000,
            flywheel=4.2, ai_rate=4.0, pain=4.2, gap=3.8, access=3.0),

    # ── STAFFING / HR ─────────────────────────────────────────────────────────
    Segment("Staffing", "Healthcare staffing agencies", "small", 5000, 4000,
            flywheel=4.0, ai_rate=4.2, pain=4.5, gap=3.5, access=3.0),
    Segment("Staffing", "Executive search firms", "small", 6000, 5000,
            flywheel=4.2, ai_rate=4.0, pain=4.0, gap=4.0, access=3.0),
    Segment("Staffing", "Technical staffing agencies", "small", 8000, 3500,
            flywheel=3.8, ai_rate=4.2, pain=4.2, gap=3.2, access=3.0),
    Segment("Staffing", "HR consulting boutiques", "small", 6000, 3500,
            flywheel=3.8, ai_rate=4.2, pain=4.0, gap=3.8, access=3.0),

    # ── REAL ESTATE ──────────────────────────────────────────────────────────
    Segment("Real Estate", "Commercial brokers (multifamily)", "small", 8000, 4000,
            flywheel=4.0, ai_rate=4.2, pain=4.2, gap=3.5, access=2.8),
    Segment("Real Estate", "Residential top-producer teams", "small", 15000, 3000,
            flywheel=4.0, ai_rate=4.5, pain=4.5, gap=2.5, access=3.5,
            notes="Listing content + BD AI-ready; Zillow crowded"),
    Segment("Real Estate", "Property management companies", "small", 12000, 3000,
            flywheel=3.8, ai_rate=4.2, pain=4.2, gap=3.2, access=3.0),
    Segment("Real Estate", "Land brokers (commercial)", "small", 4000, 5000,
            flywheel=4.0, ai_rate=4.0, pain=3.8, gap=4.5, access=2.8),

    # ── TECHNOLOGY SERVICES ───────────────────────────────────────────────────
    Segment("Tech Services", "IT MSPs, small (1–5 staff)", "micro", 30000, 2500,
            flywheel=3.8, ai_rate=4.0, pain=4.2, gap=3.0, access=3.0),
    Segment("Tech Services", "IT MSPs, medium (5–20 staff)", "small", 15000, 4000,
            flywheel=3.8, ai_rate=4.0, pain=4.0, gap=3.0, access=2.8),
    Segment("Tech Services", "Cybersecurity consultants", "small", 8000, 5000,
            flywheel=4.0, ai_rate=4.2, pain=4.8, gap=3.5, access=3.0),

    # ── OTHER PROFESSIONAL SERVICES ───────────────────────────────────────────
    Segment("Professional Services", "Franchise development consultants", "small", 2000, 5000,
            flywheel=4.2, ai_rate=4.5, pain=4.5, gap=4.0, access=3.0),
    Segment("Professional Services", "Engineering consulting (civil/structural)", "small", 10000, 4000,
            flywheel=3.8, ai_rate=4.0, pain=4.0, gap=4.2, access=2.8),
    Segment("Professional Services", "Environmental consulting", "small", 6000, 4500,
            flywheel=3.8, ai_rate=4.2, pain=4.0, gap=4.2, access=2.8),
    Segment("Professional Services", "Management consulting boutiques", "small", 8000, 5000,
            flywheel=3.5, ai_rate=4.5, pain=4.0, gap=3.8, access=2.8),
    Segment("Professional Services", "PR firms, small", "small", 5000, 4000,
            flywheel=3.8, ai_rate=4.8, pain=4.0, gap=3.0, access=3.0),
    Segment("Professional Services", "Training / L&D companies", "small", 6000, 3500,
            flywheel=3.8, ai_rate=4.8, pain=4.0, gap=3.5, access=3.0),

    # ── HOME SERVICES / TRADES ────────────────────────────────────────────────
    Segment("Home Services", "HVAC companies (residential)", "small", 60000, 1800,
            flywheel=4.0, ai_rate=4.0, pain=4.5, gap=3.0, access=3.0),
    Segment("Home Services", "Roofing companies (residential/commercial)", "small", 50000, 2000,
            flywheel=4.0, ai_rate=4.2, pain=4.5, gap=3.0, access=3.0),
    Segment("Home Services", "Landscaping / lawn care", "small", 80000, 1500,
            flywheel=4.0, ai_rate=4.2, pain=4.3, gap=3.5, access=3.2),
    Segment("Home Services", "Pool service companies", "micro", 15000, 1800,
            flywheel=4.2, ai_rate=4.2, pain=4.2, gap=4.0, access=3.2),

    # ── NONPROFITS ────────────────────────────────────────────────────────────
    Segment("Nonprofit", "Arts nonprofits, small", "small", 12000, 2500,
            flywheel=4.2, ai_rate=4.8, pain=4.5, gap=4.8, access=3.0),
    Segment("Nonprofit", "Religious organizations / churches", "micro", 80000, 1500,
            flywheel=4.8, ai_rate=4.8, pain=4.3, gap=4.9, access=3.5),
    Segment("Nonprofit", "Social service nonprofits", "small", 30000, 2500,
            flywheel=4.0, ai_rate=4.5, pain=4.3, gap=4.5, access=3.0),
    Segment("Nonprofit", "Community foundations", "medium", 800, 6000,
            flywheel=4.2, ai_rate=4.5, pain=4.2, gap=4.5, access=2.8),
    Segment("Nonprofit", "Education-adjacent nonprofits (tutoring, enrichment)", "small", 8000, 2000,
            flywheel=4.2, ai_rate=4.8, pain=4.2, gap=4.8, access=3.5),

    # ── HOSPITALITY ───────────────────────────────────────────────────────────
    Segment("Hospitality", "Independent fine dining restaurants", "micro", 15000, 2000,
            flywheel=3.8, ai_rate=4.5, pain=4.8, gap=2.8, access=2.8),
    Segment("Hospitality", "Independent boutique hotels", "small", 5000, 3500,
            flywheel=3.8, ai_rate=4.5, pain=4.5, gap=3.0, access=2.8),
    Segment("Hospitality", "Catering companies", "small", 15000, 2500,
            flywheel=4.0, ai_rate=4.5, pain=4.3, gap=4.0, access=3.0),
    Segment("Hospitality", "Independent fitness studios / gyms", "micro", 25000, 2000,
            flywheel=4.2, ai_rate=4.5, pain=4.8, gap=2.8, access=3.2),
]


# ─────────────────────────────────────────────────────────────────────────────
# Default weights  (flywheel-first, matches strategy priority)
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_WEIGHTS = {
    "flywheel": 0.30,
    "ai":       0.25,
    "pain":     0.20,
    "gap":      0.15,
    "access":   0.10,
}


# ─────────────────────────────────────────────────────────────────────────────
# Core logic
# ─────────────────────────────────────────────────────────────────────────────

def rank_segments(
    segments: List[Segment],
    weights: dict,
    industry_filter: Optional[str] = None,
    top_n: int = 20,
) -> List[tuple]:
    if industry_filter:
        segments = [s for s in segments if industry_filter.lower() in s.industry.lower()]
    ranked = sorted(segments, key=lambda s: s.weighted_score(weights), reverse=True)
    return [(i + 1, seg, seg.weighted_score(weights)) for i, seg in enumerate(ranked[:top_n])]


# ─────────────────────────────────────────────────────────────────────────────
# Display
# ─────────────────────────────────────────────────────────────────────────────

COL_W = 52  # segment name column width

def print_results(ranked: List[tuple], weights: dict, total: int):
    w = weights
    header = (
        f"\n{'='*130}\n"
        f"  MARKET SUB-SEGMENT RANKING\n"
        f"  Weights: flywheel={w['flywheel']:.0%}  ai={w['ai']:.0%}  "
        f"pain={w['pain']:.0%}  gap={w['gap']:.0%}  access={w['access']:.0%}\n"
        f"{'='*130}"
    )
    print(header)
    print(
        f"{'Rank':<5} {'Industry':<20} {'Segment':<{COL_W}} "
        f"{'Score':>6}  {'Fly':>4} {'AI':>4} {'Pain':>5} {'Gap':>4} {'Acc':>4}  "
        f"{'Fee/mo':>8}  {'Mkt (US)':>10}"
    )
    print("-" * 130)
    for rank, seg, score in ranked:
        note = f"  ← {seg.notes}" if seg.notes else ""
        print(
            f"#{rank:<4} {seg.industry:<20} {seg.name:<{COL_W}} "
            f"{score:>6.2f}  "
            f"{seg.flywheel:>4.1f} {seg.ai_rate:>4.1f} {seg.pain:>5.1f} "
            f"{seg.gap:>4.1f} {seg.access:>4.1f}  "
            f"${seg.monthly_fee:>6,}/mo  {seg.market_us:>9,}"
            f"{note}"
        )
    print("=" * 130)
    print(f"\nShowing top {len(ranked)} of {total} segments\n")


def print_sensitivity(segments: List[Segment], top_n: int = 10):
    """Compare top rankings under three different strategic weight scenarios."""
    scenarios = {
        "① Flywheel-first   [fly=30% ai=25% pain=20% gap=15% acc=10%]": DEFAULT_WEIGHTS,
        "② AI-delivery-first [fly=15% ai=40% pain=20% gap=15% acc=10%]": dict(
            flywheel=0.15, ai=0.40, pain=0.20, gap=0.15, access=0.10
        ),
        "③ Vibe-access-first [fly=20% ai=20% pain=20% gap=10% acc=30%]": dict(
            flywheel=0.20, ai=0.20, pain=0.20, gap=0.10, access=0.30
        ),
    }
    print(f"\n{'='*90}")
    print("  SENSITIVITY ANALYSIS — top 10 under 3 weight scenarios")
    print(f"{'='*90}")
    for label, w in scenarios.items():
        print(f"\n  {label}")
        print(f"  {'Rank':<5} {'Score':>6}  {'Industry':<20} Segment")
        print(f"  {'-'*80}")
        for rank, seg, score in rank_segments(segments, w, top_n=top_n):
            print(f"  #{rank:<4} {score:>6.2f}  {seg.industry:<20} {seg.name}")
    print()


def export_csv(segments: List[Segment], weights: dict, filepath: str):
    ranked_all = rank_segments(segments, weights, top_n=len(segments))
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "rank", "industry", "name", "size", "market_us", "monthly_fee",
            "score", "flywheel", "ai_rate", "pain", "gap", "access", "notes",
        ])
        for rank, seg, score in ranked_all:
            writer.writerow([
                rank, seg.industry, seg.name, seg.size, seg.market_us,
                seg.monthly_fee, score,
                seg.flywheel, seg.ai_rate, seg.pain, seg.gap, seg.access,
                seg.notes,
            ])
    print(f"Exported {len(ranked_all)} segments → {filepath}")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="OpenVibe Market Sub-Segment Ranker",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--top",         type=int,   default=20,   help="Show top N results (default 20)")
    parser.add_argument("--industry",    type=str,   default=None, help="Filter by industry keyword (e.g. education)")
    parser.add_argument("--csv",         type=str,   default=None, help="Export all ranked results to CSV")
    parser.add_argument("--sensitivity", action="store_true",      help="Show top 10 under 3 weight scenarios")
    parser.add_argument(
        "--weights", type=float, nargs=5, default=None,
        metavar=("FLY", "AI", "PAIN", "GAP", "ACC"),
        help="Custom dimension weights — must sum to 1.0",
    )
    args = parser.parse_args()

    weights = DEFAULT_WEIGHTS.copy()
    if args.weights:
        total = sum(args.weights)
        if abs(total - 1.0) > 0.01:
            print(f"Error: weights must sum to 1.0 (got {total:.3f})")
            sys.exit(1)
        weights = dict(zip(["flywheel", "ai", "pain", "gap", "access"], args.weights))

    if args.sensitivity:
        print_sensitivity(SEGMENTS)
        return

    if args.csv:
        export_csv(SEGMENTS, weights, args.csv)
        return

    ranked = rank_segments(SEGMENTS, weights, industry_filter=args.industry, top_n=args.top)
    print_results(ranked, weights, total=len(SEGMENTS))


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""
fix_figs.py — 修正 Fig5 分支逻辑 + Fig6 表达
Fig5: MPN 池从全库直接分支（不经过"有标准化药名"），改用正交折线
Fig6: Panel A 刻度可读化；Panel B 改分组柱状图
"""
import json, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

ROOT = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒"
FIG = os.path.join(ROOT, "03_figures")
SUP = json.load(open(os.path.join(ROOT, "00_data", "readus_supplement.json"), encoding="utf-8"))
PATCH = json.load(open(os.path.join(ROOT, "00_data", "readus_supplement_patch.json"), encoding="utf-8"))

N_ALL = SUP["flow"]["all"]
N_HAS = SUP["flow"]["has_generic_name"]
N_MPN = SUP["flow"]["mpn_pool"]
N_ANY = PATCH["dedup"]["any_drug"]

# ================= FIG 5 =================
fig, ax = plt.subplots(figsize=(8.2, 6.5), dpi=300)
ax.set_xlim(0, 10); ax.set_ylim(3.05, 10.95); ax.axis("off")
C_BOX, C_EDGE = "#EEF2F7", "#7A8794"
C_HI, C_HI_E = "#FDF0E6", "#B5651D"


def box(x, y, w, h, text, fc=C_BOX, ec=C_EDGE, fs=8.4):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=0.9, zorder=2))
    ax.text(x+w/2, y+h/2, text, ha="center", va="center", fontsize=fs, zorder=3, linespacing=1.5)


def down(x, ytop, ybot):
    ax.add_patch(FancyArrowPatch((x, ytop), (x, ybot), arrowstyle="-|>", mutation_scale=11,
                                 linewidth=1.0, color="#5F6B76", zorder=1))


box(3.0, 10.05, 4.0, 0.68, f"FAERS database\nAll reports received 2004-2026   n = {N_ALL:,}", fs=8.0)

ax.plot([2.40, 2.40], [9.55, 9.55], color="#5F6B76", lw=1.0, zorder=1)
ax.plot([2.40, 7.60], [9.55, 9.55], color="#5F6B76", lw=1.0, zorder=1)
ax.plot([5.00, 5.00], [10.05, 9.55], color="#5F6B76", lw=1.0, zorder=1)
down(2.40, 9.55, 9.02)
down(7.60, 9.55, 9.02)

ax.text(2.55, 9.74, "drug name recorded", fontsize=7.0, color="#42505C", ha="left")
ax.text(7.45, 9.74, "MPN indication recorded", fontsize=7.0, color="#42505C", ha="right")

box(0.35, 8.30, 4.1, 0.72,
    f"Reports with a standardised drug name\nn = {N_HAS:,} ({N_HAS/N_ALL*100:.1f}%)")
box(5.55, 8.30, 4.1, 0.72, f"MPN-indicated reports, any drug\nn = {N_MPN:,}")

down(2.40, 8.30, 7.78)
down(7.60, 8.30, 7.78)
box(0.35, 7.00, 4.1, 0.78, f"Reports containing >=1 study drug\nn = {N_ANY:,} (deduplicated)")
box(5.55, 7.00, 4.1, 0.78, "Level 2 reference\nMPN-indicated reports", fc=C_HI, ec=C_HI_E)

down(2.40, 7.00, 6.45)
down(7.60, 7.00, 6.45)
box(0.35, 5.65, 4.1, 0.80, "Six drugs x 16 MedDRA preferred terms\n114,431 drug-reports (6,062 overlap)")
box(5.55, 5.65, 4.1, 0.80, "Level 3 reference\nSame-disease active comparator\nET: anagrelide vs hydroxyurea", fc="#E8F3EC", ec="#4A7C59", fs=7.9)

down(2.40, 5.65, 5.25)
box(0.35, 4.30, 4.1, 0.95, "Level 1 reference\nAll other drugs in the database", fc=C_HI, ec=C_HI_E)

ax.text(5.0, 3.88, "Disproportionality analysis: ROR with 95% CI, four-criteria signal definition",
        ha="center", fontsize=8.2, color="#2E3A45", fontweight="bold")
ax.text(5.0, 3.56, "Sensitivity analyses: (i) excluding reports listing both comparator drugs;  (ii) serious reports only",
        ha="center", fontsize=7.4, color="#42505C")
ax.text(5.0, 3.26, "Reported according to READUS-PV", ha="center", fontsize=7.4, color="#6B7783", style="italic")

plt.tight_layout()
plt.savefig(os.path.join(FIG, "Fig5_flow_diagram.png"), bbox_inches="tight", facecolor="white")
plt.close()
print("[OK] Fig5")

# ================= FIG 6 =================
trend = SUP["trend"]
years = list(range(2004, 2027))


def series(key):
    d = trend.get(key, {})
    return [d.get(str(y), d.get(y, 0)) for y in years]


fig, axes = plt.subplots(1, 2, figsize=(9.6, 3.9), dpi=300)

ax1 = axes[0]
for key, color, lab, mk in [("Ruxolitinib|ALL", "#B5651D", "Ruxolitinib (all reports)", "o"),
                            ("MPN_POOL|ALL", "#2E5E8C", "MPN-indicated reports (all drugs)", "s"),
                            ("Hydroxyurea|ALL", "#4A7C59", "Hydroxyurea (all reports)", "^")]:
    ax1.plot(years, series(key), marker=mk, ms=2.4, lw=1.4, color=color, label=lab)
ax1.set_yscale("symlog", linthresh=10)
ax1.set_yticks([0, 10, 100, 1000, 10000])
ax1.set_yticklabels(["0", "10", "100", "1,000", "10,000"])
ax1.set_xlabel("Year of report receipt", fontsize=9)
ax1.set_ylabel("Number of reports", fontsize=9)
ax1.set_title("A  Report volume by year (log scale)", fontsize=9.5, loc="left")
ax1.legend(fontsize=7.0, frameon=False, loc="lower right")
ax1.tick_params(labelsize=8)
ax1.grid(alpha=0.22, lw=0.5)

ax2 = axes[1]
ax2.bar([y - 0.19 for y in years], series("Ruxolitinib|Splenic infarction"),
        width=0.38, color="#B5651D", label="Ruxolitinib - splenic infarction")
ax2.bar([y + 0.19 for y in years], series("Anagrelide|Myocardial infarction"),
        width=0.38, color="#8E3B5E", label="Anagrelide - myocardial infarction")
ax2.set_xlabel("Year of report receipt", fontsize=9)
ax2.set_ylabel("Number of reports", fontsize=9)
ax2.set_title("B  The two key drug-event pairs, by year", fontsize=9.5, loc="left")
ax2.legend(fontsize=7.0, frameon=False, loc="upper left")
ax2.tick_params(labelsize=8)
ax2.grid(alpha=0.22, lw=0.5, axis="y")
ax2.set_ylim(0, 12)
ax2.text(0.985, 0.93, "Total 56 and 55 reports over 15 years",
         transform=ax2.transAxes, ha="right", fontsize=7.2, color="#5F5E5A", style="italic")

plt.tight_layout()
plt.savefig(os.path.join(FIG, "Fig6_time_trend.png"), bbox_inches="tight", facecolor="white")
plt.close()
print("[OK] Fig6")

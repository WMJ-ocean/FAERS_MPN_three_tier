# -*- coding: utf-8 -*-
"""
fix_fig5_table1.py
  1) 补 Luspatercept / Ropeginterferon 的 occurcountry（上次因切片漏查）
  2) 重建 Table 1
  3) 重画 Fig 5（修正上一版方框重叠）
"""
import requests, json, time, os, csv

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, Rectangle

BASE = "https://api.fda.gov/drug/event.json"
ROOT = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒"
FIG = os.path.join(ROOT, "03_figures")
TAB = os.path.join(ROOT, "02_tables")

S = requests.Session()
S.headers.update({"User-Agent": "FAERS-pharmacovigilance-research/1.0"})

SUP = json.load(open(os.path.join(ROOT, "00_data", "readus_supplement.json"), encoding="utf-8"))
PATCH = json.load(open(os.path.join(ROOT, "00_data", "readus_supplement_patch.json"), encoding="utf-8"))

DRUGS = {
    "Ruxolitinib": 'patient.drug.openfda.generic_name:"RUXOLITINIB"',
    "Hydroxyurea": 'patient.drug.openfda.generic_name:"HYDROXYUREA"',
    "Anagrelide": 'patient.drug.openfda.generic_name:"ANAGRELIDE"',
    "Busulfan": 'patient.drug.openfda.generic_name:"BUSULFAN"',
    "Luspatercept": 'patient.drug.openfda.generic_name:"LUSPATERCEPT"',
    "Ropeginterferon": 'patient.drug.openfda.generic_name:"ROPEGINTERFERON ALFA-2B"',
}

# ---- 1. 补国家 ----
for d in ["Luspatercept", "Ropeginterferon"]:
    if d in PATCH["country"] and PATCH["country"][d]:
        continue
    r = S.get(BASE, params={"search": DRUGS[d], "count": "occurcountry.exact", "limit": 6}, timeout=60)
    time.sleep(0.4)
    if r.status_code == 200:
        PATCH["country"][d] = {x["term"].strip(): x["count"] for x in r.json()["results"]}
    print(f"  {d}: {PATCH['country'].get(d)}")
json.dump(PATCH, open(os.path.join(ROOT, "00_data", "readus_supplement_patch.json"), "w",
                      encoding="utf-8"), ensure_ascii=False, indent=1)

# ---- 2. Table 1 ----
N_MPN = SUP["flow"]["mpn_pool"]
rows = []
for d in DRUGS:
    n = SUP["flow"][d]
    sx = PATCH["sex"][d]; n_sx = sum(sx.values())
    rp = PATCH["reporter"][d]; n_rp = sum(rp.values())
    ag = SUP["age"][d]; n_ag = sum(v for k, v in ag.items() if k != "missing")
    ct = PATCH["country"].get(d, {})
    top_c = max(ct.items(), key=lambda x: x[1]) if ct else ("NA", 0)
    rows.append({
        "Drug": d, "Reports_n": n,
        "Sex_recorded_pct": round(n_sx/n*100, 1),
        "Male_pct": round(sx["Male"]/n_sx*100, 1) if n_sx else None,
        "Age_recorded_pct": round(n_ag/n*100, 1),
        "Age_65plus_pct": round((ag["65-74"]+ag["75+"])/n_ag*100, 1) if n_ag else None,
        "Healthcare_pct": round((rp["Physician"]+rp["Pharmacist"]+rp["Other HCP"])/n_rp*100, 1) if n_rp else None,
        "Consumer_pct": round(rp["Consumer"]/n_rp*100, 1) if n_rp else None,
        "Top_country": top_c[0],
        "Top_country_pct": round(top_c[1]/n*100, 1),
        "Serious_pct": SUP["serious"][d]["pct"],
    })

with open(os.path.join(TAB, "table1_characteristics.csv"), "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

md = ["| Drug | Reports | Sex rec. | Male | Age rec. | Age >=65 | Healthcare reporter | Consumer reporter | Top country | Serious |",
      "|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    md.append(f"| {r['Drug']} | {r['Reports_n']:,} | {r['Sex_recorded_pct']}% | {r['Male_pct']}% | "
              f"{r['Age_recorded_pct']}% | {r['Age_65plus_pct']}% | {r['Healthcare_pct']}% | "
              f"{r['Consumer_pct']}% | {r['Top_country']} ({r['Top_country_pct']}%) | {r['Serious_pct']}% |")
sx = PATCH["sex"]["MPN_POOL"]; n_sx = sum(sx.values())
rp = PATCH["reporter"]["MPN_POOL"]; n_rp = sum(rp.values())
md.append(f"| **MPN pool** | {N_MPN:,} | {n_sx/N_MPN*100:.1f}% | {sx['Male']/n_sx*100:.1f}% | - | - | "
          f"{(rp['Physician']+rp['Pharmacist']+rp['Other HCP'])/n_rp*100:.1f}% | "
          f"{rp['Consumer']/n_rp*100:.1f}% | - | - |")
open(os.path.join(TAB, "table1_characteristics.md"), "w", encoding="utf-8").write(
    "## Table 1. Characteristics of reports for the six study drugs and the MPN pool\n\n"
    "Percentages for sex, age and reporter type are calculated among reports in which that field was recorded.\n\n"
    + "\n".join(md) + "\n\n"
    "Note: ruxolitinib shows a marked structural deficit of patient-level fields (sex recorded in 29.8% of reports,\n"
    "against 87.9% database-wide). These reports are concentrated from 2017 onward, are predominantly submitted\n"
    "by consumers, and their leading reported term is off-label use rather than an adverse reaction.\n")
print(open(os.path.join(TAB, "table1_characteristics.md"), encoding="utf-8").read())

# ---- 3. Fig 5 ----
fig, ax = plt.subplots(figsize=(8.2, 6.1), dpi=300)
ax.set_xlim(0, 10); ax.set_ylim(3.4, 10.8); ax.axis("off")
C_BOX, C_EDGE = "#EEF2F7", "#7A8794"
C_HI, C_HI_E = "#FDF0E6", "#B5651D"


def box(x, y, w, h, text, fc=C_BOX, ec=C_EDGE, fs=8.5):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=0.9, zorder=2))
    ax.text(x+w/2, y+h/2, text, ha="center", va="center", fontsize=fs, zorder=3, linespacing=1.5)


def arr(p1, p2, txt=None, dx=0, dy=0, ha="center"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle="-|>", mutation_scale=11,
                                 linewidth=1.0, color="#5F6B76", zorder=1))
    if txt:
        mx, my = (p1[0]+p2[0])/2 + dx, (p1[1]+p2[1])/2 + dy
        ax.text(mx, my, txt, ha=ha, va="center", fontsize=7.2, color="#42505C", zorder=4,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none"))


box(3.0, 9.90, 4.0, 0.70, f"FAERS database\nAll reports received 2004-2026\nn = {SUP['flow']['all']:,}", fs=8.2)
box(3.0, 8.85, 4.0, 0.70, f"Reports with a standardised drug name\nn = {SUP['flow']['has_generic_name']:,} (84.1%)")
arr((5.0, 9.90), (5.0, 9.55), "84.1% of all reports", dx=1.05)

box(0.35, 7.55, 4.1, 0.78, f"Reports containing >=1 study drug\nn = {PATCH['dedup']['any_drug']:,} (deduplicated)")
box(5.55, 7.55, 4.1, 0.78, f"MPN-indicated reports, any drug\nn = {N_MPN:,}")
arr((3.70, 8.85), (2.40, 8.33), "at least one study drug", dx=-0.36, dy=0.20)
arr((6.30, 8.85), (7.60, 8.33), "MPN diagnosis recorded", dx=0.42, dy=0.20)

box(0.35, 6.20, 4.1, 0.78, "Six drugs x 16 MedDRA preferred terms\n114,431 drug-reports (6,062 overlap)")
box(5.55, 6.20, 4.1, 0.78, "Level 2 reference\nMPN-indicated reports", fc=C_HI, ec=C_HI_E)
arr((2.40, 7.55), (2.40, 6.98))
arr((7.60, 7.55), (7.60, 6.98))

box(0.35, 4.60, 4.1, 0.95, "Level 1 reference\nAll other drugs in the database", fc=C_HI, ec=C_HI_E)
box(5.55, 4.60, 4.1, 0.95, "Level 3 reference\nSame-disease active comparator\nET: anagrelide vs hydroxyurea", fc="#E8F3EC", ec="#4A7C59", fs=8)
arr((2.40, 6.20), (2.40, 5.55))
arr((7.60, 6.20), (7.60, 5.55))

ax.text(5.0, 4.12, "Disproportionality analysis: ROR with 95% CI, four-criteria signal definition",
        ha="center", fontsize=8.2, color="#2E3A45", fontweight="bold")
ax.text(5.0, 3.80, "(i) excluding reports listing both comparator drugs;  (ii) serious reports only",
        ha="center", fontsize=7.6, color="#42505C")
ax.text(5.0, 3.52, "Reported according to READUS-PV", ha="center",
        fontsize=7.6, color="#6B7783", style="italic")

plt.tight_layout()
p5 = os.path.join(FIG, "Fig5_flow_diagram.png")
plt.savefig(p5, bbox_inches="tight", facecolor="white")
plt.close()
print(f"[OK] {p5}")

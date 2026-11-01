# -*- coding: utf-8 -*-
"""
make_readus_tables_figs.py
  1) 补剩余 3 药的年龄分箱
  2) 生成 Table 1（人群特征）— CSV + Markdown
  3) Fig 5 报告纳入流程图（READUS-PV 8a）
  4) Fig 6 时间趋势（notoriety bias，READUS-PV 13）
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
CACHE = os.path.join(ROOT, "00_data", "readus_cache.json")
CACHE_D = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
SUP = json.load(open(os.path.join(ROOT, "00_data", "readus_supplement.json"), encoding="utf-8"))
PATCH = json.load(open(os.path.join(ROOT, "00_data", "readus_supplement_patch.json"), encoding="utf-8"))


def total(search):
    if search in CACHE_D:
        return CACHE_D[search]
    for _ in range(4):
        try:
            r = S.get(BASE, params={"search": search, "limit": 1}, timeout=60)
            if r.status_code == 200:
                n = r.json()["meta"]["results"]["total"]
                CACHE_D[search] = n
                time.sleep(0.3)
                return n
            if r.status_code == 404:
                CACHE_D[search] = 0
                time.sleep(0.3)
                return 0
            time.sleep(2)
        except Exception:
            time.sleep(2)
    return 0


DRUGS = {
    "Ruxolitinib": 'patient.drug.openfda.generic_name:"RUXOLITINIB"',
    "Hydroxyurea": 'patient.drug.openfda.generic_name:"HYDROXYUREA"',
    "Anagrelide": 'patient.drug.openfda.generic_name:"ANAGRELIDE"',
    "Busulfan": 'patient.drug.openfda.generic_name:"BUSULFAN"',
    "Luspatercept": 'patient.drug.openfda.generic_name:"LUSPATERCEPT"',
    "Ropeginterferon": 'patient.drug.openfda.generic_name:"ROPEGINTERFERON ALFA-2B"',
}
MPN_Q = ('(patient.drug.drugindication:"MYELOFIBROSIS"'
         ' OR patient.drug.drugindication:"PRIMARY MYELOFIBROSIS"'
         ' OR patient.drug.drugindication:"MYELOPROLIFERATIVE NEOPLASM"'
         ' OR patient.drug.drugindication:"MYELOPROLIFERATIVE DISORDER"'
         ' OR patient.drug.drugindication:"POLYCYTHAEMIA VERA"'
         ' OR patient.drug.drugindication:"ESSENTIAL THROMBOCYTHAEMIA")')
AGE_BINS = [("0-17", 0, 17), ("18-44", 18, 44), ("45-64", 45, 64),
            ("65-74", 65, 74), ("75+", 75, 130)]

# ---------- 1. 补年龄 ----------
print("补年龄分箱 ...")
for d, q in DRUGS.items():
    if d in SUP.get("age", {}):
        continue
    row = {}
    for lab, lo, hi in AGE_BINS:
        row[lab] = total(f"{q} AND patient.patientonsetage:[{lo} TO {hi}]")
    row["missing"] = total(f"{q} AND NOT _exists_:patient.patientonsetage")
    SUP["age"][d] = row
    print(f"  {d}: {row}")

json.dump(CACHE_D, open(CACHE, "w", encoding="utf-8"))
json.dump(SUP, open(os.path.join(ROOT, "00_data", "readus_supplement.json"), "w",
                    encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- 2. Table 1 ----------
N_ALL = SUP["flow"]["all"]
N_HAS = SUP["flow"]["has_generic_name"]
N_MPN = SUP["flow"]["mpn_pool"]

rows = []
for d in DRUGS:
    n = SUP["flow"][d]
    sx = PATCH["sex"][d]
    n_sx = sum(sx.values())
    rp = PATCH["reporter"][d]
    n_rp = sum(rp.values())
    ag = SUP["age"][d]
    n_ag = sum(v for k, v in ag.items() if k != "missing")
    ct = PATCH["country"].get(d, {})
    top_c = max(ct.items(), key=lambda x: x[1]) if ct else ("NA", 0)
    se = SUP["serious"][d]
    rows.append({
        "Drug": d,
        "Reports_n": n,
        "Sex_recorded_pct": round(n_sx / n * 100, 1) if n else 0,
        "Male_pct_of_recorded": round(sx["Male"] / n_sx * 100, 1) if n_sx else None,
        "Age_recorded_pct": round(n_ag / n * 100, 1) if n else 0,
        "Age_65plus_pct_of_recorded": round((ag["65-74"] + ag["75+"]) / n_ag * 100, 1) if n_ag else None,
        "Reporter_healthcare_pct": round((rp["Physician"] + rp["Pharmacist"] + rp["Other HCP"]) / n_rp * 100, 1) if n_rp else None,
        "Reporter_consumer_pct": round(rp["Consumer"] / n_rp * 100, 1) if n_rp else None,
        "Top_country": top_c[0],
        "Top_country_pct": round(top_c[1] / n * 100, 1) if n else None,
        "Serious_pct": se["pct"],
    })

p1 = os.path.join(TAB, "table1_characteristics.csv")
with open(p1, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print(f"[OK] {p1}")

md = ["| Drug | Reports | Sex recorded | Male | Age recorded | Age >=65 | Healthcare reporter | Consumer reporter | Top country | Serious |",
      "|---|---|---|---|---|---|---|---|---|---|"]
for r in rows:
    md.append(f"| {r['Drug']} | {r['Reports_n']:,} | {r['Sex_recorded_pct']}% | "
              f"{r['Male_pct_of_recorded']}% | {r['Age_recorded_pct']}% | "
              f"{r['Age_65plus_pct_of_recorded']}% | {r['Reporter_healthcare_pct']}% | "
              f"{r['Reporter_consumer_pct']}% | {r['Top_country']} ({r['Top_country_pct']}%) | "
              f"{r['Serious_pct']}% |")
sx = PATCH["sex"]["MPN_POOL"]
n_sx = sum(sx.values())
rp = PATCH["reporter"]["MPN_POOL"]
n_rp = sum(rp.values())
md.append(f"| **MPN pool** | {N_MPN:,} | {n_sx/N_MPN*100:.1f}% | {sx['Male']/n_sx*100:.1f}% | — | — | "
          f"{(rp['Physician']+rp['Pharmacist']+rp['Other HCP'])/n_rp*100:.1f}% | "
          f"{rp['Consumer']/n_rp*100:.1f}% | — | — |")
open(os.path.join(TAB, "table1_characteristics.md"), "w", encoding="utf-8").write(
    "## Table 1. Characteristics of reports for the six study drugs and the MPN pool\n\n"
    "Percentages for sex, age and reporter are calculated among reports with that field recorded.\n\n"
    + "\n".join(md) + "\n")

# ---------- 3. Fig 5 流程图 ----------
fig, ax = plt.subplots(figsize=(8.2, 6.4), dpi=300)
ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")

C_BOX = "#EEF2F7"; C_EDGE = "#7A8794"; C_HI = "#FDF0E6"; C_HI_E = "#B5651D"


def box(x, y, w, h, text, fc=C_BOX, ec=C_EDGE, fs=9, bold=False):
    ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=0.9, zorder=2))
    ax.text(x + w/2, y + h/2, text, ha="center", va="center", fontsize=fs,
            fontweight="bold" if bold else "normal", zorder=3, linespacing=1.45)


def arrow(x1, y1, x2, y2, txt=None, tx=0, ty=0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>",
                                 mutation_scale=11, linewidth=1.0,
                                 color="#5F6B76", zorder=1))
    if txt:
        ax.text((x1+x2)/2 + tx, (y1+y2)/2 + ty, txt, ha="center", va="center",
                fontsize=7.5, color="#42505C", zorder=4,
                bbox=dict(boxstyle="round,pad=0.22", fc="white", ec="none"))


box(2.9, 9.0, 4.2, 0.82, f"FAERS database\nAll reports, 2004-2026\nn = {N_ALL:,}", fs=9)
arrow(5.0, 9.0, 5.0, 8.2, f"standardised drug name available (84.1%)", tx=1.55, ty=0.0)
box(2.9, 7.38, 4.2, 0.82, f"Reports with any openFDA generic name\nn = {N_HAS:,}", fs=9)
arrow(5.0, 7.38, 5.0, 6.6, f"at least one study drug", tx=1.05)
box(2.9, 5.78, 4.2, 0.82, f"Study-drug exposed reports (deduplicated)\nn = {PATCH['dedup']['any_drug']:,}", fs=9)
arrow(3.7, 5.78, 2.4, 4.75)
arrow(6.3, 5.78, 7.6, 4.75)

box(0.35, 3.95, 4.0, 0.80, "Level 1 reference\nAll other drugs in database", fc=C_HI, ec=C_HI_E, fs=8.5)
box(5.65, 3.95, 4.0, 0.80, "Level 2 reference\nMPN-indicated reports", fc=C_HI, ec=C_HI_E, fs=8.5)

arrow(5.0, 7.38, 2.35, 4.75)
ax.text(3.05, 6.55, "", fontsize=7)

box(5.65, 5.62, 4.0, 0.82, f"MPN-indicated reports (any drug)\nn = {N_MPN:,}", fs=8.5)
box(0.35, 5.62, 4.0, 0.82, "Six drugs x 16 MedDRA PT\n114,431 drug-reports (6,062 overlap)", fs=8.5)

box(0.35, 2.55, 4.0, 0.80, "Level 3: same-disease active comparator\nET: anagrelide vs hydroxyurea\nMF: ruxolitinib vs hydroxyurea", fc="#E8F3EC", ec="#4A7C59", fs=8.5)
box(5.65, 2.55, 4.0, 0.80, "Case-by-case review not performed\n(no narrative text via openFDA)", fs=8.5)
arrow(2.35, 3.95, 2.35, 3.35)
arrow(7.65, 3.95, 7.65, 3.35)

ax.text(5.0, 1.85, "Disproportionality analysis: ROR with 95% CI, four-criteria signal definition",
        ha="center", fontsize=8.5, color="#2E3A45", fontweight="bold")
ax.text(5.0, 1.45, "Sensitivity: (i) excluding reports listing both comparator drugs; (ii) serious reports only",
        ha="center", fontsize=8, color="#42505C")
ax.text(5.0, 0.95, "Reported according to READUS-PV",
        ha="center", fontsize=8, color="#6B7783", style="italic")

plt.tight_layout()
p5 = os.path.join(FIG, "Fig5_flow_diagram.png")
plt.savefig(p5, bbox_inches="tight", facecolor="white")
plt.close()
print(f"[OK] {p5}")

# ---------- 4. Fig 6 时间趋势 ----------
trend = SUP["trend"]
years = list(range(2004, 2027))
fig, axes = plt.subplots(1, 2, figsize=(9.4, 3.9), dpi=300)

ax1 = axes[0]
for name, color, lab in [("Ruxolitinib|ALL", "#B5651D", "Ruxolitinib (all reports)"),
                         ("MPN_POOL|ALL", "#2E5E8C", "MPN-indicated reports (all drugs)"),
                         ("Hydroxyurea|ALL", "#4A7C59", "Hydroxyurea (all reports)")]:
    if name in trend:
        ax1.plot(years, [trend[name].get(str(y), trend[name].get(y, 0)) for y in years],
                 marker="o", ms=2.5, lw=1.4, color=color, label=lab)
ax1.set_yscale("symlog")
ax1.set_xlabel("Year of report receipt", fontsize=9)
ax1.set_ylabel("Number of reports", fontsize=9)
ax1.set_title("A  Report volume by year", fontsize=10, loc="left")
ax1.legend(fontsize=7.3, frameon=False)
ax1.tick_params(labelsize=8)
ax1.grid(alpha=0.25, lw=0.5)

ax2 = axes[1]
for name, color, lab in [("Ruxolitinib|Splenic infarction", "#B5651D", "Ruxolitinib - splenic infarction"),
                         ("Anagrelide|Myocardial infarction", "#8E3B5E", "Anagrelide - myocardial infarction")]:
    if name in trend:
        ax2.plot(years, [trend[name].get(str(y), trend[name].get(y, 0)) for y in years],
                 marker="s", ms=3, lw=1.4, color=color, label=lab)
ax2.set_xlabel("Year of report receipt", fontsize=9)
ax2.set_ylabel("Number of reports", fontsize=9)
ax2.set_title("B  Key drug-event pairs", fontsize=10, loc="left")
ax2.legend(fontsize=7.3, frameon=False)
ax2.tick_params(labelsize=8)
ax2.grid(alpha=0.25, lw=0.5)
ax2.set_ylim(bottom=0)

plt.tight_layout()
p6 = os.path.join(FIG, "Fig6_time_trend.png")
plt.savefig(p6, bbox_inches="tight", facecolor="white")
plt.close()
print(f"[OK] {p6}")

print()
print(open(os.path.join(TAB, "table1_characteristics.md"), encoding="utf-8").read())

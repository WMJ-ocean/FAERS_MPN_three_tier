# -*- coding: utf-8 -*-
"""
make_figures.py — 出图（全部从 CSV 读取，不手写任何数字）
Fig 1  全库对照 vs MPN 内对照的 ROR 散点（展示系统性衰减）
Fig 2  ET 内 anagrelide vs hydroxyurea 森林图（主分析 + 两个敏感性）
Fig 3  六药 × 十六 PT 的 ROR 热图（全库对照，展示"信号遍地"的假象）
Fig 4  MF 内 ruxolitinib vs hydroxyurea 森林图
"""
import os, csv, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

TAB = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒\02_tables"
FIG = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒\03_figures"
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 9,
    "axes.linewidth": 0.8,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
})


def rd(path):
    rows = []
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


# ============ Fig 1  全库 vs MPN 内 ============
allr = rd(os.path.join(TAB, "faers_ror_all.csv"))
mpnr = rd(os.path.join(TAB, "faers_ror_mpn_stratified.csv"))
M = {(r["drug"], r["pt"]): r for r in mpnr}

xs, ys, labels = [], [], []
for r in allr:
    k = (r["drug"], r["pt"])
    if k not in M:
        continue
    x, y = f(r["ROR"]), f(M[k]["ROR"])
    if x and y and x > 0 and y > 0:
        xs.append(x); ys.append(y); labels.append(k)

fig, ax = plt.subplots(figsize=(5.6, 5.2))
lim = (0.08, 45)
ax.plot(lim, lim, ls="--", lw=0.8, color="grey", zorder=1, label="identity (no change)")
ax.axhline(1, lw=0.6, color="grey", alpha=0.5)
ax.axvline(1, lw=0.6, color="grey", alpha=0.5)

ax.scatter(xs, ys, s=22, c="#3b6ea5", alpha=0.75, edgecolors="white",
           linewidths=0.4, zorder=2)

# 只标注全库 ROR 最大的三个点（均集中于脾/门静脉事件），标签置于点左侧并垂直错开
ABBR = {"Ruxolitinib": "rux", "Hydroxyurea": "HU", "Anagrelide": "ana",
        "Busulfan": "bus", "Luspatercept": "lus", "Ropeginterferon alfa-2b": "rope"}
hi = sorted([(k, x, y) for k, x, y in zip(labels, xs, ys) if x > 10],
            key=lambda t: -t[2])[:3]
offsets = [(-7, 10), (-7, -6), (-7, -22)]
for (k, x, y), off in zip(hi, offsets):
    ax.annotate(f"{k[1]} ({ABBR.get(k[0], k[0][:4])})",
                (x, y), fontsize=5.8, xytext=off, textcoords="offset points",
                color="#b03a2e", va="center", ha="right")

ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlim(*lim); ax.set_ylim(*lim)
ax.set_xlabel("ROR — unselected background (all FAERS reports)")
ax.set_ylabel("ROR — within-MPN background")
ax.set_title("Shrinkage of disproportionality signals after\nrestricting the background to MPN reports", fontsize=10)
ax.legend(frameon=False, fontsize=7.5, loc="lower right")
ax.text(0.03, 0.96, f"n = {len(xs)} drug–event pairs",
        transform=ax.transAxes, fontsize=7.5, va="top", color="#444")
fig.savefig(os.path.join(FIG, "Fig1_unselected_vs_MPN.png"))
plt.close(fig)
print("[OK] Fig1")

# ============ Fig 2 / Fig 4  森林图 ============
h2h = rd(os.path.join(TAB, "faers_head_to_head.csv"))
sens = rd(os.path.join(TAB, "faers_sensitivity.csv"))

SENS = {}
for r in sens:
    SENS[(r["disease"], r["pair"], r["pt"], r["scenario"])] = r


def forest(dis, da, db, fname, title):
    rows = [r for r in h2h if r["disease"] == dis and f"{r['drug_a']}_vs_{r['drug_b']}" == f"{da}_vs_{db}"]
    rows = [r for r in rows if f(r["ROR"]) and f(r["ROR025"]) and f(r["ROR975"])]
    # 按主分析 ROR 排序（升序 → 图上从下到上）
    rows.sort(key=lambda r: f(r["ROR"]))

    fig, ax = plt.subplots(figsize=(6.2, 0.42 * len(rows) + 1.6))
    ypos = np.arange(len(rows))

    for i, r in enumerate(rows):
        ror, lo, hi_ = f(r["ROR"]), f(r["ROR025"]), f(r["ROR975"])
        ax.plot([lo, hi_], [i, i], color="#2c3e50", lw=1.1, zorder=2)
        ax.scatter([ror], [i], s=34, color="#2c3e50", zorder=3, marker="s")

        # S1 排除联用
        s1 = SENS.get((dis, f"{da}_vs_{db}", r["pt"], "S1_excl_combo"))
        if s1 and f(s1["ROR"]) and f(s1["ROR025"]) and f(s1["ROR975"]):
            ax.plot([f(s1["ROR025"]), f(s1["ROR975"])], [i + .16, i + .16],
                    color="#c0392b", lw=1.0, zorder=2, alpha=.9)
            ax.scatter([f(s1["ROR"])], [i + .16], s=26, color="#c0392b",
                       zorder=3, marker="o", alpha=.9)

    ax.axvline(1, ls="--", lw=0.9, color="grey")
    ax.set_yticks(ypos)
    ax.set_yticklabels([r["pt"] for r in rows], fontsize=8)
    ax.set_xscale("log")
    ax.set_xlabel(f"ROR  ({da} vs {db})")
    ax.set_title(title, fontsize=10)
    ax.set_ylim(-0.7, len(rows) - 0.3)
    ax.grid(axis="x", ls=":", lw=0.5, alpha=0.6)

    # 自定义图例
    from matplotlib.lines import Line2D
    ax.legend(handles=[
        Line2D([], [], color="#2c3e50", marker="s", lw=1.1, ms=5,
               label="all reports (drug A vs drug B)"),
        Line2D([], [], color="#c0392b", marker="o", lw=1.0, ms=4,
               label="excluding reports using both drugs"),
    ], frameon=False, fontsize=7.5, loc="lower right")

    fig.savefig(os.path.join(FIG, fname))
    plt.close(fig)
    print(f"[OK] {fname}  ({len(rows)} PT)")


forest("ET", "Anagrelide", "Hydroxyurea", "Fig2_forest_ET_anagrelide_vs_HU.png",
       "Essential thrombocythaemia: anagrelide vs hydroxyurea")
forest("MF", "Ruxolitinib", "Hydroxyurea", "Fig3_forest_MF_ruxolitinib_vs_HU.png",
       "Myelofibrosis: ruxolitinib vs hydroxyurea")

# ============ Fig 5  热图 ============
drugs = ["Ruxolitinib", "Hydroxyurea", "Anagrelide", "Busulfan",
         "Luspatercept", "Ropeginterferon alfa-2b"]
pts = ["Splenic infarction", "Portal vein thrombosis", "Budd-Chiari syndrome",
       "Splenic vein thrombosis", "Arterial thrombosis", "Transient ischaemic attack",
       "Thrombosis", "Embolism", "Venous thrombosis", "Pulmonary embolism",
       "Myocardial infarction", "Cerebrovascular accident",
       "Thrombophlebitis", "Deep vein thrombosis", "Retinal vein occlusion", "Haemorrhage"]

mat = np.full((len(drugs), len(pts)), np.nan)
sig = np.zeros_like(mat, dtype=bool)
for r in allr:
    if r["drug"] in drugs and r["pt"] in pts:
        i, j = drugs.index(r["drug"]), pts.index(r["pt"])
        v = f(r["ROR"])
        if v and v > 0:
            mat[i, j] = math.log2(v)
            sig[i, j] = (r["signal"] == "YES")

fig, ax = plt.subplots(figsize=(7.6, 3.6))
vmax = 3.2
im = ax.imshow(mat, cmap="RdBu_r", vmin=-vmax, vmax=vmax, aspect="auto")
for i in range(len(drugs)):
    for j in range(len(pts)):
        if np.isnan(mat[i, j]):
            continue
        if sig[i, j]:
            ax.text(j, i, "*", ha="center", va="center", fontsize=11, color="black")
ax.set_xticks(range(len(pts)))
ax.set_xticklabels(pts, rotation=55, ha="right", fontsize=7)
ax.set_yticks(range(len(drugs)))
ax.set_yticklabels(drugs, fontsize=7.5)
ax.set_title("Reporting odds ratios against the unselected FAERS background\n"
             "(* = meets all four signal criteria)", fontsize=9.5)
cb = fig.colorbar(im, ax=ax, fraction=0.026, pad=0.015)
cb.set_label("log$_2$ ROR", fontsize=8)
cb.ax.tick_params(labelsize=7)
fig.savefig(os.path.join(FIG, "Fig4_heatmap_unselected.png"))
plt.close(fig)
print("[OK] Fig4 heatmap")

print()
print("文件清单：")
for fn in sorted(os.listdir(FIG)):
    p = os.path.join(FIG, fn)
    print(f"  {fn:46s} {os.path.getsize(p)//1024:>5} KB")

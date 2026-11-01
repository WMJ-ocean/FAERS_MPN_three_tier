# -*- coding: utf-8 -*-
"""
figures_final.py — 投稿版图件（300 dpi，180 mm 宽，无内嵌标题）
=============================================================
Fig 1  报告纳入流程
Fig 2  信号衰减散点（L1 全库参照 → L2 MPN 内参照）
Fig 3  森林图两联：(A) ET 阿那格雷 vs 羟基脲；(B) MF 芦可替尼 vs 羟基脲
Fig 4  六药 × 十六事件热图（L1）
Fig 5  报告量时间趋势（notoriety bias）
"""
import csv, os, math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

BASE = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒"
FIG = os.path.join(BASE, "03_figures")
os.makedirs(FIG, exist_ok=True)

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "DejaVu Sans"],
    "font.size": 8.5,
    "axes.linewidth": 0.8,
    "axes.labelsize": 9,
    "xtick.labelsize": 8,
    "ytick.labelsize": 8,
    "legend.fontsize": 7.5,
    "savefig.dpi": 300,
    "savefig.bbox": "tight",
    "figure.dpi": 300,
})

INK = "#1B2A38"
MUTED = "#6B7885"
RED = "#B03A2E"
BLUE = "#2C5F7C"
LIGHT = "#E8EDF2"


def rd(p):
    with open(p, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


L1 = {(r["drug"], r["pt"]): r for r in rd(os.path.join(BASE, "02_tables", "faers_ror_all.csv"))}
L2 = {(r["drug"], r["pt"]): r for r in rd(os.path.join(BASE, "02_tables", "faers_ror_mpn_stratified.csv"))}

SPLANCHNIC = ["Splenic infarction", "Portal vein thrombosis", "Splenic vein thrombosis",
              "Budd-Chiari syndrome"]


# ============================================================ Fig 1  流程图
def fig1():
    fig, ax = plt.subplots(figsize=(6.9, 5.3))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis("off")

    def box(x, y, w, h, text, fc="white", ec=INK, fs=7.6, bold=False, lw=0.9):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.10,rounding_size=0.12",
                                    linewidth=lw, edgecolor=ec, facecolor=fc, zorder=3))
        ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs,
                color=INK, zorder=4, linespacing=1.45,
                fontweight="bold" if bold else "normal")

    def arrow(x1, y1, x2, y2, style="-|>", ls="-"):
        ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                     mutation_scale=9, color=MUTED, lw=0.8,
                                     linestyle=ls, zorder=2, shrinkA=0, shrinkB=2))

    # 顶端
    box(2.35, 8.85, 5.3, 0.85, "FAERS / openFDA drug-event reports\nretrieved 1 November 2026\ntotal N = 20,692,690",
        fc=LIGHT, bold=True, fs=8.0)

    # 两条分支：从顶端盒底中点引出，再横向分开
    ax.plot([5.0, 5.0], [8.85, 8.55], color=MUTED, lw=0.8, zorder=1)
    ax.plot([2.55, 7.45], [8.55, 8.55], color=MUTED, lw=0.8, zorder=1)
    ax.plot([2.55, 2.55], [8.55, 8.15], color=MUTED, lw=0.8, zorder=1)
    ax.plot([7.45, 7.45], [8.55, 8.15], color=MUTED, lw=0.8, zorder=1)
    arrow(2.55, 8.15, 2.55, 7.99)
    arrow(7.45, 8.15, 7.45, 7.99)
    ax.text(3.75, 8.33, "drug-based selection", fontsize=7.2, color=MUTED,
            ha="center", va="center")
    ax.text(6.20, 8.33, "indication-based selection", fontsize=7.2, color=MUTED,
            ha="center", va="center")

    # 左支：药物
    box(0.35, 7.02, 4.4, 0.90,
        "Reports with a standardised drug name\nn = 17,409,949  (84.1% of all reports)", fs=7.4)
    arrow(2.55, 7.02, 2.55, 6.70)
    box(0.35, 5.80, 4.4, 0.88,
        "Reports naming at least one of the\nsix study drugs\nn = 108,369 (unique reports)", fs=7.4)
    arrow(2.55, 5.80, 2.55, 5.48)
    box(0.35, 4.58, 4.4, 0.88,
        "Drug-event pairs analysed\n6 drugs \u00d7 16 MedDRA preferred terms\nn = 96 pairs", fs=7.4)
    ax.text(2.55, 4.28, "114,431 drug mentions in total;\n6,062 reports named more than one study drug",
            fontsize=7.0, color=MUTED, ha="center", va="top", linespacing=1.4)

    # 右支：适应证
    box(5.25, 7.02, 4.4, 0.90,
        "Reports recording an MPN indication\nin any drug field\nn = 58,602  (0.28% of all reports)", fs=7.4)
    arrow(7.45, 7.02, 7.45, 6.70)
    box(5.25, 5.80, 4.4, 0.88,
        "MPN reference pool for tier 2\n58,602 reports; 14,800 exposed to\nnone of the six drugs", fs=7.4)
    arrow(7.45, 5.80, 7.45, 5.48)
    box(5.25, 4.58, 4.4, 0.88,
        "Within-disease reference\n(drug-exposed vs unexposed MPN)", fs=7.4)
    ax.text(7.45, 4.28, "Independent selection: MPN reports need not\nname a study drug",
            fontsize=7.0, color=MUTED, ha="center", va="top", linespacing=1.4)

    # 底部：三层参照
    box(0.55, 1.60, 2.85, 1.95,
        "Tier 1\nall other reports\ndatabase-wide\n(reference c, d)", fc="#F4F1EC", fs=7.4)
    box(3.55, 1.60, 2.85, 1.95,
        "Tier 2\nMPN reports without\nthe index drug\n(reference c, d)", fc="#F4F1EC", fs=7.4)
    box(6.55, 1.60, 2.85, 1.95,
        "Tier 3\nsame disease,\ncomparator drug\n(head-to-head)", fc="#F4F1EC", fs=7.4)
    ax.text(5.0, 1.20, "Three reference definitions applied to the same drug-event pairs",
            fontsize=7.8, color=INK, ha="center", va="center", fontweight="bold")
    ax.text(5.0, 0.62, "Reporting odds ratio = (a/b) / (c/d)",
            fontsize=8.4, color=INK, ha="center", va="center", style="italic")

    fig.savefig(os.path.join(FIG, "Fig1_flow_diagram.png"), facecolor="white")
    plt.close(fig)
    print("[Fig1] ok")


# ============================================================ Fig 2  衰减散点
def fig2():
    pts = []
    for (d, p), r in L1.items():
        if r["ROR"] in ("", None):
            continue
        r2 = L2.get((d, p))
        if not r2 or r2["ROR"] in ("", None):
            continue
        v1, v2 = float(r["ROR"]), float(r2["ROR"])
        if v1 <= 0 or v2 <= 0:
            continue
        pts.append((d, p, v1, v2))

    fig, ax = plt.subplots(figsize=(5.6, 5.2))
    x = np.array([p[2] for p in pts])
    y = np.array([p[3] for p in pts])

    ax.axhline(1, color=MUTED, lw=0.6, ls="-", zorder=1)
    ax.axvline(1, color=MUTED, lw=0.6, ls="-", zorder=1)
    lim = [0.09, 60]
    ax.plot(lim, lim, color=MUTED, lw=0.8, ls=(0, (4, 2.5)), zorder=1,
            label="no change (identity)")

    sig = np.array([L1[(p[0], p[1])]["signal"].strip() == "YES" for p in pts])
    ax.scatter(x[~sig], y[~sig], s=22, facecolor="white", edgecolor=BLUE, linewidth=0.8,
               zorder=3, label="not a signal at tier 1 (n = %d)" % (~sig).sum())
    ax.scatter(x[sig], y[sig], s=30, facecolor=BLUE, edgecolor=BLUE, linewidth=0.8,
               zorder=4, label="signal at tier 1 (n = %d)" % sig.sum())

    # 三个关键点用编号标注，说明文字集中放在右下空白区，避免引线交叉
    annots = [
        ("Anagrelide", "Myocardial infarction", "1", (6, 6), "left"),
        ("Hydroxyurea", "Splenic infarction", "2", (-11, 5), "right"),
        ("Ruxolitinib", "Splenic infarction", "3", (6, -8), "left"),
    ]
    for d, p, num, off, ha in annots:
        r2 = L2.get((d, p))
        if not r2 or not r2["ROR"]:
            continue
        xv, yv = float(L1[(d, p)]["ROR"]), float(r2["ROR"])
        ax.scatter([xv], [yv], s=150, facecolor="none", edgecolor=RED, linewidth=1.0,
                   zorder=5)
        ax.annotate(num, xy=(xv, yv), xytext=off, textcoords="offset points",
                    fontsize=7.4, color=RED, ha=ha, va="center", fontweight="bold",
                    zorder=6)
    ax.text(0.975, 0.10,
            "1  anagrelide \u2013 myocardial infarction\n"
            "2  hydroxyurea \u2013 splenic infarction\n"
            "3  ruxolitinib \u2013 splenic infarction",
            transform=ax.transAxes, fontsize=7.0, color=RED, ha="right", va="bottom",
            linespacing=1.6)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlim(lim)
    ax.set_ylim(lim)
    ax.set_xlabel("ROR against all other reports (tier 1)")
    ax.set_ylabel("ROR against MPN reports (tier 2)")
    ax.legend(loc="upper left", frameon=False, handletextpad=0.5, borderpad=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.text(0.985, 0.03, "points below the dashed line shrank", transform=ax.transAxes,
            fontsize=7.0, color=MUTED, ha="right", style="italic")

    fig.savefig(os.path.join(FIG, "Fig2_attenuation_scatter.png"), facecolor="white")
    plt.close(fig)
    print("[Fig2] ok  n=%d" % len(pts))


# ============================================================ Fig 3  富集-衰减
def fig3():
    en = {r["pt"]: float(r["enrichment"]) for r in
          rd(os.path.join(BASE, "02_tables", "background_enrichment.csv"))}
    pairs = []
    for (d, p), r in L1.items():
        r2 = L2.get((d, p))
        if not r.get("ROR") or not r2 or not r2.get("ROR"):
            continue
        v1, v2 = float(r["ROR"]), float(r2["ROR"])
        if v1 <= 0 or v2 <= 0:
            continue
        pairs.append((p, en[p], v1 / v2, r["signal"].strip() == "YES"))

    fig, ax = plt.subplots(figsize=(5.4, 4.6))
    xs = np.log2([q[1] for q in pairs])
    ys = np.log2([q[2] for q in pairs])
    isgn = np.array([q[3] for q in pairs])

    ax.axhline(0, color=MUTED, lw=0.6)
    ax.axvline(0, color=MUTED, lw=0.6)

    # OLS on log2 scale
    b = np.sum((xs - xs.mean()) * (ys - ys.mean())) / np.sum((xs - xs.mean()) ** 2)
    a0 = ys.mean() - b * xs.mean()
    r2 = 1 - np.sum((ys - (a0 + b * xs)) ** 2) / np.sum((ys - ys.mean()) ** 2)
    grid = np.linspace(xs.min() - 0.3, xs.max() + 0.3, 50)
    ax.plot(2 ** grid, 2 ** (a0 + b * grid), color=RED, lw=1.3, zorder=2,
            label=f"fitted: slope {b:.2f}, $R^2$ = {r2:.2f}")

    ax.scatter(2 ** xs[~isgn], 2 ** ys[~isgn], s=24, facecolor="white", edgecolor=BLUE,
               linewidth=0.8, zorder=3, label="not a signal at tier 1")
    ax.scatter(2 ** xs[isgn], 2 ** ys[isgn], s=32, facecolor=BLUE, edgecolor=BLUE,
               linewidth=0.8, zorder=4, label="signal at tier 1")

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Background enrichment of the event in MPN reports\n"
                  "(MPN prevalence \u00f7 database prevalence)")
    ax.set_ylabel("Signal inflation at tier 1\n(ROR tier 1 \u00f7 ROR tier 2)")
    ax.legend(loc="upper left", frameon=False, handletextpad=0.5, borderpad=0.2,
              labelspacing=0.4)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.text(0.975, 0.035,
            "slope \u2248 1: the inflation factor equals\nthe disease-driven enrichment",
            transform=ax.transAxes, fontsize=7.0, color=RED, ha="right", va="bottom",
            linespacing=1.5)

    fig.savefig(os.path.join(FIG, "Fig3_enrichment_vs_inflation.png"), facecolor="white")
    plt.close(fig)
    print(f"[Fig3] ok  n={len(pairs)}  slope={b:.3f}  R2={r2:.3f}")


# ============================================================ Fig 4  森林图
def forest_panel(ax, rows, title):
    rows = [r for r in rows if r["ROR"] not in ("", None)]
    rows.sort(key=lambda r: float(r["ROR"]))
    ys = np.arange(len(rows))
    for i, r in enumerate(rows):
        v, lo, hi = float(r["ROR"]), float(r["ROR025"]), float(r["ROR975"])
        col = RED if lo > 1 else (BLUE if hi < 1 else MUTED)
        ax.plot([lo, hi], [i, i], color=col, lw=1.1, solid_capstyle="butt", zorder=2)
        ax.plot(v, i, marker="s", ms=4.0, color=col, zorder=3)
    ax.axvline(1, color=INK, lw=0.7, ls=(0, (3, 2)), zorder=1)
    ax.set_yticks(ys)
    ax.set_yticklabels([r["pt"] for r in rows], fontsize=7.2)
    ax.set_xscale("log")
    ax.set_xlim(0.02, 60)
    ax.set_ylim(-0.8, len(rows) - 0.2)
    ax.set_xlabel("ROR (log scale)")
    ax.set_title(title, fontsize=8.6, color=INK, pad=6, loc="left", fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    return rows


def fig4():
    h2h = rd(os.path.join(BASE, "02_tables", "faers_head_to_head.csv"))
    fig, axes = plt.subplots(1, 2, figsize=(7.1, 3.9), sharex=True,
                             gridspec_kw={"wspace": 0.52})
    forest_panel(axes[0], [r for r in h2h if r["disease"] == "ET"],
                 "A  Essential thrombocythaemia\nanagrelide vs hydroxyurea")
    forest_panel(axes[1], [r for r in h2h if r["disease"] == "MF"],
                 "B  Myelofibrosis\nruxolitinib vs hydroxyurea")
    handles = [plt.Line2D([], [], color=RED, marker="s", ms=4, lw=1.1, label="higher on index drug"),
               plt.Line2D([], [], color=MUTED, marker="s", ms=4, lw=1.1, label="95% CI includes 1"),
               plt.Line2D([], [], color=BLUE, marker="s", ms=4, lw=1.1, label="lower on index drug")]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, fontsize=7.2,
               handletextpad=0.4, columnspacing=2.2, bbox_to_anchor=(0.5, -0.045))
    fig.savefig(os.path.join(FIG, "Fig4_forest_head_to_head.png"), facecolor="white")
    plt.close(fig)
    print("[Fig4] ok")


# ============================================================ Fig S1  热图
def figS1():
    drugs = ["Ruxolitinib", "Hydroxyurea", "Anagrelide", "Busulfan", "Luspatercept",
             "Ropeginterferon alfa-2b"]
    pts = ["Splenic infarction", "Portal vein thrombosis", "Splenic vein thrombosis",
           "Budd-Chiari syndrome", "Arterial thrombosis", "Myocardial infarction",
           "Cerebrovascular accident", "Transient ischaemic attack", "Retinal vein occlusion",
           "Thrombosis", "Venous thrombosis", "Embolism", "Pulmonary embolism",
           "Deep vein thrombosis", "Thrombophlebitis", "Haemorrhage"]
    M = np.full((len(drugs), len(pts)), np.nan)
    S = np.zeros((len(drugs), len(pts)), dtype=bool)
    A = np.zeros((len(drugs), len(pts)), dtype=int)
    for i, d in enumerate(drugs):
        for j, p in enumerate(pts):
            r = L1.get((d, p))
            if not r or r["ROR"] in ("", None):
                continue
            M[i, j] = math.log2(float(r["ROR"]))
            S[i, j] = r["signal"].strip() == "YES"
            A[i, j] = int(float(r["a"]))
    M = np.clip(M, -3.2, 3.2)
    cmap = plt.get_cmap("RdBu_r").copy()
    cmap.set_bad("#FFFFFF")

    fig, ax = plt.subplots(figsize=(7.1, 3.5))
    im = ax.imshow(M, cmap=cmap, vmin=-3.2, vmax=3.2, aspect="auto")
    ax.set_xticks(range(len(pts)))
    ax.set_xticklabels(pts, rotation=48, ha="right", fontsize=6.9)
    ax.set_yticks(range(len(drugs)))
    ax.set_yticklabels(drugs, fontsize=7.4)
    ax.set_xticks(np.arange(-0.5, len(pts), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(drugs), 1), minor=True)
    ax.grid(which="minor", color="white", lw=0.8)
    ax.tick_params(which="minor", length=0)
    ax.tick_params(axis="x", length=0)
    for i in range(len(drugs)):
        for j in range(len(pts)):
            if S[i, j]:
                ax.text(j, i, "*", ha="center", va="center", fontsize=8.5, color="white")
    cb = fig.colorbar(im, ax=ax, fraction=0.026, pad=0.015)
    cb.set_label("log$_2$ ROR", fontsize=7.5)
    cb.ax.tick_params(labelsize=6.8, length=2)
    cb.set_ticks([-3, -2, -1, 0, 1, 2, 3])
    ax.text(1.0, -0.30, "* meets all four signal criteria \u00b7 white = fewer than three reports",
            transform=ax.transAxes, fontsize=6.8, color=MUTED, ha="right", va="top")

    fig.savefig(os.path.join(FIG, "FigS1_heatmap_tier1.png"), facecolor="white")
    plt.close(fig)
    print("[FigS1] ok")


# ============================================================ Fig 5  时间趋势
def fig5():
    rows = rd(os.path.join(BASE, "02_tables", "readus_time_trend.csv"))
    years = [int(c) for c in rows[0].keys() if c.isdigit()]
    data = {}
    for r in rows:
        data[r["series"]] = [int(r[str(y)]) for y in years]
    years = [y for y in years if y <= 2025]
    n = len(years)
    for k in data:
        data[k] = data[k][:n]

    fig, axes = plt.subplots(1, 2, figsize=(7.1, 3.1), gridspec_kw={"wspace": 0.32})

    ax = axes[0]
    ax.plot(years, data["Ruxolitinib|ALL"], color=BLUE, lw=1.4, label="ruxolitinib, all reports")
    ax.plot(years, data["MPN_POOL|ALL"], color=MUTED, lw=1.2, ls=(0, (4, 2)),
            label="all MPN reports")
    ax.plot(years, data["Hydroxyurea|ALL"], color="#8A9AA6", lw=1.0, ls=(0, (1, 1.6)),
            label="hydroxyurea, all reports")
    ax.set_ylabel("Reports per year")
    ax.set_xlabel("Year of receipt")
    ax.set_xlim(min(years), max(years))
    ax.set_title("A  Report volume", fontsize=8.4, loc="left", fontweight="bold")
    ax.legend(loc="upper left", frameon=False, fontsize=6.8, handlelength=1.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax = axes[1]
    d = data["Ruxolitinib|Splenic infarction"]
    ax.bar(years, d, color=RED, width=0.72, alpha=0.85)
    ax.set_ylabel("Reports per year")
    ax.set_xlabel("Year of receipt")
    ax.set_xlim(min(years) - 0.6, max(years) + 0.6)
    ax.set_title("B  Ruxolitinib and splenic infarction", fontsize=8.4, loc="left",
                 fontweight="bold")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    tot = sum(d)
    ax.text(0.03, 0.96, f"total {tot} reports over {len([x for x in d if x>0])} years\n"
                        f"peak {max(d)} in {years[d.index(max(d))]}",
            transform=ax.transAxes, ha="left", va="top", fontsize=6.9, color=INK,
            linespacing=1.5)

    fig.savefig(os.path.join(FIG, "Fig5_time_trend.png"), facecolor="white")
    plt.close(fig)
    print("[Fig5] ok")


fig1(); fig2(); fig3(); fig4(); figS1(); fig5()
print("done")

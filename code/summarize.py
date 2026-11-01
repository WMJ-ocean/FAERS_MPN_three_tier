# -*- coding: utf-8 -*-
"""
summarize.py — 从 CSV 生成可直接粘贴的 markdown 表格（杜绝手抄数字）
"""
import csv, os

TAB = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒\02_tables"
OUT = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒\00_data"


def rd(name):
    with open(os.path.join(TAB, name), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def f(x, d=2):
    try:
        return f"{float(x):.{d}f}"
    except (TypeError, ValueError):
        return "—"


lines = []

# ---------- Table 1  三层对照的代表性衰减 ----------
allr = {(r["drug"], r["pt"]): r for r in rd("faers_ror_all.csv")}
mpn = {(r["drug"], r["pt"]): r for r in rd("faers_ror_mpn_stratified.csv")}

KEY = [
    ("Hydroxyurea", "Splenic infarction"),
    ("Ruxolitinib", "Splenic infarction"),
    ("Anagrelide", "Splenic infarction"),
    ("Hydroxyurea", "Portal vein thrombosis"),
    ("Ruxolitinib", "Portal vein thrombosis"),
    ("Hydroxyurea", "Budd-Chiari syndrome"),
    ("Ruxolitinib", "Budd-Chiari syndrome"),
    ("Hydroxyurea", "Pulmonary embolism"),
    ("Ruxolitinib", "Pulmonary embolism"),
    ("Ruxolitinib", "Myocardial infarction"),
    ("Ruxolitinib", "Cerebrovascular accident"),
]

lines.append("### Table 1  |  ROR 随对照背景的收缩（同一药–事件对，两种背景）\n")
lines.append("| 药物 | 事件 | 全库背景 ROR (95%CI) | MPN 背景 ROR (95%CI) | 收缩幅度 | a (全库→MPN) |")
lines.append("|---|---|---|---|---|---|")
for d, p in KEY:
    A, M = allr.get((d, p)), mpn.get((d, p))
    if not A or not M:
        continue
    r1, r2 = A.get("ROR"), M.get("ROR")
    if r1 in (None, "") or r2 in (None, ""):
        continue
    r1f, r2f = float(r1), float(r2)
    shrink = (1 - r2f / r1f) * 100 if r1f else 0
    # 收缩为正 = 信号变弱；为负 = 换成 MPN 背景后反而升高
    s_txt = f"−{shrink:.0f}%" if shrink >= 0 else f"+{-shrink:.0f}% (↑)"
    lines.append(
        f"| {d} | {p} | {f(r1)} ({f(A['ROR025'])}–{f(A['ROR975'])}) | "
        f"{f(r2)} ({f(M['ROR025'])}–{f(M['ROR975'])}) | "
        f"{s_txt} | {A['a']} → {M['a']} |"
    )

# ---------- Table 2  全库对照下达信号的组合 ----------
lines.append("\n### Table 2  |  全库背景下达到全部四项判定的组合\n")
sig = [r for r in rd("faers_ror_all.csv") if r["signal"] == "YES"]
sig.sort(key=lambda r: -float(r["ROR025"] or 0))
lines.append("| 药物 | 事件 | a | ROR (95%CI) | PRR | q (BH) |")
lines.append("|---|---|---|---|---|---|")
for r in sig:
    lines.append(
        f"| {r['drug']} | {r['pt']} | {r['a']} | "
        f"{f(r['ROR'])} ({f(r['ROR025'])}–{f(r['ROR975'])}) | {f(r['PRR'])} | "
        f"{float(r['q']):.1e} |" if r["q"] not in (None, "") else
        f"| {r['drug']} | {r['pt']} | {r['a']} | {f(r['ROR'])} | {f(r['PRR'])} | — |"
    )

# ---------- Table 3  ET 头对头 ----------
h2h = rd("faers_head_to_head.csv")
sens = {(r["scenario"], r["disease"], r["pair"], r["pt"]): r
        for r in rd("faers_sensitivity.csv")}

lines.append("\n### Table 3  |  ET: anagrelide vs hydroxyurea（含两项敏感性）\n")
lines.append("| 事件 | 主分析 ROR (95%CI) | 排除联用 ROR (95%CI) | 仅严重报告 ROR (95%CI) |")
lines.append("|---|---|---|---|")
et = [r for r in h2h if r["disease"] == "ET"]
et.sort(key=lambda r: -float(r["ROR"] or 0))
for r in et:
    if r["ROR"] in (None, ""):
        continue
    k1 = ("S1_excl_combo", "ET", "Anagrelide_vs_Hydroxyurea", r["pt"])
    k2 = ("S2_serious_only", "ET", "Anagrelide_vs_Hydroxyurea", r["pt"])
    s1, s2 = sens.get(k1), sens.get(k2)
    v1 = f"{f(s1['ROR'])} ({f(s1['ROR025'])}–{f(s1['ROR975'])})" if s1 and s1["ROR"] else "—"
    v2 = f"{f(s2['ROR'])} ({f(s2['ROR025'])}–{f(s2['ROR975'])})" if s2 and s2["ROR"] else "—"
    lines.append(f"| {r['pt']} | {f(r['ROR'])} ({f(r['ROR025'])}–{f(r['ROR975'])}) | {v1} | {v2} |")

# ---------- Table 4  MF 头对头 ----------
lines.append("\n### Table 4  |  MF: ruxolitinib vs hydroxyurea\n")
lines.append("| 事件 | 主分析 ROR (95%CI) | 排除联用 ROR (95%CI) |")
lines.append("|---|---|---|")
mf = [r for r in h2h if r["disease"] == "MF"]
mf.sort(key=lambda r: -float(r["ROR"] or 0))
for r in mf:
    if r["ROR"] in (None, ""):
        continue
    s1 = sens.get(("S1_excl_combo", "MF", "Ruxolitinib_vs_Hydroxyurea", r["pt"]))
    v1 = f"{f(s1['ROR'])} ({f(s1['ROR025'])}–{f(s1['ROR975'])})" if s1 and s1["ROR"] else "—"
    lines.append(f"| {r['pt']} | {f(r['ROR'])} ({f(r['ROR025'])}–{f(r['ROR975'])}) | {v1} |")

txt = "\n".join(lines)
p = os.path.join(OUT, "tables_generated.md")
open(p, "w", encoding="utf-8").write(txt)
print(txt)
print()
print(f"[OK] {p}")

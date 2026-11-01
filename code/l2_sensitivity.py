# -*- coding: utf-8 -*-
"""
l2_sensitivity.py — L2 适应证内对照的稳健性检验
================================================
问题：MPN 池 58,602 份报告中，含芦可替尼的约 35,849 份（61.2%）。
      因此对羟基脲、阿那格雷等药而言，L2 的"疾病内对照"实质是
      "以芦可替尼报告为主的混合对照"，组间并不同质。

两个敏感性分析：
  S3  从 MPN 池中剔除含芦可替尼的报告后重算 L2
      —— 消除单一药物对对照组的支配
  S4  把参照组换成"未使用六种研究药物的 MPN 报告"（真正未暴露的疾病背景）
      —— 最保守的疾病内参照。注意其 2x2 不能把药物从池中排除，否则分子恒为 0；
      正确构造是：用药组（MPN∩药）vs 未暴露组（MPN∩无六药），两组互斥。

输出：02_tables/faers_l2_sensitivity.csv
"""
import requests, json, time, math, os, csv
from math import log, exp, sqrt

BASE = "https://api.fda.gov/drug/event.json"
OUT = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒\00_data"
CACHE = os.path.join(OUT, "counts_l2sens_cache.json")
S = requests.Session()
S.headers.update({"User-Agent": "FAERS-pharmacovigilance-research/1.0"})

MPN = ('(patient.drug.drugindication:"MYELOFIBROSIS"'
       ' OR patient.drug.drugindication:"PRIMARY MYELOFIBROSIS"'
       ' OR patient.drug.drugindication:"MYELOPROLIFERATIVE NEOPLASM"'
       ' OR patient.drug.drugindication:"MYELOPROLIFERATIVE DISORDER"'
       ' OR patient.drug.drugindication:"POLYCYTHAEMIA VERA"'
       ' OR patient.drug.drugindication:"ESSENTIAL THROMBOCYTHAEMIA")')

DRUGS = {
    "Ruxolitinib":             'patient.drug.openfda.generic_name:"RUXOLITINIB"',
    "Hydroxyurea":             'patient.drug.openfda.generic_name:"HYDROXYUREA"',
    "Anagrelide":              'patient.drug.openfda.generic_name:"ANAGRELIDE"',
    "Busulfan":                'patient.drug.openfda.generic_name:"BUSULFAN"',
    "Luspatercept":            'patient.drug.openfda.generic_name:"LUSPATERCEPT"',
    "Ropeginterferon alfa-2b": 'patient.drug.openfda.generic_name:"ROPEGINTERFERON ALFA-2B"',
}
# 只检验 L1 或 L2 曾达信号、且 a>=3 的药-事件组合（其余无稳健性可言）
TARGETS = {
    "Hydroxyurea":   ["Splenic infarction", "Portal vein thrombosis", "Splenic vein thrombosis",
                      "Budd-Chiari syndrome", "Thrombophlebitis", "Venous thrombosis",
                      "Arterial thrombosis", "Transient ischaemic attack"],
    "Anagrelide":    ["Myocardial infarction", "Cerebrovascular accident",
                      "Transient ischaemic attack", "Haemorrhage", "Splenic infarction"],
    "Busulfan":      ["Portal vein thrombosis", "Splenic vein thrombosis",
                      "Venous thrombosis", "Thrombophlebitis"],
    "Luspatercept":  ["Arterial thrombosis", "Retinal vein occlusion", "Myocardial infarction",
                      "Thrombosis"],
    "Ropeginterferon alfa-2b": ["Myocardial infarction", "Cerebrovascular accident"],
}
PTQ = lambda pt: f'patient.reaction.reactionmeddrapt:"{pt}"'

CACHE_D = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
CALLS = [0]


def total(q):
    if q in CACHE_D:
        return CACHE_D[q]
    for _ in range(4):
        try:
            r = S.get(BASE, params={"search": q, "limit": 1}, timeout=60)
            if r.status_code == 200:
                n = r.json()["meta"]["results"]["total"]
                CACHE_D[q] = n
                CALLS[0] += 1
                if CALLS[0] % 20 == 0:
                    json.dump(CACHE_D, open(CACHE, "w", encoding="utf-8"))
                time.sleep(0.33)
                return n
            if r.status_code == 404:
                CACHE_D[q] = 0
                time.sleep(0.33)
                return 0
            time.sleep(3)
        except Exception:
            time.sleep(3)
    raise RuntimeError(q[:90])


def analyse(a, b, c, d):
    r = {"a": a, "b": b, "c": c, "d": d}
    if min(a, b, c, d) <= 0:
        for k in ["ROR", "ROR025", "ROR975", "PRR", "chi2", "IC", "IC025"]:
            r[k] = None
        return r
    ror = (a / b) / (c / d)
    se = sqrt(1/a + 1/b + 1/c + 1/d)
    r["ROR"] = ror
    r["ROR025"] = exp(log(ror) - 1.96 * se)
    r["ROR975"] = exp(log(ror) + 1.96 * se)
    r["PRR"] = (a / (a + b)) / (c / (c + d))
    n = a + b + c + d
    den = (a + b) * (c + d) * (a + c) * (b + d)
    r["chi2"] = n * (a*d - b*c)**2 / den if den else None
    ic = math.log2(a * n / ((a + b) * (a + c)))
    r["IC"] = ic
    r["IC025"] = ic - 2 * sqrt(1/a + 1/b + 1/c + 1/d) / log(2)
    return r


print("=" * 78)
print("STEP 1  三个池的大小")
print("=" * 78)
N_MPN = total(MPN)
Q_NO_RUX = f"{MPN} AND NOT {DRUGS['Ruxolitinib']}"
N_NO_RUX = total(Q_NO_RUX)
Q_NONE = MPN + "".join(f" AND NOT {q}" for q in DRUGS.values())
N_NONE = total(Q_NONE)
print(f"  MPN 全部                {N_MPN:>8,}")
print(f"  剔除芦可替尼后 (S3 池)   {N_NO_RUX:>8,}   ({N_NO_RUX/N_MPN*100:.1f}%)")
print(f"  未用六药者   (S4 池)     {N_NONE:>8,}   ({N_NONE/N_MPN*100:.1f}%)")

print()
print("=" * 78)
print("STEP 2  逐组合计算")
print("=" * 78)

rows = []
for drug, pts in TARGETS.items():
    dq = DRUGS[drug]
    # ---- S3：池内对照（剔芦可替尼后，药组 vs 池内非药组）----
    nd3 = total(f"{Q_NO_RUX} AND {dq}")
    for pt in pts:
        a = total(f"{Q_NO_RUX} AND {dq} AND {PTQ(pt)}")
        c = total(f"{Q_NO_RUX} AND {PTQ(pt)}") - a
        b = nd3 - a
        dd = N_NO_RUX - a - b - c
        r = analyse(a, b, c, dd)
        r.update(scenario="S3_no_ruxolitinib", drug=drug, pt=pt,
                 pool_n=N_NO_RUX, n_drug=nd3)
        rows.append(r)

    # ---- S4：用药组 vs 真正未暴露的 MPN 组（两组互斥）----
    nd4 = total(f"{MPN} AND {dq}")
    for pt in pts:
        a = total(f"{MPN} AND {dq} AND {PTQ(pt)}")
        b = nd4 - a
        c = total(f"{Q_NONE} AND {PTQ(pt)}")
        dd = N_NONE - c
        r = analyse(a, b, c, dd)
        r.update(scenario="S4_untreated_MPN", drug=drug, pt=pt,
                 pool_n=N_NONE, n_drug=nd4)
        rows.append(r)
    print(f"  [{drug}] 完成")

json.dump(CACHE_D, open(CACHE, "w", encoding="utf-8"))

path = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒\02_tables\faers_l2_sensitivity.csv"
cols = ["scenario", "drug", "pt", "a", "b", "c", "d", "ROR", "ROR025", "ROR975",
        "PRR", "chi2", "IC", "IC025", "pool_n", "n_drug"]
with open(path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow({k: (f"{r[k]:.6g}" if isinstance(r[k], float) else r.get(k)) for k in cols})
print(f"\n[OK] {path}  {len(rows)} 行")

# ---------- 汇总：与主 L2 对比 ----------
main = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒\02_tables\faers_ror_mpn_stratified.csv"
L2 = {}
with open(main, encoding="utf-8-sig") as f:
    for x in csv.DictReader(f):
        L2[(x["drug"], x["pt"])] = x

print()
print("=" * 78)
print("STEP 3  L2 主分析 vs S3（剔芦可替尼） vs S4（未暴露 MPN）")
print("=" * 78)
print(f"{'药':<24}{'PT':<28}{'L2主':>14}{'S3':>14}{'S4':>14}")
print("-" * 96)
summary = []
for drug, pts in TARGETS.items():
    for pt in pts:
        m = L2.get((drug, pt), {})
        mv = f'{float(m["ROR"]):.2f} ({float(m["ROR025"]):.2f})' if m.get("ROR") else "NA"
        outs = {}
        for sc in ["S3_no_ruxolitinib", "S4_untreated_MPN"]:
            rr = [x for x in rows if x["scenario"] == sc and x["drug"] == drug and x["pt"] == pt]
            if rr and rr[0]["ROR"]:
                outs[sc] = f'{rr[0]["ROR"]:.2f} ({rr[0]["ROR025"]:.2f})'
            else:
                outs[sc] = "NA"
        print(f"{drug:<24}{pt:<28}{mv:>14}{outs['S3_no_ruxolitinib']:>14}{outs['S4_untreated_MPN']:>14}")
        summary.append(dict(drug=drug, pt=pt, l2=mv,
                            s3=outs["S3_no_ruxolitinib"], s4=outs["S4_untreated_MPN"]))
print()
print("  （格式：ROR (95%CI 下限)）")

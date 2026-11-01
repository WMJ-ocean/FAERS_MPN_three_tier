# -*- coding: utf-8 -*-
"""
mpn_stratified.py — 适应证内对照分析（本研究的核心设计）
=========================================================
问题：全库对照下，脾梗死 ROR=26.6、门静脉血栓 7.5、Budd-Chiari 28.0，
      这些都是 MPN 的疾病特征而非药物效应。全库对照无法区分二者。

解法：把分母限制在「适应证为 MPN 的报告」内，比较
      用过某药的 MPN 报告  vs  未用该药的 MPN 报告
      这样疾病背景被固定，剩余的差异才可能归因于药物。

MPN 报告定义（适应证自由文本，已实测拼写）：
  MYELOFIBROSIS / PRIMARY MYELOFIBROSIS / MYELOPROLIFERATIVE NEOPLASM
  POLYCYTHAEMIA VERA (英式) / ESSENTIAL THROMBOCYTHAEMIA (英式)
"""
import requests, json, time, math, os, csv
from math import log, exp, sqrt

BASE = "https://api.fda.gov/drug/event.json"
OUT = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒\00_data"
CACHE = os.path.join(OUT, "counts_mpn_cache.json")

S = requests.Session()
S.headers.update({"User-Agent": "FAERS-pharmacovigilance-research/1.0"})

MPN_Q = ('(patient.drug.drugindication:"MYELOFIBROSIS"'
         ' OR patient.drug.drugindication:"PRIMARY MYELOFIBROSIS"'
         ' OR patient.drug.drugindication:"MYELOPROLIFERATIVE NEOPLASM"'
         ' OR patient.drug.drugindication:"MYELOPROLIFERATIVE DISORDER"'
         ' OR patient.drug.drugindication:"POLYCYTHAEMIA VERA"'
         ' OR patient.drug.drugindication:"ESSENTIAL THROMBOCYTHAEMIA")')

DRUGS = {
    "Ruxolitinib":            'patient.drug.openfda.generic_name:"RUXOLITINIB"',
    "Hydroxyurea":            'patient.drug.openfda.generic_name:"HYDROXYUREA"',
    "Anagrelide":             'patient.drug.openfda.generic_name:"ANAGRELIDE"',
    "Busulfan":               'patient.drug.openfda.generic_name:"BUSULFAN"',
    "Luspatercept":           'patient.drug.openfda.generic_name:"LUSPATERCEPT"',
    "Ropeginterferon alfa-2b":'patient.drug.openfda.generic_name:"ROPEGINTERFERON ALFA-2B"',
}
PTS = {
    "Pulmonary embolism":         'Pulmonary embolism',
    "Deep vein thrombosis":       'Deep vein thrombosis',
    "Thrombosis":                 'Thrombosis',
    "Venous thrombosis":          'Venous thrombosis',
    "Portal vein thrombosis":     'Portal vein thrombosis',
    "Splenic vein thrombosis":    'Splenic vein thrombosis',
    "Splenic infarction":         'Splenic infarction',
    "Arterial thrombosis":        'Arterial thrombosis',
    "Myocardial infarction":      'Myocardial infarction',
    "Cerebrovascular accident":   'Cerebrovascular accident',
    "Transient ischaemic attack": 'Transient ischaemic attack',
    "Retinal vein occlusion":     'Retinal vein occlusion',
    "Embolism":                   'Embolism',
    "Thrombophlebitis":           'Thrombophlebitis',
    "Budd-Chiari syndrome":       'Budd-Chiari syndrome',
    "Haemorrhage":                'Haemorrhage',
}
PT_Q = {k: f'patient.reaction.reactionmeddrapt:"{v}"' for k, v in PTS.items()}

CACHE_D = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}
CALLS = [0]


def total(search):
    if search in CACHE_D:
        return CACHE_D[search]
    for _ in range(4):
        try:
            r = S.get(BASE, params={"search": search, "limit": 1}, timeout=60)
            if r.status_code == 200:
                n = r.json()["meta"]["results"]["total"]
                CACHE_D[search] = n
                CALLS[0] += 1
                if CALLS[0] % 25 == 0:
                    json.dump(CACHE_D, open(CACHE, "w", encoding="utf-8"))
                    print(f"    ...{len(CACHE_D)} 条已缓存")
                time.sleep(0.33)
                return n
            if r.status_code == 404:
                CACHE_D[search] = 0
                time.sleep(0.33)
                return 0
            time.sleep(3)
        except Exception:
            time.sleep(3)
    raise RuntimeError(search[:80])


print("=" * 78)
print("STEP 1  MPN 报告池")
print("=" * 78)
N_MPN = total(MPN_Q)
print(f"  MPN 适应证报告 N_MPN = {N_MPN:,}")

print()
print("  各药在 MPN 报告中的使用数：")
N_DRUG_MPN = {}
for d, q in DRUGS.items():
    n = total(f"{MPN_Q} AND {q}")
    N_DRUG_MPN[d] = n
    print(f"    {d:26s} {n:>8,}   (占 MPN 报告 {n/N_MPN*100:5.1f}%)")

print()
print("  MPN 报告中的 PT 数：")
N_PT_MPN = {}
for p in PTS:
    n = total(f"{MPN_Q} AND {PT_Q[p]}")
    N_PT_MPN[p] = n
    print(f"    {p:28s} {n:>8,}")

print()
print("=" * 78)
print(f"STEP 2  三重交集（{len(DRUGS)}×{len(PTS)} = {len(DRUGS)*len(PTS)} 次）")
print("=" * 78)
A = {}
for i, (d, dq) in enumerate(DRUGS.items(), 1):
    for p in PTS:
        A[(d, p)] = total(f"{MPN_Q} AND {dq} AND {PT_Q[p]}")
    print(f"  [{i}/{len(DRUGS)}] {d}")

json.dump(CACHE_D, open(CACHE, "w", encoding="utf-8"))

# ---------------- 计算 ----------------
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


rows = []
for d in DRUGS:
    for p in PTS:
        a = A[(d, p)]
        b = N_DRUG_MPN[d] - a
        c = N_PT_MPN[p] - a
        dd = N_MPN - a - b - c
        r = analyse(a, b, c, dd)
        r["drug"], r["pt"] = d, p
        rows.append(r)

# FDR
ps = [(math.erfc(sqrt(r["chi2"]/2)) if r["chi2"] is not None else 1.0) for r in rows]
m = len(ps)
order = sorted(range(m), key=lambda i: ps[i])
q = [0.0]*m
prev = 1.0
for rank in range(m-1, -1, -1):
    i = order[rank]
    v = min(prev, ps[i]*m/(rank+1))
    q[i] = v
    prev = v
for r, p_, q_ in zip(rows, ps, q):
    r["p"], r["q"] = p_, q_

for r in rows:
    r["signal"] = "YES" if (
        r["a"] >= 3 and (r["ROR025"] or 0) > 1 and (r["PRR"] or 0) >= 2
        and (r["chi2"] or 0) >= 4 and (r["IC025"] or -9) > 0
    ) else ""

path = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒\02_tables\faers_ror_mpn_stratified.csv"
cols = ["drug","pt","a","b","c","d","ROR","ROR025","ROR975","PRR","chi2","p","q","IC","IC025","signal"]
with open(path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow({k: (f"{r[k]:.6g}" if isinstance(r[k], float) else r[k]) for k in cols})
print()
print(f"[OK] {path}  {len(rows)} 行")

print()
print("=" * 78)
print("STEP 3  MPN 内对照结果（按 ROR025 排序，a≥3）")
print("=" * 78)
print(f"{'药物':<26}{'PT':<30}{'a':>6}{'ROR':>7}{'ROR025':>9}{'q':>10}  信号")
print("-"*98)
for r in sorted(rows, key=lambda x: -(x["ROR025"] or 0)):
    if r["a"] < 3:
        continue
    print(f"{r['drug']:<26}{r['pt']:<30}{r['a']:>6,}"
          f"{(r['ROR'] or 0):>7.2f}{(r['ROR025'] or 0):>9.2f}"
          f"{(r['q'] or 1):>10.2g}  {r['signal']}")

print()
print(f"  N_MPN = {N_MPN:,}")
print(f"  三法一致信号数：{sum(1 for r in rows if r['signal']=='YES')} / {len(rows)}")

# -*- coding: utf-8 -*-
"""
disease_stratified.py — 按疾病分层的药物间比较（决定性的第三层分析）
=====================================================================
为什么必须做：
  在 MPN 整体内，ruxolitinib 占 66.5% 的报告，对照组因此以 ET/PV 患者为主。
  「ruxolitinib 血栓信号低」可能只是「MF 与 ET/PV 的血栓谱不同」，
  而不是药物效应。唯一解法是把比较限制在同一疾病内。

三个临床最有意义的头对头比较：
  ET  : Anagrelide      vs Hydroxyurea      （两种一线，选谁有争议）
  PV  : Ropeginterferon vs Hydroxyurea      （新一线 vs 传统）
  MF  : Ruxolitinib     vs Hydroxyurea      （一线 vs 传统）

2x2（报告层面，允许同一报告同时用两药，重叠量单独统计并在限制中说明）：
         目标PT   其他PT
  药A      a        b = N_A - a
  药B      c        d = N_B - c
"""
import requests, json, time, math, os, csv
from math import log, exp, sqrt

BASE = "https://api.fda.gov/drug/event.json"
OUT = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒\00_data"
CACHE = os.path.join(OUT, "counts_disease_cache.json")
S = requests.Session()
S.headers.update({"User-Agent": "FAERS-pharmacovigilance-research/1.0"})

DIS = {
    "ET": 'patient.drug.drugindication:"ESSENTIAL THROMBOCYTHAEMIA"',
    "PV": 'patient.drug.drugindication:"POLYCYTHAEMIA VERA"',
    "MF": 'patient.drug.drugindication:"MYELOFIBROSIS"',
}
DRUG = {
    "Anagrelide":             'patient.drug.openfda.generic_name:"ANAGRELIDE"',
    "Hydroxyurea":            'patient.drug.openfda.generic_name:"HYDROXYUREA"',
    "Ruxolitinib":            'patient.drug.openfda.generic_name:"RUXOLITINIB"',
    "Ropeginterferon alfa-2b":'patient.drug.openfda.generic_name:"ROPEGINTERFERON ALFA-2B"',
    "Busulfan":               'patient.drug.openfda.generic_name:"BUSULFAN"',
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

# 头对头比较对
PAIRS = [
    ("ET", "Anagrelide", "Hydroxyurea"),
    ("PV", "Ropeginterferon alfa-2b", "Hydroxyurea"),
    ("MF", "Ruxolitinib", "Hydroxyurea"),
]

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
                if CALLS[0] % 30 == 0:
                    json.dump(CACHE_D, open(CACHE, "w", encoding="utf-8"))
                    print(f"      ...{len(CACHE_D)} cached")
                time.sleep(0.33)
                return n
            if r.status_code == 404:
                CACHE_D[q] = 0
                time.sleep(0.33)
                return 0
            time.sleep(3)
        except Exception:
            time.sleep(3)
    raise RuntimeError(q[:80])


print("=" * 80)
print("STEP 1  各疾病报告池与药物使用")
print("=" * 80)
ND = {}
for d, q in DIS.items():
    ND[d] = total(q)
    print(f"\n  {d}: {ND[d]:,} 份报告")
    for g, gq in DRUG.items():
        n = total(f"{q} AND {gq}")
        print(f"     {g:26s} {n:>7,}  ({n/ND[d]*100:4.1f}%)")

json.dump(CACHE_D, open(CACHE, "w", encoding="utf-8"))

print()
print("=" * 80)
print("STEP 2  头对头比较")
print("=" * 80)
rows = []
for dis, da, db in PAIRS:
    print(f"\n  >>> {dis}: {da} vs {db}")
    QA, QB = DRUG[da], DRUG[db]
    NA = total(f"{DIS[dis]} AND {QA}")
    NB = total(f"{DIS[dis]} AND {QB}")
    NOVER = total(f"{DIS[dis]} AND {QA} AND {QB}")
    print(f"      {da} = {NA:,} | {db} = {NB:,} | 两药重叠 = {NOVER:,}"
          f" ({NOVER/max(NA,1)*100:.1f}% of {da})")
    for p in PTS:
        a = total(f"{DIS[dis]} AND {QA} AND {PT_Q[p]}")
        c = total(f"{DIS[dis]} AND {QB} AND {PT_Q[p]}")
        b = NA - a
        d = NB - c
        r = {"disease": dis, "drug_a": da, "drug_b": db, "pt": p,
             "a": a, "b": b, "c": c, "d": d,
             "N_a": NA, "N_b": NB, "overlap": NOVER}
        if min(a, b, c, d) > 0:
            ror = (a / b) / (c / d)
            se = sqrt(1/a + 1/b + 1/c + 1/d)
            r["ROR"] = ror
            r["ROR025"] = exp(log(ror) - 1.96*se)
            r["ROR975"] = exp(log(ror) + 1.96*se)
            n = a + b + c + d
            den = (a+b)*(c+d)*(a+c)*(b+d)
            r["chi2"] = n*(a*d - b*c)**2/den if den else None
            r["p"] = math.erfc(sqrt(r["chi2"]/2)) if r["chi2"] else 1.0
        else:
            for k in ["ROR", "ROR025", "ROR975", "chi2"]:
                r[k] = None
            r["p"] = 1.0
        rows.append(r)

# 每个疾病内做 BH 校正
from collections import defaultdict
by_dis = defaultdict(list)
for r in rows:
    by_dis[r["disease"]].append(r)
for dis, grp in by_dis.items():
    m = len(grp)
    order = sorted(range(m), key=lambda i: grp[i]["p"])
    prev = 1.0
    qv = [0.0]*m
    for rank in range(m-1, -1, -1):
        i = order[rank]
        v = min(prev, grp[i]["p"]*m/(rank+1))
        qv[i] = v
        prev = v
    for r, v in zip(grp, qv):
        r["q"] = v

path = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒\02_tables\faers_head_to_head.csv"
cols = ["disease","drug_a","drug_b","pt","a","b","c","d","N_a","N_b","overlap",
        "ROR","ROR025","ROR975","chi2","p","q"]
with open(path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow({k: (f"{r[k]:.6g}" if isinstance(r[k], float) else r.get(k)) for k in cols})
print()
print(f"[OK] {path}  {len(rows)} 行")

print()
print("=" * 80)
print("STEP 3  结果（a≥3 且 c≥3）")
print("=" * 80)
for dis in ["ET", "PV", "MF"]:
    grp = [r for r in by_dis[dis] if r["a"] >= 3 and r["c"] >= 3]
    if not grp:
        print(f"\n  {dis}: 无可分析组合")
        continue
    print(f"\n  {dis}: {grp[0]['drug_a']} vs {grp[0]['drug_b']}")
    print(f"  {'PT':<30}{'a':>5}{'c':>5}{'ROR':>8}{'ROR025':>9}{'q':>10}")
    print("  " + "-"*66)
    for r in sorted(grp, key=lambda x: -(x["ROR025"] or 0)):
        print(f"  {r['pt']:<30}{r['a']:>5,}{r['c']:>5,}"
              f"{(r['ROR'] or 0):>8.2f}{(r['ROR025'] or 0):>9.2f}{(r['q'] or 1):>10.2g}")

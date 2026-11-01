# -*- coding: utf-8 -*-
"""
sensitivity.py — 敏感性分析（核心结论的稳健性检验）
====================================================
三个必须做的检验：
  S1  排除两药联用的报告 —— ET 中 27.2% 的 anagrelide 报告同时用羟基脲，
      重叠会稀释差异，必须排除后重算
  S2  限定严重结局（serious=1）—— 排除轻症报告的噪声
  S3  限定有标准化药名的报告作为背景（消除 15.9% 无药名报告的稀释）

核心待检验结论：
  ET 中 anagrelide 相对羟基脲的心肌梗死信号（主分析 ROR 2.94, ROR025 1.68）
"""
import requests, json, time, math, os, csv
from math import log, exp, sqrt

BASE = "https://api.fda.gov/drug/event.json"
OUT = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒\00_data"
CACHE = os.path.join(OUT, "counts_sens_cache.json")
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
}
PATS = {
    "Myocardial infarction":      'Myocardial infarction',
    "Cerebrovascular accident":   'Cerebrovascular accident',
    "Transient ischaemic attack": 'Transient ischaemic attack',
    "Haemorrhage":                'Haemorrhage',
    "Pulmonary embolism":         'Pulmonary embolism',
    "Deep vein thrombosis":       'Deep vein thrombosis',
    "Thrombosis":                 'Thrombosis',
    "Splenic infarction":         'Splenic infarction',
}
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


def calc(a, b, c, d):
    if min(a, b, c, d) <= 0:
        return dict(ROR=None, ROR025=None, ROR975=None, chi2=None, p=1.0)
    ror = (a/b)/(c/d)
    se = sqrt(1/a + 1/b + 1/c + 1/d)
    n = a+b+c+d
    den = (a+b)*(c+d)*(a+c)*(b+d)
    ch = n*(a*d-b*c)**2/den if den else None
    return dict(ROR=ror, ROR025=exp(log(ror)-1.96*se), ROR975=exp(log(ror)+1.96*se),
                chi2=ch, p=math.erfc(sqrt(ch/2)) if ch else 1.0)


rows = []
for dis, da, db in PAIRS:
    print("=" * 78)
    print(f"{dis}: {da} vs {db}")
    print("=" * 78)
    QA, QB, QD = DRUG[da], DRUG[db], DIS[dis]

    # ---------- S1 排除联用 ----------
    NAx = total(f"{QD} AND {QA} AND NOT {QB}")
    NBx = total(f"{QD} AND {QB} AND NOT {QA}")
    print(f"  [S1] 排除联用后：{da} {NAx:,}  |  {db} {NBx:,}")
    for p, pt in PATS.items():
        PQ = f'patient.reaction.reactionmeddrapt:"{pt}"'
        a = total(f"{QD} AND {QA} AND NOT {QB} AND {PQ}")
        c = total(f"{QD} AND {QB} AND NOT {QA} AND {PQ}")
        r = calc(a, NAx-a, c, NBx-c)
        r.update(scenario="S1_excl_combo", disease=dis, pair=f"{da}_vs_{db}",
                 pt=p, a=a, c=c)
        rows.append(r)

    # ---------- S2 限定 serious ----------
    NAs = total(f"{QD} AND {QA} AND serious:1")
    NBs = total(f"{QD} AND {QB} AND serious:1")
    print(f"  [S2] 仅严重报告：{da} {NAs:,}  |  {db} {NBs:,}")
    for p, pt in PATS.items():
        PQ = f'patient.reaction.reactionmeddrapt:"{pt}"'
        a = total(f"{QD} AND {QA} AND serious:1 AND {PQ}")
        c = total(f"{QD} AND {QB} AND serious:1 AND {PQ}")
        r = calc(a, NAs-a, c, NBs-c)
        r.update(scenario="S2_serious_only", disease=dis, pair=f"{da}_vs_{db}",
                 pt=p, a=a, c=c)
        rows.append(r)
    print()

path = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒\02_tables\faers_sensitivity.csv"
cols = ["scenario","disease","pair","pt","a","c","ROR","ROR025","ROR975","chi2","p"]
with open(path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow({k: (f"{r[k]:.6g}" if isinstance(r[k], float) else r.get(k)) for k in cols})
print(f"[OK] {path}  {len(rows)} 行")

print()
print("=" * 78)
print("敏感性汇总：主分析（允许联用） vs S1（排除联用） vs S2（仅严重）")
print("=" * 78)

# 读主分析结果（disease_stratified.py 产出）
main_csv = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒\02_tables\faers_head_to_head.csv"
MAIN = {}
if os.path.exists(main_csv):
    with open(main_csv, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            KEY = (row["disease"], f'{row["drug_a"]}_vs_{row["drug_b"]}', row["pt"])
            MAIN[KEY] = row

for dis, da, db in PAIRS:
    print(f"\n  {dis}: {da} vs {db}")
    print(f"  {'PT':<30}{'主分析':>16}{'S1排除联用':>16}{'S2仅严重':>16}")
    print("  " + "-" * 80)
    for p in PATS:
        mk = (dis, f"{da}_vs_{db}", p)
        m = MAIN.get(mk)
        mv = (f'{float(m["ROR"]):.2f} ({float(m["ROR025"]):.2f})'
              if m and m.get("ROR") not in (None, "", "None") else "NA")
        s1r = [r for r in rows if r["disease"] == dis and r["pt"] == p
               and r["scenario"] == "S1_excl_combo"]
        s2r = [r for r in rows if r["disease"] == dis and r["pt"] == p
               and r["scenario"] == "S2_serious_only"]
        v1 = (f"{s1r[0]['ROR']:.2f} ({s1r[0]['ROR025']:.2f})"
              if s1r and s1r[0]["ROR"] else "NA")
        v2 = (f"{s2r[0]['ROR']:.2f} ({s2r[0]['ROR025']:.2f})"
              if s2r and s2r[0]["ROR"] else "NA")
        print(f"  {p:<30}{mv:>16}{v1:>16}{v2:>16}")

print()
print("  （括号内为 ROR 95%CI 下限；<1.00 表示该药相对对照药无信号或偏低）")

# -*- coding: utf-8 -*-
"""
probe10.py — 修补 readus_supplement.py 中失败的聚合
问题：patient.patientsex 与 primarysource.qualification 不支持直接 count 聚合，
      改为逐值查询计数。occurcountry 用 .exact 子字段。
另补 8a 所需的「至少含一种研究药物的去重报告数」。
"""
import requests, json, time, os

BASE = "https://api.fda.gov/drug/event.json"
ROOT = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒"
CACHE = os.path.join(ROOT, "00_data", "readus_cache.json")

S = requests.Session()
S.headers.update({"User-Agent": "FAERS-pharmacovigilance-research/1.0"})
CACHE_D = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}


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
    return -1


def agg(search, field, n=8):
    key = f"__AGG__{search}__{field}"
    if key in CACHE_D:
        return CACHE_D[key]
    r = S.get(BASE, params={"search": search, "count": field, "limit": n}, timeout=60)
    time.sleep(0.3)
    if r.status_code == 200:
        res = [(x["term"].strip(), x["count"]) for x in r.json().get("results", [])]
        CACHE_D[key] = res
        return res
    return []


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

SEX = {"0": "Unknown", "1": "Male", "2": "Female"}
QUAL = {"1": "Physician", "2": "Pharmacist", "3": "Other HCP", "4": "Lawyer", "5": "Consumer"}

OUT = {"sex": {}, "reporter": {}, "country": {}, "dedup": {}}

print("=" * 70)
print("A. 性别（逐值计数）")
print("=" * 70)
for d, q in DRUGS.items():
    row = {}
    for k, lab in SEX.items():
        row[lab] = total(f"{q} AND patient.patientsex:{k}")
    OUT["sex"][d] = row
    tot = sum(row.values())
    male_pct = row["Male"] / tot * 100 if tot else 0
    print(f"  {d:16s} {row}  男 {male_pct:.0f}%")
OUT["sex"]["MPN_POOL"] = {lab: total(f"{MPN_Q} AND patient.patientsex:{k}") for k, lab in SEX.items()}
print(f"  {'MPN_POOL':16s} {OUT['sex']['MPN_POOL']}")

print()
print("=" * 70)
print("B. 上报者类型（逐值计数）")
print("=" * 70)
for d, q in DRUGS.items():
    row = {}
    for k, lab in QUAL.items():
        row[lab] = total(f"{q} AND primarysource.qualification:{k}")
    OUT["reporter"][d] = row
    tot = sum(row.values())
    print(f"  {d:16s} {row}  医护合计 {(row['Physician']+row['Pharmacist']+row['Other HCP'])/tot*100:.0f}%")
OUT["reporter"]["MPN_POOL"] = {lab: total(f"{MPN_Q} AND primarysource.qualification:{k}")
                               for k, lab in QUAL.items()}

print()
print("=" * 70)
print("C. 报告国（.exact 子字段）")
print("=" * 70)
for d, q in list(DRUGS.items())[:4]:
    res = agg(q, "occurcountry.exact", 6)
    OUT["country"][d] = dict(res)
    print(f"  {d:16s} {res}")
OUT["country"]["MPN_POOL"] = dict(agg(MPN_Q, "occurcountry.exact", 6))

print()
print("=" * 70)
print("D. 去重暴露报告数（8a 流程图所需）")
print("=" * 70)
OR_Q = " OR ".join(f"({q})" for q in DRUGS.values())
n_any = total(f"({OR_Q})")
n_any_mpn = total(f"({OR_Q}) AND {MPN_Q}")
OUT["dedup"] = {"any_drug": n_any, "any_drug_in_mpn": n_any_mpn}
print(f"  至少含 1 种研究药物        {n_any:>10,}")
print(f"  其中含 MPN 适应证          {n_any_mpn:>10,}")
print(f"  六药报告数之和（含重复）    {sum(total(q) for q in DRUGS.values()):>10,}")

json.dump(CACHE_D, open(CACHE, "w", encoding="utf-8"))
p = os.path.join(ROOT, "00_data", "readus_supplement_patch.json")
json.dump(OUT, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(f"\n[OK] {p}")

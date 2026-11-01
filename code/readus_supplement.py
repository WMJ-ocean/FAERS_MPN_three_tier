# -*- coding: utf-8 -*-
"""
readus_supplement.py — READUS-PV 合规补充分析
==============================================
覆盖条目：
  5a  数据库名称/托管方/覆盖范围
  6c  药物角色（suspect vs concomitant）
  8a  各阶段纳入报告数（流程图形数据）
  8b  人群特征（性别/年龄/国家/报告者类型/严重性）
  13  报告偏倚（时间趋势 = notoriety bias 量化）

输出：00_data/readus_supplement.json
      02_tables/readus_supplement.csv
      02_tables/readus_time_trend.csv
"""
import requests, json, time, os, csv

BASE = "https://api.fda.gov/drug/event.json"
ROOT = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒"
CACHE = os.path.join(ROOT, "00_data", "readus_cache.json")

S = requests.Session()
S.headers.update({"User-Agent": "FAERS-pharmacovigilance-research/1.0"})
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
                if CALLS[0] % 40 == 0:
                    json.dump(CACHE_D, open(CACHE, "w", encoding="utf-8"))
                time.sleep(0.32)
                return n
            if r.status_code == 404:
                CACHE_D[search] = 0
                time.sleep(0.32)
                return 0
            time.sleep(3)
        except Exception:
            time.sleep(3)
    return -1


def agg(search, field, n=12):
    """count 聚合，返回 [(term, count)]"""
    key = f"__AGG__{search}__{field}"
    if key in CACHE_D:
        return CACHE_D[key]
    for _ in range(3):
        try:
            r = S.get(BASE, params={"search": search, "count": field, "limit": n}, timeout=60)
            if r.status_code == 200:
                res = [(x["term"].strip(), x["count"]) for x in r.json().get("results", [])]
                CACHE_D[key] = res
                time.sleep(0.35)
                return res
            time.sleep(2)
        except Exception:
            time.sleep(2)
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

OUT = {}

print("=" * 76)
print("STEP 1  纳入流程（READUS-PV 8a）")
print("=" * 76)
N_ALL = total("_exists_:receivedate")
N_HASDRUG = total("_exists_:patient.drug.openfda.generic_name")
print(f"  全库报告              {N_ALL:>12,}")
print(f"  含可标准化药名(openfda) {N_HASDRUG:>12,}  ({N_HASDRUG/N_ALL*100:.1f}%)")
OUT["flow"] = {"all": N_ALL, "has_generic_name": N_HASDRUG}
for d, q in DRUGS.items():
    n = total(q)
    OUT["flow"][d] = n
    print(f"    {d:18s} {n:>12,}")
N_MPN = total(MPN_Q)
OUT["flow"]["mpn_pool"] = N_MPN
print(f"  MPN 适应证报告池       {N_MPN:>12,}")

print()
print("=" * 76)
print("STEP 2  人群特征（READUS-PV 8b）")
print("=" * 76)
SEX_MAP = {"0": "Unknown", "1": "Male", "2": "Female"}
QUAL_MAP = {"1": "Physician", "2": "Pharmacist", "3": "Other HCP",
            "4": "Lawyer", "5": "Consumer"}

OUT["sex"], OUT["age"], OUT["country"], OUT["reporter"], OUT["serious"] = {}, {}, {}, {}, {}

for d, q in DRUGS.items():
    print(f"  --- {d}")
    sx = agg(q, "patient.patientsex")
    OUT["sex"][d] = {SEX_MAP.get(t, t): c for t, c in sx}
    print(f"      性别 {OUT['sex'][d]}")

    ql = agg(q, "primarysource.qualification")
    OUT["reporter"][d] = {QUAL_MAP.get(t, t): c for t, c in ql}
    print(f"      上报者 {OUT['reporter'][d]}")

    ct = agg(q, "occurcountry", 8)
    OUT["country"][d] = dict(ct)

    n_ser = total(f"{q} AND serious:1")
    n_tot = OUT["flow"][d]
    OUT["serious"][d] = {"serious": n_ser, "total": n_tot,
                         "pct": round(n_ser / n_tot * 100, 1) if n_tot else None}
    print(f"      严重报告 {n_ser:,}/{n_tot:,} ({OUT['serious'][d]['pct']}%)")

OUT["sex"]["MPN_POOL"] = {SEX_MAP.get(t, t): c for t, c in agg(MPN_Q, "patient.patientsex")}
OUT["reporter"]["MPN_POOL"] = {QUAL_MAP.get(t, t): c for t, c in agg(MPN_Q, "primarysource.qualification")}
print(f"  --- MPN 池 性别 {OUT['sex']['MPN_POOL']}")

print()
print("  年龄分箱（onset age）")
AGE_BINS = [("0-17", 0, 17), ("18-44", 18, 44), ("45-64", 45, 64),
            ("65-74", 65, 74), ("75+", 75, 130)]
for d, q in list(DRUGS.items())[:3]:
    row = {}
    for lab, lo, hi in AGE_BINS:
        n = total(f"{q} AND patient.patientonsetage:[{lo} TO {hi}]")
        row[lab] = n
    n_unk = total(f"{q} AND NOT _exists_:patient.patientonsetage")
    row["missing"] = n_unk
    OUT["age"][d] = row
    print(f"    {d:16s} {row}")

print()
print("=" * 76)
print("STEP 3  时间趋势（READUS-PV 13，notoriety bias）")
print("=" * 76)
YEARS = list(range(2004, 2027))
trend = {}
focus = [("Ruxolitinib", DRUGS["Ruxolitinib"], None),
         ("Ruxolitinib", DRUGS["Ruxolitinib"], "Splenic infarction"),
         ("Hydroxyurea", DRUGS["Hydroxyurea"], None),
         ("Anagrelide", DRUGS["Anagrelide"], "Myocardial infarction"),
         ("MPN_POOL", MPN_Q, None)]
for name, q, pt in focus:
    key = f"{name}|{pt or 'ALL'}"
    ser = {}
    for y in YEARS:
        s = f"{q} AND receivedate:[{y}0101 TO {y}1231]"
        if pt:
            s += f' AND patient.reaction.reactionmeddrapt:"{pt}"'
        ser[y] = total(s)
    trend[key] = ser
    nz = {y: v for y, v in ser.items() if v}
    if nz:
        peak = max(nz, key=lambda k: nz[k])
        print(f"  {key:45s} peak {peak} = {nz[peak]:>7,}   合计 {sum(nz.values()):>8,}")
    else:
        print(f"  {key:45s} 无数据")

OUT["trend"] = trend

json.dump(CACHE_D, open(CACHE, "w", encoding="utf-8"))
json.dump(OUT, open(os.path.join(ROOT, "00_data", "readus_supplement.json"), "w",
                    encoding="utf-8"), ensure_ascii=False, indent=1)

with open(os.path.join(ROOT, "02_tables", "readus_time_trend.csv"), "w",
          encoding="utf-8-sig", newline="") as f:
    w = csv.writer(f)
    w.writerow(["series"] + YEARS)
    for k, v in trend.items():
        w.writerow([k] + [v[y] for y in YEARS])

print()
print(f"[OK] 补充分析完成，API 调用 {CALLS[0]} 次")

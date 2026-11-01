# -*- coding: utf-8 -*-
"""probe12.py — 芦可替尼约 5 万份报告缺 patient 块，查其年份分布与上报者特征"""
import requests, time, json, os

BASE = "https://api.fda.gov/drug/event.json"
S = requests.Session()
S.headers.update({"User-Agent": "FAERS-pharmacovigilance-research/1.0"})
ROOT = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒"
CACHE = os.path.join(ROOT, "00_data", "readus_cache.json")
D = json.load(open(CACHE, encoding="utf-8")) if os.path.exists(CACHE) else {}


def total(search):
    if search in D:
        return D[search]
    r = S.get(BASE, params={"search": search, "limit": 1}, timeout=60)
    time.sleep(0.3)
    if r.status_code == 200:
        n = r.json()["meta"]["results"]["total"]
        D[search] = n
        return n
    if r.status_code == 404:
        D[search] = 0
        return 0
    return -1


RUX = 'patient.drug.openfda.generic_name:"RUXOLITINIB"'
print("=" * 72)
print("A. 芦可替尼：缺 patientsex 的报告按年分布")
print("=" * 72)
print(f"{'年':<6}{'总报告':>9}{'有性别':>9}{'无性别':>9}{'缺失率':>8}")
rows = []
for y in range(2011, 2027):
    base = f'{RUX} AND receivedate:[{y}0101 TO {y}1231]'
    n = total(base)
    ns = total(f"{base} AND _exists_:patient.patientsex")
    miss = n - ns if n and n > 0 else 0
    pct = miss / n * 100 if n and n > 0 else 0
    rows.append((y, n, ns, miss, pct))
    print(f"{y:<6}{n:>9,}{ns:>9,}{miss:>9,}{pct:>7.1f}%")
json.dump(D, open(CACHE, "w", encoding="utf-8"))

print()
print("=" * 72)
print("B. 缺 patient 块的报告，来自哪类上报者")
print("=" * 72)
Q_MISS = f"{RUX} AND NOT _exists_:patient.patientsex"
for k, lab in [("1", "Physician"), ("2", "Pharmacist"), ("3", "Other HCP"),
               ("4", "Lawyer"), ("5", "Consumer")]:
    n = total(f"{Q_MISS} AND primarysource.qualification:{k}")
    print(f"  {lab:<14} {n:>8,}")

print()
print("  有 patient 块者作对照：")
Q_HAS = f"{RUX} AND _exists_:patient.patientsex"
for k, lab in [("1", "Physician"), ("3", "Other HCP"), ("5", "Consumer")]:
    n = total(f"{Q_HAS} AND primarysource.qualification:{k}")
    print(f"  {lab:<14} {n:>8,}")

print()
print("=" * 72)
print("C. 缺 patient 块报告中的严重性与主要事件")
print("=" * 72)
n_ser = total(f"{Q_MISS} AND serious:1")
n_miss = total(Q_MISS)
print(f"  serious:1   {n_ser:,} / {n_miss:,}  ({n_ser/n_miss*100:.1f}%)")
n_ser_h = total(f"{Q_HAS} AND serious:1")
n_has = total(Q_HAS)
print(f"  有 patient 块者 {n_ser_h:,} / {n_has:,}  ({n_ser_h/n_has*100:.1f}%)")

r = S.get(BASE, params={"search": Q_MISS, "count": "patient.reaction.reactionmeddrapt.exact",
                        "limit": 8}, timeout=60)
time.sleep(0.35)
if r.status_code == 200:
    for x in r.json()["results"]:
        print(f"    {x['term'][:44]:<46} {x['count']:>7,}")

json.dump(D, open(CACHE, "w", encoding="utf-8"))

# -*- coding: utf-8 -*-
"""probe5.py — 枚举 generic_name 中所有含 INTERFERON 的精确值"""
import requests, time

BASE = "https://api.fda.gov/drug/event.json"
S = requests.Session()
S.headers.update({"User-Agent": "FAERS-research/1.0"})

for field in ["patient.drug.openfda.generic_name", "patient.drug.openfda.substance_name"]:
    print("=" * 76)
    print("枚举", field)
    print("=" * 76)
    r = S.get(BASE, params={
        "search": f"{field}:INTERFERON",
        "count": f"{field}.exact",
        "limit": 100,
    }, timeout=60)
    if r.status_code == 200:
        rows = r.json().get("results", [])
        print(f"  共 {len(rows)} 个 term")
        for it in rows[:30]:
            print(f"   {it['term'][:56]:58s} {it['count']:>8,}")
    else:
        print("  HTTP", r.status_code, r.text[:150])
    time.sleep(0.5)
    print()

# 单独确认 MPN 用干扰素亚型
print("=" * 76)
print("MPN 相关干扰素亚型逐个测试")
print("=" * 76)
cands = [
    "INTERFERON ALFA-2A", "INTERFERON ALFA-2B", "INTERFERON ALFA",
    "INTERFERON ALFA-2B (PEGYLATED)", "PEGINTERFERON ALFA-2B",
    "PEGINTERFERON ALFA-2A", "ROPEGINTERFERON ALFA-2B",
    "PEG-INTERFERON ALFA-2A", "PEG-INTERFERON ALFA-2B",
]
for c in cands:
    q = f'patient.drug.openfda.generic_name:"{c}"'
    try:
        r = S.get(BASE, params={"search": q, "limit": 1}, timeout=60)
        n = r.json()["meta"]["results"]["total"] if r.status_code == 200 else 0
    except Exception:
        n = -1
    print(f"  {c:36s} {n:>9,}")
    time.sleep(0.34)

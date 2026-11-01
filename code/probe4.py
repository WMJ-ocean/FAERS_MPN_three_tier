# -*- coding: utf-8 -*-
"""probe4.py — 干扰素类到底怎么检索"""
import requests, time

BASE = "https://api.fda.gov/drug/event.json"
S = requests.Session()
S.headers.update({"User-Agent": "FAERS-research/1.0"})


def tot(q):
    try:
        r = S.get(BASE, params={"search": q, "limit": 1}, timeout=60)
        if r.status_code == 200:
            return r.json()["meta"]["results"]["total"]
        return 0
    except Exception:
        return -1


tests = [
    ("medicinalproduct:INTERFERON", 'patient.drug.medicinalproduct:INTERFERON'),
    ('medicinalproduct:"INTERFERON ALFA"', 'patient.drug.medicinalproduct:"INTERFERON ALFA"'),
    ('medicinalproduct:"INTERFERON ALFA-2B"', 'patient.drug.medicinalproduct:"INTERFERON ALFA-2B"'),
    ("substance_name:INTERFERON", 'patient.drug.openfda.substance_name:INTERFERON'),
    ('substance_name:"INTERFERON ALFA-2B"', 'patient.drug.openfda.substance_name:"INTERFERON ALFA-2B"'),
    ('generic_name:"INTERFERON"', 'patient.drug.openfda.generic_name:"INTERFERON"'),
    ('brand_name:"INTRON A"', 'patient.drug.openfda.brand_name:"INTRON A"'),
    ('brand_name:"PEGASYS"', 'patient.drug.openfda.brand_name:"PEGASYS"'),
    ('brand_name:"BESREMI"', 'patient.drug.openfda.brand_name:"BESREMI"'),
    ('brand_name:"PEG-INTRON"', 'patient.drug.openfda.brand_name:"PEG-INTRON"'),
    ('brand_name:"SILIQ"（对照-非干扰素）', 'patient.drug.openfda.brand_name:"SILIQ"'),
]
print("=" * 74)
print("干扰素类检索路径")
print("=" * 74)
for lab, q in tests:
    print(f"  {lab:42s} {tot(q):>10,}")
    time.sleep(0.34)

print()
print("=" * 74)
print("count 枚举：medicinalproduct 里含 INTERFERON 的实际写法")
print("=" * 74)
try:
    r = S.get(BASE, params={
        "search": "patient.drug.medicinalproduct:INTERFERON",
        "count": "patient.drug.medicinalproduct.exact",
        "limit": 30,
    }, timeout=60)
    if r.status_code == 200:
        for it in r.json().get("results", [])[:25]:
            print(f"   {it['term'][:56]:58s} {it['count']:>8,}")
    else:
        print("   count 失败:", r.status_code)
except Exception as e:
    print("   ERR", e)

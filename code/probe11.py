# -*- coding: utf-8 -*-
"""probe11.py — 核实人口学字段的全库覆盖率，判断芦可替尼 29.8% 是否异常"""
import requests, json, time

BASE = "https://api.fda.gov/drug/event.json"
S = requests.Session()
S.headers.update({"User-Agent": "FAERS-pharmacovigilance-research/1.0"})


def total(search):
    r = S.get(BASE, params={"search": search, "limit": 1}, timeout=60)
    time.sleep(0.3)
    if r.status_code == 200:
        return r.json()["meta"]["results"]["total"]
    return -1


N = total("_exists_:receivedate")
print(f"全库 N = {N:,}\n")
print("全库字段覆盖率：")
for f in ["patient.patientsex", "patient.patientonsetage", "occurcountry",
          "primarysource.qualification", "patient.drug.drugindication", "serious"]:
    n = total(f"_exists_:{f}")
    print(f"  {f:36s} {n:>12,}  ({n/N*100:5.1f}%)")

print()
print("各药字段覆盖率：")
DRUGS = {"RUXOLITINIB": 71241, "HYDROXYUREA": 21024, "ANAGRELIDE": 2284,
         "BUSULFAN": 15642, "LUSPATERCEPT": 2464, "ROPEGINTERFERON ALFA-2B": 1776}
for d, exp in DRUGS.items():
    q = f'patient.drug.openfda.generic_name:"{d}"'
    parts = []
    for f in ["patient.patientsex", "patient.patientonsetage", "occurcountry"]:
        n = total(f"{q} AND _exists_:{f}")
        parts.append(f"{f.split('.')[-1]}={n/exp*100:4.1f}%")
    print(f"  {d:26s} " + "  ".join(parts))

print()
print("国家字段取样（新药）：")
for d in ["LUSPATERCEPT", "ROPEGINTERFERON ALFA-2B"]:
    q = f'patient.drug.openfda.generic_name:"{d}"'
    for field in ["occurcountry", "occurcountry.exact", "primarysource.country"]:
        r = S.get(BASE, params={"search": q, "count": field, "limit": 6}, timeout=60)
        time.sleep(0.35)
        st = r.status_code
        if st == 200:
            res = [(x["term"].strip(), x["count"]) for x in r.json().get("results", [])]
            print(f"  {d:24s} {field:24s} {st}  {res}")
        else:
            print(f"  {d:24s} {field:24s} {st}  {r.text[:110]}")

# -*- coding: utf-8 -*-
"""
probe2.py — 第二轮探测：药名枚举、适应证分布、严重结局
决定研究设计能否成立的三个前置问题：
  Q1 干扰素类在 openFDA 里到底怎么拼（第一轮 INTERFERON ALFA 无匹配）
  Q2 ruxolitinib 报告的适应证分布——MPN 占多少？能否做适应证分层？
  Q3 严重结局字段能否用于敏感性分析
"""
import requests, json, time
from collections import Counter

BASE = "https://api.fda.gov/drug/event.json"
S = requests.Session()
S.headers.update({"User-Agent": "FAERS-research/1.0"})


def count(field, search=None, limit=100, exact=True):
    params = {"count": field + (".exact" if exact else ""), "limit": limit}
    if search:
        params["search"] = search
    for i in range(3):
        try:
            r = S.get(BASE, params=params, timeout=60)
            if r.status_code == 200:
                return r.json().get("results", [])
            return None
        except Exception:
            time.sleep(2)
    return None


def total(search):
    try:
        r = S.get(BASE, params={"search": search, "limit": 1}, timeout=60)
        if r.status_code == 200:
            return r.json()["meta"]["results"]["total"]
        return 0
    except Exception:
        return -1


print("=" * 78)
print("Q1  含 INTERFERON 的标准药名（前 25）")
print("=" * 78)
res = count("patient.drug.openfda.generic_name",
            'patient.drug.openfda.generic_name:INTERFERON*', limit=200)
if res:
    for r in res[:25]:
        print(f"   {r['term'][:52]:54s} {r['count']:>8,}")
    print(f"   ... 共 {len(res)} 个 term")
else:
    print("   查询失败")

print()
print("=" * 78)
print("Q2  ruxolitinib 报告的适应证分布（前 20）")
print("=" * 78)
res = count("patient.drug.drugindication",
            'patient.drug.openfda.generic_name:"RUXOLITINIB"', limit=30, exact=True)
if res:
    for r in res[:20]:
        print(f"   {str(r['term'])[:60]:62s} {r['count']:>7,}")
else:
    print("   查询失败或无该字段")

print()
print("=" * 78)
print("Q2b  ruxolitinib 报告中 MPN 相关适应证的直接计数")
print("=" * 78)
for term in ["MYELOFIBROSIS", "PRIMARY MYELOFIBROSIS", "MYELOPROLIFERATIVE",
             "POLYCYTHEMIA VERA", "ESSENTIAL THROMBOCYTHEMIA", "MYELODYSPLASTIC"]:
    n = total(f'patient.drug.openfda.generic_name:"RUXOLITINIB" AND patient.drug.drugindication:"{term}"')
    print(f"   {term:34s} {n:>8,}")
    time.sleep(0.35)

print()
print("=" * 78)
print("Q2c  改用 reaction 之外的路径：检查报告是否含 MPN 关键词（全字段）")
print("=" * 78)
n_all_mf = total('patient.drug.drugindication:"MYELOFIBROSIS"')
print(f"   全库适应证=MYELOFIBROSIS 的报告            {n_all_mf:>10,}")
n_all_mpn = total('patient.drug.drugindication:"MYELOPROLIFERATIVE"')
print(f"   全库适应证含 MYELOPROLIFERATIVE 的报告     {n_all_mpn:>10,}")

print()
print("=" * 78)
print("Q3  严重结局字段")
print("=" * 78)
for label, f in [
    ("serious（总体）", "serious:1"),
    ("死亡", "seriousnessdeath:1"),
    ("住院", "seriousnesshospitalization:1"),
    ("危及生命", "seriousnesslifethreatening:1"),
]:
    n = total(f)
    print(f"   {label:24s} {n:>12,}")
    time.sleep(0.35)

print()
print("=" * 78)
print("Q4  ruxolitinib 之中严重报告的比例")
print("=" * 78)
for label, f in [
    ("ruxolitinib 总", 'patient.drug.openfda.generic_name:"RUXOLITINIB"'),
    ("ruxolitinib 死亡", 'patient.drug.openfda.generic_name:"RUXOLITINIB" AND seriousnessdeath:1'),
    ("ruxolitinib 住院", 'patient.drug.openfda.generic_name:"RUXOLITINIB" AND seriousnesshospitalization:1'),
]:
    n = total(f)
    print(f"   {label:24s} {n:>12,}")
    time.sleep(0.35)

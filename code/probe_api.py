# -*- coding: utf-8 -*-
"""
probe_api.py — 探测 openFDA 接口能力，决定 2x2 表能否直接由 API 构造
关键问题：
  1. total 是"报告数"还是"记录数"？
  2. generic_name 与 medicinalproduct 的覆盖差异
  3. 交集查询是否准确（数组字段）
  4. NOT 语法是否可用
  5. openfda 字段缺失率
"""
import requests, json, time, sys

BASE = "https://api.fda.gov/drug/event.json"
UA = {"User-Agent": "FAERS-research/1.0"}
S = requests.Session()
S.headers.update(UA)


def q(search, limit=1, retries=3):
    """返回 (status, total, error_msg)"""
    params = {"limit": limit}
    if search:
        params["search"] = search
    for i in range(retries):
        try:
            r = S.get(BASE, params=params, timeout=60)
            j = r.json()
            if r.status_code == 200:
                return 200, j.get("meta", {}).get("results", {}).get("total"), ""
            return r.status_code, None, j.get("error", {}).get("message", "")[:110]
        except Exception as e:
            if i == retries - 1:
                return -1, None, f"{type(e).__name__}: {str(e)[:90]}"
            time.sleep(2)
    return -1, None, "unknown"


def show(label, search):
    st, tot, err = q(search)
    mark = "OK " if st == 200 else "ERR"
    print(f"  [{mark}] {label:52s} {tot:>12,} " if st == 200 else f"  [{mark}] {label:52s} {err}")
    time.sleep(0.35)
    return tot


print("=" * 78)
print("A. 基础计数")
print("=" * 78)
n_total = show("全库报告数", None)
n_rux_g = show("ruxolitinib (generic_name)", 'patient.drug.openfda.generic_name:"RUXOLITINIB"')
n_rux_m = show("ruxolitinib (medicinalproduct)", 'patient.drug.medicinalproduct:"RUXOLITINIB"')
n_pe = show("PT: Pulmonary embolism", 'patient.reaction.reactionmeddrapt:"Pulmonary embolism"')
n_dvt = show("PT: Deep vein thrombosis", 'patient.reaction.reactionmeddrapt:"Deep vein thrombosis"')

print()
print("=" * 78)
print("B. 交集查询（数组字段的 AND 语义）")
print("=" * 78)
n_both = show("ruxolitinib AND pulmonary embolism",
              'patient.drug.openfda.generic_name:"RUXOLITINIB" AND patient.reaction.reactionmeddrapt:"Pulmonary embolism"')

print()
print("=" * 78)
print("C. NOT 语法（用于构造非暴露组）")
print("=" * 78)
n_not = show("NOT ruxolitinib", 'NOT patient.drug.openfda.generic_name:"RUXOLITINIB"')
n_not2 = show("_exists_ 反向（对照）", '_exists_:patient.drug.openfda.generic_name')

print()
print("=" * 78)
print("D. openfda 字段覆盖率")
print("=" * 78)
cover = show("有 openfda.generic_name 的报告",
             '_exists_:patient.drug.openfda.generic_name')

print()
print("=" * 78)
print("E. 一致性校验")
print("=" * 78)
if n_total and n_rux_g and n_not:
    print(f"  全库 {n_total:,}  vs  有药 {n_rux_g:,} + 无药 {n_not:,} = {n_rux_g + n_not:,}")
    print(f"  差值 {n_total - (n_rux_g + n_not):,}  （应为 0；非 0 说明 NOT 语义有误）")
if n_total and cover:
    print(f"  openfda.generic_name 覆盖率 = {cover / n_total * 100:.1f}%")

print()
print("=" * 78)
print("F. 2x2 表构造（ruxolitinib x PE）")
print("=" * 78)
if all(v is not None for v in [n_total, n_rux_g, n_pe, n_both]):
    a = n_both
    b = n_rux_g - a
    c = n_pe - a
    d = n_total - a - b - c
    print(f"  a (药+事件) = {a:>10,}")
    print(f"  b (药+其他) = {b:>10,}")
    print(f"  c (其他药+事件) = {c:>10,}")
    print(f"  d (其他)     = {d:>10,}")
    print(f"  合计 = {a+b+c+d:,}  vs 全库 {n_total:,}  差 {n_total-(a+b+c+d):,}")
    if a and b and c and d:
        import math
        ror = (a / b) / (c / d) if b and c else float("inf")
        se = math.sqrt(1/a + 1/b + 1/c + 1/d)
        lo, hi = math.exp(math.log(ror) - 1.96*se), math.exp(math.log(ror) + 1.96*se)
        print(f"  ROR = {ror:.2f} (95%CI {lo:.2f}-{hi:.2f})")

print()
print("=" * 78)
print("G. 其他候选药的计数（检查拼写）")
print("=" * 78)
for name in ["HYDROXYUREA", "ANAGRELIDE", "INTERFERON ALFA", "INTERFERON ALFA-2A",
             "BUSULFAN", "LUSPATERCEPT", "PEGINTERFERON ALFA-2A"]:
    show(name, f'patient.drug.openfda.generic_name:"{name}"')

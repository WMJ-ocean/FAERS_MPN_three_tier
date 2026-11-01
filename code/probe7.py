# -*- coding: utf-8 -*-
"""
probe7.py — 直接回答"这些报告是什么病人报的、有没有依据"
核心：脾梗死/心梗在 MPN 人群中的背景富集倍数
"""
import requests, time

BASE = "https://api.fda.gov/drug/event.json"
S = requests.Session()
S.headers.update({"User-Agent": "FAERS-research/1.0"})

MPN_IND = ["POLYCYTHAEMIA VERA", "ESSENTIAL THROMBOCYTHAEMIA",
           "MYELOFIBROSIS", "PRIMARY MYELOFIBROSIS"]


def q(search, retries=3):
    for i in range(retries):
        try:
            r = S.get(BASE, params={"search": search, "limit": 1}, timeout=60)
            j = r.json()
            if r.status_code == 200:
                return j["meta"]["results"]["total"]
            return -1
        except Exception:
            if i == retries - 1:
                return -1
            time.sleep(2)
    return -1


def s(search):
    n = q(search)
    time.sleep(0.35)
    return n


TOTAL = s('_exists_:receivedate')
print(f"全库 N = {TOTAL:,}\n")

print("=" * 84)
print("A. MPN 适应证的总盘子（分母的基线）")
print("=" * 84)
mpn_or = " OR ".join(f'"{x}"' for x in MPN_IND)
n_mpn = s(f'patient.drug.drugindication:({mpn_or})')
print(f"  含任一 MPN 适应证的报告              {n_mpn:>12,}  ({n_mpn/TOTAL*100:.3f}% of 全库)")
for x in MPN_IND:
    n = s(f'patient.drug.drugindication:"{x}"')
    print(f"    {x:<32} {n:>12,}")
print()

print("=" * 84)
print("B. 事件的背景富集：MPN 人群 vs 全库")
print("=" * 84)
EVTS = ["Splenic infarction", "Portal vein thrombosis", "Budd-Chiari syndrome",
        "Myocardial infarction", "Pulmonary embolism"]
print(f"{'事件':<26}{'全库':>10}{'MPN内':>10}{'富集倍数':>10}")
print("-" * 84)
for ev in EVTS:
    n_all = s(f'patient.reaction.reactionmeddrapt:"{ev}"')
    n_mpn_ev = s(f'patient.drug.drugindication:({mpn_or}) AND '
                 f'patient.reaction.reactionmeddrapt:"{ev}"')
    rate_all = n_all / TOTAL
    rate_mpn = n_mpn_ev / n_mpn if n_mpn else 0
    fold = rate_mpn / rate_all if rate_all else 0
    print(f"{ev:<26}{n_all:>10,}{n_mpn_ev:>10,}{fold:>9.1f}x")
print()

print("=" * 84)
print("C. 关键药-事件报告里，MPN 适应证占多少（这些报告到底是什么病人）")
print("=" * 84)
CASES = [("HYDROXYUREA", "Splenic infarction"),
         ("RUXOLITINIB", "Splenic infarction"),
         ("ANAGRELIDE", "Myocardial infarction"),
         ("HYDROXYUREA", "Pulmonary embolism")]
print(f"{'药 × 事件':<46}{'总':>8}{'含MPN':>8}{'占比':>8}")
print("-" * 84)
for drug, ev in CASES:
    base = (f'patient.drug.openfda.generic_name:"{drug}" AND '
            f'patient.reaction.reactionmeddrapt:"{ev}"')
    n = s(base)
    nm = s(base + f' AND patient.drug.drugindication:({mpn_or})')
    pct = nm / n * 100 if n and n > 0 else 0
    print(f"{drug + ' × ' + ev:<46}{n:>8,}{nm:>8,}{pct:>7.0f}%")
print()

print("=" * 84)
print("D. 对照：这些药的整体适应证构成（不含事件限定）")
print("=" * 84)
for drug in ["HYDROXYUREA", "RUXOLITINIB", "ANAGRELIDE"]:
    tot = s(f'patient.drug.openfda.generic_name:"{drug}"')
    nm = s(f'patient.drug.openfda.generic_name:"{drug}" AND '
           f'patient.drug.drugindication:({mpn_or})')
    print(f"  {drug:<14} 总 {tot:>8,}   含MPN {nm:>8,}  ({nm/tot*100:5.1f}%)")
print()

print("=" * 84)
print("E. 羟基脲的其他主要适应证（解释为什么 MPN 只占一部分）")
print("=" * 84)
for ind in ["SICKLE CELL ANAEMIA", "SICKLE CELL DISEASE", "CHRONIC MYELOID LEUKAEMIA",
            "ESSENTIAL THROMBOCYTHAEMIA", "POLYCYTHAEMIA VERA"]:
    n = s(f'patient.drug.openfda.generic_name:"HYDROXYUREA" AND '
          f'patient.drug.drugindication:"{ind}"')
    print(f"  {ind:<32} {n:>8,}")

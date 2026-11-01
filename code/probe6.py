# -*- coding: utf-8 -*-
"""
probe6.py — 核查一个可能影响全部结论的问题：
现有检索只用了 generic_name，**未限定 drugcharacterization**。
若大量"药-事件"报告里该药其实是 Concomitant（合并用药）而非 Suspect（可疑药），
则 L1 的 ROR 会进一步虚高，且"报告说这个药引发血栓"的说法根本不成立。

drugcharacterization: 1=Suspect 2=Concomitant 3=Interacting 4=not administered
"""
import requests, time

BASE = "https://api.fda.gov/drug/event.json"
S = requests.Session()
S.headers.update({"User-Agent": "FAERS-research/1.0"})


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


def row(label, base, char=None):
    s = base if char is None else f'{base} AND patient.drug.drugcharacterization:{char}'
    n = q(s)
    time.sleep(0.35)
    return n


DRUGS = {
    "HYDROXYUREA": "脾梗死|Splenic infarction",
    "ANAGRELIDE": "心肌梗死|Myocardial infarction",
    "RUXOLITINIB": "脾梗死|Splenic infarction",
}

print("=" * 84)
print("A. 各药报告的药物角色构成（限定事件 / 不限定事件）")
print("=" * 84)
print(f"{'药物':<14}{'事件':<10}{'总报告':>10}{'可疑药':>10}{'合并药':>10}{'可疑占比':>9}")
print("-" * 84)

out = {}
for drug, spec in DRUGS.items():
    ev = spec.split("|")[1]
    base_ev = (f'patient.drug.openfda.generic_name:"{drug}" AND '
               f'patient.reaction.reactionmeddrapt:"{ev}"')
    base_all = f'patient.drug.openfda.generic_name:"{drug}"'
    for tag, base in [("不限事件", base_all), (ev, base_ev)]:
        tot = row(tag, base)
        s1 = row(tag, base, 1)
        s2 = row(tag, base, 2)
        pct = s1 / tot * 100 if tot and tot > 0 and s1 > 0 else float("nan")
        print(f"{drug:<14}{tag:<10}{tot:>10,}{s1:>10,}{s2:>10,}{pct:>8.1f}%")
        out[(drug, tag)] = (tot, s1, s2)

print()
print("=" * 84)
print("B. 只看可疑药（char=1）重算 ROR —— 对比原口径")
print("=" * 84)
print("注：openFDA 数组字段无法约束'同一 drug 对象'，char 限定为报告级近似。")
print()

TOTAL = q('_exists_:receivedate')
print(f"全库报告数 N = {TOTAL:,}")
print()

CASES = [
    ("HYDROXYUREA", "Splenic infarction", "脾梗死"),
    ("HYDROXYUREA", "Pulmonary embolism", "肺栓塞"),
    ("RUXOLITINIB", "Splenic infarction", "脾梗死"),
    ("ANAGRELIDE", "Myocardial infarction", "心肌梗死"),
]


def ror(a, b, c, d):
    import math
    if min(a, b, c, d) == 0:
        return None, None, None
    r = (a / b) / (c / d)
    se = math.sqrt(1/a + 1/b + 1/c + 1/d)
    return r, math.exp(math.log(r) - 1.96*se), math.exp(math.log(r) + 1.96*se)


print(f"{'药物':<14}{'事件':<22}{'口径':<12}{'a':>8}{'ROR':>9}{'95%CI':>18}")
print("-" * 84)

for drug, ev, cn in CASES:
    for tag, extra in [("原口径", ""), ("仅可疑药", " AND patient.drug.drugcharacterization:1")]:
        base = (f'patient.drug.openfda.generic_name:"{drug}" AND '
                f'patient.reaction.reactionmeddrapt:"{ev}"{extra}')
        a = row(tag, base)
        n_drug = row(tag, f'patient.drug.openfda.generic_name:"{drug}"{extra}')
        n_ev = row(tag, f'patient.reaction.reactionmeddrapt:"{ev}"')
        n_ev_s = n_ev if not extra else row(tag, f'patient.reaction.reactionmeddrapt:"{ev}"{extra}')
        b = n_drug - a
        c = n_ev_s - a
        d = TOTAL - a - b - c
        r, lo, hi = ror(a, b, c, d)
        ci = f"{lo:.2f}-{hi:.2f}" if r else "NA"
        rv = f"{r:.2f}" if r else "NA"
        print(f"{drug:<14}{cn:<22}{tag:<12}{a:>8,}{rv:>9}{ci:>18}")
    print("-" * 84)

print()
print("=" * 84)
print("C. 报告是否含因果判断字段（说明上报者是否归因）")
print("=" * 84)
for f in ["patient.drug.drugadditional",
          "patient.reaction.reactionoutcome",
          "patient.drug.actiondrug",
          "patient.drug.drugindication"]:
    n = q(f'_exists_:{f}')
    pct = n / TOTAL * 100 if n and n > 0 else 0
    print(f"  {f:<38} 有值 {n:>12,}  ({pct:5.1f}%)")
    time.sleep(0.35)

print()
print("=" * 84)
print("D. 羟基脲报告中 MPN 适应证的占比（背景发生率问题的核心）")
print("=" * 84)
for ind in ["POLYCYTHAEMIA VERA", "ESSENTIAL THROMBOCYTHAEMIA",
            "MYELOFIBROSIS", "PRIMARY MYELOFIBROSIS"]:
    n = q(f'patient.drug.openfda.generic_name:"HYDROXYUREA" AND '
          f'patient.drug.drugindication:"{ind}"')
    print(f"  羟基脲 × 适应证 {ind:<28} {n:>8,}")
    time.sleep(0.35)

# -*- coding: utf-8 -*-
"""
case_series.py — READUS-PV 第 7d / 10 条：个例层面的结构化描述
==============================================================
openFDA 不提供叙述文本（narrative）与因果关系评估字段，因此这里做的是
"结构化个例回顾"：对每个目标药-事件组合抽取报告，读其结构化字段
（适应证、药物角色、合并用药、全部 PT、转归），用以判断
"该报告能否支持药物致病"这一具体问题。

抽取策略：
  每个组合取最多 100 份报告，保留字段最完整者；
  再按"是否记录了 MPN 适应证""是否为可疑药""是否有合并用药"分层，
  挑出可代表三类情形（典型/混杂/难判）的个案各若干。

输出：02_tables/case_series.csv
"""
import requests, json, time, os, csv

BASE = "https://api.fda.gov/drug/event.json"
OUT = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒\00_data"
os.makedirs(OUT, exist_ok=True)
S = requests.Session()
S.headers.update({"User-Agent": "FAERS-pharmacovigilance-research/1.0"})

COMBOS = [
    ("HYDROXYUREA", "Splenic infarction"),
    ("RUXOLITINIB", "Splenic infarction"),
    ("ANAGRELIDE", "Myocardial infarction"),
    ("HYDROXYUREA", "Budd-Chiari syndrome"),
    ("ROPEGINTERFERON ALFA-2B", "Myocardial infarction"),
]

MPN_TERMS = ["MYELOFIBROSIS", "PRIMARY MYELOFIBROSIS", "MYELOPROLIFERATIVE NEOPLASM",
             "MYELOPROLIFERATIVE DISORDER", "POLYCYTHAEMIA VERA", "ESSENTIAL THROMBOCYTHAEMIA",
             "POLYCYTHEMIA VERA", "ESSENTIAL THROMBOCYTHEMIA"]

cache_path = os.path.join(OUT, "case_series_raw.json")
RAW = json.load(open(cache_path, encoding="utf-8")) if os.path.exists(cache_path) else {}


def fetch(drug, pt, limit=100, skip=0):
    key = f"{drug}|{pt}|{limit}|{skip}"
    if key in RAW:
        return RAW[key]
    q = (f'patient.drug.openfda.generic_name:"{drug}" '
         f'AND patient.reaction.reactionmeddrapt:"{pt}"')
    for _ in range(4):
        try:
            r = S.get(BASE, params={"search": q, "limit": limit, "skip": skip}, timeout=90)
            if r.status_code == 200:
                RAW[key] = r.json().get("results", [])
                json.dump(RAW, open(cache_path, "w", encoding="utf-8"))
                time.sleep(0.5)
                return RAW[key]
            if r.status_code == 404:
                return []
            time.sleep(4)
        except Exception:
            time.sleep(4)
    return []


def gw(d, path, default=""):
    cur = d
    for k in path.split("."):
        if isinstance(cur, list):
            cur = cur[0] if cur else {}
        if not isinstance(cur, dict):
            return default
        cur = cur.get(k, default)
    if isinstance(cur, list):
        return cur[0] if cur else default
    return cur


def extract(rec, drug, pt):
    """把一份 ICSR 压成一行结构化摘要"""
    drugs = rec.get("patient", {}).get("drug", []) or []
    rxns = rec.get("patient", {}).get("reaction", []) or []
    suspect = []
    mpn_ind = []
    for d in drugs:
        nm = gw(d, "openfda.generic_name")
        ind = (d.get("drugindication") or "").strip()
        role = gw(d, "drugcharacterization")
        if not nm:
            nm = (d.get("medicinalproduct") or "").strip()
        if role == "1":
            suspect.append(nm.upper()[:28])
        if any(t in ind.upper() for t in MPN_TERMS):
            mpn_ind.append(ind.upper()[:32])
    age = gw(rec, "patient.patientonsetage")
    if not age:
        age = gw(rec, "patient.patientagegroup")
    return dict(
        drug=drug,
        pt=pt,
        report_id=rec.get("safetyreportid", ""),
        date=rec.get("receiptdate", ""),
        country=rec.get("occurcountry", ""),
        sex={"1": "M", "2": "F", "0": "?", "": "?"}.get(gw(rec, "patient.patientsex"), "?"),
        age=str(age),
        reporter=gw(rec, "primarysource.qualification"),
        serious=rec.get("serious", ""),
        outcome=gw(rec, "patient.reaction.reactionoutcome"),
        n_drugs=len(drugs),
        n_reactions=len(rxns),
        suspect_drugs="; ".join(suspect[:4]),
        mpn_indication="; ".join(sorted(set(mpn_ind))[:3]),
        reactions="; ".join([(x.get("reactionmeddrapt") or "")[:30] for x in rxns[:5]]),
        drug_role_of_interest=next(
            (gw(d, "drugcharacterization") for d in drugs
             if (gw(d, "openfda.generic_name") or "").upper() == drug.upper()), ""),
        drug_indication_of_interest=next(
            ((d.get("drugindication") or "").strip() for d in drugs
             if (gw(d, "openfda.generic_name") or "").upper() == drug.upper()), ""),
    )


all_rows = []
for drug, pt in COMBOS:
    recs = fetch(drug, pt)
    # 再翻一页，提高遇到字段完整者的概率
    if len(recs) >= 100:
        recs += fetch(drug, pt, skip=100)
    rows = [extract(r, drug, pt) for r in recs]
    all_rows += rows
    print(f"[{drug} x {pt}] 取到 {len(rows)} 份")

path = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒\02_tables\case_series.csv"
cols = ["drug", "pt", "report_id", "date", "country", "sex", "age", "reporter", "serious",
        "outcome", "n_drugs", "n_reactions", "drug_role_of_interest",
        "drug_indication_of_interest", "mpn_indication", "suspect_drugs", "reactions"]
with open(path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in all_rows:
        w.writerow({k: r.get(k, "") for k in cols})
print(f"\n[OK] {path}  {len(all_rows)} 行")

# ---------- 描述性统计 ----------
print()
print("=" * 78)
print("结构化特征（全部抽取报告）")
print("=" * 78)
n = len(all_rows)
if n:
    n_ind = sum(1 for r in all_rows if r["mpn_indication"])
    n_role1 = sum(1 for r in all_rows if r["drug_role_of_interest"] == "1")
    n_multi = sum(1 for r in all_rows if r["n_drugs"] > 1)
    n_age = sum(1 for r in all_rows if r["age"])
    print(f"  报告数                          {n}")
    print(f"  记录到 MPN 适应证               {n_ind} ({n_ind/n*100:.1f}%)")
    print(f"  目标药标为 suspect (role=1)      {n_role1} ({n_role1/n*100:.1f}%)")
    print(f"  含 >1 种合并用药                 {n_multi} ({n_multi/n*100:.1f}%)")
    print(f"  记录年龄                         {n_age} ({n_age/n*100:.1f}%)")

# ---------- 候选个案 ----------
print()
print("=" * 78)
print("候选个案（MPN 适应证明确 + 字段完整）")
print("=" * 78)
cands = [r for r in all_rows if r["mpn_indication"] and r["age"] and r["sex"] in ("M", "F")]
seen = set()
for r in cands:
    if r["drug"] + r["pt"] in seen:
        continue
    seen.add(r["drug"] + r["pt"])
    print(f"\n  · {r['drug']} × {r['pt']}  ID={r['report_id']}  {r['date']}  {r['country']}")
    print(f"    {r['sex']} / {r['age']}y  reporter={r['reporter']}  serious={r['serious']}  outcome={r['outcome']}")
    print(f"    目标药适应证: {r['drug_indication_of_interest']}   角色={r['drug_role_of_interest']}")
    print(f"    合并用药 {r['n_drugs']} 种: {r['suspect_drugs']}")
    print(f"    事件: {r['reactions']}")

# -*- coding: utf-8 -*-
"""
case_analysis.py — 结构化个例回顾（READUS-PV 7d / 10）
=====================================================
openFDA 不提供叙述文本，也不提供因果关系评估字段。因此本脚本在
"个例"层面能做的、且审稿人会要的只有三件事：

  1. 药物角色：目标药在报告里被标为可疑药（1）、合并用药（2）还是
     相互作用（3）——这决定该报告是否把事件归给该药
  2. 适应证是否记录：没有适应证的报告，无法判断事件是否属于疾病本身
  3. 共报告事件：是否伴随脾大、门脉高压、疾病进展等"疾病本身即可解释"
     的表现

输出：02_tables/case_series_summary.csv 与 02_tables/case_exemplars.csv
"""
import json, os, csv, collections

BASE = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒"
RAW = json.load(open(os.path.join(BASE, "00_data", "case_series_raw.json"), encoding="utf-8"))

MPN_TERMS = ["MYELOFIBROSIS", "MYELOPROLIFERATIVE", "POLYCYTHAEMIA VERA", "POLYCYTHEMIA VERA",
             "ESSENTIAL THROMBOCYTHAEMIA", "ESSENTIAL THROMBOCYTHEMIA"]
# 疾病本身即可解释该事件的共报告表现
DISEASE_CONSISTENT = ["SPLENOMEGALY", "HEPATOMEGALY", "PORTAL HYPERTENSION", "VARICES",
                      "MYELOFIBROSIS", "DISEASE PROGRESSION", "SPLENIC VEIN THROMBOSIS",
                      "PORTAL VEIN THROMBOSIS", "THROMBOCYTOSIS", "HAEMOGLOBIN INCREASED",
                      "OFF LABEL USE", "PRODUCT USE ISSUE", "NO ADVERSE EVENT"]
ROLE = {"1": "Suspect", "2": "Concomitant", "3": "Interacting"}


def gname(d):
    o = (d.get("openfda") or {}).get("generic_name") or []
    if isinstance(o, str):
        o = [o]
    return (o[0] if o else (d.get("medicinalproduct") or "")).strip().upper()


def one(rec, drug, pt):
    p = rec.get("patient", {})
    drugs = p.get("drug", []) or []
    rxns = p.get("reaction", []) or []
    hits = [d for d in drugs if gname(d) == drug.upper()]
    roles = [d.get("drugcharacterization", "") for d in hits]
    ind = next((d.get("drugindication") or "" for d in hits if d.get("drugindication")), "")
    all_ind = " | ".join((d.get("drugindication") or "") for d in drugs).upper()
    terms = [(r.get("reactionmeddrapt") or "") for r in rxns]
    dm = [t for t in terms if any(k in t.upper() for k in DISEASE_CONSISTENT)]
    co = [gname(d) for d in drugs if gname(d) != drug.upper() and gname(d)]
    age = p.get("patientonsetage") or ""
    return dict(
        drug=drug, pt=pt, report_id=rec.get("safetyreportid", ""),
        date=rec.get("receiptdate", ""), country=rec.get("occurcountry", "")
        or rec.get("primarysourcecountry", ""),
        sex={"1": "M", "2": "F"}.get(p.get("patientsex", ""), "NR"),
        age=age,
        reporter={"1": "Physician", "2": "Pharmacist", "3": "Other HCP", "4": "Lawyer",
                  "5": "Consumer", "": "NR"}.get(rec.get("primarysource", {}).get("qualification", ""), "NR"),
        serious=rec.get("serious", ""),
        n_drugs=len(drugs), n_reactions=len(rxns),
        role=(";".join(sorted(set(r for r in roles if r))) or "NR"),
        role_label=ROLE.get(roles[0], "Not listed") if roles else "Not listed",
        indication=ind,
        mpn_recorded="Y" if any(t in all_ind for t in MPN_TERMS) else "N",
        disease_consistent="; ".join(dm[:4]),
        co_drugs="; ".join(sorted(set(co))[:4]),
        n_co=len(set(co)),
        reactions="; ".join(terms[:6]),
    )


rows = []
for key, recs in RAW.items():
    drug, pt = key.split("|")[0], key.split("|")[1]
    for r in recs:
        rows.append(one(r, drug, pt))

# 去重（同一 safetyreportid 可能在两页重复）
seen, uniq = set(), []
for r in rows:
    k = (r["report_id"], r["drug"], r["pt"])
    if k in seen:
        continue
    seen.add(k)
    uniq.append(r)
rows = uniq
print(f"去重后 {len(rows)} 份报告")

# ---------- 组合层面的汇总 ----------
summ = []
print()
print("=" * 96)
print(f"{'药 × 事件':<44}{'n':>5}{'suspect':>9}{'concom':>8}{'MPN记录':>9}{'疾病可解释':>11}{'多药':>7}")
print("=" * 96)
for drug, pt in [("HYDROXYUREA", "Splenic infarction"),
                 ("RUXOLITINIB", "Splenic infarction"),
                 ("ANAGRELIDE", "Myocardial infarction"),
                 ("HYDROXYUREA", "Budd-Chiari syndrome"),
                 ("ROPEGINTERFERON ALFA-2B", "Myocardial infarction")]:
    g = [r for r in rows if r["drug"] == drug and r["pt"] == pt]
    n = len(g)
    ns = sum(1 for r in g if "1" in r["role"].split(";"))
    nc = sum(1 for r in g if r["role"].strip() in ("2", "2;3"))
    nm = sum(1 for r in g if r["mpn_recorded"] == "Y")
    nd = sum(1 for r in g if r["disease_consistent"])
    nmulti = sum(1 for r in g if r["n_drugs"] > 1)
    print(f"{drug + ' × ' + pt:<44}{n:>5}{ns:>9}{nc:>8}{nm:>9}{nd:>11}{nmulti:>7}")
    summ.append(dict(drug=drug, pt=pt, n=n, suspect=ns, concomitant=nc,
                     mpn_recorded=nm, disease_consistent=nd, multidrug=nmulti))

with open(os.path.join(BASE, "02_tables", "case_series_summary.csv"), "w",
          encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(summ[0].keys()))
    w.writeheader()
    w.writerows(summ)

# ---------- 挑选 5 例典型 ----------
print()
print("=" * 96)
print("候选典型个例（MPN 适应证明确、字段较完整）")
print("=" * 96)


def score(r):
    s = 0
    s += 2 if r["mpn_recorded"] == "Y" else 0
    s += 1 if r["age"] and r["age"].isdigit() else 0
    s += 1 if r["sex"] in ("M", "F") else 0
    s += 1 if r["disease_consistent"] else 0
    s += 1 if r["role_label"] == "Suspect" else 0
    return s


picks = []
for drug, pt in [("RUXOLITINIB", "Splenic infarction"),
                 ("HYDROXYUREA", "Splenic infarction"),
                 ("ANAGRELIDE", "Myocardial infarction"),
                 ("HYDROXYUREA", "Budd-Chiari syndrome"),
                 ("ROPEGINTERFERON ALFA-2B", "Myocardial infarction")]:
    g = [r for r in rows if r["drug"] == drug and r["pt"] == pt
         and r["mpn_recorded"] == "Y" and r["role_label"] == "Suspect"]
    g.sort(key=lambda r: -score(r))
    if g:
        picks.append(g[0])

for i, r in enumerate(picks, 1):
    print(f"\n[Case {i}] {r['drug']} × {r['pt']}")
    print(f"  ID {r['report_id']} | {r['date']} | {r['country']} | {r['sex']} {r['age']}y | "
          f"reporter {r['reporter']} | serious={r['serious']}")
    print(f"  目标药适应证: {r['indication']}   角色: {r['role_label']}")
    print(f"  合并用药 {r['n_co']} 种: {r['co_drugs']}")
    print(f"  共报告: {r['reactions']}")
    print(f"  疾病可解释项: {r['disease_consistent'] or '—'}")

cols = ["drug", "pt", "report_id", "date", "country", "sex", "age", "reporter", "serious",
        "role_label", "indication", "mpn_recorded", "co_drugs", "n_co",
        "disease_consistent", "reactions"]
with open(os.path.join(BASE, "02_tables", "case_exemplars.csv"), "w",
          encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in picks:
        w.writerow({k: r.get(k, "") for k in cols})

# ---------- 全样本角色分布 ----------
print()
print("=" * 96)
cnt = collections.Counter(r["role_label"] for r in rows)
print("全部 169 份报告的角色归属：", dict(cnt))
print(f"MPN 适应证记录率：{sum(1 for r in rows if r['mpn_recorded']=='Y')}/{len(rows)}")
print(f"含 >1 种药物：{sum(1 for r in rows if r['n_drugs']>1)}/{len(rows)}")
print(f"含疾病可解释的共报告事件：{sum(1 for r in rows if r['disease_consistent'])}/{len(rows)}")

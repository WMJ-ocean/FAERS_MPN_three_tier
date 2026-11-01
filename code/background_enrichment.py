# -*- coding: utf-8 -*-
"""
background_enrichment.py — 疾病背景富集倍数
==========================================
定义：某事件在 MPN 报告池中的报告占比 / 该事件在全库报告中的占比。
若某事件在 MPN 人群中本就高发，则倍数 >1，说明"用 MPN 药物的人"
本身就有更高的事件基线——这是 L1 信号膨胀的机制来源。

这一指标是本文的关键中介变量：它预测了 L1→L2 的衰减幅度。
输出：02_tables/background_enrichment.csv
"""
import requests, json, os, csv, time

BASE = "https://api.fda.gov/drug/event.json"
OUT = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒"
S = requests.Session()
S.headers.update({"User-Agent": "FAERS-pharmacovigilance-research/1.0"})

CACHE = json.load(open(os.path.join(OUT, "00_data", "counts_mpn_cache.json"), encoding="utf-8"))
CACHE2 = json.load(open(os.path.join(OUT, "00_data", "counts_cache.json"), encoding="utf-8"))
ALL = {**CACHE2, **CACHE}

N_ALL = 20692690
MPN = ('(patient.drug.drugindication:"MYELOFIBROSIS"'
       ' OR patient.drug.drugindication:"PRIMARY MYELOFIBROSIS"'
       ' OR patient.drug.drugindication:"MYELOPROLIFERATIVE NEOPLASM"'
       ' OR patient.drug.drugindication:"MYELOPROLIFERATIVE DISORDER"'
       ' OR patient.drug.drugindication:"POLYCYTHAEMIA VERA"'
       ' OR patient.drug.drugindication:"ESSENTIAL THROMBOCYTHAEMIA")')
N_MPN = 58602

PTS = ["Splenic infarction", "Splenic vein thrombosis", "Portal vein thrombosis",
       "Budd-Chiari syndrome", "Arterial thrombosis", "Myocardial infarction",
       "Cerebrovascular accident", "Transient ischaemic attack", "Retinal vein occlusion",
       "Thrombosis", "Venous thrombosis", "Embolism", "Pulmonary embolism",
       "Deep vein thrombosis", "Thrombophlebitis", "Haemorrhage"]


def total(q):
    if q in ALL:
        return ALL[q]
    for _ in range(4):
        try:
            r = S.get(BASE, params={"search": q, "limit": 1}, timeout=60)
            if r.status_code == 200:
                n = r.json()["meta"]["results"]["total"]
                ALL[q] = n
                time.sleep(0.33)
                return n
            if r.status_code == 404:
                return 0
            time.sleep(3)
        except Exception:
            time.sleep(3)
    return 0


rows = []
print(f"{'PT':<30}{'MPN n':>8}{'MPN%':>9}{'DB n':>10}{'DB%':>9}{'ratio':>8}")
print("-" * 74)
for pt in PTS:
    pq = f'patient.reaction.reactionmeddrapt:"{pt}"'
    n_mpn = total(f"{MPN} AND {pq}")
    n_db = total(pq)
    p_mpn = n_mpn / N_MPN * 100
    p_db = n_db / N_ALL * 100
    ratio = p_mpn / p_db if p_db else float("nan")
    print(f"{pt:<30}{n_mpn:>8,}{p_mpn:>8.3f}%{n_db:>10,}{p_db:>8.3f}%{ratio:>8.1f}")
    rows.append(dict(pt=pt, n_mpn=n_mpn, pct_mpn=round(p_mpn, 3),
                     n_db=n_db, pct_db=round(p_db, 3), enrichment=round(ratio, 2)))

with open(os.path.join(OUT, "02_tables", "background_enrichment.csv"), "w",
          encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    w.writeheader()
    w.writerows(rows)
print("\n[OK] 02_tables/background_enrichment.csv")

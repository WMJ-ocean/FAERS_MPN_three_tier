# -*- coding: utf-8 -*-
import requests, time
S = requests.Session()
S.headers.update({"User-Agent": "FAERS-research/1.0"})
BASE = "https://api.fda.gov/drug/event.json"

print("--- 测试 exact 字段 ---")
for f in ["patient.drug.drugindication.exact", "patient.drug.openfda.generic_name.exact"]:
    r = S.get(BASE, params={"search": 'patient.reaction.reactionmeddrapt:"Splenic infarction"',
                            "count": f}, timeout=60)
    print(f, r.status_code)
    if r.status_code == 200:
        print("   ", [(x["term"], x["count"]) for x in r.json()["results"][:5]])
    else:
        print("   ", r.text[:160])
    time.sleep(0.4)

print()
print("--- 目标组合的适应证分布 ---")
for drug, ev in [("HYDROXYUREA", "Splenic infarction"),
                 ("RUXOLITINIB", "Splenic infarction"),
                 ("ANAGRELIDE", "Myocardial infarction")]:
    q = ('patient.drug.openfda.generic_name:"%s" AND '
         'patient.reaction.reactionmeddrapt:"%s"') % (drug, ev)
    r = S.get(BASE, params={"search": q, "count": "patient.drug.drugindication.exact", "limit": 10},
              timeout=60)
    print("=" * 68)
    print("%s x %s  -> %d" % (drug, ev, r.status_code))
    if r.status_code == 200:
        for x in r.json()["results"][:10]:
            print("    %-46s %3d" % (x["term"].strip()[:46], x["count"]))
    else:
        print("    ", r.text[:160])
    time.sleep(0.5)

# -*- coding: utf-8 -*-
import requests, time
S = requests.Session()
S.headers.update({"User-Agent": "FAERS-research/1.0"})
BASE = "https://api.fda.gov/drug/event.json"


def cnt(search, field, n=8):
    r = S.get(BASE, params={"search": search, "count": field}, timeout=60)
    if r.status_code != 200:
        print("    ERR", r.status_code, r.text[:200])
        return []
    res = r.json().get("results", [])
    return [(x["term"].strip()[:46], x["count"]) for x in res[:n]]


for drug, ev in [("HYDROXYUREA", "Splenic infarction"),
                 ("RUXOLITINIB", "Splenic infarction"),
                 ("ANAGRELIDE", "Myocardial infarction")]:
    q = ('patient.drug.openfda.generic_name:"%s" AND '
         'patient.reaction.reactionmeddrapt:"%s"') % (drug, ev)
    print("=" * 72)
    print("%s x %s" % (drug, ev))
    print("  适应证分布:")
    for t, c in cnt(q, "patient.drug.drugindication"):
        print("      %-48s %3d" % (t, c))
    time.sleep(0.5)

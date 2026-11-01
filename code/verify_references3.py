# -*- coding: utf-8 -*-
"""verify_references3.py — 第三轮：补充文献"""
import requests, time

S = requests.Session()
S.headers.update({"User-Agent": "ref-check/1.0"})

QUERIES = [
    ("hazell", 'AUTH:"Hazell L" AND TITLE:"Under-reporting"'),
    ("noren", 'AUTH:"Noren GN" AND TITLE:"Extending the methods used to screen the WHO drug safety database"'),
    ("barbui", 'TITLE:"Thrombosis in myeloproliferative neoplasms" AND TITLE:"viewpoint"'),
    ("chrysafi", 'TITLE:"Anticoagulation for splanchnic vein thrombosis in myeloproliferative neoplasms"'),
    ("samuelson15", 'TITLE:"Anagrelide compared with hydroxyurea in essential thrombocythemia" AND TITLE:"meta-analysis"'),
]

for tag, term in QUERIES:
    r = S.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search",
              params={"query": term, "format": "json", "pageSize": 4, "resultType": "core"},
              timeout=60)
    print("=" * 90)
    print("[" + tag + "]")
    if r.status_code != 200:
        print("  HTTP", r.status_code)
        continue
    res = r.json().get("resultList", {}).get("result", [])
    if not res:
        print("  (no hits)")
    for x in res:
        ji = x.get("journalInfo") or {}
        line = "  PMID {} | {};{}({}):{} | doi {}".format(
            x.get("pmid"), x.get("pubYear"), ji.get("volume", ""),
            ji.get("issue", ""), x.get("pageInfo") or "", x.get("doi"))
        print(line)
        print("      " + str(x.get("title"))[:130])
        print("      " + str(x.get("authorString") or "")[:120])
    time.sleep(0.4)

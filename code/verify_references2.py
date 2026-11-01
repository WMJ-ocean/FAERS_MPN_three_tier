# -*- coding: utf-8 -*-
"""verify_references2.py — 第二轮题录核实"""
import requests, time

S = requests.Session()
S.headers.update({"User-Agent": "ref-check/1.0"})

QUERIES = [
    ('proud', 'TITLE:"ropeginterferon" AND (TITLE:"PROUD-PV" OR TITLE:"CONTINUATION-PV" OR TITLE:"phase 3")'),
    ('ifn_thrombosis', 'TITLE:"interferon" AND TITLE:"polycythemia vera" AND (TITLE:"thrombotic" OR TITLE:"thrombosis") AND PUB_YEAR:[2013 TO 2025]'),
    ('mpn_death', 'TITLE:"myeloproliferative neoplasms" AND (TITLE:"cause of death" OR TITLE:"mortality") AND PUB_YEAR:[2015 TO 2025]'),
    ('splanchnic', 'TITLE:"splanchnic" AND TITLE:"myeloproliferative" AND PUB_YEAR:[2015 TO 2025]'),
    ('anagrelide_pde3', 'TITLE:"anagrelide" AND (TITLE:"phosphodiesterase" OR TITLE:"PDE3" OR TITLE:"cardiovascular")'),
    ('faers_limit', 'TITLE:"disproportionality" AND TITLE:"spontaneous reporting" AND PUB_YEAR:[2015 TO 2025] AND (TITLE:"limitations" OR TITLE:"pitfalls" OR TITLE:"bias")'),
    ('noren_bcpnn', 'TITLE:"Bayesian" AND TITLE:"neural network" AND TITLE:"adverse drug reaction" AND AUTH:"Noren"'),
    ('hydroxyurea_scd', 'TITLE:"hydroxyurea" AND TITLE:"sickle cell" AND PUB_YEAR:[2019 TO 2025] AND (TITLE:"trial" OR TITLE:"cohort")'),
    ('faers_indication', 'TITLE:"FAERS" AND (TITLE:"indication" OR TITLE:"confounding")'),
]

for tag, term in QUERIES:
    r = S.get("https://www.ebi.ac.uk/europepmc/webservices/rest/search",
              params={"query": term, "format": "json", "pageSize": 6, "resultType": "core"},
              timeout=60)
    print("=" * 100)
    print(f"[{tag}]  {term}")
    if r.status_code != 200:
        print("  HTTP", r.status_code)
        continue
    res = r.json().get("resultList", {}).get("result", [])
    if not res:
        print("  (no hits)")
    for x in res:
        ji = x.get("journalInfo") or {}
        print(f"  PMID {x.get('pmid')} | {x.get('pubYear')};{ji.get('volume','')}"
              f"({ji.get('issue','')}):{x.get('pageInfo') or ''} | {x.get('doi')}")
        print(f"      {x.get('title')}")
        print(f"      {(x.get('authorString') or '')[:110]}")
    time.sleep(0.4)

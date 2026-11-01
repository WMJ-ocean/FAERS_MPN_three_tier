# -*- coding: utf-8 -*-
"""verify_references.py — 用 Europe PMC 精确检索取题录，不凭记忆写 PMID"""
import requests, time, json

S = requests.Session()
S.headers.update({"User-Agent": "ref-check/1.0"})

QUERIES = [
    ('fusaroli', 'TITLE:"Charting and Sidestepping the Pitfalls of Disproportionality Analysis"'),
    ('readus', 'TITLE:"READUS-PV"'),
    ('pv_et_thrombosis', 'TITLE:"thrombosis" AND TITLE:"polycythemia vera" AND TITLE:"essential thrombocythemia" AND (PUB_YEAR:2019 OR PUB_YEAR:2020 OR PUB_YEAR:2021)'),
    ('anagrelide_hu', 'TITLE:"anagrelide" AND TITLE:"hydroxyurea" AND (TITLE:"thrombocythemia" OR TITLE:"thrombocythaemia") AND PUB_YEAR:[2000 TO 2025]'),
    ('ropeg', 'TITLE:"ropeginterferon" AND TITLE:"polycythemia vera"'),
    ('rux_thrombosis', 'TITLE:"ruxolitinib" AND TITLE:"myelofibrosis" AND (TITLE:"thrombosis" OR TITLE:"thrombotic")'),
    ('mpn_mortality', 'TITLE:"myeloproliferative" AND TITLE:"thrombosis" AND TITLE:"risk" AND PUB_YEAR:[2018 TO 2024]'),
    ('pde3', 'TITLE:"anagrelide" AND (TITLE:"mechanism" OR TITLE:"phosphodiesterase")'),
    ('ic100', 'TITLE:"information component" AND TITLE:"disproportionate"'),
    ('scd_hu', 'TITLE:"hydroxyurea" AND TITLE:"sickle cell" AND TITLE:"vaso-occlusive"'),
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
        au = (x.get("authorString") or "")
        print(f"  PMID {x.get('pmid')} | {x.get('journalTitle')} {x.get('pubYear')};"
              f"{(x.get('journalInfo') or {}).get('volume','')}"
              f"({(x.get('journalInfo') or {}).get('issue','')}):"
              f"{(x.get('pageInfo') or '')} | doi {x.get('doi')}")
        print(f"      {x.get('title')}")
        print(f"      {au[:120]}")
    time.sleep(0.4)

# -*- coding: utf-8 -*-
"""
probe3.py — 解决拼写陷阱
openFDA 的两个坑：
  1. MedDRA/适应证多用英式拼写：POLYCYTHAEMIA / THROMBOCYTHAEMIA / ischaemic
     用美式拼写查询会静默返回 0，不报错 —— 这是最危险的一类错误
  2. 干扰素类药名不确定，需要枚举
本脚本逐个验证候选写法，只保留真实存在的
"""
import requests, time, json

BASE = "https://api.fda.gov/drug/event.json"
S = requests.Session()
S.headers.update({"User-Agent": "FAERS-research/1.0"})


def total(search):
    try:
        r = S.get(BASE, params={"search": search, "limit": 1}, timeout=60)
        if r.status_code == 200:
            return r.json()["meta"]["results"]["total"]
        return 0
    except Exception:
        return -1


def probe_list(title, queries):
    print("=" * 80)
    print(title)
    print("=" * 80)
    ok = []
    for label, qs in queries:
        n = total(qs)
        mark = "  ✔" if n and n > 0 else "  ✘"
        print(f"{mark} {label:44s} {n:>10,}")
        if n and n > 0:
            ok.append((label, qs, n))
        time.sleep(0.34)
    print()
    return ok


# ---------- 1. 适应证英式/美式拼写 ----------
probe_list("1. 适应证拼写（MPN 三种疾病）", [
    ("Myelofibrosis",            'patient.drug.drugindication:"MYELOFIBROSIS"'),
    ("Primary myelofibrosis",    'patient.drug.drugindication:"PRIMARY MYELOFIBROSIS"'),
    ("Myeloproliferative neoplasm", 'patient.drug.drugindication:"MYELOPROLIFERATIVE NEOPLASM"'),
    ("Polycythaemia vera (英式)", 'patient.drug.drugindication:"POLYCYTHAEMIA VERA"'),
    ("Polycythemia vera (美式)",  'patient.drug.drugindication:"POLYCYTHEMIA VERA"'),
    ("Essential thrombocythaemia (英式)", 'patient.drug.drugindication:"ESSENTIAL THROMBOCYTHAEMIA"'),
    ("Essential thrombocythemia (美式)",  'patient.drug.drugindication:"ESSENTIAL THROMBOCYTHEMIA"'),
])

# ---------- 2. 干扰素类药名 ----------
probe_list("2. 干扰素类（逐个试）", [
    ("INTERFERON ALFA-2A",        'patient.drug.openfda.generic_name:"INTERFERON ALFA-2A"'),
    ("INTERFERON ALFA-2B",        'patient.drug.openfda.generic_name:"INTERFERON ALFA-2B"'),
    ("INTERFERON ALFA",           'patient.drug.openfda.generic_name:"INTERFERON ALFA"'),
    ("PEGINTERFERON ALFA-2A",     'patient.drug.openfda.generic_name:"PEGINTERFERON ALFA-2A"'),
    ("PEGINTERFERON ALFA-2B",     'patient.drug.openfda.generic_name:"PEGINTERFERON ALFA-2B"'),
    ("INTERFERON ALFA-2B, RECOMBINANT",
     'patient.drug.openfda.generic_name:"INTERFERON ALFA-2B, RECOMBINANT"'),
    ("PEGINTERFERON ALFA-2B, RECOMBINANT",
     'patient.drug.openfda.generic_name:"PEGINTERFERON ALFA-2B, RECOMBINANT"'),
    ("substance: INTERFERON ALFA-2B", 'patient.drug.openfda.substance_name:"INTERFERON ALFA-2B"'),
    ("substance: INTERFERON ALFA-2A", 'patient.drug.openfda.substance_name:"INTERFERON ALFA-2A"'),
])

# ---------- 3. 血栓 PT 拼写 ----------
probe_list("3. 血栓栓塞 PT 逐条验证", [
    ("Pulmonary embolism",        'patient.reaction.reactionmeddrapt:"Pulmonary embolism"'),
    ("Deep vein thrombosis",      'patient.reaction.reactionmeddrapt:"Deep vein thrombosis"'),
    ("Thrombosis",                'patient.reaction.reactionmeddrapt:"Thrombosis"'),
    ("Portal vein thrombosis",    'patient.reaction.reactionmeddrapt:"Portal vein thrombosis"'),
    ("Splenic infarction",        'patient.reaction.reactionmeddrapt:"Splenic infarction"'),
    ("Myocardial infarction",     'patient.reaction.reactionmeddrapt:"Myocardial infarction"'),
    ("Cerebrovascular accident",  'patient.reaction.reactionmeddrapt:"Cerebrovascular accident"'),
    ("Transient ischaemic attack (英)", 'patient.reaction.reactionmeddrapt:"Transient ischaemic attack"'),
    ("Transient ischemic attack (美)",  'patient.reaction.reactionmeddrapt:"Transient ischemic attack"'),
    ("Arterial thrombosis",       'patient.reaction.reactionmeddrapt:"Arterial thrombosis"'),
    ("Retinal vein occlusion",    'patient.reaction.reactionmeddrapt:"Retinal vein occlusion"'),
    ("Venous thrombosis",         'patient.reaction.reactionmeddrapt:"Venous thrombosis"'),
    ("Embolism",                  'patient.reaction.reactionmeddrapt:"Embolism"'),
    ("Thrombophlebitis",          'patient.reaction.reactionmeddrapt:"Thrombophlebitis"'),
    ("Splenic vein thrombosis",   'patient.reaction.reactionmeddrapt:"Splenic vein thrombosis"'),
    ("Budd-Chiari syndrome",      'patient.reaction.reactionmeddrapt:"Budd-Chiari syndrome"'),
])

# ---------- 4. 六个暴露药最终确认 ----------
probe_list("4. 暴露药物最终计数", [
    ("Ruxolitinib",   'patient.drug.openfda.generic_name:"RUXOLITINIB"'),
    ("Hydroxyurea",   'patient.drug.openfda.generic_name:"HYDROXYUREA"'),
    ("Anagrelide",    'patient.drug.openfda.generic_name:"ANAGRELIDE"'),
    ("Busulfan",      'patient.drug.openfda.generic_name:"BUSULFAN"'),
    ("Luspatercept",  'patient.drug.openfda.generic_name:"LUSPATERCEPT"'),
    ("Ropeginterferon alfa-2b", 'patient.drug.openfda.generic_name:"ROPEGINTERFERON ALFA-2B"'),
])

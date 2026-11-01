# -*- coding: utf-8 -*-
"""
faers_main.py — FAERS 药物警戒主分析
=====================================
设计：
  暴露  6 种 MPN 治疗药物（openfda.generic_name 标准化名）
  结局  16 个血栓栓塞相关 MedDRA PT
  指标  ROR(+95%CI) / PRR(+χ²) / IC(BCPNN, 近似)
  判定  Evans 标准：a≥3 且 ROR025>1 且 PRR≥2 且 χ²≥4

2x2 表（以报告为单位）：
             目标PT   其他PT
  目标药       a        b
  其他药       c        d

  a = 药 ∧ PT
  b = N_drug - a
  c = N_pt   - a
  d = N_total - a - b - c

已确认的坑（probe 系列实测）：
  - 必须用 openfda.generic_name，不能用 medicinalproduct（差 6.7 倍）
  - 适应证/PT 多为英式拼写（POLYCYTHAEMIA、THROMBOCYTHAEMIA、ischaemic）
  - 干扰素 alfa-2a/2b 在 generic_name 中不存在，只有 ROPEGINTERFERON ALFA-2B
  - openfda.generic_name 覆盖率仅 84.1%，另 15.9% 落入"非暴露组"，会稀释效应
"""
import requests, json, time, math, os, csv
from math import log, exp, sqrt

BASE = "https://api.fda.gov/drug/event.json"
OUT = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒\00_data"
CACHE = os.path.join(OUT, "counts_cache.json")
os.makedirs(OUT, exist_ok=True)

S = requests.Session()
S.headers.update({"User-Agent": "FAERS-pharmacovigilance-research/1.0"})

# ---------------- 定义 ----------------
DRUGS = {
    "Ruxolitinib":            'patient.drug.openfda.generic_name:"RUXOLITINIB"',
    "Hydroxyurea":            'patient.drug.openfda.generic_name:"HYDROXYUREA"',
    "Anagrelide":             'patient.drug.openfda.generic_name:"ANAGRELIDE"',
    "Busulfan":               'patient.drug.openfda.generic_name:"BUSULFAN"',
    "Luspatercept":           'patient.drug.openfda.generic_name:"LUSPATERCEPT"',
    "Ropeginterferon alfa-2b":'patient.drug.openfda.generic_name:"ROPEGINTERFERON ALFA-2B"',
}

# PT 名称已逐条实测，确认计数 > 0
PTS = {
    "Pulmonary embolism":         'Pulmonary embolism',
    "Deep vein thrombosis":       'Deep vein thrombosis',
    "Thrombosis":                 'Thrombosis',
    "Venous thrombosis":          'Venous thrombosis',
    "Portal vein thrombosis":     'Portal vein thrombosis',
    "Splenic vein thrombosis":    'Splenic vein thrombosis',
    "Splenic infarction":         'Splenic infarction',
    "Arterial thrombosis":        'Arterial thrombosis',
    "Myocardial infarction":      'Myocardial infarction',
    "Cerebrovascular accident":   'Cerebrovascular accident',
    "Transient ischaemic attack": 'Transient ischaemic attack',
    "Retinal vein occlusion":     'Retinal vein occlusion',
    "Embolism":                   'Embolism',
    "Thrombophlebitis":           'Thrombophlebitis',
    "Budd-Chiari syndrome":       'Budd-Chiari syndrome',
    "Haemorrhage":                'Haemorrhage',   # 阴性对照（应无强信号）
}


def load_cache():
    if os.path.exists(CACHE):
        return json.load(open(CACHE, encoding="utf-8"))
    return {}


CACHE_D = load_cache()
CALLS = [0]


def total(search, tag=""):
    """带缓存的 total 查询"""
    if search in CACHE_D:
        return CACHE_D[search]
    for attempt in range(4):
        try:
            r = S.get(BASE, params={"search": search, "limit": 1}, timeout=60)
            if r.status_code == 200:
                n = r.json()["meta"]["results"]["total"]
                CACHE_D[search] = n
                CALLS[0] += 1
                if CALLS[0] % 20 == 0:
                    json.dump(CACHE_D, open(CACHE, "w", encoding="utf-8"))
                    print(f"    ...已缓存 {len(CACHE_D)} 条查询")
                time.sleep(0.32)
                return n
            elif r.status_code == 404:
                CACHE_D[search] = 0
                time.sleep(0.32)
                return 0
            else:
                time.sleep(3)
        except Exception:
            time.sleep(3)
    raise RuntimeError(f"查询失败: {search}")


# ---------------- 采集 ----------------
print("=" * 78)
print("STEP 1  基础计数")
print("=" * 78)
# 全库总数：不带 search 参数
r0 = S.get(BASE, params={"limit": 1}, timeout=60)
N_TOTAL = r0.json()["meta"]["results"]["total"]
print(f"  全库报告数 N = {N_TOTAL:,}")

# 分母敏感性：限定有标准化药名的报告
N_STD = total('_exists_:patient.drug.openfda.generic_name')
print(f"  有 generic_name 的报告 = {N_STD:,}  ({N_STD/N_TOTAL*100:.1f}%)")

print()
print("  药物计数：")
N_DRUG = {}
for d, q in DRUGS.items():
    N_DRUG[d] = total(q)
    print(f"    {d:26s} {N_DRUG[d]:>9,}")

print()
print("  PT 计数：")
N_PT = {}
for p, pt in PTS.items():
    N_PT[p] = total(f'patient.reaction.reactionmeddrapt:"{pt}"')
    print(f"    {p:28s} {N_PT[p]:>9,}")

print()
print("=" * 78)
print(f"STEP 2  交集查询（{len(DRUGS)}×{len(PTS)} = {len(DRUGS)*len(PTS)} 次）")
print("=" * 78)
A = {}
for i, (d, dq) in enumerate(DRUGS.items(), 1):
    for p, pt in PTS.items():
        q = f'{dq} AND patient.reaction.reactionmeddrapt:"{pt}"'
        A[(d, p)] = total(q)
    print(f"  [{i}/{len(DRUGS)}] {d} 完成")

json.dump(CACHE_D, open(CACHE, "w", encoding="utf-8"))
print(f"  缓存已保存，共 {len(CACHE_D)} 条查询")

# ---------------- 计算 ----------------
def analyse(a, b, c, d):
    """返回各指标字典"""
    res = {"a": a, "b": b, "c": c, "d": d}
    if min(a, b, c, d) <= 0:
        res.update(ROR=None, ROR025=None, ROR975=None, PRR=None, chi2=None, IC=None, IC025=None)
        return res
    ror = (a / b) / (c / d)
    se = sqrt(1/a + 1/b + 1/c + 1/d)
    res["ROR"] = ror
    res["ROR025"] = exp(log(ror) - 1.96 * se)
    res["ROR975"] = exp(log(ror) + 1.96 * se)
    prr = (a / (a + b)) / (c / (c + d))
    res["PRR"] = prr
    n = a + b + c + d
    denom = (a + b) * (c + d) * (a + c) * (b + d)
    res["chi2"] = n * (a*d - b*c)**2 / denom if denom else None
    # BCPNN 信息成分（近似）
    ic = math.log2(a * n / ((a + b) * (a + c)))
    res["IC"] = ic
    res["IC025"] = ic - 2 * sqrt(1/a + 1/b + 1/c + 1/d) / log(2)
    return res


rows = []
for d in DRUGS:
    for p in PTS:
        a = A[(d, p)]
        b = N_DRUG[d] - a
        c = N_PT[p] - a
        d4 = N_TOTAL - a - b - c
        r = analyse(a, b, c, d4)
        r["drug"] = d
        r["pt"] = p
        rows.append(r)

# ---------------- FDR 校正 ----------------
ps = []
for r in rows:
    if r["chi2"] is None:
        ps.append(1.0)
    else:
        # χ²(1) 的 p 值
        x = r["chi2"]
        p = math.erfc(sqrt(x / 2))
        ps.append(p)
m = len(ps)
order = sorted(range(m), key=lambda i: ps[i])
qvals = [0.0] * m
prev = 1.0
for rank in range(m - 1, -1, -1):
    i = order[rank]
    val = min(prev, ps[i] * m / (rank + 1))
    qvals[i] = val
    prev = val
for r, q in zip(rows, qvals):
    r["p"] = None
    r["q"] = q

for r in rows:
    if r["chi2"] is not None:
        r["p"] = math.erfc(sqrt(r["chi2"] / 2))

# ---------------- 判定 ----------------
for r in rows:
    sig = (
        r["a"] >= 3
        and r["ROR025"] is not None and r["ROR025"] > 1
        and r["PRR"] is not None and r["PRR"] >= 2
        and r["chi2"] is not None and r["chi2"] >= 4
        and r["IC025"] is not None and r["IC025"] > 0
    )
    r["signal"] = "YES" if sig else ""

# ---------------- 输出 ----------------
csv_path = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒\02_tables\faers_ror_all.csv"
cols = ["drug", "pt", "a", "b", "c", "d", "ROR", "ROR025", "ROR975",
        "PRR", "chi2", "p", "q", "IC", "IC025", "signal"]
with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
    w = csv.DictWriter(f, fieldnames=cols)
    w.writeheader()
    for r in rows:
        w.writerow({k: (f"{r[k]:.6g}" if isinstance(r[k], float) else r[k]) for k in cols})
print()
print(f"[OK] {csv_path}  共 {len(rows)} 行")

# ---------------- 摘要 ----------------
print()
print("=" * 78)
print("STEP 3  结果摘要")
print("=" * 78)
print(f"  全库 N = {N_TOTAL:,}")
print()
print(f"{'药物':<26}{'PT':<30}{'a':>7}{'ROR':>8}{'ROR025':>9}{'PRR':>7}{'q':>9}  信号")
print("-" * 100)
for r in sorted(rows, key=lambda x: -(x["ROR025"] or 0)):
    if r["a"] < 3:
        continue
    print(f"{r['drug']:<26}{r['pt']:<30}{r['a']:>7,}"
          f"{(r['ROR'] or 0):>8.2f}{(r['ROR025'] or 0):>9.2f}"
          f"{(r['PRR'] or 0):>7.2f}{(r['q'] or 1):>9.2g}  {r['signal']}")

n_sig = sum(1 for r in rows if r["signal"] == "YES")
print()
print(f"  达到三法一致判定的组合：{n_sig} / {len(rows)}")
print(f"  其中 q<0.05 的：{sum(1 for r in rows if r['q'] < 0.05)}")

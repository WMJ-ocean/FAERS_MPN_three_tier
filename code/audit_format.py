# -*- coding: utf-8 -*-
"""
audit_format.py — 按 Drug Safety（Adis/Springer）投稿要求逐条核查投稿包
=====================================================================
只读检查，不改任何文件。输出一张通过/不通过的核对表。
"""
import os
import re
import sys

from docx import Document
from PIL import Image

BASE = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒"
SUB = os.path.join(BASE, "05_submission")
FIG = os.path.join(SUB, "figures")

rows = []


def add(item, ok, detail):
    rows.append((item, "PASS" if ok else "CHECK", detail))


def cm(v):
    return v / 360000.0


def paras(path):
    return [p.text.strip() for p in Document(path).paragraphs if p.text.strip()]


def main():
    ms = paras(os.path.join(SUB, "02_Manuscript.docx"))
    full = "\n".join(ms)
    tp = paras(os.path.join(SUB, "01_Title_page.docx"))
    tfull = "\n".join(tp)

    md = open(os.path.join(SUB, "manuscript.md"), encoding="utf-8").read()
    sec = [m for m in re.findall(r"^## (.+)$", md, flags=re.M)]

    # 1 文章类型与字数 ---------------------------------------------------
    body = md.split("## 1 Introduction", 1)[1].split("## Figure legends", 1)[0]
    wc = lambda t: len(re.sub(r"^#+\s*", "", t, flags=re.M).replace("**", "").replace("*", "").replace("`", "").split())
    add("Original Research ≤ 6,000 words", wc(body) <= 6000, f"{wc(body):,} words")

    ab = md.split("## Abstract", 1)[1].split("## Key Points", 1)[0]
    add("Abstract 150–250 (≤450 for original research)", 250 <= wc(ab) <= 450, f"{wc(ab)} words")
    heads = [h for h in ("Background", "Methods", "Results", "Conclusions") if h in ab]
    add("Abstract structured, 4 headings", len(heads) == 4, ", ".join(heads))

    # 2 结构 -------------------------------------------------------------
    order_ok = sec.index("Abstract") < sec.index("Key Points") < sec.index("1 Introduction")
    add("Key Points after Abstract, before Introduction", order_ok,
        " → ".join(sec[:3]))
    need = ["1 Introduction", "2 Methods", "3 Results", "4 Discussion", "5 Conclusions",
            "Figure legends", "Declarations", "References"]
    add("Decimal numbered sections 1–5", all(s in sec for s in need[:5]),
        " / ".join(s for s in sec if re.match(r"^\d ", s)))
    add("Declarations precede References", sec.index("Declarations") < sec.index("References"), "yes")
    deep = re.findall(r"^#{4,} ", md, flags=re.M)
    add("Headings ≤ 3 levels", not deep, f"{len(deep)} deeper headings")

    # 3 声明 -------------------------------------------------------------
    decl = md.split("## Declarations", 1)[1].split("## References", 1)[0]
    items = ["Funding", "Conflicts of interest", "Ethics approval", "Consent to participate",
             "Consent to publish", "Data availability", "Code availability", "Author contributions"]
    missing = [i for i in items if f"**{i}**" not in decl]
    add("Required declarations present", not missing, "missing: " + ", ".join(missing) if missing else "all 8")

    # 4 题名页 -----------------------------------------------------------
    add("Title page: title", ms[0].lower().startswith("background selection"), ms[0][:60] + "…")
    add("Title page: corresponding author e-mail", "huxiaomei_2@163.com" in tfull, "huxiaomei_2@163.com")
    add("Title page: telephone", "+86 10 6283 5307" in tfull, "+86 10 6283 5307")
    add("Title page: affiliations + corresponding marked", "Corresponding author" in tfull, "2 affiliations")
    add("Title page: funding with grant number", "XYZX0405-28" in tfull, "XYZX0405-28")
    add("Title page: ORCID supplied", "ORCID" in tfull, "NOT SUPPLIED")

    # 5 参考文献 ---------------------------------------------------------
    refs = [l for l in md.split("## References", 1)[1].splitlines() if re.match(r"^\d+\.\s", l)]
    doied = [r for r in refs if "https://doi.org/" in r]
    add("References numbered, all with DOI", len(refs) == len(doied), f"{len(doied)}/{len(refs)} with DOI")
    over = [r[:40] for r in refs if len(re.findall(r"[A-Z][a-z]+ [A-Z]{1,3}", r.split(".")[0])) > 7]
    add("≤6 authors then et al.", not over, "ok" if not over else str(over))
    cited = set()
    for m in re.findall(r"\[([0-9,\s\u2013\-]+)\]", full):
        for part in m.replace("\u2013", "-").split(","):
            part = part.strip()
            if "-" in part:
                a, b = part.split("-")
                cited.update(range(int(a), int(b) + 1))
            elif part.isdigit():
                cited.add(int(part))
    add("Every reference cited in text", set(range(1, len(refs) + 1)) <= cited,
        f"cited {sorted(cited)}")

    # 6 图表 -------------------------------------------------------------
    add("5 main figures with legends", len(re.findall(r"^\*\*Fig\. \d\*\*", md, flags=re.M)) == 5, "Fig. 1–5")
    add("4 main tables, all cited", all(f"Table {i}" in full for i in range(1, 5)), "Table 1–4")
    add("Supplementary cited as ESM", "ESM Table S" in full and "ESM Fig. S1" in full,
        f"{len(re.findall('ESM Table S', full))} mentions")
    no_bar = "electronic supplementary" not in full
    add("No mixed supplementary wording", no_bar, "uniform ESM")

    sup = paras(os.path.join(SUB, "04_Supplementary.docx"))[:4]
    sup_head = " ".join(sup)
    have = [k for k in ("Drug Safety", "Xiaomei Hu", "huxiaomei_2@163.com",
                        "Department of Hematology") if k in sup_head]
    add("ESM first page: title+journal+authors+affiliation+e-mail",
        len(have) == 4, f"{len(have)}/4 elements")

    # 7 图件 -------------------------------------------------------------
    for f in ["Fig1.png", "Fig2.png", "Fig3.png", "Fig4.png", "Fig5.png", "FigS1.png"]:
        p = os.path.join(FIG, f)
        im = Image.open(p)
        dpi = im.info.get("dpi", (0, 0))[0]
        width_mm = im.size[0] / 600 * 25.4
        ok = dpi >= 595 and width_mm <= 174.5 and im.mode == "RGB"
        add(f"{f}: 600 dpi, RGB, ≤174 mm", ok,
            f"{im.size[0]}×{im.size[1]}, {dpi:.0f} dpi, {width_mm:.0f} mm, {im.mode}")

    # 8 排版 -------------------------------------------------------------
    d = Document(os.path.join(SUB, "02_Manuscript.docx"))
    s = d.sections[0]
    a4 = abs(cm(s.page_width) - 21.0) < 0.1 and abs(cm(s.page_height) - 29.7) < 0.1
    add("Page size A4", a4, f"{cm(s.page_width):.1f}×{cm(s.page_height):.1f} cm")
    add("Continuous line numbers", "lnNumType" in d.element.xml, "w:lnNumType")
    add("Page numbers in footer",
        "PAGE" in d.sections[0].footer.paragraphs[0]._p.xml, "PAGE field")
    fonts = {r.font.name for p in d.paragraphs for r in p.runs if r.font.name}
    add("Single font family", fonts == {"Times New Roman"}, ", ".join(sorted(fonts)))
    add("No markdown residue in docx", not any(("*" in t or "`" in t) for t in ms), "clean")
    add("Marks up italics as real formatting",
        any(r.italic for p in d.paragraphs for r in p.runs),
        f"{sum(1 for p in d.paragraphs for r in p.runs if r.italic)} italic runs")

    # 9 交付物 -----------------------------------------------------------
    files = ["01_Title_page.docx", "02_Manuscript.docx", "03_Tables.docx",
             "04_Supplementary.docx", "05_Cover_letter.docx", "06_READUS-PV_checklist.docx"]
    miss = [f for f in files if not os.path.exists(os.path.join(SUB, f))]
    add("Six submission documents present", not miss, "missing: " + ", ".join(miss) if miss else "6/6")

    # 输出 ---------------------------------------------------------------
    w = max(len(r[0]) for r in rows)
    for item, status, detail in rows:
        print(f"[{status:5}] {item:<{w}}  {detail}")
    bad = sum(1 for r in rows if r[1] != "PASS")
    print(f"\n{len(rows) - bad}/{len(rows)} pass, {bad} to check")


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""verify_docx.py — 投稿包结构化校验"""
import os, re, zipfile
from docx import Document
from docx.shared import Cm, Emu
from docx.oxml.ns import qn

SUB = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒\05_submission"


def check(path):
    d = Document(path)
    name = os.path.basename(path)
    cp = d.core_properties
    xml = zipfile.ZipFile(path).read("word/document.xml").decode("utf-8", "ignore")
    has_ln = "lnNumType" in xml
    footer_parts = [n for n in zipfile.ZipFile(path).namelist()
                    if n.startswith("word/footer")]
    has_page = False
    for fp in footer_parts:
        t = zipfile.ZipFile(path).read(fp).decode("utf-8", "ignore")
        if "PAGE" in t:
            has_page = True
    print("=" * 78)
    print(f"{name}")
    print(f"  author        : {cp.author!r}")
    print(f"  title         : {(cp.title or '')[:70]!r}")
    print(f"  paragraphs    : {len(d.paragraphs)}")
    print(f"  tables        : {len(d.tables)}")
    print(f"  line numbers  : {has_ln}")
    print(f"  page numbers  : {has_page}")
    for i, s in enumerate(d.sections):
        usable = Emu(s.page_width - s.left_margin - s.right_margin)
        print(f"  section {i}      : {s.page_width.cm:.1f} x {s.page_height.cm:.1f} cm, "
              f"usable width {usable.cm:.1f} cm, orient={s.orientation}")
    for i, t in enumerate(d.tables):
        ncol = len(t.columns)
        # 估算设定宽度
        w = 0
        try:
            for c in t.rows[0].cells:
                if c.width:
                    w += c.width.cm
        except Exception:
            pass
        print(f"  table {i}        : {len(t.rows)} rows x {ncol} cols, "
              f"first-row total width {w:.1f} cm")


for f in sorted(os.listdir(SUB)):
    if f.endswith(".docx"):
        check(os.path.join(SUB, f))

# 稿件章节完整性
print("\n" + "=" * 78)
d = Document(os.path.join(SUB, "02_Manuscript.docx"))
heads = [p.text.strip() for p in d.paragraphs
         if p.text.strip() and p.runs and p.runs[0].bold and len(p.text) < 90]
print("稿件结构：")
for x in heads:
    print("   ", x)
txt = "\n".join(p.text for p in d.paragraphs)
print(f"\n全文词数（含表注外的所有段落）: "
      f"{len(re.findall(r'[A-Za-z0-9][A-Za-z0-9’' + chr(39) + r'hyphen-]*'.replace('hyphen-',''), txt))}")
for key in ["Key Points", "Abstract", "1 Introduction", "2 Methods", "3 Results",
            "4 Discussion", "5 Conclusions", "Figure legends", "Declarations",
            "References"]:
    print(f"   {'OK ' if key in txt else 'MISSING'} {key}")

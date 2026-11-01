# -*- coding: utf-8 -*-
"""
build_submission.py — 生成正式投稿包
====================================
产出：
  01_Title_page.docx
  02_Manuscript.docx
  03_Tables.docx
  04_Supplementary.docx
  05_Cover_letter.docx
  06_READUS-PV_checklist.docx
  07_回复审稿人用_数字核对表.xlsx   （不出，改为 md）
"""
import csv, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from docx.shared import Pt, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING

import docx_kit as K

BASE = r"C:\Users\Hero\WorkBuddy\文章库\11_FAERS_药物警戒"
SUB = os.path.join(BASE, "05_submission")
TAB = os.path.join(BASE, "02_tables")
AUTHOR = "Mingjing Wang"
TITLE = ("Background selection determines the conclusion: a three-tier disproportionality "
         "analysis of thrombotic signals for myeloproliferative neoplasm therapies in FAERS")


def rd(name):
    with open(os.path.join(TAB, name), encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def f2(x, nd=2):
    try:
        return f"{float(x):.{nd}f}"
    except (TypeError, ValueError):
        return "—"


def ci(r, key="ROR"):
    lo, hi = r.get(key + "025"), r.get(key + "975")
    if r.get(key) in (None, "", "None") or lo in (None, "", "None"):
        return "not estimable"
    return f"{float(r[key]):.2f} ({float(lo):.2f}\u2013{float(hi):.2f})"


# =====================================================================
# Markdown → docx
# =====================================================================
INLINE = re.compile(r"(\*\*.+?\*\*|\*[^*]+?\*|`[^`]+?`)")


def add_inline(para, text, size=12, bold_all=False):
    """把 **粗体** / *斜体* / `代码` 三种行内标记落成真正的 run 格式。"""
    for seg in INLINE.split(text):
        if not seg:
            continue
        if seg.startswith("**") and seg.endswith("**") and len(seg) > 4:
            run = para.add_run(seg[2:-2])
            K._set_run_font(run, size=size, bold=True)
        elif seg.startswith("`") and seg.endswith("`") and len(seg) > 2:
            run = para.add_run(seg[1:-1])
            K._set_run_font(run, size=size, bold=bold_all)
        elif seg.startswith("*") and seg.endswith("*") and len(seg) > 2:
            run = para.add_run(seg[1:-1])
            K._set_run_font(run, size=size, bold=bold_all, italic=True)
        else:
            run = para.add_run(seg)
            K._set_run_font(run, size=size, bold=bold_all)


def md_to_doc(md_path, out_path, include_title=True):
    text = open(md_path, encoding="utf-8").read()
    lines = text.split("\n")
    doc = K.new_doc(double=True, line_numbers=True, page_numbers=True)
    K.meta(doc, AUTHOR, TITLE, subject="Pharmacovigilance / disproportionality analysis",
           keywords="FAERS; disproportionality analysis; confounding by indication; "
                    "myeloproliferative neoplasms; pharmacovigilance")

    in_refs = False
    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            continue
        if line.startswith("# "):
            K.h(doc, line[2:].strip(), level=1, size=14, space_before=0, space_after=12)
            continue
        if line.startswith("## "):
            title = line[3:].strip()
            in_refs = title.lower() == "references"
            K.h(doc, title, level=2, size=12, space_before=14, space_after=6)
            continue
        if line.startswith("### "):
            K.h(doc, line[4:].strip(), level=3, size=12, space_before=10, space_after=4)
            continue
        if line.startswith("- "):
            para = doc.add_paragraph(style="List Bullet")
            para.paragraph_format.space_after = Pt(4)
            add_inline(para, line[2:].strip(), size=12)
            continue
        if in_refs and re.match(r"^\d+\.\s", line):
            para = doc.add_paragraph()
            para.paragraph_format.left_indent = Cm(0.75)
            para.paragraph_format.first_line_indent = Cm(-0.75)
            para.paragraph_format.space_after = Pt(4)
            add_inline(para, line, size=11)
            continue
        # 普通段落
        para = doc.add_paragraph()
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        para.paragraph_format.space_after = Pt(0)
        add_inline(para, line, size=12)

    doc.save(out_path)
    print("[OK]", os.path.basename(out_path))
    return out_path


def manuscript_metrics(path=None):
    """从 manuscript.md 实时计算字数，避免题名页出现手写的旧数字。"""
    path = path or os.path.join(SUB, "manuscript.md")
    text = open(path, encoding="utf-8").read()

    sections = {}
    for chunk in re.split(r"^## ", text, flags=re.M)[1:]:
        name, _, body = chunk.partition("\n")
        sections[name.strip()] = body

    def wc(t):
        t = re.sub(r"^#+\s*", "", t, flags=re.M)
        t = t.replace("**", "").replace("*", "").replace("`", "")
        return len(t.split())

    body_text = text.split("## 1 Introduction", 1)[1].split("## Figure legends", 1)[0]

    return {
        "body": wc(body_text),
        "abstract": wc(sections["Abstract"]),
        "keypoints": wc(sections["Key Points"]),
        "refs": len(re.findall(r"^\d+\.\s", text.split("## References", 1)[1], flags=re.M)),
    }


# =====================================================================
# 1. 标题页
# =====================================================================
def build_title_page():
    doc = K.new_doc(double=True, line_numbers=False, page_numbers=True)
    K.meta(doc, AUTHOR, TITLE, subject="Pharmacovigilance / disproportionality analysis")

    K.p(doc, "Drug Safety \u2014 Original Research", size=11, italic=True, align="center",
        space_after=24)

    K.p(doc, TITLE, size=14, bold=True, align="center", space_after=24)

    K.p(doc, "Mingjing Wang\u00b9, Yi Chen\u00b9\u00b2, Yan Lv\u00b9, Richeng Quan\u00b9, "
             "Xiaomei Hu\u00b9\u207a", size=12, align="center", space_after=16)

    K.p(doc, "\u00b9 Department of Hematology, Xiyuan Hospital, China Academy of Chinese "
             "Medical Sciences, Beijing, China", size=10.5, align="center", space_after=4)
    K.p(doc, "\u00b2 Graduate School, Beijing University of Chinese Medicine, Beijing, China",
        size=10.5, align="center", space_after=4)
    K.p(doc, "\u207a Corresponding author", size=10.5, align="center", space_after=24)

    K.h(doc, "Corresponding author", level=2, size=12, space_before=4)
    K.p(doc, "Xiaomei Hu, MD", size=12)
    K.p(doc, "Department of Hematology, Xiyuan Hospital, China Academy of Chinese Medical "
             "Sciences, 1 Xiyuan Playground, Haidian District, Beijing 100091, China",
        size=12)
    K.p(doc, "Email: huxiaomei_2@163.com", size=12)
    K.p(doc, "Telephone: +86 10 6283 5307", size=12,
        space_after=18)

    K.h(doc, "Running title", level=2, size=12, space_before=4)
    K.p(doc, "How much of a thrombotic signal is the disease?", size=12, space_after=18)

    K.h(doc, "Manuscript metrics", level=2, size=12, space_before=4)
    m = manuscript_metrics()
    rows = [
        ["Main text (Introduction to Conclusions)", f"{m['body']:,} words"],
        ["Abstract", f"{m['abstract']} words, structured"],
        ["Key Points", f"4 points, {m['keypoints']} words"],
        ["Tables", "4 (main text) + 7 (electronic supplementary)"],
        ["Figures", "5 (main text) + 1 (electronic supplementary)"],
        ["References", str(m["refs"])],
        ["Reporting guideline", "READUS-PV, checklist supplied"],
    ]
    K.table(doc, ["Item", "Count"], rows, font_size=10, col_widths=[9.5, 6.0],
            align_right_from=1)

    K.h(doc, "Funding", level=2, size=12, space_before=14)
    K.p(doc, "Xiyuan Hospital, China Academy of Chinese Medical Sciences Enhancement Fund, "
             "grant number XYZX0405-28.", size=11)

    doc.save(os.path.join(SUB, "01_Title_page.docx"))
    print("[OK] 01_Title_page.docx")


# =====================================================================
# 2. 表 1–4
# =====================================================================
def build_tables():
    doc = K.new_doc(double=False, line_numbers=False, page_numbers=True)
    K.meta(doc, AUTHOR, TITLE + " - tables", subject="Tables")

    # ---------------- Table 1 ----------------
    t1 = rd("table1_characteristics.csv")
    name_map = {"Ropeginterferon": "Ropeginterferon alfa-2b"}
    rows = []
    for r in t1:
        nm = name_map.get(r["Drug"], r["Drug"])
        rows.append([nm, f"{int(r['Reports_n']):,}", f"{r['Sex_recorded_pct']}%",
                     f"{r['Male_pct']}%", f"{r['Age_recorded_pct']}%",
                     f"{r['Age_65plus_pct']}%", f"{r['Healthcare_pct']}%",
                     f"{r['Consumer_pct']}%",
                     f"{r['Top_country']} ({r['Top_country_pct']}%)",
                     f"{r['Serious_pct']}%"])
    rows.append(["**MPN pool**", "58,602", "38.8%", "49.5%", "—", "—", "43.6%", "56.3%",
                 "—", "—"])

    K.p(doc, "**Table 1** Characteristics of reports for the six study drugs and for the "
             "myeloproliferative neoplasm pool", size=10, space_after=6)
    K.table(doc,
            ["Drug", "Reports", "Sex recorded", "Male", "Age recorded", "\u226565 years",
             "Healthcare reporter", "Consumer reporter", "Top country", "Serious"],
            rows, font_size=7.8)
    K.p(doc, "Percentages for sex, age and reporter type are calculated among reports in "
             "which that field was recorded, not among all reports. Seriousness is the "
             "reporter's own flag. Country is the country of occurrence. The MPN pool is "
             "defined by a recorded myeloproliferative indication in any drug field and "
             "does not require a standardised drug name, so it is not a subset of the drug "
             "column totals. Ruxolitinib shows a marked structural deficit of patient-level "
             "fields (sex recorded in 29.8% of reports against 87.9% database-wide); these "
             "reports are concentrated from 2017 onward, are predominantly submitted by "
             "consumers, and their leading reported term is off-label use rather than an "
             "adverse reaction. MPN myeloproliferative neoplasm.",
        font_size=7.4)

    # ---------------- Table 2 ----------------
    L1 = {(r["drug"], r["pt"]): r for r in rd("faers_ror_all.csv")}
    L2 = {(r["drug"], r["pt"]): r for r in rd("faers_ror_mpn_stratified.csv")}
    sig = [r for r in L1.values() if r["signal"].strip() == "YES"]
    sig.sort(key=lambda r: -float(r["ROR"]))

    rows = []
    for r in sig:
        r2 = L2[(r["drug"], r["pt"])]
        a2 = int(float(r2["a"]))
        if r2["ROR"] in ("", None) or a2 == 0:
            fall = "not estimable"
        else:
            fall = f"{(1 - float(r2['ROR'])/float(r['ROR']))*100:.0f}%"
        rows.append([r["drug"], r["pt"], r["a"], ci(r),
                     a2 if a2 else "0", ci(r2), fall])

    K.p(doc, "**Table 2** Drug\u2013event pairs meeting all four signal criteria against the "
             "unselected reference (tier 1), and their behaviour against the "
             "disease-matched reference (tier 2)", size=10, space_after=6)
    K.table(doc,
            ["Drug", "MedDRA preferred term", "a (tier 1)", "ROR tier 1 (95% CI)",
             "a (tier 2)", "ROR tier 2 (95% CI)", "Fall"],
            rows, font_size=7.6, col_widths=[3.0, 4.4, 1.5, 3.4, 1.5, 3.4, 2.0])
    K.p(doc, "ROR reporting odds ratio, CI confidence interval, a reports naming both the "
             "drug and the event. Pairs are ordered by tier-1 ROR. Fall is the percentage "
             "reduction in the point estimate from tier 1 to tier 2. The median fall across "
             "the ten splanchnic pairs with estimable values in both tiers was 90% "
             "(range 77\u201396%). \u201cNot estimable\u201d indicates that no report in the "
             "disease-matched pool named the drug\u2013event combination. Complete counts, "
             "including b, c and d, are given in Tables S1 and S2.",
        font_size=7.4)

    K.page_break(doc)

    # ---------------- Table 3 ----------------
    h2h = rd("faers_head_to_head.csv")
    H = {(r["disease"], r["pt"]): r for r in h2h if r["ROR"] not in ("", None)}
    EVENTS = ["Myocardial infarction", "Transient ischaemic attack",
              "Cerebrovascular accident", "Haemorrhage", "Arterial thrombosis", "Thrombosis",
              "Splenic infarction", "Portal vein thrombosis", "Pulmonary embolism",
              "Deep vein thrombosis"]

    K.p(doc, "**Table 3** Head-to-head comparisons within a single disease, and sensitivity "
             "analyses for the essential thrombocythaemia arterial signal", size=10,
        space_after=6)
    K.p(doc, "**(a) Index drug versus hydroxyurea, by disease**", size=9.5, space_after=4)
    rows = []
    for ev in EVENTS:
        row = [ev]
        for dis in ["ET", "PV", "MF"]:
            r = H.get((dis, ev))
            row.append(ci(r) if r else "not estimable")
        rows.append(row)
    K.table(doc, ["MedDRA preferred term",
                  "ET: anagrelide vs hydroxyurea",
                  "PV: ropeginterferon vs hydroxyurea",
                  "MF: ruxolitinib vs hydroxyurea"],
            rows, font_size=7.8, col_widths=[4.6, 4.0, 4.4, 4.2])
    K.p(doc, "Values are reporting odds ratios with 95% confidence intervals; a value above "
             "1 means more reporting on the index drug. Complete results for all 16 events "
             "are given in Table S3. ET essential thrombocythaemia, PV polycythaemia vera, "
             "MF myelofibrosis.", font_size=7.4)

    K.p(doc, "**(b) Anagrelide versus hydroxyurea in essential thrombocythaemia under each "
             "analysis**", size=9.5, space_after=4)
    sens = rd("faers_sensitivity.csv")
    l2s = rd("faers_l2_sensitivity.csv")
    S1 = {(r["pt"]): r for r in sens if r["scenario"] == "S1_excl_combo"}
    S2 = {(r["pt"]): r for r in sens if r["scenario"] == "S2_serious_only"}
    S3 = {(r["pt"]): r for r in l2s
          if r["scenario"] == "S3_no_ruxolitinib" and r["drug"] == "Anagrelide"}
    S4 = {(r["pt"]): r for r in l2s
          if r["scenario"] == "S4_untreated_MPN" and r["drug"] == "Anagrelide"}
    ET_EV = ["Myocardial infarction", "Transient ischaemic attack",
             "Cerebrovascular accident", "Haemorrhage"]
    rows = []
    for lab, src in [("Main analysis", H_ET := {(r["pt"]): r for r in h2h
                                                if r["disease"] == "ET"
                                                and r["ROR"] not in ("", None)}),
                     ("S1 excluding combination users", S1),
                     ("S2 serious reports only", S2),
                     ("S3 pool without ruxolitinib", S3),
                     ("S4 unexposed MPN reference", S4)]:
        rows.append([lab] + [ci(src.get(ev)) if src.get(ev) else "not estimable"
                             for ev in ET_EV])
    K.table(doc, ["Analysis"] + ET_EV, rows, font_size=7.8,
            col_widths=[4.6, 4.0, 4.0, 4.0, 3.6])
    K.p(doc, "Values are reporting odds ratios with 95% confidence intervals for anagrelide "
             "versus the stated comparator. S1 removes the 221 reports naming both drugs. "
             "S2 restricts to reports flagged serious. S3 removes ruxolitinib-containing "
             "reports from the disease pool, which otherwise contributes 61.2% of it. S4 "
             "uses reports recording a myeloproliferative neoplasm but none of the six study "
             "drugs as the reference. MPN myeloproliferative neoplasm.",
        font_size=7.4)

    K.page_break(doc)

    # ---------------- Table 4 ----------------
    cs = rd("case_series_summary.csv")
    nm = {"HYDROXYUREA": "Hydroxyurea", "RUXOLITINIB": "Ruxolitinib",
          "ANAGRELIDE": "Anagrelide", "ROPEGINTERFERON ALFA-2B": "Ropeginterferon alfa-2b"}
    rows = []
    for r in cs:
        n = int(r["n"])
        rows.append([nm.get(r["drug"], r["drug"]), r["pt"], n, r["suspect"],
                     r["concomitant"], f"{int(r['mpn_recorded'])} ({int(r['mpn_recorded'])/n*100:.0f}%)",
                     f"{int(r['disease_consistent'])} ({int(r['disease_consistent'])/n*100:.0f}%)",
                     f"{int(r['multidrug'])} ({int(r['multidrug'])/n*100:.0f}%)"])
    K.p(doc, "**Table 4** Structured review of 169 individual case reports for five "
             "drug\u2013event pairs", size=10, space_after=6)
    K.table(doc, ["Drug", "Event", "Reports retrieved", "Index drug suspect",
                  "Index drug concomitant", "MPN indication recorded",
                  "Disease-consistent co-reports", "More than one drug"],
            rows, font_size=7.8, col_widths=[3.0, 4.0, 1.9, 2.0, 2.2, 2.2, 2.4, 2.0])
    K.p(doc, "All available reports for each pair were retrieved through the openFDA "
             "endpoint. Drug role is the reporter's own characterisation in the "
             "drugcharacterization field. Disease-consistent co-reports are co-reported "
             "splenomegaly, hepatomegaly, portal hypertension, varices, disease progression "
             "or off-label use, any of which makes the event explicable by the underlying "
             "condition. Percentages are of reports retrieved. The full extraction with "
             "report identifiers, dates, countries, ages and reaction lists is given in "
             "Table S7. MPN myeloproliferative neoplasm.", font_size=7.4)

    doc.save(os.path.join(SUB, "03_Tables.docx"))
    print("[OK] 03_Tables.docx")


# =====================================================================
# 3. 补充材料
# =====================================================================
def build_supplementary():
    doc = K.new_doc(double=False, line_numbers=False, page_numbers=True)
    K.meta(doc, AUTHOR, TITLE + " - electronic supplementary material",
           subject="Supplementary material")
    K.p(doc, "**Electronic supplementary material**", size=12, bold=True, space_after=10)
    K.p(doc, TITLE, size=10.5, italic=True, space_after=6)
    K.p(doc, "Drug Safety (Springer Nature). Mingjing Wang, Yi Chen, Yan Lv, Richeng Quan, "
             "Xiaomei Hu. Department of Hematology, Xiyuan Hospital, China Academy of Chinese "
             "Medical Sciences, Beijing, China. Corresponding author: Xiaomei Hu, "
             "huxiaomei_2@163.com.", size=9, space_after=14)
    K.p(doc, "Contents: Table S1 tier-1 results for all 96 pairs; Table S2 tier-2 results for "
             "all 96 pairs; Table S3 complete head-to-head results; Table S4 head-to-head "
             "sensitivity analyses; Table S5 background enrichment of the 16 events; "
             "Table S6 disease-pool sensitivity analyses; Table S7 complete case-series "
             "extraction; Fig. S1 heatmap of tier-1 results.", size=9.5, space_after=12)

    # S1 / S2
    for fname, label, ref in [("faers_ror_all.csv", "Table S1",
                               "unselected reference (tier 1)"),
                              ("faers_ror_mpn_stratified.csv", "Table S2",
                               "disease-matched reference (tier 2)")]:
        rows = rd(fname)
        rows.sort(key=lambda r: (r["drug"], -float(r["ROR"]) if r["ROR"] else 0))
        body = []
        for r in rows:
            body.append([r["drug"], r["pt"], r["a"], r["b"], r["c"], r["d"],
                         ci(r), f2(r["PRR"]), f2(r["chi2"], 1), f"{float(r['q']):.2g}"
                         if r["q"] else "—", "yes" if r["signal"].strip() else "no"])
        K.p(doc, f"**{label}** Complete results for all 96 drug\u2013event pairs against the "
                 f"{ref}", size=10, space_after=4)
        K.table(doc, ["Drug", "Preferred term", "a", "b", "c", "d", "ROR (95% CI)", "PRR",
                      "\u03c7\u00b2", "q", "Signal"],
                body, font_size=6.6)
        K.p(doc, "a reports with both drug and event; b reports with the drug but not the "
                 "event; c reports with the event but not the drug; d neither. q is the "
                 "Benjamini\u2013Hochberg adjusted p value across the 96 pairs within the "
                 "tier. Signal requires a \u2265 3, lower 95% confidence limit > 1, PRR "
                 "\u2265 2, \u03c7\u00b2 \u2265 4 and lower information component bound > 0.",
            font_size=7.0)
        K.page_break(doc)

    # S3
    h2h = rd("faers_head_to_head.csv")
    body = []
    for r in h2h:
        body.append([r["disease"], f'{r["drug_a"]} vs {r["drug_b"]}', r["pt"], r["a"], r["c"],
                     r["N_a"], r["N_b"], r["overlap"], ci(r), f2(r["p"], 3)
                     if r["p"] else "—"])
    K.p(doc, "**Table S3** Complete head-to-head results within each disease", size=10,
        space_after=4)
    K.table(doc, ["Disease", "Comparison", "Preferred term", "a", "c", "N index",
                  "N comparator", "Overlap", "ROR (95% CI)", "p"],
            body, font_size=6.8)
    K.p(doc, "a reports on the index drug with the event; c reports on the comparator with "
             "the event; N is the number of reports naming that drug within the disease; "
             "overlap is the number naming both drugs.", font_size=7.0)
    K.page_break(doc)

    # S4
    sens = rd("faers_sensitivity.csv")
    body = []
    for r in sens:
        body.append([r["scenario"].replace("S1_excl_combo", "S1 excluding combination")
                    .replace("S2_serious_only", "S2 serious only"),
                     r["disease"], r["pt"], r["a"], r["c"], ci(r), f2(r["p"], 3)
                     if r["p"] else "—"])
    K.p(doc, "**Table S4** Head-to-head sensitivity analyses", size=10, space_after=4)
    K.table(doc, ["Analysis", "Disease", "Preferred term", "a", "c", "ROR (95% CI)", "p"],
            body, font_size=6.8)
    K.p(doc, "S1 excludes reports naming both drugs of the pair; S2 restricts to reports "
             "flagged serious.", font_size=7.0)
    K.page_break(doc)

    # S5
    en = rd("background_enrichment.csv")
    body = [[r["pt"], f"{int(r['n_mpn']):,}", f"{float(r['pct_mpn']):.3f}%",
             f"{int(r['n_db']):,}", f"{float(r['pct_db']):.3f}%",
             f"{float(r['enrichment']):.1f}"]
            for r in en]
    K.p(doc, "**Table S5** Background enrichment of the 16 events in the myeloproliferative "
             "population", size=10, space_after=4)
    K.table(doc, ["Preferred term", "MPN reports", "MPN prevalence", "All reports",
                  "Database prevalence", "Enrichment"], body, font_size=7.4)
    K.p(doc, "Enrichment is MPN prevalence divided by database prevalence, where prevalence "
             "is the proportion of reports containing the term. MPN pool 58,602 reports; "
             "database 20,692,690 reports. A value above 1 indicates that the event is "
             "over-represented among patients with a myeloproliferative neoplasm and hence "
             "that users of these drugs carry a higher baseline than the database average.",
        font_size=7.0)
    K.page_break(doc)

    # S6
    l2s = rd("faers_l2_sensitivity.csv")
    body = []
    for r in l2s:
        body.append([r["scenario"].replace("S3_no_ruxolitinib", "S3 pool without ruxolitinib")
                    .replace("S4_untreated_MPN", "S4 unexposed MPN"),
                     r["drug"], r["pt"], r["a"], r["c"], ci(r)])
    K.p(doc, "**Table S6** Disease-pool sensitivity analyses (S3 and S4)", size=10,
        space_after=4)
    K.table(doc, ["Analysis", "Drug", "Preferred term", "a", "c", "ROR (95% CI)"],
            body, font_size=6.8)
    K.p(doc, "S3 restricts the disease pool to reports without ruxolitinib, which otherwise "
             "accounts for 61.2% of it. S4 uses reports recording a myeloproliferative "
             "neoplasm but none of the six study drugs as the reference; the exposed and "
             "unexposed groups are disjoint. MPN myeloproliferative neoplasm.",
        font_size=7.0)
    K.page_break(doc)

    # S7  （横向页：13 列）
    K.new_landscape_section(doc)
    cs = rd("case_series.csv")
    body = []
    for r in cs:
        body.append([r["drug"], r["pt"], r["report_id"], r["date"], r["country"],
                     r["sex"], r["age"], r["reporter"], r["serious"],
                     r["drug_role_of_interest"], r["mpn_indication"][:34],
                     r["n_drugs"], r["reactions"][:52]])
    K.p(doc, "**Table S7** Complete extraction of the 169 individual case reports", size=10,
        space_after=4)
    K.table(doc, ["Drug", "Event", "Report ID", "Received", "Country", "Sex", "Age",
                  "Reporter", "Serious", "Role", "MPN indication", "No. of drugs",
                  "Co-reported terms"],
            body, font_size=5.6)
    K.p(doc, "Reporter codes follow the FAERS primary source qualification field: 1 "
             "physician, 2 pharmacist, 3 other healthcare professional, 5 consumer. Role "
             "codes follow drugcharacterization: 1 suspect, 2 concomitant, 3 interacting. "
             "All identifiers are the public FAERS safety report identifiers; the data are "
             "already de-identified by the source and no attempt at re-identification was "
             "made. MPN myeloproliferative neoplasm.", font_size=7.0)

    doc.save(os.path.join(SUB, "04_Supplementary.docx"))
    print("[OK] 04_Supplementary.docx")


# =====================================================================
# 4. 投稿信
# =====================================================================
def build_cover_letter():
    doc = K.new_doc(double=False, line_numbers=False, page_numbers=False)
    K.meta(doc, AUTHOR, "Cover letter - " + TITLE, subject="Cover letter")
    for line in [
        "1 November 2026",
        "",
        "The Editor-in-Chief",
        "Drug Safety",
        "",
    ]:
        K.p(doc, line, size=11, space_after=2)

    K.p(doc, "Dear Editor,", size=11, space_after=10)

    K.p(doc, "We submit for your consideration an original research article entitled "
             "\u201cBackground selection determines the conclusion: a three-tier "
             "disproportionality analysis of thrombotic signals for myeloproliferative "
             "neoplasm therapies in FAERS\u201d.",
        size=11, space_after=10)

    K.p(doc, "The paper addresses a problem that your journal has recently done more than any "
             "other to define. Fusaroli and colleagues, in Drug Safety, set out the pitfalls "
             "of disproportionality analysis and closed by calling for tools that detect and "
             "mitigate bias rather than merely name it. We have tried to supply one, and to "
             "attach a number to it.",
        size=11, space_after=10)

    K.p(doc, "Myeloproliferative neoplasms are an ideal calibration system because the "
             "expected answer is known in advance: hydroxyurea, ruxolitinib and the other "
             "cytoreductive agents are prescribed in order to lower thrombotic risk, so any "
             "positive signal for thrombosis is a priori suspect. Against all other reports "
             "in FAERS, these drugs produce some of the strongest splanchnic signals in the "
             "database, with a reporting odds ratio of 26.57 for hydroxyurea and splenic "
             "infarction. Restricting the reference to reports that record a "
             "myeloproliferative neoplasm removes a median of 90% of that signal, and the "
             "amount removed is almost exactly proportional to how much more common the "
             "event is in the diseased population (slope 0.95, R\u00b2 = 0.64).",
        size=11, space_after=10)

    K.p(doc, "Three things follow, and we believe they are of interest to your readership. "
             "First, the bias is quantifiable in advance from disease epidemiology, which "
             "makes it correctable rather than merely disclosable. Second, applying a "
             "disease-matched reference isolates a single signal that survives every test we "
             "could devise \u2014 anagrelide and myocardial infarction in essential "
             "thrombocythaemia, reporting odds ratio 2.94, rising to 4.77 after excluding "
             "combination users \u2014 which is a finding of direct clinical relevance. "
             "Third, the same three-step design transfers to any condition that generates the "
             "outcome of interest, and we set out five examples.",
        size=11, space_after=10)

    K.p(doc, "The manuscript follows READUS-PV and the completed checklist is enclosed. It "
             "also reports, rather than conceals, three findings that argue against a naive "
             "reading of our own data: 50,024 ruxolitinib reports (70.2%) contain no patient "
             "block at all, consumer reporting ranges from 5.1% to 70.9% across the six drugs, "
             "and in 22 of 45 hydroxyurea\u2013splenic infarction reports the drug was "
             "recorded as a concomitant rather than the suspect agent. We think these belong "
             "in the paper because they are the mechanism, not an embarrassment.",
        size=11, space_after=10)

    K.p(doc, "The work is original, has not been published previously and is not under "
             "consideration elsewhere. All five authors have approved the submitted version "
             "and agree to its submission to Drug Safety. All analysis code and the complete "
             "response cache are publicly archived, so every reported count can be reproduced. "
             "The authors declare no competing interests. The study used publicly available, "
             "de-identified aggregate data and required no ethics approval.",
        size=11, space_after=10)

    K.p(doc, "We suggest that the paper is best handled as a methods-oriented original "
             "research article rather than as a signal-detection report, and we would welcome "
             "reviewers with expertise in pharmacoepidemiology as well as in "
             "myeloproliferative neoplasms.",
        size=11, space_after=10)

    K.p(doc, "Thank you for your consideration.", size=11, space_after=16)

    K.p(doc, "Yours sincerely,", size=11, space_after=2)
    K.p(doc, "Xiaomei Hu, MD", size=11, bold=True, space_after=0)
    K.p(doc, "Department of Hematology, Xiyuan Hospital, China Academy of Chinese Medical "
             "Sciences, Beijing, China", size=10.5, space_after=0)
    K.p(doc, "huxiaomei_2@163.com", size=10.5, space_after=0)
    K.p(doc, "on behalf of all authors", size=10.5, italic=True)

    doc.save(os.path.join(SUB, "05_Cover_letter.docx"))
    print("[OK] 05_Cover_letter.docx")


# =====================================================================
# 5. READUS-PV 清单
# =====================================================================
def build_checklist():
    text = open(os.path.join(SUB, "READUS-PV_checklist.md"), encoding="utf-8").read()
    doc = K.new_doc(double=False, line_numbers=False, page_numbers=True)
    K.meta(doc, AUTHOR, "READUS-PV checklist")

    in_table = False
    tbl_header, tbl_rows = None, []

    def flush():
        nonlocal tbl_header, tbl_rows, in_table
        if tbl_header:
            ncol = len(tbl_header)
            widths = None
            if ncol == 5:
                widths = [1.2, 4.6, 1.9, 7.0]
            K.table(doc, tbl_header, tbl_rows, font_size=7.4, col_widths=widths)
        tbl_header, tbl_rows = None, []
        in_table = False

    for raw in text.split("\n"):
        line = raw.rstrip()
        if line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if all(set(c) <= set("-: ") for c in cells):
                continue
            if not in_table:
                tbl_header, tbl_rows, in_table = cells, [], True
            else:
                tbl_rows.append(cells)
            continue
        flush()
        if not line.strip():
            continue
        if line.startswith("### "):
            K.h(doc, line[4:].strip(), level=3, size=10.5, space_before=10, space_after=3)
        elif line.startswith("## "):
            K.h(doc, line[3:].strip(), level=2, size=11.5, space_before=12, space_after=4)
        elif line.startswith("# "):
            K.h(doc, line[2:].strip(), level=1, size=13, space_before=0, space_after=8)
        elif line.startswith("- "):
            para = doc.add_paragraph(style="List Bullet")
            run = para.add_run(line[2:].strip())
            K._set_run_font(run, size=9)
        elif re.match(r"^\d+\.\s", line):
            para = doc.add_paragraph()
            para.paragraph_format.left_indent = Cm(0.6)
            for i, seg in enumerate(line.strip().split("**")):
                if not seg:
                    continue
                run = para.add_run(seg)
                K._set_run_font(run, size=9, bold=(i % 2 == 1))
        else:
            para = doc.add_paragraph()
            para.paragraph_format.space_after = Pt(3)
            for i, seg in enumerate(line.split("**")):
                if not seg:
                    continue
                run = para.add_run(seg)
                K._set_run_font(run, size=9, bold=(i % 2 == 1))
    flush()

    doc.save(os.path.join(SUB, "06_READUS-PV_checklist.docx"))
    print("[OK] 06_READUS-PV_checklist.docx")


if __name__ == "__main__":
    md_to_doc(os.path.join(SUB, "manuscript.md"), os.path.join(SUB, "02_Manuscript.docx"))
    build_title_page()
    build_tables()
    build_supplementary()
    build_cover_letter()
    build_checklist()
    print("\nAll built.")

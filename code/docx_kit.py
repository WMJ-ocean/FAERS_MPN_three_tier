# -*- coding: utf-8 -*-
"""
docx_kit.py — 期刊排版工具函数（Word）
=====================================
统一处理：Times New Roman 12 pt、双倍行距、连续行号、页脚页码、
表头重复、表注、标题层级。
"""
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_SECTION
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def _set_run_font(run, name="Times New Roman", size=12, bold=None, italic=None,
                  color=None):
    run.font.name = name
    run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic
    if color:
        run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts")
        rpr.append(rf)
    for attr in ("w:ascii", "w:hAnsi", "w:cs", "w:eastAsia"):
        rf.set(qn(attr), name)


def _add_line_numbers(doc):
    sectPr = doc.sections[0]._sectPr
    ln = OxmlElement("w:lnNumType")
    ln.set(qn("w:countBy"), "1")
    ln.set(qn("w:restart"), "continuous")
    ln.set(qn("w:distance"), "360")
    cols = sectPr.find(qn("w:cols"))
    if cols is not None:
        cols.addprevious(ln)
    else:
        sectPr.append(ln)


def _add_page_number_footer(doc):
    footer = doc.sections[0].footer
    para = footer.paragraphs[0]
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = para.add_run()
    _set_run_font(run, size=10)
    fld1 = OxmlElement("w:fldChar")
    fld1.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld2 = OxmlElement("w:fldChar")
    fld2.set(qn("w:fldCharType"), "end")
    run._r.append(fld1)
    run._r.append(instr)
    run._r.append(fld2)


def new_doc(double=True, line_numbers=True, page_numbers=True, margins_cm=2.5):
    doc = Document()
    st = doc.styles["Normal"]
    st.font.name = "Times New Roman"
    st.font.size = Pt(12)
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    pf = st.paragraph_format
    pf.line_spacing_rule = (WD_LINE_SPACING.DOUBLE if double
                            else WD_LINE_SPACING.SINGLE)
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    for s in doc.sections:
        s.top_margin = Cm(margins_cm)
        s.bottom_margin = Cm(margins_cm)
        s.left_margin = Cm(margins_cm)
        s.right_margin = Cm(margins_cm)
    if page_numbers:
        _add_page_number_footer(doc)
    if line_numbers:
        _add_line_numbers(doc)
    return doc


def meta(doc, author, title, subject="", keywords=""):
    cp = doc.core_properties
    cp.author = author
    cp.last_modified_by = author
    cp.title = title
    cp.subject = subject
    cp.keywords = keywords
    cp.comments = ""


def h(doc, text, level=1, size=None, space_before=12, space_after=4):
    sizes = {1: 14, 2: 12, 3: 12}
    sz = size or sizes.get(level, 12)
    para = doc.add_paragraph()
    para.paragraph_format.space_before = Pt(space_before)
    para.paragraph_format.space_after = Pt(space_after)
    para.paragraph_format.keep_with_next = True
    run = para.add_run(text)
    _set_run_font(run, size=sz, bold=True)
    return para


def p(doc, text, size=12, bold=False, italic=False, align=None, space_after=0,
      indent_first=False, double=True, font_size=None):
    if font_size is not None:
        size = font_size
    para = doc.add_paragraph()
    if align == "center":
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    elif align == "justify":
        para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    elif align == "right":
        para.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    para.paragraph_format.space_after = Pt(space_after)
    if indent_first:
        para.paragraph_format.first_line_indent = Cm(0.75)
    if not double:
        para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
    # 支持 **加粗** 片段
    parts = text.split("**")
    for i, seg in enumerate(parts):
        if not seg:
            continue
        run = para.add_run(seg)
        _set_run_font(run, size=size, bold=(bold or i % 2 == 1), italic=italic)
    return para


def _shade(cell, hexcolor):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hexcolor)
    tcPr.append(shd)


def _repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def table(doc, header, rows, caption=None, note=None, font_size=8.5,
          col_widths=None, header_fill="F2F4F6", align_right_from=1,
          caption_above=True):
    if caption:
        cp = doc.add_paragraph()
        cp.paragraph_format.space_before = Pt(10)
        cp.paragraph_format.space_after = Pt(4)
        cp.paragraph_format.keep_with_next = True
        parts = caption.split("**")
        for i, seg in enumerate(parts):
            if not seg:
                continue
            run = cp.add_run(seg)
            _set_run_font(run, size=10, bold=(i % 2 == 1))

    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = True

    hdr = t.rows[0]
    _repeat_header(hdr)
    for i, txt in enumerate(header):
        cell = hdr.cells[i]
        cell.text = ""
        para = cell.paragraphs[0]
        para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        para.paragraph_format.space_after = Pt(1)
        run = para.add_run(str(txt))
        _set_run_font(run, size=font_size, bold=True)
        _shade(cell, header_fill)

    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            para = cells[i].paragraphs[0]
            para.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
            para.paragraph_format.space_after = Pt(1)
            if i >= align_right_from:
                para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = para.add_run("" if val is None else str(val))
            _set_run_font(run, size=font_size)

    if col_widths:
        total = sum(col_widths)
        usable = 16.0
        scale = usable / total if total > usable else 1.0
        for row in t.rows:
            for i, w in enumerate(col_widths):
                row.cells[i].width = Cm(w * scale)
        # 固定表格总宽，避免 Word 自动扩张
        tblPr = t._tbl.tblPr
        tblW = tblPr.find(qn("w:tblW"))
        if tblW is None:
            tblW = OxmlElement("w:tblW")
            tblPr.append(tblW)
        tblW.set(qn("w:type"), "pct")
        tblW.set(qn("w:w"), "5000")

    if note:
        np_ = doc.add_paragraph()
        np_.paragraph_format.space_before = Pt(3)
        np_.paragraph_format.space_after = Pt(10)
        np_.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
        run = np_.add_run(note)
        _set_run_font(run, size=font_size - 0.5, italic=False)
        run.font.color.rgb = RGBColor(0x44, 0x4A, 0x52)
    return t


def page_break(doc):
    doc.add_page_break()


def new_landscape_section(doc):
    """插入一个横向页面节（用于超宽表格）"""
    from docx.enum.section import WD_ORIENT
    sec = doc.add_section(WD_SECTION.NEW_PAGE)
    sec.orientation = WD_ORIENT.LANDSCAPE
    w, h = sec.page_width, sec.page_height
    if w < h:
        sec.page_width, sec.page_height = h, w
    sec.top_margin = Cm(2.0)
    sec.bottom_margin = Cm(2.0)
    sec.left_margin = Cm(2.0)
    sec.right_margin = Cm(2.0)
    return sec

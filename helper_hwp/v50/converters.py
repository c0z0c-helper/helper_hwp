"""
HWP 5.0 문서 변환 로직 (converters)

hwp_to_markdown / hwp_to_pdf 구현을 담당합니다.
parser.py의 공개 API 함수에서 호출됩니다.
"""

import os
from typing import TYPE_CHECKING, List, Optional, Set, Tuple

from .constants import ElementType
from .parsed_elements import ParsedParagraph, ParsedTable


# ---------------------------------------------------------------------------
# 마크다운 헬퍼
# ---------------------------------------------------------------------------


def _format_text(text: str, font_size: float, bold: bool) -> str:
    """폰트 크기·굵기 → 마크다운 헤딩/볼드 변환"""
    if not text:
        return ""
    if font_size >= 28:
        return f"# {text}"
    elif font_size >= 20:
        return f"## {text}"
    elif font_size >= 14:
        return f"### {text}"
    elif bold:
        return f"**{text}**"
    else:
        return text


def _create_markdown_table(
    paragraphs: List[str],
    rows: int,
    cols: int,
    cell_para_counts: List[int],
    cell_colspans: Optional[List[int]] = None,
    cell_rowspans: Optional[List[int]] = None,
) -> str:
    """셀 문단 목록으로 마크다운 표 생성"""
    if not paragraphs or rows == 0 or cols == 0:
        return ""

    # 병합 셀 위치 계산
    skip_cells: Set[Tuple[int, int]] = set()
    if cell_colspans and cell_rowspans:
        p_idx = 0
        l_row = l_col = 0
        while p_idx < len(cell_para_counts):
            while (l_row, l_col) in skip_cells:
                l_col += 1
                if l_col >= cols:
                    l_col = 0
                    l_row += 1
            cs = cell_colspans[p_idx] if p_idx < len(cell_colspans) else 1
            rs = cell_rowspans[p_idx] if p_idx < len(cell_rowspans) else 1
            for r in range(l_row, l_row + rs):
                for c in range(l_col, l_col + cs):
                    if not (r == l_row and c == l_col):
                        skip_cells.add((r, c))
            l_col += 1
            if l_col >= cols:
                l_col = 0
                l_row += 1
            p_idx += 1

    lines: List[str] = []
    para_idx = 0
    cell_idx = 0

    for row_idx in range(rows):
        row_cells = []
        for col_idx in range(cols):
            if (row_idx, col_idx) in skip_cells:
                row_cells.append("")
                continue
            count = cell_para_counts[cell_idx] if cell_idx < len(cell_para_counts) else 0
            parts = []
            for _ in range(count):
                if para_idx < len(paragraphs):
                    parts.append(paragraphs[para_idx].lstrip("#").strip().replace("**", ""))
                    para_idx += 1
            row_cells.append(" ".join(parts))
            cell_idx += 1
        lines.append("| " + " | ".join(row_cells) + " |")
        if row_idx == 0:
            lines.append("| " + " | ".join(["---"] * cols) + " |")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 공개 변환 함수
# ---------------------------------------------------------------------------


def convert_to_markdown(hwp_path: str) -> str:
    """
    HWP 파일을 마크다운으로 변환.

    Args:
        hwp_path: 입력 HWP 파일 경로

    Returns:
        마크다운 문자열
    """
    # 순환 import 방지: parser는 converters를 import하므로 여기서는 지연 import
    from .parser import open_hwp

    md_lines: List[str] = []
    table_paras: List[str] = []
    in_table = False
    t_rows = t_cols = 0
    t_cell_counts: List[int] = []
    t_elem = None

    def _flush_table():
        nonlocal in_table, table_paras, t_rows, t_cols, t_cell_counts, t_elem
        if table_paras:
            tmd = _create_markdown_table(
                table_paras,
                t_rows,
                t_cols,
                t_cell_counts,
                getattr(t_elem, "cell_colspans", None),
                getattr(t_elem, "cell_rowspans", None),
            )
            md_lines.append(tmd)
            md_lines.append("")
        in_table = False
        table_paras = []
        t_cell_counts = []

    with open_hwp(hwp_path) as doc:
        for etype, elem in doc.tags:
            if etype in (
                ElementType.PICTURE,
                ElementType.COMMENT,
                ElementType.FOOTNOTE,
                ElementType.ENDNOTE,
            ):
                continue

            elif etype == ElementType.TABLE and isinstance(elem, ParsedTable):
                if in_table:
                    _flush_table()
                in_table = True
                table_paras = []
                t_rows = elem.rows or 0
                t_cols = elem.cols or 0
                t_cell_counts = elem.cell_para_counts or []
                t_elem = elem

            elif etype == ElementType.PARAGRAPH and isinstance(elem, ParsedParagraph):
                text = (elem.text or "").strip()
                if elem.char_shape:
                    md_text = _format_text(text, elem.char_shape.font_size, elem.char_shape.bold)
                else:
                    md_text = text

                if in_table:
                    table_paras.append(md_text.replace("\n", " ").replace("\r", " "))
                    if t_cell_counts and len(table_paras) >= sum(t_cell_counts):
                        _flush_table()
                else:
                    if text:
                        md_lines.append(md_text)
                        md_lines.append("")

    if in_table:
        _flush_table()

    return "\n".join(md_lines)


def convert_to_pdf(hwp_path: str, output_pdf_path: Optional[str] = None) -> str:
    """
    HWP 파일을 PDF로 변환 (playwright 사용).

    Args:
        hwp_path: 입력 HWP 파일 경로
        output_pdf_path: 출력 PDF 경로 (None이면 입력 파일명 기반 자동 생성)

    Returns:
        생성된 PDF 파일 경로
    """
    from helper_md_doc import md_to_html
    from playwright.sync_api import sync_playwright

    if not os.path.isfile(hwp_path):
        raise FileNotFoundError(f"HWP 파일을 찾을 수 없습니다: {hwp_path}")

    md = convert_to_markdown(hwp_path)
    html = md_to_html(md, use_base64=True)

    if output_pdf_path is None:
        output_pdf_path = hwp_path.rsplit(".", 1)[0] + ".pdf"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html)
        page.pdf(path=output_pdf_path, format="A4", print_background=True)
        browser.close()

    return output_pdf_path

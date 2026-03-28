"""
helper_hwp 최상위 변환 함수 (포맷 자동 감지 dispatch)

파일 포맷(HWP 5.0 / HWP 97 / HWPX)에 관계없이 동일한 함수 시그니처로
텍스트·마크다운 변환을 수행합니다.

설계 원칙:
    외부 인터페이스(함수 시그니처)는 통일 유지.
    내부에서 detect_format() 으로 포맷을 감지한 뒤 open_hwp() 을 통해
    Document 객체를 얻어 iter_tags() 패턴으로 직접 변환합니다.
    각 서브모듈의 변환 함수에 의존하지 않습니다.

함수 목록:
    open_hwp(file_path, iter_mode) -> Document  # 포맷 자동 감지 Document 반환
    to_txt(file_path)              -> str        # 텍스트 추출
    to_md(file_path)               -> str        # 마크다운 변환
    to_pdf(file_path, output_path) -> str        # PDF 변환 (playwright 필요)
"""

import os
from pathlib import Path
from typing import List, Optional, Set, Tuple, Union

from .constants import ElementType
from .detector import HwpFormat, detect_format


# ---------------------------------------------------------------------------
# 마크다운 헬퍼 (v50/converters.py 에서 이동)
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
# 통합 Document 반환
# ---------------------------------------------------------------------------


def open_hwp(file_path: Union[str, Path], iter_mode=None):
    """HWP / HWP97 / HWPX 파일을 포맷 자동 감지 후 Document 객체 반환.

    반환된 Document 는 세 포맷 모두 동일한 외부 인터페이스를 제공합니다:
        doc.iter_tags(mode)     -> (ElementType, element) 제너레이터
        doc.tags                -> iter_tags() 간편 접근
        doc.to_text()           -> str
        doc.to_md()             -> str

    포맷별 dispatch:
        HwpFormat.HWP_V5  -> v50.parser.HwpDocument
        HwpFormat.HWP_V10 -> v97.parser.Hwp97Document
        HwpFormat.HWPX    -> owpml.parser.HwpxDocument

    Args:
        file_path: HWP, HWP97, 또는 HWPX 파일 경로
        iter_mode: IterMode 값 (None 이면 각 포맷 기본값 사용)

    Returns:
        HwpDocument | Hwp97Document | HwpxDocument
    """
    fmt = detect_format(file_path)
    kwargs = {"iter_mode": iter_mode} if iter_mode is not None else {}

    if fmt == HwpFormat.HWP_V5:
        from .v50.parser import HwpDocument

        return HwpDocument(str(file_path), **kwargs)
    if fmt == HwpFormat.HWP_V10:
        from .v97.parser import Hwp97Document

        return Hwp97Document(str(file_path), **kwargs)
    if fmt == HwpFormat.HWPX:
        from .owpml.parser import HwpxDocument

        return HwpxDocument(str(file_path), **kwargs)
    raise ValueError(f"지원하지 않는 파일 포맷입니다: {file_path}")


# ---------------------------------------------------------------------------
# 텍스트 변환
# ---------------------------------------------------------------------------


def to_txt(file_path: Union[str, Path]) -> str:
    """HWP / HWP97 / HWPX 파일에서 텍스트 추출 (포맷 자동 감지).

    내부적으로 open_hwp() + iter_tags() 를 사용합니다.
    ElementType.PARAGRAPH 요소의 text 를 줄바꿈으로 연결합니다.

    Args:
        file_path: HWP, HWP97, 또는 HWPX 파일 경로

    Returns:
        추출된 텍스트 문자열

    Raises:
        ValueError: 지원하지 않는 파일 포맷
        FileNotFoundError: 파일 없음
    """
    doc = open_hwp(file_path)
    lines: List[str] = []
    for etype, elem in doc.iter_tags():
        if etype == ElementType.PARAGRAPH:
            text = getattr(elem, "text", "") or ""
            if text.strip():
                lines.append(text)
        elif etype == ElementType.TABLE:
            table_text = getattr(elem, "to_text", None)
            if callable(table_text):
                t = table_text()
                if t:
                    lines.append(t)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 마크다운 변환
# ---------------------------------------------------------------------------


def to_md(file_path: Union[str, Path]) -> str:
    """HWP / HWP97 / HWPX 파일을 마크다운으로 변환 (포맷 자동 감지).

    내부적으로 open_hwp() + iter_tags() 를 사용합니다.
    v50 포맷은 font_size / bold 기반 헤딩/볼드 변환이 적용됩니다.
    표는 마크다운 표 형식으로 변환됩니다.

    Args:
        file_path: HWP, HWP97, 또는 HWPX 파일 경로

    Returns:
        마크다운 문자열

    Raises:
        ValueError: 지원하지 않는 파일 포맷
        FileNotFoundError: 파일 없음
    """
    fmt = detect_format(file_path)
    doc = open_hwp(file_path)

    md_lines: List[str] = []
    table_paras: List[str] = []
    in_table = False
    t_rows = t_cols = 0
    t_cell_counts: List[int] = []
    t_elem = None

    def _flush_table() -> None:
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
        table_paras.clear()
        t_cell_counts.clear()

    for etype, elem in doc.iter_tags():
        if etype in (
            ElementType.PICTURE,
            ElementType.COMMENT,
            ElementType.FOOTNOTE,
            ElementType.ENDNOTE,
        ):
            continue

        elif etype == ElementType.TABLE:
            if in_table:
                _flush_table()
            # v50: ParsedTable 에 cell_para_counts 존재 → _create_markdown_table 사용
            # v97/owpml: to_markdown() 메서드 사용
            if hasattr(elem, "cell_para_counts") and elem.cell_para_counts is not None:
                in_table = True
                table_paras = []
                t_rows = elem.rows or 0
                t_cols = elem.cols or 0
                t_cell_counts = elem.cell_para_counts or []
                t_elem = elem
            else:
                # v97/owpml: ParsedTable.to_markdown() 직접 호출
                to_md_fn = getattr(elem, "to_markdown", None)
                if callable(to_md_fn):
                    md_lines.append(to_md_fn())
                    md_lines.append("")

        elif etype == ElementType.PARAGRAPH:
            text = (getattr(elem, "text", "") or "").strip()
            char_shape = getattr(elem, "char_shape", None)

            if fmt == HwpFormat.HWP_V5 and char_shape is not None:
                md_text = _format_text(text, char_shape.font_size, char_shape.bold)
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


# ---------------------------------------------------------------------------
# PDF 변환
# ---------------------------------------------------------------------------


def to_pdf(file_path: Union[str, Path], output_pdf_path: Optional[str] = None) -> str:
    """HWP / HWP97 / HWPX 파일을 PDF로 변환 (playwright 필요).

    내부적으로 to_md() 으로 마크다운을 생성한 뒤
    helper_md_doc.md_to_html + playwright 로 PDF를 렌더링합니다.

    Args:
        file_path: 입력 파일 경로
        output_pdf_path: 출력 PDF 경로 (None 이면 입력 파일명 기반 자동 생성)

    Returns:
        생성된 PDF 파일 경로
    """
    from helper_md_doc import md_to_html
    from playwright.sync_api import sync_playwright

    file_path = str(file_path)
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    md = to_md(file_path)
    html = md_to_html(md, use_base64=True)

    if output_pdf_path is None:
        output_pdf_path = file_path.rsplit(".", 1)[0] + ".pdf"

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.set_content(html)
        page.pdf(path=output_pdf_path, format="A4", print_background=True)
        browser.close()

    return output_pdf_path


__all__ = [
    "open_hwp",
    "to_txt",
    "to_md",
    "to_pdf",
    "_format_text",
    "_create_markdown_table",
]

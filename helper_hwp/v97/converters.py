"""
HWP 97 (V3.00) 문서 변환 로직 (converters)

convert_to_text / convert_to_markdown 구현.
parser.py 의 공개 API 함수에서 호출됩니다.
"""

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .document_structure import Hwp97File

from .parsed_elements import ParsedParagraph, ParsedTable


# ---------------------------------------------------------------------------
# 텍스트 변환 헬퍼
# ---------------------------------------------------------------------------


def convert_to_text(hwp: "Hwp97File") -> str:
    """HWP 97 (V3.00) 문서를 순수 텍스트로 변환.

    Args:
        hwp: Hwp97File 파싱 결과

    Returns:
        줄바꾸으로 문단 구분된 텍스트
    """
    lines: List[str] = []
    for para in hwp.paragraphs:
        if isinstance(para, ParsedTable):
            for row in para.cell_texts:
                lines.append("\t".join(row))
        else:
            lines.append(para.text)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 마크다운 변환 헬퍼
# ---------------------------------------------------------------------------


def _format_text(text: str, font_size_pt: float, bold: bool) -> str:
    """글자 크기·굵기 → 마크다운 헤딩/볼드 변환"""
    if not text:
        return ""
    if font_size_pt >= 28:
        return f"# {text}"
    elif font_size_pt >= 20:
        return f"## {text}"
    elif font_size_pt >= 14:
        return f"### {text}"
    elif bold:
        return f"**{text}**"
    return text


def _create_markdown_table(cell_texts: List[List[str]]) -> str:
    """2D 셀 텍스트 → 마크다운 표 생성"""
    if not cell_texts:
        return ""
    rows = cell_texts
    cols = max(len(r) for r in rows)

    lines: List[str] = []
    for row_idx, row in enumerate(rows):
        # 열 수 패딩
        padded = row + [""] * (cols - len(row))
        cells = [c.replace("\n", " ").replace("|", "\\|") for c in padded]
        lines.append("| " + " | ".join(cells) + " |")
        if row_idx == 0:
            lines.append("| " + " | ".join(["---"] * cols) + " |")
    return "\n".join(lines)


def convert_to_markdown(hwp: "Hwp97File") -> str:
    """HWP 97 (V3.00) 문서를 마크다운으로 변환.

    - 글자 크기에 따라 헤딩(#, ##, ###) 적용
    - 굵게 속성 → **텍스트**
    - 표(BOX, box_type=0) → 마크다운 표

    Args:
        hwp: Hwp97File 파싱 결과

    Returns:
        마크다운 문자열
    """
    md_lines: List[str] = []

    for para in hwp.paragraphs:
        if isinstance(para, ParsedTable):
            cell_texts = para.cell_texts
            if cell_texts:
                table_md = _create_markdown_table(cell_texts)
                md_lines.append(table_md)
                md_lines.append("")
            continue

        text = para.text.strip()
        if not text:
            md_lines.append("")
            continue

        cs = para.char_shape
        if cs is not None:
            font_size_pt = cs.font_size_pt
            bold = cs.bold
        else:
            font_size_pt = 10.0
            bold = False

        formatted = _format_text(text, font_size_pt, bold)
        md_lines.append(formatted)

    # 연속 빈 줄 정리 (최대 1개)
    result: List[str] = []
    prev_blank = False
    for line in md_lines:
        if line == "":
            if not prev_blank:
                result.append("")
            prev_blank = True
        else:
            result.append(line)
            prev_blank = False

    return "\n".join(result)

"""
HWP 5.0 문서 순회 로직 (iterators)

HwpDocument._iter_sequential / _iter_structured 구현을 담당합니다.
parser.py의 HwpDocument에서 위임(delegate) 방식으로 호출됩니다.

참고:
- HWP 5.0 스펙: 문단 내 제어문자 (4.3.1~4.3.3)
  * CharType.INLINE_CONTROL  → 인라인 제어 (size=8, 별도 객체 없음)
  * CharType.EXTENDED_CONTROL → 확장 제어 (size=8, 별도 객체 포인터)
- control_data 첫 4바이트 = Control ID (리틀엔디언 UINT32)
"""

import struct
from typing import Dict, Generator, List, Optional, Tuple

from .char_paragraph import CharType, Paragraph
from .constants import (
    ControlID,
    ElementType,
    ExtendedControlCode,
    InlineControlCode,
    IterMode,
    ParagraphConstants,
)
from .document_structure import CharShapeInfo, HwpFile, Section
from .parsed_elements import ParsedParagraph, ParsedTable


# ---------------------------------------------------------------------------
# 공통 헬퍼
# ---------------------------------------------------------------------------


def _build_char_shape(
    paragraph: Paragraph,
    char_shapes_map: Dict,
) -> Tuple[Optional[CharShapeInfo], list]:
    """
    문단의 글자 모양 정보를 요약하여 반환.

    Returns:
        (대표 CharShapeInfo, [(pos, CharShapeInfo), ...])
    """
    char_shape = None
    char_shapes_list = []

    if paragraph.char_shape_ids:
        all_shapes = []
        for pos, shape_id in paragraph.char_shape_ids:
            shape = char_shapes_map.get(shape_id)
            if shape:
                all_shapes.append(shape)
                char_shapes_list.append((pos, shape))

        if all_shapes:
            char_shape = CharShapeInfo(
                font_size=max(s.font_size for s in all_shapes),
                font_id=all_shapes[0].font_id,
                bold=any(s.bold for s in all_shapes),
                italic=any(s.italic for s in all_shapes),
                underline=any(s.underline for s in all_shapes),
                expansion=max(s.expansion for s in all_shapes),
                spacing=all_shapes[0].spacing,
                color=all_shapes[0].color,
            )
    elif paragraph.char_shape_id is not None:
        shape = char_shapes_map.get(paragraph.char_shape_id)
        if shape:
            char_shape = shape
            char_shapes_list = [(0, shape)]

    return char_shape, char_shapes_list


def _build_table_from_info(
    code: int,
    control_data: Optional[bytes],
    control_id: Optional[int],
    table_counter: int,
    table_info: dict,
) -> ParsedTable:
    """table_metadata dict에서 ParsedTable 생성"""
    return ParsedTable(
        code=code,
        data=control_data,
        control_id=control_id,
        table_index=table_counter,
        x=table_info.get("x"),
        y=table_info.get("y"),
        width=table_info.get("width"),
        height=table_info.get("height"),
        margin_left=table_info.get("margin_left"),
        margin_right=table_info.get("margin_right"),
        margin_top=table_info.get("margin_top"),
        margin_bottom=table_info.get("margin_bottom"),
        rows=table_info.get("rows"),
        cols=table_info.get("cols"),
        cell_count=(
            table_info.get("cell_para_counts", [])[-1]
            if table_info.get("cell_para_counts")
            else None
        ),
        cell_para_counts=table_info.get("cell_para_counts"),
        cell_spacing=table_info.get("cell_spacing"),
        row_sizes=table_info.get("row_sizes"),
        cell_widths=table_info.get("cell_widths"),
        cell_heights=table_info.get("cell_heights"),
        cell_colspans=table_info.get("cell_colspans"),
        cell_rowspans=table_info.get("cell_rowspans"),
    )


def _get_control_id(control_data: Optional[bytes]) -> Optional[int]:
    """control_data 첫 4바이트에서 Control ID 추출"""
    if control_data and len(control_data) >= ParagraphConstants.CONTROL_ID_SIZE:
        return struct.unpack("<I", control_data[: ParagraphConstants.CONTROL_ID_SIZE])[0]
    return None


def _yield_extended_control(
    code: int,
    control_data: Optional[bytes],
    control_id: Optional[int],
    table_counter: int,
    all_table_metadata: List[dict],
):
    """
    확장 제어 문자 1개를 (ElementType, element) 튜플로 변환.

    Yields:
        (ElementType, ParsedTable) 또는 테이블 counter 업데이트 후 동일
    Returns:
        업데이트된 table_counter
    """
    _simple = {
        ExtendedControlCode.PICTURE: ElementType.PICTURE,
        ExtendedControlCode.OLE: ElementType.OLE,
        ExtendedControlCode.EQUATION: ElementType.EQUATION,
        ExtendedControlCode.FOOTNOTE: ElementType.FOOTNOTE,
        ExtendedControlCode.ENDNOTE: ElementType.ENDNOTE,
        ExtendedControlCode.HYPERLINK: ElementType.HYPERLINK,
        ExtendedControlCode.COMMENT: ElementType.COMMENT,
        ExtendedControlCode.SHAPE: ElementType.SHAPE,
    }

    is_table = control_id == ControlID.TABLE or code == ExtendedControlCode.TABLE
    if is_table:
        table_counter += 1
        table_info = (
            all_table_metadata[table_counter - 1]
            if table_counter <= len(all_table_metadata)
            else {}
        )
        yield (
            ElementType.TABLE,
            _build_table_from_info(code, control_data, control_id, table_counter, table_info),
        )
        return table_counter

    if control_id == ControlID.AUTO_NUMBER:
        yield (
            ElementType.AUTO_NUMBER,
            ParsedTable(code=code, data=control_data, control_id=control_id),
        )
    elif control_id == ControlID.PAGE_NUM_POS:
        yield (
            ElementType.PAGE_NUM_POS,
            ParsedTable(code=code, data=control_data, control_id=control_id),
        )
    elif control_id == ControlID.HEADER:
        yield (ElementType.HEADER, ParsedTable(code=code, data=control_data, control_id=control_id))
    elif control_id == ControlID.FOOTER:
        yield (ElementType.FOOTER, ParsedTable(code=code, data=control_data, control_id=control_id))
    elif code in _simple:
        yield (_simple[code], ParsedTable(code=code, data=control_data, control_id=control_id))
    else:
        yield (
            ElementType.SHAPE_COMPONENT,
            ParsedTable(code=code, data=control_data, control_id=control_id),
        )

    return table_counter


# ---------------------------------------------------------------------------
# SEQUENTIAL 순회
# ---------------------------------------------------------------------------


def iter_sequential(hwp: HwpFile):
    """
    SEQUENTIAL 모드: 문서 출현 순서로 (ElementType, element) yield.

    Args:
        hwp: HwpFile 인스턴스
    """
    # 섹션 전체에서 테이블 메타데이터 수집
    all_table_metadata = [
        info
        for section in hwp.body.sections
        for info in section.table_metadata
        if info.get("ctrl_id") == ControlID.TABLE
    ]
    table_counter = 0

    for section in hwp.body.sections:
        for paragraph in section.paragraphs:
            # 페이지 구분
            if paragraph.is_page_break:
                yield (
                    ElementType.PAGE_BREAK,
                    ParsedParagraph(text=paragraph.to_string().strip(), paragraph=paragraph),
                )

            # 문단
            char_shape, char_shapes_list = _build_char_shape(paragraph, hwp.char_shapes)
            yield (
                ElementType.PARAGRAPH,
                ParsedParagraph(
                    text=paragraph.to_string().strip(),
                    paragraph=paragraph,
                    char_shape=char_shape,
                    char_shapes=char_shapes_list,
                ),
            )

            # 인라인/확장 제어
            for char in paragraph.chars:
                if char.char_type == CharType.INLINE_CONTROL:
                    if char.code == InlineControlCode.PAGE_NUMBER:
                        yield (
                            ElementType.AUTO_NUMBER,
                            ParsedTable(code=char.code, data=char.control_data, control_id=None),
                        )

                elif char.char_type == CharType.EXTENDED_CONTROL:
                    control_id = _get_control_id(char.control_data)
                    gen = _yield_extended_control(
                        char.code, char.control_data, control_id, table_counter, all_table_metadata
                    )
                    for item in gen:
                        if isinstance(item, int):
                            table_counter = item
                        else:
                            if isinstance(item[1], ParsedTable) and item[0] == ElementType.TABLE:
                                table_counter = item[1].table_index or table_counter
                            yield item

            # ctrl_headers
            for ctrl_id, ctrl_data in paragraph.ctrl_headers:
                _ctrl_map = {
                    ControlID.AUTO_NUMBER: (21, ElementType.AUTO_NUMBER),
                    ControlID.NEW_NUMBER: (21, ElementType.NEW_NUMBER),
                    ControlID.PAGE_NUM_POS: (21, ElementType.PAGE_NUM_POS),
                    ControlID.HEADER: (16, ElementType.HEADER),
                    ControlID.FOOTER: (16, ElementType.FOOTER),
                }
                if ctrl_id in _ctrl_map:
                    code, etype = _ctrl_map[ctrl_id]
                    yield (etype, ParsedTable(code=code, data=ctrl_data[4:], control_id=ctrl_id))


# ---------------------------------------------------------------------------
# STRUCTURED 순회
# ---------------------------------------------------------------------------


def iter_structured(hwp: HwpFile):
    """
    STRUCTURED 모드: Section → Paragraph → Char 계층 구조로 yield.

    Args:
        hwp: HwpFile 인스턴스
    """
    all_table_metadata = [
        info
        for section in hwp.body.sections
        for info in section.table_metadata
        if info.get("ctrl_id") == ControlID.TABLE
    ]
    table_counter = 0

    for section_idx, section in enumerate(hwp.body.sections):
        yield (
            ElementType.SECTION,
            ParsedParagraph(text=f"[Section {section_idx}]", paragraph=Paragraph()),
        )

        for para_idx, paragraph in enumerate(section.paragraphs):
            if paragraph.is_page_break:
                yield (
                    ElementType.PAGE_BREAK,
                    ParsedParagraph(
                        text=f"[Section {section_idx}, Para {para_idx}] PAGE_BREAK",
                        paragraph=paragraph,
                    ),
                )

            char_shape, char_shapes_list = _build_char_shape(paragraph, hwp.char_shapes)
            yield (
                ElementType.PARAGRAPH,
                ParsedParagraph(
                    text=paragraph.to_string().strip(),
                    paragraph=paragraph,
                    char_shape=char_shape,
                    char_shapes=char_shapes_list,
                ),
            )

            for char in paragraph.chars:
                if char.char_type == CharType.EXTENDED_CONTROL:
                    control_id = _get_control_id(char.control_data)
                    gen = _yield_extended_control(
                        char.code, char.control_data, control_id, table_counter, all_table_metadata
                    )
                    for item in gen:
                        if isinstance(item[1], ParsedTable) and item[0] == ElementType.TABLE:
                            table_counter = item[1].table_index or table_counter
                        yield item

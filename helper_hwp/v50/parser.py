"""
HWP 문서 파서 (고수준 API)

이 모듈은 한글(HWP) 문서 파일 형식 5.0 스펙을 참고하여 문서 구조(Section, Paragraph,
컨트롤 등)를 Pythonic하게 접근할 수 있도록 래핑한 고수준 API를 제공합니다.

참고:
- "한글문서파일형식_5.0_revision1.3.txt" (프로젝트 docs/) — HWP 5.0 스펙
  주요 참조 항목:
    * 본문(BodyText) / Section 스트림(표 5)
    * 문단 헤더(HWPTAG_PARA_HEADER) 및 문단 내 제어문자(표 58, 4.3.1 ~ 4.3.3)
    * 제어 문자 종류: char / inline control / extended control (본문 설명)
    * 컨트롤 헤더(HWPTAG_CTRL_HEADER)와 컨트롤 데이터 매핑(4.3.6)
    * 표(Table) 메타데이터: Section.table_metadata 사용(본문/스펙 참조)

설계 노트 (요약)
- 문단 내 제어문자: 코드 0-31 영역을 특수용도로 사용. (HWP 스펙 4.3)
  - Inline Control: 별도 오브젝트 포인터 미사용, size=8 (예: 쪽 번호)
  - Extended Control: 별도 오브젝트를 가리키는 확장 제어, size=8 (예: 표, 그림)
- 본 구현은 문단 수준에서 다음을 제공:
  - Paragraph 단위 텍스트/글자모양 추출 (ParsedParagraph)
  - Section 레벨의 테이블 메타데이터를 이용한 표(ParsedTable) 매핑
  - iter_tags()로 SEQUENTIAL / STRUCTURED 순회 지원

주의
- 주석/문서화만 추가했으며 코드 동작은 변경하지 않았습니다.
"""

import os
import struct
from typing import List, Optional, Union

from .char_paragraph import CharType, Paragraph
from .constants import (
    ControlID,
    ElementType,
    ExtendedControlCode,
    IterMode,
    ParagraphConstants,
)
from .document_structure import CharShapeInfo, HwpFile, Section
from .models import Version
from .parsed_elements import ParsedPage, ParsedParagraph, ParsedTable


class HwpDocument:
    """
    HWP 문서 - 고수준 Pythonic API

    이 클래스는 HwpFile 객체를 래핑하여 문서 요소(문단, 표, 페이지 구분 등)를
    쉽게 순회하고 추출할 수 있도록 합니다.

    주요 기능:
    - pages: 페이지 단위로 문단을 그룹화 (문단의 is_page_break 플래그 사용)
    - get_elements_by_type: ElementType 기반 요소 검색 (문단/표/쪽나누기 등)
    - iter_tags: 제너레이터 형태의 문서 태그 순회 (SEQUENTIAL / STRUCTURED)
    - to_text: 문서 전체 텍스트 추출

    구현 세부:
    - 글자 모양(char_shape) 추출은 paragraph.char_shape_ids(범위별 모양) 또는
      paragraph.char_shape_id(단일 모양)을 기준으로 하며, 여러 글자모양이 존재할 경우
      '최대(font_size 기준) 우선'으로 대표 값을 선택합니다. (스펙: DocInfo 내 CHAR_SHAPE)
    - 표(Table)는 본문(Section) 레벨의 table_metadata에서 상세 정보를 참조하여
      확장 제어(EXTENDED_CONTROL)로 나타나는 위치 기반 제어와 매핑합니다.
    """

    def __init__(self, file_path: str, iter_mode: IterMode = IterMode.SEQUENTIAL):
        """
        HWP 파일 로드

        Args:
            file_path: HWP 파일 경로
            iter_mode: 순회 모드 (SEQUENTIAL: 문서 출현 순서, STRUCTURED: 계층 구조)
        """
        self._hwp = HwpFile.from_file(file_path)
        self.file_path = file_path
        self.iter_mode = iter_mode

    @property
    def compressed(self) -> bool:
        """압축 여부"""
        return self._hwp.header.flags.compressed

    @property
    def encrypted(self) -> bool:
        """암호화 여부"""
        return self._hwp.header.flags.encrypted

    @property
    def pages(self) -> List[ParsedPage]:
        """페이지별로 그룹화된 문단 리스트

        동작:
        - 섹션을 순회하면서 문단을 누적
        - paragraph.is_page_break가 True이면 현재 페이지를 종료하고 다음 페이지로 이동
        - 각 문단에 대해 글자 모양 정보를 요약하여 ParsedParagraph로 반환
        """
        pages = []
        current_page_paragraphs = []
        page_number = 1

        for section in self.sections:
            for paragraph in section.paragraphs:
                para_text = paragraph.to_string().strip()
                # 빈 문단도 포함 (테이블 셀 구조 보존)
                # 글자 모양 정보 추출 (max 기준)
                char_shape = None
                char_shapes_list = []

                if paragraph.char_shape_ids:
                    all_shapes = []
                    for pos, shape_id in paragraph.char_shape_ids:
                        shape = self._hwp.char_shapes.get(shape_id)
                        if shape:
                            all_shapes.append(shape)
                            char_shapes_list.append((pos, shape))

                    if all_shapes:
                        # 여러 글자모양이 존재하면 대표값을 선택 (스펙/문서 정보 기반)
                        max_font_size = max(s.font_size for s in all_shapes)
                        max_expansion = max(s.expansion for s in all_shapes)
                        any_bold = any(s.bold for s in all_shapes)
                        any_italic = any(s.italic for s in all_shapes)
                        any_underline = any(s.underline for s in all_shapes)
                        char_shape = CharShapeInfo(
                            font_size=max_font_size,
                            font_id=all_shapes[0].font_id,
                            bold=any_bold,
                            italic=any_italic,
                            underline=any_underline,
                            expansion=max_expansion,
                            spacing=all_shapes[0].spacing,
                            color=all_shapes[0].color,
                        )
                elif paragraph.char_shape_id is not None:
                    # 단일 글자 모양 참조
                    char_shape = self._hwp.char_shapes.get(paragraph.char_shape_id)
                    if char_shape:
                        char_shapes_list = [(0, char_shape)]

                parsed_para = ParsedParagraph(
                    text=para_text,
                    paragraph=paragraph,
                    char_shape=char_shape,
                    char_shapes=char_shapes_list,
                )
                current_page_paragraphs.append(parsed_para)

                # 페이지 구분 체크 (쪽 나누기)
                # 스펙: 문단 내 페이지 제어는 인라인/확장 제어 또는 문단 속성으로 표현될 수 있음
                if paragraph.is_page_break:
                    if current_page_paragraphs:
                        pages.append(
                            ParsedPage(page_number=page_number, paragraphs=current_page_paragraphs)
                        )
                        current_page_paragraphs = []
                        page_number += 1

        # 마지막 페이지 추가
        if current_page_paragraphs:
            pages.append(ParsedPage(page_number=page_number, paragraphs=current_page_paragraphs))

        return pages

    @property
    def sections(self) -> List[Section]:
        """문서 섹션 리스트"""
        return self._hwp.body.sections

    @property
    def tags(self):
        """iter_tags()의 간편 접근 (기본 모드 사용)"""
        return self.iter_tags()

    @property
    def version(self) -> Version:
        """문서 버전"""
        return self._hwp.header.version

    def get_elements_by_type(self, element_type: Union[ElementType, str]) -> List:
        """
        문서 내 특정 타입의 요소를 검색 (HWP 5.0 스펙 기반)

        설명:
        - element_type이 'paragraph'인 경우 문단 단위로 순회하여 ParsedParagraph 리스트 반환
        - 'table'인 경우 Section.table_metadata를 사용하여 문서에 저장된 테이블 메타데이터를 읽어 반환
        - 'page_break'는 paragraph.is_page_break 기반으로 검사

        주의:
        - 표(Table)는 확장 제어(문단 내 EXTENDED_CONTROL)로도 존재할 수 있으며,
          본 메서드는 문서에 저장된 메타데이터 중심으로 결과를 구성합니다.

        Args:
            element_type: 검색할 요소 타입
                - ElementType.PARAGRAPH 또는 'paragraph': 문단 (HWPTAG_PARA_HEADER)
                - ElementType.TABLE 또는 'table': 표 (HWPTAG_TABLE)
                - ElementType.PAGE_BREAK 또는 'page_break': 페이지 구분 (쪽 나누기)
                - ElementType.PICTURE 또는 'picture': 그림
                - ElementType.EQUATION 또는 'equation': 수식 (미구현)
                - ElementType.FOOTNOTE 또는 'footnote': 각주 (미구현)
                - ElementType.ENDNOTE 또는 'endnote': 미주 (미구현)
                - ElementType.HEADER 또는 'header': 머리글 (미구현)
                - ElementType.FOOTER 또는 'footer': 바닥글 (미구현)
                - ElementType.CAPTION 또는 'caption': 캡션 (미구현)

        Returns:
            검색된 요소 리스트

        Examples:
            >>> doc.get_elements_by_type(ElementType.PARAGRAPH)
            >>> doc.get_elements_by_type('paragraph')  # 하위 호환
            >>> doc.get_elements_by_type(ElementType.PAGE_BREAK)  # 페이지 구분자 검색
        """
        # 문자열 입력 시 Enum으로 변환
        if isinstance(element_type, str):
            element_type = ElementType.from_string(element_type)

        results = []

        if element_type == ElementType.PARAGRAPH:
            # 모든 문단 검색
            for section in self.sections:
                for paragraph in section.paragraphs:
                    para_text = paragraph.to_string().strip()
                    # 빈 문단도 포함 (테이블 셀 구조 보존)
                    # 글자 모양 정보 추출 (max 기준)
                    char_shape = None
                    char_shapes_list = []

                    if paragraph.char_shape_ids:
                        all_shapes = []
                        for pos, shape_id in paragraph.char_shape_ids:
                            shape = self._hwp.char_shapes.get(shape_id)
                            if shape:
                                all_shapes.append(shape)
                                char_shapes_list.append((pos, shape))

                        if all_shapes:
                            max_font_size = max(s.font_size for s in all_shapes)
                            max_expansion = max(s.expansion for s in all_shapes)
                            any_bold = any(s.bold for s in all_shapes)
                            any_italic = any(s.italic for s in all_shapes)
                            any_underline = any(s.underline for s in all_shapes)
                            char_shape = CharShapeInfo(
                                font_size=max_font_size,
                                font_id=all_shapes[0].font_id,
                                bold=any_bold,
                                italic=any_italic,
                                underline=any_underline,
                                expansion=max_expansion,
                                spacing=all_shapes[0].spacing,
                                color=all_shapes[0].color,
                            )
                    elif paragraph.char_shape_id is not None:
                        char_shape = self._hwp.char_shapes.get(paragraph.char_shape_id)
                        if char_shape:
                            char_shapes_list = [(0, char_shape)]

                    results.append(
                        ParsedParagraph(
                            text=para_text,
                            paragraph=paragraph,
                            char_shape=char_shape,
                            char_shapes=char_shapes_list,
                        )
                    )

        elif element_type == ElementType.TABLE:
            # 테이블 검색 (table_metadata 직접 사용)
            # 스펙: Section.stream의 HWPTAG_TABLE / 컨트롤 헤더와 연계된 표 객체 정보
            table_counter = 0
            for section_idx, section in enumerate(self.sections):
                for table_idx, info in enumerate(section.table_metadata):
                    # section.table_metadata는 본 구현의 내부 표현(스펙의 표 메타데이터를 파싱한 결과)
                    if info.get("ctrl_id") == ControlID.TABLE:
                        table_counter += 1
                        table = ParsedTable(
                            code=ExtendedControlCode.TABLE,
                            data=None,
                            control_id=info.get("ctrl_id"),
                            x=info.get("x"),
                            y=info.get("y"),
                            width=info.get("width"),
                            height=info.get("height"),
                            margin_left=info.get("margin_left"),
                            margin_right=info.get("margin_right"),
                            margin_top=info.get("margin_top"),
                            margin_bottom=info.get("margin_bottom"),
                            rows=info.get("rows"),
                            cols=info.get("cols"),
                            cell_count=(
                                info.get("cell_para_counts", [])[-1]
                                if info.get("cell_para_counts")
                                else None
                            ),
                            cell_para_counts=info.get("cell_para_counts"),
                            cell_spacing=info.get("cell_spacing"),
                            row_sizes=info.get("row_sizes"),
                            cell_widths=info.get("cell_widths"),
                            cell_heights=info.get("cell_heights"),
                            cell_colspans=info.get("cell_colspans"),
                            cell_rowspans=info.get("cell_rowspans"),
                            table_index=table_counter,
                        )
                        results.append(table)

        elif element_type == ElementType.PAGE_BREAK:
            # 페이지 구분자 검색 (쪽 나누기)
            for section in self.sections:
                for paragraph in section.paragraphs:
                    if paragraph.is_page_break:
                        results.append(
                            ParsedParagraph(text=paragraph.to_string().strip(), paragraph=paragraph)
                        )

        else:
            # 다른 타입은 아직 미구현
            pass

        return results

    def iter_tags(self, mode: Optional[IterMode] = None):
        """
        문서 요소를 순회하는 제너레이터 (속도 우선)

        mode:
          - IterMode.SEQUENTIAL: 문서 출현 순서 기반 순회 (빠름, 기본)
          - IterMode.STRUCTURED: Section → Paragraph → Char 계층 구조로 상세 순회

        반환:
          (ElementType, ParsedElement) 튜플을 순차적으로 yield

        구현 참고:
        - SEQUENTIAL 모드는 문단 단위로 먼저 yield하고, 문단 내부의 문자(char)들을 검사하여
          인라인/확장 제어를 추가적으로 yield합니다.
        - STRUCTURED 모드는 구조적(계층적) 순회를 수행하여 각 섹션/문단/문자 위치 정보를 유지합니다.

        Examples:
            >>> for element_type, element in hwp.iter_tags():
            ...     if element_type == ElementType.PARAGRAPH:
            ...         print(element.text)
            ...     elif element_type == ElementType.TABLE:
            ...         print(f"표: {element.code}")
        """
        mode = mode or self.iter_mode

        if mode == IterMode.SEQUENTIAL:
            yield from self._iter_sequential()
        else:
            yield from self._iter_structured()

    def _iter_sequential(self):
        """SEQUENTIAL 모드 위임 (iterators.iter_sequential)"""
        from .iterators import iter_sequential

        yield from iter_sequential(self._hwp)

    def _iter_structured(self):
        """STRUCTURED 모드 위임 (iterators.iter_structured)"""
        from .iterators import iter_structured

        yield from iter_structured(self._hwp)

    def to_text(self) -> str:
        """전체 텍스트 추출"""
        return self._hwp.to_text()

    def __enter__(self):
        """Context Manager 진입"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context Manager 종료"""
        # 필요시 리소스 정리
        return False

    def __repr__(self):
        return f"HwpDocument(file='{self.file_path}', version={self.version}, sections={len(self.sections)})"


def open_hwp(file_path: str, iter_mode: IterMode = IterMode.SEQUENTIAL) -> HwpDocument:
    """
    HWP 파일을 여는 Pythonic API

    반환되는 HwpDocument는 with 문으로 사용 가능하며 내부적으로 HwpFile.from_file을 호출합니다.
    Context Manager를 반환하여 with 문으로 사용할 수 있습니다.

    사용 예:
        # 기본 모드 (SEQUENTIAL, 속도 우선)
        with open_hwp('document.hwp') as doc:
            for element_type, element in doc.tags:
                if element_type == ElementType.PARAGRAPH:
                    print(element.text)

        # STRUCTURED 모드 (계층 구조)
        with open_hwp('document.hwp', IterMode.STRUCTURED) as doc:
            for element_type, element in doc.iter_tags():
                print(element_type, element)

    Args:
        file_path: HWP 파일 경로
        iter_mode: 순회 모드 (기본: SEQUENTIAL)

    Returns:
        HwpDocument 인스턴스
    """
    return HwpDocument(file_path, iter_mode)

"""
HWP 97 (V3.00) 문서 파서 (고수준 API)

이 모듈은 HWP 97 (V3.00) 파일을 Pythonic하게 접근할 수 있도록
래핑한 고수준 API를 제공합니다.

참고: 한글문서파일형식97분석보고서

외부 인터페이스 통일화:
    iter_tags() 는 (ElementType, element) 튜플을 yield 합니다.
    ElementType 은 helper_hwp.constants 에서 공유되는 통합 Enum 입니다.

    내부 파싱 태그 → 외부 ElementType 매핑:
        SpecialCharCode.BOX (10) + BoxType.TABLE (0) -> ElementType.TABLE
        SpecialCharCode.PICTURE (11)                 -> ElementType.PICTURE
        ParaFlag.PAGE_BREAK (0x02)                   -> ElementType.PAGE_BREAK
        (일반 문단)                                   -> ElementType.PARAGRAPH
"""

import contextlib
from contextlib import contextmanager
from typing import Generator, Iterator, List, Optional, Tuple, Union

from helper_hwp.constants import ElementType, IterMode

from .converters import convert_to_markdown, convert_to_text
from .document_structure import Hwp97File
from .parsed_elements import ParsedParagraph, ParsedTable


class Hwp97Document:
    """HWP 97 (V3.00) 문서 - 고수준 Pythonic API

    v50의 HwpDocument, owpml의 HwpxDocument 와 동일한 외부 인터페이스를 제공합니다.

    주요 기능:
    - iter_tags(mode): (ElementType, element) 튜플 제너레이터 (통합 API)
    - tags: iter_tags() 의 간편 접근
    - to_text: 문서 전체 텍스트 추출
    - to_markdown: 마크다운 변환
    - paragraphs: 문단 리스트 (ParsedParagraph)
    - doc_info, doc_summary: 문서 메타데이터 접근

    내부 파싱 태그 → 외부 ElementType 변환:
        SpecialCharCode.BOX (10) + BoxType.TABLE (0) -> ElementType.TABLE
        SpecialCharCode.PICTURE (11)                 -> ElementType.PICTURE
        ParsedParagraph.is_page_break                -> ElementType.PAGE_BREAK
        (일반 문단)                                   -> ElementType.PARAGRAPH
    """

    def __init__(self, file_path: str, iter_mode: IterMode = IterMode.SEQUENTIAL) -> None:
        """HWP 97 (V3.00) 파일 로드.

        Args:
            file_path: HWP 파일 경로
            iter_mode: 순회 모드 (기본: SEQUENTIAL)
        """
        self._hwp = Hwp97File.from_file(file_path)
        self.file_path = file_path
        self.iter_mode = iter_mode

    @property
    def doc_info(self):
        """문서 정보 (DocumentInfo)"""
        return self._hwp.doc_info

    @property
    def doc_summary(self):
        """문서 요약 (DocumentSummary)"""
        return self._hwp.doc_summary

    @property
    def compressed(self) -> bool:
        """압축 여부"""
        return self._hwp.doc_info.compressed

    @property
    def paragraphs(self) -> List[ParsedParagraph]:
        """문서 본문 문단 리스트"""
        return self._hwp.paragraphs

    @property
    def font_names(self) -> List[List[str]]:
        """글꼴 이름 (7개 언어)"""
        return self._hwp.font_names

    @property
    def styles(self):
        """스타일 리스트"""
        return self._hwp.styles

    @property
    def tags(self) -> Iterator[Tuple[ElementType, Union[ParsedParagraph, ParsedTable]]]:
        """iter_tags() 의 간편 접근 (기본 모드)"""
        return self.iter_tags()

    def iter_tags(
        self, mode: Optional[IterMode] = None
    ) -> Generator[Tuple[ElementType, Union[ParsedParagraph, ParsedTable]], None, None]:
        """문서 요소를 순회하는 제너레이터.

        v50 HwpDocument.iter_tags() / owpml HwpxDocument.iter_tags() 와
        동일한 외부 인터페이스를 제공합니다.

        내부적으로 ParsedParagraph.char_shape 의 BoxType / is_page_break 플래그를
        읽어 적절한 ElementType 으로 변환하여 yield 합니다.

        Args:
            mode: IterMode.SEQUENTIAL (기본) 또는 IterMode.STRUCTURED

        Yields:
            (ElementType, element) 튜플

        Examples:
            >>> with open_hwp97("test.hwp") as doc:
            ...     for etype, elem in doc.iter_tags():
            ...         if etype == ElementType.PARAGRAPH:
            ...             print(elem.text)
            ...         elif etype == ElementType.TABLE:
            ...             print(f"표: {elem.rows}x{elem.cols}")
        """
        mode = mode or self.iter_mode
        if mode == IterMode.SEQUENTIAL:
            yield from self._iter_sequential()
        else:
            yield from self._iter_structured()

    def _iter_sequential(
        self,
    ) -> Generator[Tuple[ElementType, Union[ParsedParagraph, ParsedTable]], None, None]:
        """SEQUENTIAL 모드: 문서 출현 순서로 (ElementType, element) yield.

        내부 파싱 결과(ParsedParagraph / ParsedTable)를 외부 ElementType 으로 변환합니다.
        - ParsedParagraph.is_page_break=True  -> PAGE_BREAK 먼저, 이후 PARAGRAPH
        - ParsedTable (box_type=0)            -> TABLE
        - ParsedTable (box_type=2)            -> EQUATION
        - ParsedTable (box_type=1,3)          -> SHAPE (텍스트박스/버튼)
        - ParsedParagraph (일반)              -> PARAGRAPH
        """
        for item in self._hwp.paragraphs:
            if isinstance(item, ParsedTable):
                etype = _box_type_to_element(item.box_type)
                yield (etype, item)
            elif isinstance(item, ParsedParagraph):
                if item.is_page_break:
                    yield (ElementType.PAGE_BREAK, item)
                yield (ElementType.PARAGRAPH, item)

    def _iter_structured(
        self,
    ) -> Generator[Tuple[ElementType, Union[ParsedParagraph, ParsedTable]], None, None]:
        """STRUCTURED 모드: 섹션 구분 없이 순차와 동일 (v97은 단일 섹션 구조).

        v97은 섹션 개념이 없으므로 SEQUENTIAL 과 동일하게 동작합니다.
        """
        yield from self._iter_sequential()

    def to_text(self) -> str:
        """문서 전체 텍스트 반환.

        Returns:
            줄바꿈으로 문단 구분된 문자열
        """
        return convert_to_text(self._hwp)

    def to_markdown(self) -> str:
        """문서를 마크다운으로 변환.

        Returns:
            마크다운 문자열
        """
        return convert_to_markdown(self._hwp)

    def iter_paragraphs(self) -> Generator[ParsedParagraph, None, None]:
        """문단 이터레이터 (하위 호환)"""
        yield from self._hwp.paragraphs

    def __enter__(self) -> "Hwp97Document":
        return self

    def __exit__(self, *args) -> None:
        pass

    def __repr__(self) -> str:
        return f"Hwp97Document(file_path='{self.file_path}', paragraphs={len(self.paragraphs)})"


# ---------------------------------------------------------------------------
# 내부 헬퍼: BoxType → ElementType 변환
# ---------------------------------------------------------------------------


def _box_type_to_element(box_type: int) -> ElementType:
    """v97 BoxType (내부) → ElementType (외부 인터페이스) 변환.

    Args:
        box_type: ParsedTable.box_type (0=표, 1=텍스트박스, 2=수식, 3=버튼)

    Returns:
        대응하는 ElementType
    """
    _MAP = {
        0: ElementType.TABLE,
        1: ElementType.SHAPE,  # 텍스트박스
        2: ElementType.EQUATION,  # 수식
        3: ElementType.SHAPE,  # 버튼
    }
    return _MAP.get(box_type, ElementType.SHAPE)


# ---------------------------------------------------------------------------
# 편의 함수
# ---------------------------------------------------------------------------


@contextmanager
def open_hwp97(file_path: str, iter_mode: IterMode = IterMode.SEQUENTIAL):
    """HWP 97 (V3.00) 파일을 컨텍스트 매니저로 열기.

    Args:
        file_path: HWP 파일 경로
        iter_mode: 순회 모드 (기본: SEQUENTIAL)

    Yields:
        Hwp97Document 인스턴스

    Examples:
        >>> with open_hwp97("test10.hwp") as doc:
        ...     for etype, elem in doc.iter_tags():
        ...         if etype == ElementType.PARAGRAPH:
        ...             print(elem.text)
    """
    doc = Hwp97Document(file_path, iter_mode=iter_mode)
    yield doc

"""
HwpxDocument - HWPX/OWPML 고수준 파서 API

v50의 HwpDocument와 동일한 인터페이스를 제공합니다.
HWPX(OWPML) 파일을 열고 문단·표·페이지 단위로 순회하거나
텍스트/마크다운으로 변환합니다.

참고:
- OWPML 스펙: HWPX 파일은 ZIP 패키지 내 XML 파일들의 묶음
- 본 구현은 Contents/section*.xml 기반 순회를 제공합니다.
"""

import contextlib
import logging
from pathlib import Path
from typing import Generator, Iterator, List, Optional, Tuple, Union

from .constants import ElementType, IterMode
from .document_structure import HwpxFile, RawParagraph, RawSection, RawTable
from .models import HwpxVersion
from .parsed_elements import ParsedPage, ParsedParagraph, ParsedTable

logger = logging.getLogger(__name__)


class HwpxDocument:
    """
    HWPX 문서 고수준 API

    v50의 HwpDocument와 동일한 인터페이스를 유지합니다.

    주요 기능:
    - iter_tags: (ElementType, element) 튜플 제너레이터
    - to_text: 전체 텍스트 추출
    - to_markdown: 마크다운 변환 (표 포함)
    - pages: 페이지 단위 문단 그룹

    사용법:
        with open_hwpx("doc.hwpx") as doc:
            for etype, elem in doc.iter_tags():
                if etype == ElementType.PARAGRAPH:
                    print(elem.text)
    """

    def __init__(self, file_path: str, iter_mode: IterMode = IterMode.SEQUENTIAL):
        self._hwpx = HwpxFile.from_file(file_path)
        self.file_path = file_path
        self.iter_mode = iter_mode

    # ------------------------------------------------------------------
    # 기본 속성
    # ------------------------------------------------------------------

    @property
    def version(self) -> HwpxVersion:
        return self._hwpx.version

    @property
    def compressed(self) -> bool:
        """HWPX는 항상 ZIP 압축"""
        return True

    @property
    def encrypted(self) -> bool:
        return self._hwpx.encrypted

    @property
    def sections(self) -> List[RawSection]:
        return self._hwpx.sections

    # ------------------------------------------------------------------
    # 페이지 단위 접근
    # ------------------------------------------------------------------

    @property
    def pages(self) -> List[ParsedPage]:
        """
        페이지 단위로 그룹화된 문단 리스트.

        HWPX에는 명시적 쪽 나누기 요소가 없으므로
        현재 구현은 섹션 경계를 페이지 구분으로 사용합니다.
        """
        pages: List[ParsedPage] = []
        page_number = 1
        for section in self.sections:
            paragraphs = [
                ParsedParagraph(text=p.text, raw=p)
                for p in section.paragraphs
                if p.runs  # 빈 placeholder 제외
            ]
            if paragraphs:
                pages.append(ParsedPage(page_number=page_number, paragraphs=paragraphs))
                page_number += 1
        return pages

    # ------------------------------------------------------------------
    # iter_tags
    # ------------------------------------------------------------------

    def iter_tags(
        self, mode: Optional[IterMode] = None
    ) -> Generator[Tuple[ElementType, Union[ParsedParagraph, ParsedTable]], None, None]:
        """
        문서 요소를 순회하는 제너레이터.

        Args:
            mode: IterMode.SEQUENTIAL(기본) 또는 IterMode.STRUCTURED

        Yields:
            (ElementType, element) 튜플
        """
        mode = mode or self.iter_mode
        if mode == IterMode.SEQUENTIAL:
            yield from self._iter_sequential()
        else:
            yield from self._iter_structured()

    def _iter_sequential(self) -> Iterator[Tuple[ElementType, Union[ParsedParagraph, ParsedTable]]]:
        """문서 출현 순서 기반 순회"""
        table_iter: Iterator[RawTable]

        for section in self.sections:
            # 섹션 내 표 목록을 순서대로 소비
            table_queue = list(section.tables)
            table_cursor = 0

            for raw_para in section.paragraphs:
                if not raw_para.runs:
                    # 빈 placeholder → 다음 표 yield
                    if table_cursor < len(table_queue):
                        raw_tbl = table_queue[table_cursor]
                        table_cursor += 1
                        yield (
                            ElementType.TABLE,
                            ParsedTable(
                                raw=raw_tbl,
                                rows=raw_tbl.rows,
                                cols=raw_tbl.cols,
                            ),
                        )
                else:
                    yield (
                        ElementType.PARAGRAPH,
                        ParsedParagraph(text=raw_para.text, raw=raw_para),
                    )

    def _iter_structured(self) -> Iterator[Tuple[ElementType, Union[ParsedParagraph, ParsedTable]]]:
        """계층 구조 기반 순회 (섹션 → 문단/표)"""
        for section in self.sections:
            table_queue = list(section.tables)
            table_cursor = 0

            yield (
                ElementType.SECTION,
                ParsedParagraph(
                    text=f"[Section {section.index}]",
                    raw=RawParagraph(),
                ),
            )
            for raw_para in section.paragraphs:
                if not raw_para.runs:
                    if table_cursor < len(table_queue):
                        raw_tbl = table_queue[table_cursor]
                        table_cursor += 1
                        yield (
                            ElementType.TABLE,
                            ParsedTable(
                                raw=raw_tbl,
                                rows=raw_tbl.rows,
                                cols=raw_tbl.cols,
                            ),
                        )
                else:
                    yield (
                        ElementType.PARAGRAPH,
                        ParsedParagraph(text=raw_para.text, raw=raw_para),
                    )

    # ------------------------------------------------------------------
    # 텍스트 / 마크다운 변환
    # ------------------------------------------------------------------

    def to_text(self) -> str:
        """전체 텍스트 추출 (표는 v50과 동일하게 탭 구분 행 텍스트)"""
        lines: List[str] = []
        for etype, elem in self.iter_tags():
            if etype == ElementType.PARAGRAPH:
                if elem.text:
                    lines.append(elem.text)
            elif etype == ElementType.TABLE:
                t = elem.to_text()
                if t:
                    lines.append(t)
        return "\n".join(lines)

    def to_markdown(self) -> str:
        """마크다운 변환 (표는 v50과 동일하게 마크다운 표 형식)"""
        parts: List[str] = []
        for etype, elem in self.iter_tags():
            if etype == ElementType.PARAGRAPH:
                if elem.text:
                    parts.append(elem.text)
            elif etype == ElementType.TABLE:
                md = elem.to_markdown()
                if md:
                    parts.append(md)
        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "HwpxDocument":
        return self

    def __exit__(self, *_) -> None:
        pass


# ---------------------------------------------------------------------------
# 공개 API 함수 (v50의 open_hwp, hwp_to_txt, hwp_to_markdown 대응)
# ---------------------------------------------------------------------------


def open_hwpx(file_path: str, iter_mode: IterMode = IterMode.SEQUENTIAL) -> HwpxDocument:
    """
    HWPX 파일을 열고 HwpxDocument 반환.

    Args:
        file_path: HWPX 파일 경로
        iter_mode: 순회 모드 (기본: SEQUENTIAL)

    Returns:
        HwpxDocument 인스턴스 (context manager 지원)

    Example:
        with open_hwpx("doc.hwpx") as doc:
            print(doc.to_text())
    """
    return HwpxDocument(file_path, iter_mode=iter_mode)

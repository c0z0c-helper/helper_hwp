"""
파싱된 요소 클래스 (OWPML/HWPX)

v50의 parsed_elements.py와 동일한 인터페이스를 유지합니다.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from .document_structure import RawParagraph, RawTable


@dataclass
class ParsedParagraph:
    """
    파싱된 문단

    Attributes:
        text: 문단 텍스트 내용
        raw: 원시 RawParagraph 객체
        is_page_first_line: 페이지 첫 줄 여부
    """

    text: str
    raw: RawParagraph
    is_page_first_line: bool = False

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"ParsedParagraph(text='{preview}')"


@dataclass
class ParsedTable:
    """
    파싱된 표

    Attributes:
        raw: 원시 RawTable 객체
        rows: 행 수
        cols: 열 수
    """

    raw: RawTable
    rows: int = 0
    cols: int = 0

    def to_markdown(self) -> str:
        """마크다운 표 형식으로 변환"""
        return self.raw.to_markdown()

    def to_text(self) -> str:
        """탭 구분 텍스트로 변환"""
        return self.raw.to_text()

    def __repr__(self) -> str:
        return f"ParsedTable(rows={self.rows}, cols={self.cols})"


@dataclass
class ParsedPage:
    """
    파싱된 페이지

    Attributes:
        page_number: 페이지 번호 (1-based)
        paragraphs: 해당 페이지의 문단 리스트
    """

    page_number: int
    paragraphs: List[ParsedParagraph] = field(default_factory=list)

    @property
    def text(self) -> str:
        """페이지 전체 텍스트"""
        return "\n".join(p.text for p in self.paragraphs if p.text)

    def __repr__(self) -> str:
        return f"ParsedPage(page={self.page_number}, paragraphs={len(self.paragraphs)})"

"""
HWP 97 (V3.00) 파싱된 요소 클래스

한글문서파일형식97분석보고서 참고
"""

from dataclasses import dataclass, field
from typing import List, Optional

from .models import CharShape


# ---------------------------------------------------------------------------
# 파싱된 문단
# ---------------------------------------------------------------------------


@dataclass
class ParsedParagraph:
    """파싱된 HWP 97 (V3.00) 문단

    Attributes:
        text: 문단 텍스트 (EUC-KR 디코딩 결과)
        char_shape: 문단 대표 글자 서식
        char_shapes: 글자별 서식 리스트 [(char_index, CharShape)]
        is_page_break: 페이지 나누기 여부
        is_column_break: 단 나누기 여부
        style_index: 스타일 인덱스
    """

    text: str
    char_shape: Optional[CharShape] = None
    char_shapes: List[tuple] = field(default_factory=list)  # [(char_index, CharShape)]
    is_page_break: bool = False
    is_column_break: bool = False
    style_index: int = 0

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        preview = self.text[:50] + "..." if len(self.text) > 50 else self.text
        return f"ParsedParagraph(text='{preview}')"


# ---------------------------------------------------------------------------
# 테이블 셀
# ---------------------------------------------------------------------------


@dataclass
class TableCell:
    """HWP 97 (V3.00) 테이블 셀

    Attributes:
        row: 행 번호 (0-based)
        col: 열 번호 (0-based)
        paragraphs: 셀 내부 문단 리스트
    """

    row: int
    col: int
    paragraphs: List[ParsedParagraph] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(p.text for p in self.paragraphs)

    def __repr__(self) -> str:
        return f"TableCell(row={self.row}, col={self.col}, text='{self.text[:20]}')"


# ---------------------------------------------------------------------------
# 파싱된 테이블
# ---------------------------------------------------------------------------


@dataclass
class ParsedTable:
    """파싱된 HWP 97 (V3.00) 표/텍스트박스/수식/버튼

    스펙: Section 10.6 (특수 문자 코드 10)

    Attributes:
        box_type: 박스 종류 (0=표, 1=텍스트박스, 2=수식, 3=버튼)
        rows: 행 개수
        cols: 열 개수
        cells: 셀 리스트
        x: 가로 위치 (shunit)
        y: 세로 위치 (shunit)
        width: 너비
        height: 높이
        is_hyperlink: 하이퍼텍스트 여부
    """

    box_type: int = 0
    rows: int = 0
    cols: int = 0
    cells: List[TableCell] = field(default_factory=list)
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    is_hyperlink: bool = False

    @property
    def is_table(self) -> bool:
        return self.box_type == 0

    @property
    def cell_texts(self) -> List[List[str]]:
        """2D 배열 형태의 셀 텍스트 반환"""
        if not self.rows or not self.cols:
            return []
        grid: List[List[str]] = [[""] * self.cols for _ in range(self.rows)]
        for cell in self.cells:
            if cell.row < self.rows and cell.col < self.cols:
                grid[cell.row][cell.col] = cell.text
        return grid

    def __repr__(self) -> str:
        return f"ParsedTable(box_type={self.box_type}, rows={self.rows}, cols={self.cols})"


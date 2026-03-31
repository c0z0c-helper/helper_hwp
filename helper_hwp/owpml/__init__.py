"""
helper_hwp.owpml

HWPX(OWPML) 파일 파서 모듈.
HWPX 파일은 ZIP 기반 XML 패키지(OPC) 형식입니다.

주요 클래스 (Hwpx* alias):
    HwpxDocument   : HWPX 맸 문서 객체 (context manager 지원)
    HwpxParagraph  : 파싱된 문단 요소
    HwpxTable      : 파싱된 표 요소
    HwpxPage       : 파싱된 페이지 요소
    HwpxVersion    : HWPX 버전 정보
    HwpxHeader     : HWPX 헤더 정보
    HwpxFile       : ZIP 저수준 파일 구조

함수:
    open_hwpx(file_path) : HWPX 전용 문서 열기
"""

from .constants import ElementType, IterMode
from .document_structure import HwpxFile
from .models import BinItem, HwpxHeader, HwpxVersion
from .parsed_elements import ParsedPage, ParsedParagraph, ParsedTable
from .parser import (
    HwpxDocument,
    open_hwpx,
)

# ---------------------------------------------------------------------------
# 명확한 접두사 alias
# ---------------------------------------------------------------------------
HwpxParagraph = ParsedParagraph
HwpxTable = ParsedTable
HwpxPage = ParsedPage

__all__ = [
    # 상수
    "ElementType",
    "IterMode",
    # 모델
    "HwpxVersion",
    "HwpxHeader",
    "BinItem",
    "HwpxFile",
    # 파싱된 요소
    "HwpxParagraph",
    "HwpxTable",
    "HwpxPage",
    # 메인 API
    "HwpxDocument",
    "open_hwpx",
]

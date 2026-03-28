"""
helper_hwp.owpml

HWPX(OWPML) 파일 파서 모듈.
HWPX 파일은 ZIP 기반 XML 패키지(OPC) 형식입니다.
"""

from .constants import ElementType, IterMode
from .document_structure import HwpxFile
from .models import BinItem, HwpxHeader, HwpxVersion
from .parsed_elements import ParsedPage, ParsedParagraph, ParsedTable
from .parser import (
    HwpxDocument,
    open_hwpx,
)

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
    "ParsedParagraph",
    "ParsedTable",
    "ParsedPage",
    # 메인 API
    "HwpxDocument",
    "open_hwpx",
]

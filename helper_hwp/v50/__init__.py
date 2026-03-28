"""
helper_hwp.v50

HWP 5.x 포맷 파서 구현 모듈.
HWP (Hangul Word Processor) 파일 형식 5.0 스펙 기반 파싱 로직을 포함합니다.
"""

from .constants import ElementType, IterMode
from .document_structure import HwpFile
from .models import Header, Version
from .parsed_elements import ParsedPage, ParsedParagraph, ParsedTable
from .parser import (
    HwpDocument,
    open_hwp,
)
from .utils import hwpunit_to_cm, hwpunit_to_inch, hwpunit_to_px

__all__ = [
    # 상수
    "ElementType",
    "IterMode",
    # 모델
    "Version",
    "Header",
    "HwpFile",
    # 파싱된 요소
    "ParsedParagraph",
    "ParsedTable",
    "ParsedPage",
    # 메인 API
    "HwpDocument",
    "open_hwp",
    # 유틸리티
    "hwpunit_to_cm",
    "hwpunit_to_inch",
    "hwpunit_to_px",
]

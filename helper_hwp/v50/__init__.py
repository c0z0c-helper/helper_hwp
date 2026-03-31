"""
helper_hwp.v50

HWP 5.x 포맷 파서 구현 모듈.
HWP (Hangul Word Processor) 파일 형식 5.0 스펙 기반 파싱 로직을 포함합니다.

주요 클래스 (Hwp50* alias):
    Hwp50Document    : HWP 5.x 맸 문서 객체 (context manager 지원)
    Hwp50Paragraph   : 파싱된 문단 요소
    Hwp50Table       : 파싱된 표 요소
    Hwp50Page        : 파싱된 페이지 요소
    Hwp50Version     : 문서 버전 정보
    Hwp50Header      : 문서 헤더 정보
    Hwp50File        : CFB 저수준 파일 구조

함수:
    open_hwp50(file_path)        : HWP 5.x 전용 문서 열기
    hwp50_unit_to_cm(hwpunit)    : HWPUNIT -> cm 변환
    hwp50_unit_to_inch(hwpunit)  : HWPUNIT -> inch 변환
    hwp50_unit_to_px(hwpunit)    : HWPUNIT -> px 변환
"""

from .constants import ElementType, IterMode
from .document_structure import HwpFile
from .models import Header, Version
from .parsed_elements import ParsedPage, ParsedParagraph, ParsedTable
from .parser import HwpDocument
from .parser import open_hwp as open_hwp50
from .utils import hwpunit_to_cm, hwpunit_to_inch, hwpunit_to_px

# ---------------------------------------------------------------------------
# 명확한 접두사 alias
# ---------------------------------------------------------------------------
hwp50_unit_to_cm = hwpunit_to_cm
hwp50_unit_to_inch = hwpunit_to_inch
hwp50_unit_to_px = hwpunit_to_px

Hwp50Version = Version
Hwp50Header = Header
Hwp50File = HwpFile
Hwp50Paragraph = ParsedParagraph
Hwp50Table = ParsedTable
Hwp50Page = ParsedPage
Hwp50Document = HwpDocument

__all__ = [
    # 상수
    "ElementType",
    "IterMode",
    # 모델
    "Hwp50Version",
    "Hwp50Header",
    "Hwp50File",
    # 파싱된 요소
    "Hwp50Paragraph",
    "Hwp50Table",
    "Hwp50Page",
    # Document / 열기
    "Hwp50Document",
    "open_hwp50",
    # 단위 변환
    "hwp50_unit_to_cm",
    "hwp50_unit_to_inch",
    "hwp50_unit_to_px",
]

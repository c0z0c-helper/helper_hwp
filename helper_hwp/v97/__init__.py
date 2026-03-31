"""
helper_hwp.v97

HWP 97 (V3.00) 포맷 파서 구현 모듈.
한글문서파일형식97분석보고서 스펙 기반 파싱 로직을 포함합니다.

파일 구조 (순차 읽기):
  1. 파일 인식 정보 (30 bytes, 미압축)
  2. 문서 정보 (128 bytes, 미압축)
  3. 문서 요약 (1008 bytes, 미압축)
  4. 정보 블록 (가변, 미압축)
  5. 글꼴 이름 ~ 추가 정보 블록 (압축 또는 미압축)

주요 클래스 (Hwp97* alias):
    Hwp97Document      : HWP 97 맸 문서 객체 (context manager 지원)
    Hwp97Paragraph     : 파싱된 문단 요소
    Hwp97Table         : 파싱된 표 요소
    Hwp97FileHeader    : 파일 인식 정보 (30 bytes)
    Hwp97DocumentInfo  : 문서 정보 (128 bytes)

함수:
    open_hwp97(file_path)        : HWP 97 전용 문서 열기
    hwp97_unit_to_cm(hunit)      : HUNIT -> cm 변환
    hwp97_unit_to_inch(hunit)    : HUNIT -> inch 변환
    hwp97_unit_to_px(hunit)      : HUNIT -> px 변환
"""

from .constants import BoxType, SpecialCharCode
from .models import DocumentInfo, FileHeader
from .parsed_elements import ParsedParagraph, ParsedTable
from .parser import (
    Hwp97Document,
    open_hwp97,
)
from .utils import hunit_to_cm, hunit_to_inch, hunit_to_px

# ---------------------------------------------------------------------------
# 명확한 접두사 alias
# ---------------------------------------------------------------------------
hwp97_unit_to_cm = hunit_to_cm
hwp97_unit_to_inch = hunit_to_inch
hwp97_unit_to_px = hunit_to_px

Hwp97FileHeader = FileHeader
Hwp97DocumentInfo = DocumentInfo
Hwp97Paragraph = ParsedParagraph
Hwp97Table = ParsedTable

__all__ = [
    # 상수
    "SpecialCharCode",
    "BoxType",
    # 모델
    "Hwp97FileHeader",
    "Hwp97DocumentInfo",
    # 파싱된 요소
    "Hwp97Paragraph",
    "Hwp97Table",
    # 메인 API
    "Hwp97Document",
    "open_hwp97",
    # 단위 변환
    "hwp97_unit_to_cm",
    "hwp97_unit_to_inch",
    "hwp97_unit_to_px",
]

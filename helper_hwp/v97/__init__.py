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
"""

from .constants import BoxType, SpecialCharCode
from .models import DocumentInfo, FileHeader
from .parsed_elements import ParsedParagraph, ParsedTable
from .parser import (
    Hwp97Document,
    hwp97_to_markdown,
    hwp97_to_md,
    hwp97_to_txt,
    open_hwp97,
)
from .utils import hunit_to_cm, hunit_to_inch, hunit_to_px

__all__ = [
    # 상수
    "SpecialCharCode",
    "BoxType",
    # 모델
    "FileHeader",
    "DocumentInfo",
    # 파싱된 요소
    "ParsedParagraph",
    "ParsedTable",
    # 메인 API
    "Hwp97Document",
    "open_hwp97",
    "hwp97_to_txt",
    "hwp97_to_markdown",
    "hwp97_to_md",
    # 유틸리티
    "hunit_to_cm",
    "hunit_to_inch",
    "hunit_to_px",
]


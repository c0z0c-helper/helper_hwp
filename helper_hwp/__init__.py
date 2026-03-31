"""
HWP Parser for Python

HWP (Hangul Word Processor) 파일 파싱 라이브러리
CFB (Compound File Binary) 기반 HWP 5.x 포맷 및 HWPX(OWPML) 포맷 지원

주요 기능:
- HWP 5.x 파일 구조 분석 및 파싱 (v50 모듈)
- HWPX(OWPML) 파일 파싱 (owpml 모듈)
- HWP 97 (V3.00) 파일 파싱 (v97 모듈)
- 파일 포맷 자동 감지 후 적합한 파서 선택 (hwp_open)
- 텍스트, 표, 페이지 단위 추출
- Markdown, Plain Text 변환 지원
- 단위 변환 유틸리티 (HWPUNIT <-> cm/inch/px)

네이밍 규칙:
    hwp_*      : 포맷 자동 감지 공통 API (권장)
    hwp50_*    : HWP 5.x 전용 API
    hwp97_*    : HWP 97 전용 API
    Hwpx* / open_hwpx : HWPX 전용 API

클래스 네이밍 규칙:
    Hwp50Paragraph / Hwp50Table / Hwp50Page   : HWP 5.x 파싱된 요소
    Hwp97Paragraph / Hwp97Table               : HWP 97 파싱된 요소
    HwpxParagraph  / HwpxTable  / HwpxPage    : HWPX 파싱된 요소
    Hwp50Document / Hwp97Document / HwpxDocument : 버전별 Document 객체

외부 인터페이스 통일화:
    세 포맷(v50 / v97 / owpml) 모두 동일한 ElementType, IterMode 를 사용합니다.
    내부 파싱 태그(RecordTag, OwpmlTag, SpecialCharCode 등)와 외부 Enum 은 분리됩니다.

    내부 태그 -> 외부 ElementType 매핑 예시:
        v50  RecordTag.HWPTAG_TABLE (0x4D)         -> ElementType.TABLE
        v97  SpecialCharCode.BOX (10) + TABLE(0)   -> ElementType.TABLE
        owpml OwpmlTag.TBL ("tbl")                 -> ElementType.TABLE

기본 사용법:
    >>> from helper_hwp import hwp_open, hwp_to_txt, hwp_to_md
    >>> from helper_hwp import ElementType, IterMode
    >>>
    >>> # 포맷 자동 감지 (권장)
    >>> doc = hwp_open('example.hwp')   # or .hwp97 or .hwpx
    >>> for etype, elem in doc.iter_tags():
    ...     if etype == ElementType.PARAGRAPH:
    ...         print(elem.text)
    ...     elif etype == ElementType.TABLE:
    ...         print(f"표 {elem.rows}x{elem.cols}")
    >>>
    >>> text = hwp_to_txt('example.hwp')
    >>> md   = hwp_to_md('example.hwpx')
    >>>
    >>> # 버전 특화 클래스 사용 예시
    >>> from helper_hwp import Hwp50Paragraph, Hwp50Table
    >>> from helper_hwp import Hwp97Paragraph, HwpxParagraph
"""

import importlib.util
import os
import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parents[1]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

spec = importlib.util.spec_from_file_location(
    "requirements_rnac",
    os.path.join(os.path.dirname(__file__), "v50", "requirements_rnac.py"),
)
requirements_rnac = importlib.util.module_from_spec(spec)
spec.loader.exec_module(requirements_rnac)
requirements_rnac.check_and_print_dependencies()

# ---------------------------------------------------------------------------
# 공통 외부 인터페이스 Enum (세 포맷 공유)
# ---------------------------------------------------------------------------
from .constants import ElementType, IterMode

# ---------------------------------------------------------------------------
# 포맷 자동 감지
# ---------------------------------------------------------------------------
from .detector import HwpFormat, detect_format

# ---------------------------------------------------------------------------
# 최상위 통합 변환 API (포맷 자동 dispatch) — 권장
# ---------------------------------------------------------------------------
from .converters import hwp_open, hwp_to_txt, hwp_to_md, hwp_to_pdf

# ---------------------------------------------------------------------------
# HWP 5.0 (v50) API
# ---------------------------------------------------------------------------
from .v50.document_structure import HwpFile as Hwp50File
from .v50.models import Header as Hwp50Header, Version as Hwp50Version
from .v50.parsed_elements import (
    ParsedPage as Hwp50Page,
    ParsedParagraph as Hwp50Paragraph,
    ParsedTable as Hwp50Table,
)
from .v50.parser import HwpDocument as Hwp50Document
from .v50 import open_hwp50
from .v50 import hwp50_unit_to_cm, hwp50_unit_to_inch, hwp50_unit_to_px

# ---------------------------------------------------------------------------
# HWP 97 (v97) API
# ---------------------------------------------------------------------------
from .v97.models import DocumentInfo as Hwp97DocumentInfo, FileHeader as Hwp97FileHeader
from .v97.parsed_elements import (
    ParsedParagraph as Hwp97Paragraph,
    ParsedTable as Hwp97Table,
)
from .v97.parser import Hwp97Document, open_hwp97
from .v97 import hwp97_unit_to_cm, hwp97_unit_to_inch, hwp97_unit_to_px

# ---------------------------------------------------------------------------
# HWPX (owpml) API
# ---------------------------------------------------------------------------
from .owpml.document_structure import HwpxFile
from .owpml.models import HwpxHeader, HwpxVersion
from .owpml.parsed_elements import (
    ParsedPage as HwpxPage,
    ParsedParagraph as HwpxParagraph,
    ParsedTable as HwpxTable,
)
from .owpml.parser import HwpxDocument, open_hwpx

auto_open = hwp_open
auto_to_txt = hwp_to_txt
auto_to_md = hwp_to_md
auto_to_pdf = hwp_to_pdf

auto2txt = hwp_to_txt
auto2md = hwp_to_md
auto2pdf = hwp_to_pdf

hwp2txt = hwp_to_txt
hwp2md = hwp_to_md
hwp2pdf = hwp_to_pdf

__all__ = [
    # 공통 외부 인터페이스 Enum
    "ElementType",
    "IterMode",
    # 포맷 자동 감지
    "HwpFormat",
    "detect_format",
    # 통합 API (포맷 자동 dispatch)
    "hwp_open",
    "hwp_to_txt",
    "hwp_to_md",
    "hwp_to_pdf",
    "auto_open",
    "auto_to_txt",
    "auto_to_md",
    "auto_to_pdf",
    "auto2txt",
    "auto2md",
    "auto2pdf",
    "hwp2txt",
    "hwp2md",
    "hwp2pdf",
    # HWP 5.0 — 모델
    "Hwp50Version",
    "Hwp50Header",
    "Hwp50File",
    # HWP 5.0 — 파싱된 요소
    "Hwp50Paragraph",
    "Hwp50Table",
    "Hwp50Page",
    # HWP 5.0 — Document / 열기
    "Hwp50Document",
    "open_hwp50",
    # HWP 5.0 — 단위 변환
    "hwp50_unit_to_cm",
    "hwp50_unit_to_inch",
    "hwp50_unit_to_px",
    # HWP 97 — 모델
    "Hwp97FileHeader",
    "Hwp97DocumentInfo",
    # HWP 97 — 파싱된 요소
    "Hwp97Paragraph",
    "Hwp97Table",
    # HWP 97 — Document / 열기
    "Hwp97Document",
    "open_hwp97",
    # HWP 97 — 단위 변환
    "hwp97_unit_to_cm",
    "hwp97_unit_to_inch",
    "hwp97_unit_to_px",
    # HWPX — 모델
    "HwpxVersion",
    "HwpxHeader",
    "HwpxFile",
    # HWPX — 파싱된 요소
    "HwpxParagraph",
    "HwpxTable",
    "HwpxPage",
    # HWPX — Document / 열기
    "HwpxDocument",
    "open_hwpx",
]

__version__ = "0.5.7"

# GitHub Repository URL
GITHUB_URL = "https://github.com/c0z0c-helper/helper_hwp"

# 패키지 로드 시 GitHub URL 출력
print(f"GITHUB_URL = {GITHUB_URL}")

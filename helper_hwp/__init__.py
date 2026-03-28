"""
HWP Parser for Python

HWP (Hangul Word Processor) 파일 파싱 라이브러리
CFB (Compound File Binary) 기반 HWP 5.x 포맷 및 HWPX(OWPML) 포맷 지원

주요 기능:
- HWP 5.x 파일 구조 분석 및 파싱 (v50 모듈)
- HWPX(OWPML) 파일 파싱 (owpml 모듈)
- HWP 97 (V3.00) 파일 파싱 (v97 모듈)
- 파일 포맷 자동 감지 후 적합한 파서 선택 (open_hwp)
- 텍스트, 표, 페이지 단위 추출
- Markdown, Plain Text 변환 지원
- 단위 변환 유틸리티 (HWPUNIT <-> cm/inch/px)

외부 인터페이스 통일화:
    세 포맷(v50 / v97 / owpml) 모두 동일한 ElementType, IterMode 를 사용합니다.
    내부 파싱 태그(RecordTag, OwpmlTag, SpecialCharCode 등)와 외부 Enum 은 분리됩니다.

    내부 태그 -> 외부 ElementType 매핑 예시:
        v50  RecordTag.HWPTAG_TABLE (0x4D)         -> ElementType.TABLE
        v97  SpecialCharCode.BOX (10) + TABLE(0)   -> ElementType.TABLE
        owpml OwpmlTag.TBL ("tbl")                 -> ElementType.TABLE

기본 사용법:
    >>> from helper_hwp import open_hwp, to_txt, to_md
    >>> from helper_hwp import ElementType, IterMode
    >>>
    >>> # 포맷 자동 감지 (권장)
    >>> doc = open_hwp('example.hwp')   # or .hwp97 or .hwpx
    >>> for etype, elem in doc.iter_tags():
    ...     if etype == ElementType.PARAGRAPH:
    ...         print(elem.text)
    ...     elif etype == ElementType.TABLE:
    ...         print(f"표 {elem.rows}x{elem.cols}")
    >>>
    >>> text = to_txt('example.hwp')
    >>> md   = to_md('example.hwpx')
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
# HWP 5.0 (v50) API
# ---------------------------------------------------------------------------
from .v50.document_structure import HwpFile
from .v50.models import Header, Version
from .v50.parsed_elements import ParsedPage, ParsedParagraph, ParsedTable
from .v50.parser import HwpDocument
from .v50.parser import open_hwp as open_hwp_v50
from .v50.utils import hwpunit_to_cm, hwpunit_to_inch, hwpunit_to_px

# ---------------------------------------------------------------------------
# HWPX (owpml) API
# ---------------------------------------------------------------------------
from .owpml.document_structure import HwpxFile
from .owpml.models import HwpxVersion, HwpxHeader
from .owpml.parsed_elements import (
    ParsedPage as HwpxParsedPage,
    ParsedParagraph as HwpxParsedParagraph,
    ParsedTable as HwpxParsedTable,
)
from .owpml.parser import HwpxDocument, open_hwpx

# ---------------------------------------------------------------------------
# 포맷 자동 감지
# ---------------------------------------------------------------------------
from .detector import HwpFormat, detect_format

# ---------------------------------------------------------------------------
# HWP 97 (v97) API
# ---------------------------------------------------------------------------
from .v97.parser import Hwp97Document, open_hwp97

# ---------------------------------------------------------------------------
# 최상위 통합 변환 API (포맷 자동 dispatch)
# ---------------------------------------------------------------------------
from .converters import open_hwp, to_md, to_pdf, to_txt


def auto_to_txt(file_path: str) -> str:
    """HWP/HWPX 파일에서 텍스트 추출 (포맷 자동 감지).

    .. deprecated::
        to_txt() 사용을 권장합니다.
    """
    return to_txt(file_path)


def auto_to_markdown(file_path: str) -> str:
    """HWP/HWPX 파일을 마크다운으로 변환 (포맷 자동 감지).

    .. deprecated::
        to_md() 사용을 권장합니다.
    """
    return to_md(file_path)


# 별칭
auto_to_md = auto_to_markdown

__all__ = [
    # 공통 외부 인터페이스 Enum (세 포맷 공유)
    "ElementType",
    "IterMode",
    # 통합 API (포맷 자동 dispatch, 권장)
    "open_hwp",
    "to_txt",
    "to_md",
    "to_pdf",
    # HWP 5.0 모델
    "Version",
    "Header",
    "HwpFile",
    # HWP 5.0 파싱된 요소
    "ParsedParagraph",
    "ParsedTable",
    "ParsedPage",
    # HWP 5.0 메인 API (v50 포맷 전용)
    "HwpDocument",
    "open_hwp_v50",
    # 유틸리티
    "hwpunit_to_cm",
    "hwpunit_to_inch",
    "hwpunit_to_px",
    # HWPX(OWPML) 모델
    "HwpxVersion",
    "HwpxHeader",
    "HwpxFile",
    "HwpxParsedParagraph",
    "HwpxParsedTable",
    "HwpxParsedPage",
    # HWPX 메인 API
    "HwpxDocument",
    "open_hwpx",
    # 포맷 자동 감지
    "HwpFormat",
    "detect_format",
    # 하위 호환 API (deprecated)
    "auto_to_txt",
    "auto_to_markdown",
    "auto_to_md",
    # HWP 97 (V3.00) API
    "Hwp97Document",
    "open_hwp97",
]

__version__ = "0.5.5"

# GitHub Repository URL
GITHUB_URL = "https://github.com/c0z0c-helper/helper_hwp"

# 패키지 로드 시 GitHub URL 출력
print(f"GITHUB_URL = {GITHUB_URL}")

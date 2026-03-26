"""
HWP Parser for Python

HWP (Hangul Word Processor) 파일 파싱 라이브러리
CFB (Compound File Binary) 기반 HWP 5.x 포맷 및 HWPX(OWPML) 포맷 지원

주요 기능:
- HWP 5.x 파일 구조 분석 및 파싱 (v50 모듈)
- HWPX(OWPML) 파일 파싱 (owpml 모듈)
- 파일 포맷 자동 감지 후 적합한 파서 선택 (open_auto)
- 텍스트, 표, 페이지 단위 추출
- Markdown, Plain Text 변환 지원
- 단위 변환 유틸리티 (HWPUNIT ↔ cm/inch/px)

기본 사용법:
    >>> from helper_hwp import open_hwp, hwp_to_txt, hwp_to_markdown
    >>> from helper_hwp import open_auto, auto_to_txt, auto_to_markdown
    >>>
    >>> # HWP 5.0 문서 열기
    >>> doc = open_hwp('example.hwp')
    >>>
    >>> # HWPX 문서 열기
    >>> from helper_hwp import open_hwpx, hwpx_to_txt, hwpx_to_markdown
    >>> doc = open_hwpx('example.hwpx')
    >>>
    >>> # 포맷 자동 감지
    >>> text = auto_to_txt('example.hwp')
    >>> text = auto_to_txt('example.hwpx')

주요 클래스:
    - HwpDocument: HWP 5.0 문서 파싱 및 순회
    - HwpxDocument: HWPX 문서 파싱 및 순회
    - HwpFile: HWP 5.0 파일 구조 (CFB 스토리지)
    - HwpxFile: HWPX 파일 구조 (ZIP/XML)

상수:
    - ElementType: 요소 타입 (PARAGRAPH, TABLE, PAGE)
    - IterMode: 순회 모드 (SEQUENTIAL, STRUCTURED)
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

from .v50.constants import ElementType, IterMode
from .v50.document_structure import HwpFile
from .v50.models import Header, Version
from .v50.parsed_elements import ParsedPage, ParsedParagraph, ParsedTable
from .v50.parser import (
    HwpDocument,
    hwp_to_markdown,
    hwp_to_md,
    hwp_to_pdf,
    hwp_to_txt,
    open_hwp,
)
from .v50.utils import hwpunit_to_cm, hwpunit_to_inch, hwpunit_to_px

# HWPX(OWPML) API
from .owpml.document_structure import HwpxFile
from .owpml.models import HwpxVersion, HwpxHeader
from .owpml.parsed_elements import (
    ParsedPage as HwpxParsedPage,
    ParsedParagraph as HwpxParsedParagraph,
    ParsedTable as HwpxParsedTable,
)
from .owpml.parser import (
    HwpxDocument,
    hwpx_to_markdown,
    hwpx_to_md,
    hwpx_to_txt,
    open_hwpx,
)

# 통합 자동 감지 API
from .detector import HwpFormat, detect_format


def open_auto(file_path: str, iter_mode=None):
    """
    HWP/HWPX 파일을 포맷 자동 감지 후 적합한 Document 반환.

    Args:
        file_path: HWP 또는 HWPX 파일 경로
        iter_mode: 순회 모드 (None이면 각 포맷 기본값 사용)

    Returns:
        HwpDocument (HWP 5.0) 또는 HwpxDocument (HWPX)

    Raises:
        ValueError: 지원하지 않는 파일 포맷
    """
    fmt = detect_format(file_path)
    if fmt == HwpFormat.HWP_V5:
        return open_hwp(file_path, **({"iter_mode": iter_mode} if iter_mode else {}))
    if fmt == HwpFormat.HWPX:
        return open_hwpx(file_path, **({"iter_mode": iter_mode} if iter_mode else {}))
    raise ValueError(f"지원하지 않는 파일 포맷입니다: {file_path}")


def auto_to_txt(file_path: str) -> str:
    """
    HWP/HWPX 파일에서 텍스트 추출 (포맷 자동 감지).

    Args:
        file_path: HWP 또는 HWPX 파일 경로

    Returns:
        추출된 텍스트
    """
    fmt = detect_format(file_path)
    if fmt == HwpFormat.HWP_V5:
        return hwp_to_txt(file_path)
    if fmt == HwpFormat.HWPX:
        return hwpx_to_txt(file_path)
    raise ValueError(f"지원하지 않는 파일 포맷입니다: {file_path}")


def auto_to_markdown(file_path: str) -> str:
    """
    HWP/HWPX 파일을 마크다운으로 변환 (포맷 자동 감지).

    Args:
        file_path: HWP 또는 HWPX 파일 경로

    Returns:
        마크다운 문자열
    """
    fmt = detect_format(file_path)
    if fmt == HwpFormat.HWP_V5:
        return hwp_to_markdown(file_path)
    if fmt == HwpFormat.HWPX:
        return hwpx_to_markdown(file_path)
    raise ValueError(f"지원하지 않는 파일 포맷입니다: {file_path}")


# 별칭
auto_to_md = auto_to_markdown

__all__ = [
    # 상수
    "ElementType",
    "IterMode",
    # HWP 5.0 모델
    "Version",
    "Header",
    "HwpFile",
    # HWP 5.0 파싱된 요소
    "ParsedParagraph",
    "ParsedTable",
    "ParsedPage",
    # HWP 5.0 메인 API
    "HwpDocument",
    "open_hwp",
    "hwp_to_txt",
    "hwp_to_markdown",
    "hwp_to_md",
    "hwp_to_pdf",
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
    "hwpx_to_txt",
    "hwpx_to_markdown",
    "hwpx_to_md",
    # 포맷 자동 감지 API
    "HwpFormat",
    "detect_format",
    "open_auto",
    "auto_to_txt",
    "auto_to_markdown",
    "auto_to_md",
]

__version__ = "0.5.5"

# GitHub Repository URL
GITHUB_URL = "https://github.com/c0z0c-helper/helper_hwp"

# 패키지 로드 시 GitHub URL 출력
print(f"GITHUB_URL = {GITHUB_URL}")

"""
HWP Parser for Python

HWP (Hangul Word Processor) 파일 파싱 라이브러리
CFB (Compound File Binary) 기반 HWP 5.x 포맷 지원

주요 기능:
- HWP 5.x 파일 구조 분석 및 파싱
- 텍스트, 표, 페이지 단위 추출
- Markdown, Plain Text 변환 지원
- 단위 변환 유틸리티 (HWPUNIT ↔ cm/inch/px)

기본 사용법:
    >>> from helper_hwp import open_hwp, hwp_to_txt, hwp_to_markdown
    >>> 
    >>> # HWP 문서 열기
    >>> doc = open_hwp('example.hwp')
    >>> 
    >>> # 텍스트 추출
    >>> text = hwp_to_txt('example.hwp')
    >>> 
    >>> # 마크다운 변환
    >>> markdown = hwp_to_markdown('example.hwp')

주요 클래스:
    - HwpDocument: HWP 문서 파싱 및 순회
    - HwpFile: HWP 파일 구조 (CFB 스토리지)
    - ParsedParagraph: 파싱된 문단
    - ParsedTable: 파싱된 표
    - ParsedPage: 파싱된 페이지

상수:
    - ElementType: 요소 타입 (PARAGRAPH, TABLE, PAGE)
    - IterMode: 순회 모드 (PARAGRAPH, TABLE, PAGE)
"""

from .constants import ElementType, IterMode
from .models import Version, Header
from .document_structure import HwpFile
from .parsed_elements import ParsedParagraph, ParsedTable, ParsedPage
from .parser import HwpDocument, open_hwp, hwp_to_txt, hwp_to_markdown
from .utils import hwpunit_to_cm, hwpunit_to_inch, hwpunit_to_px

__all__ = [
    # 상수
    'ElementType',
    'IterMode',
    
    # 모델
    'Version',
    'Header',
    'HwpFile',
    
    # 파싱된 요소
    'ParsedParagraph',
    'ParsedTable',
    'ParsedPage',
    
    # 메인 API
    'HwpDocument',
    'open_hwp',
    'hwp_to_txt',
    'hwp_to_markdown',
    
    # 유틸리티
    'hwpunit_to_cm',
    'hwpunit_to_inch',
    'hwpunit_to_px',
]

__version__ = '0.5.2'

# GitHub Repository URL
GITHUB_URL = "https://github.com/c0z0c/helper_hwp"

# 패키지 로드 시 GitHub URL 출력
print(f"GITHUB_URL = {GITHUB_URL}")

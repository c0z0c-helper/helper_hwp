"""
HWPX/OWPML 파일 포맷 상수 정의

OWPML (Open Word Processor Markup Language) 기반 HWPX 포맷 상수.
HWPX 파일은 ZIP 압축된 XML 파일의 묶음(OPC 패키지)입니다.

참고:
- OWPML 스펙 (한글과컴퓨터 공개 문서)
- HWPX 파일 내부 구조: META-INF/manifest.xml, Contents/header.xml, Contents/section0.xml ...
"""

from enum import Enum, IntEnum


class OwpmlNamespace(str, Enum):
    """OWPML XML 네임스페이스"""

    HP = "http://www.hancom.co.kr/hwpml/2012/paragraph"
    HH = "http://www.hancom.co.kr/hwpml/2012/head"
    HS = "http://www.hancom.co.kr/hwpml/2012/section"
    HF = "http://www.hancom.co.kr/hwpml/2012/frameset"
    HI = "http://www.hancom.co.kr/hwpml/2012/core"
    DC = "http://purl.org/dc/elements/1.1/"


class SectionPath:
    """HWPX 내부 파일 경로 상수"""

    MANIFEST = "META-INF/manifest.xml"
    HEADER = "Contents/header.xml"
    SECTION_PREFIX = "Contents/section"
    SECTION_EXT = ".xml"

    @classmethod
    def section(cls, index: int) -> str:
        return f"{cls.SECTION_PREFIX}{index}{cls.SECTION_EXT}"


class OwpmlTag(str, Enum):
    """OWPML XML 태그명 (로컬명, 네임스페이스 제외)"""

    # 섹션/문단
    SEC = "sec"  # 섹션
    P = "p"  # 문단 (paragraph)
    T = "t"  # 텍스트 런
    RUN = "run"  # 런 (일부 버전)
    LINE_SEG = "lineSeg"  # 줄 배치

    # 표
    TBL = "tbl"  # 표
    TR = "tr"  # 행
    TC = "tc"  # 셀

    # 이미지/오브젝트
    PIC = "pic"  # 그림
    IMG = "img"  # 이미지 참조
    OLE = "ole"  # OLE 객체

    # 필드/제어
    FIELD_BEGIN = "fieldBegin"  # 필드 시작
    FIELD_END = "fieldEnd"  # 필드 끝
    SUB_LIST = "subList"  # 서브 리스트

    # 각주/미주
    FOOT_NOTE = "footNote"  # 각주
    END_NOTE = "endNote"  # 미주

    # 헤더
    HEAD = "head"
    BEGIN_NUM = "beginNum"
    REF_LIST = "refList"
    BIN_ITEM = "binItem"

    # 문서 구조
    BODY_TEXT = "bodyText"
    HP_DOC = "HPDoc"


class FieldType(str, Enum):
    """필드 타입 (fieldBegin/@type)"""

    HYPERLINK = "HYPERLINK"
    MEMO = "MEMO"
    BOOKMARK = "BOOKMARK"
    DATE = "DATE"
    PAGE_NUM = "PAGE_NUM"
    TOTAL_PAGE = "TOTAL_PAGE"


# ---------------------------------------------------------------------------
# 공통 외부 인터페이스 Enum (helper_hwp.constants 에서 re-export)
#
# 내부 파싱 태그(OwpmlTag, FieldType 등)와 분리하여
# 외부 API는 포맷에 관계없이 동일한 ElementType / IterMode 를 사용합니다.
#
# owpml 내부 태그 → 외부 ElementType 매핑 예시:
#   OwpmlTag.TBL ("tbl")          -> ElementType.TABLE
#   OwpmlTag.P   ("p")            -> ElementType.PARAGRAPH
#   OwpmlTag.FOOT_NOTE            -> ElementType.FOOTNOTE
#   RawParagraph.is_page_break    -> ElementType.PAGE_BREAK
# ---------------------------------------------------------------------------
from helper_hwp.constants import ElementType, IterMode  # noqa: F401  (re-export)

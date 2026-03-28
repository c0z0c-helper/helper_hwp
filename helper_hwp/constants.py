"""
helper_hwp 공통 상수 정의

v50 (HWP 5.x), v97 (HWP 97), owpml (HWPX) 세 모듈이 공유하는
ElementType, IterMode Enum을 이 파일에서 단일 정의합니다.

각 모듈의 constants.py는 이 파일에서 재내보내기(re-export)하므로
기존 ``from helper_hwp.v50.constants import ElementType`` 형태의
import도 그대로 동작합니다.

사용법:
    # 최상위 패키지에서 직접 사용 (권장)
    from helper_hwp.constants import ElementType, IterMode

    # 또는 기존 방식 유지 (하위 호환)
    from helper_hwp.v50.constants import ElementType
    from helper_hwp.owpml.constants import ElementType
"""

from enum import Enum


class ElementType(Enum):
    """문서 요소 타입 (v50 · v97 · owpml 공통)

    각 포맷에서 지원하지 않는 타입은 파서가 단순히 yield하지 않으므로
    Enum 값 자체는 통합 정의하고 포맷별 지원 여부는 파서에서 결정합니다.

    포맷별 지원 현황:
        PARAGRAPH       : v50 / v97 / owpml  [O]
        TABLE           : v50 / v97 / owpml  [O]
        PAGE_BREAK      : v50 / owpml        [O]  (v97 파라그래프 플래그 기반)
        SECTION         : owpml (STRUCTURED) [O]
        PICTURE         : v50 / v97          [O]
        EQUATION        : v50 / v97          [O]
        FOOTNOTE        : v50 / owpml        [O]
        ENDNOTE         : v50 / owpml        [O]
        HYPERLINK       : v50 / owpml / v97  [O]
        FIELD           : v50 / owpml        [O]
        SHAPE           : v50                [O]
        SHAPE_COMPONENT : v50                [O]
        COMMENT         : v50                [O]
        OLE             : v50 / owpml        [O]
        HEADER          : v50                [O]
        FOOTER          : v50                [O]
        CAPTION         : v50                [O]
        CTRL_HEADER     : v50                [O]
        CTRL_DATA       : v50                [O]
        LIST_HEADER     : v50                [O]
        PAGE_DEF        : v50                [O]
        AUTO_NUMBER     : v50                [O]
        NEW_NUMBER      : v50                [O]
        PAGE_NUM_POS    : v50                [O]
        BOOKMARK        : v50 / owpml / v97  [O]
    """

    PARAGRAPH = "paragraph"
    TABLE = "table"
    PAGE_BREAK = "page_break"
    SECTION = "section"
    PICTURE = "picture"
    EQUATION = "equation"
    FOOTNOTE = "footnote"
    ENDNOTE = "endnote"
    HYPERLINK = "hyperlink"
    FIELD = "field"
    SHAPE = "shape"
    SHAPE_COMPONENT = "shape_component"
    COMMENT = "comment"
    OLE = "ole"
    HEADER = "header"
    FOOTER = "footer"
    CAPTION = "caption"
    CTRL_HEADER = "ctrl_header"
    CTRL_DATA = "ctrl_data"
    LIST_HEADER = "list_header"
    PAGE_DEF = "page_def"
    AUTO_NUMBER = "auto_number"
    NEW_NUMBER = "new_number"
    PAGE_NUM_POS = "page_num_pos"
    BOOKMARK = "bookmark"

    @classmethod
    def from_string(cls, value: str) -> "ElementType":
        """문자열을 ElementType으로 변환 (하위 호환성)"""
        value_lower = value.lower()
        for member in cls:
            if member.value == value_lower:
                return member
        raise ValueError(f"Unknown element type: {value}")


class IterMode(Enum):
    """문서 순회 모드 (v50 · v97 · owpml 공통)

    SEQUENTIAL : 문서 출현 순서 기반 순회 (기본, 속도 우선)
    STRUCTURED : Section → Paragraph → Char 계층 구조 순회
    """

    SEQUENTIAL = "sequential"
    STRUCTURED = "structured"


__all__ = [
    "ElementType",
    "IterMode",
]

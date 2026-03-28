"""
HWP 97 (V3.00) 파일 포맷 상수 정의

한글문서파일형식97분석보고서 참고
"""

from enum import IntEnum


# ---------------------------------------------------------------------------
# 파일 레이아웃 상수
# ---------------------------------------------------------------------------

FILE_SIGNATURE = b"HWP Document File V3.00 \x1a\x01\x02\x03\x04\x05"
FILE_SIGNATURE_SIZE = 30

DOCUMENT_INFO_SIZE = 128
DOCUMENT_SUMMARY_SIZE = 1008

# 정보 블록 구조: ID(word) + 길이(word) + 내용
INFO_BLOCK_HEADER_SIZE = 4

# 추가 정보 블록 구조: ID(dword) + 길이(dword) + 내용
EXTRA_BLOCK_HEADER_SIZE = 8
EXTRA_BLOCK_END_ID = 0x80000000

# 글꼴 언어 종류 수 (한글, 영문, 한자, 일어, 기타, 기호, 사용자)
FONT_LANG_COUNT = 7
FONT_NAME_SIZE = 40

# 스타일 1개 크기 (이름 20 + 글자모양 31 + 문단모양 187)
STYLE_ENTRY_SIZE = 238
STYLE_NAME_SIZE = 20

# 글자 모양 구조 크기
CHAR_SHAPE_SIZE = 31

# 문단 모양 구조 크기
PARA_SHAPE_SIZE = 187

# 줄 정보 항목 크기
LINE_INFO_SIZE = 14

# 문단 정보 최소 크기 (앞문단 모양 따를 때)
PARA_INFO_MIN_SIZE = 43
# 문단 정보 최대 크기 (문단 모양 포함)
PARA_INFO_MAX_SIZE = 230  # 43 + 187


# ---------------------------------------------------------------------------
# 특수 문자 코드 (hchar, 0-31 범위)
# ---------------------------------------------------------------------------


class SpecialCharCode(IntEnum):
    """HWP 97 (V3.00) 특수 문자 코드 (문단 내 hchar 0-31)

    문단 내 코드값 0-31인 hchar 는 일반 글자가 아니라 특수 제어 코드로 사용됩니다.
    """

    FIELD_CODE = 5  # 필드 코드 (계산식, 누름틀 등)
    BOOKMARK = 6  # 책갈피
    DATE_FORMAT = 7  # 날짜 형식
    DATE_CODE = 8  # 날짜 코드
    TAB = 9  # 탭
    BOX = 10  # 표/텍스트박스/수식/버튼/하이퍼텍스트
    PICTURE = 11  # 그림
    LINE = 14  # 선
    HIDDEN_COMMENT = 15  # 숨은 설명
    HEADER_FOOTER = 16  # 머리말/꼬리말
    FOOTNOTE_ENDNOTE = 17  # 각주/미주
    NUMBER_CODE = 18  # 번호 코드 넣기
    NEW_NUMBER = 19  # 새 번호로 시작
    PAGE_NUMBER = 20  # 쪽번호달기
    ODD_PAGE = 21  # 홀수쪽시작/감추기
    MAIL_MERGE = 22  # 메일머지 표시
    CHAR_OVERLAP = 23  # 글자겹침
    HYPHEN = 24  # 하이픈
    TOC_MARK = 25  # 제목/표/그림차례 표시
    INDEX_MARK = 26  # 찾아보기 표시
    OUTLINE = 28  # 개요 모양/번호
    CROSS_REF = 29  # 상호참조
    KEEP_SPACE = 30  # 묶음빈칸
    FIXED_SPACE = 31  # 고정폭빈칸
    PARA_END = 13  # CR (문단 끝)


# ---------------------------------------------------------------------------
# 박스 종류 (특수 문자 코드 10: BOX)
# ---------------------------------------------------------------------------


class BoxType(IntEnum):
    """HWP 97 (V3.00) 박스 종류 (표 정보 offset 78, word)"""

    TABLE = 0  # 표
    TEXT_BOX = 1  # 텍스트박스
    EQUATION = 2  # 수식
    BUTTON = 3  # 버튼


# ---------------------------------------------------------------------------
# 문단 정보 플래그
# ---------------------------------------------------------------------------


class ParaFlag(IntEnum):
    """문단 정보 기타 플래그 (offset 6, byte)"""

    COLUMN_BREAK = 0x01  # 단 나눔
    PAGE_BREAK = 0x02  # 페이지 나눔
    BLOCK_PROTECT = 0x04  # 블록 보호


# ---------------------------------------------------------------------------
# 글자 모양 속성 플래그 (CharShape offset 26, byte)
# ---------------------------------------------------------------------------


class CharAttr(IntEnum):
    """글자 속성 비트 플래그"""

    ITALIC = 0x01
    BOLD = 0x02
    UNDERLINE = 0x04
    STRIKEOUT = 0x08
    SUPERSCRIPT = 0x10
    SUBSCRIPT = 0x20
    SHADOW = 0x40
    OUTLINE = 0x80


# ---------------------------------------------------------------------------
# 정보 블록 ID (파일 앞부분)
# ---------------------------------------------------------------------------


class InfoBlockID(IntEnum):
    """정보 블록 ID (앞부분 고정 위치)"""

    BOOKMARK = 1  # 책갈피
    CROSS_REF = 2  # 상호참조


# ---------------------------------------------------------------------------
# 추가 정보 블록 ID (파일 끝부분)
# ---------------------------------------------------------------------------


class ExtraBlockID(IntEnum):
    """추가 정보 블록 #1 ID (파일 끝부분 압축 영역)"""

    PICTURE = 1  # 포함된 그림
    OLE = 2  # OLE 정보
    HYPERLINK = 3  # 하이퍼텍스트
    PRESENTATION = 4  # 프리젠테이션 설정
    RESERVED = 5  # 예약 정보
    BG_IMAGE = 6  # 배경이미지
    TABLE_FIELD = 7  # 테이블 확장 (셀 필드 이름)
    PRESS_FIELD = 8  # 누름틀 필드 이름


class ExtraBlock2ID(IntEnum):
    """추가 정보 블록 #2 ID (미압축, 파일 맨 끝)"""

    PREVIEW_IMAGE = 0x80000001  # 미리보기 이미지 (BMP)
    PREVIEW_TEXT = 0x80000002  # 미리보기 텍스트


# ---------------------------------------------------------------------------
# 용지 종류
# ---------------------------------------------------------------------------


class PaperType(IntEnum):
    """용지 종류 (문서 정보 offset 4, byte)"""

    A0 = 0
    A1 = 1
    A2 = 2
    A3 = 3
    A4 = 4
    A5 = 5
    B4 = 6
    B5 = 7
    POSTCARD = 8
    EXECUTIVE = 9
    LETTER = 10
    LEGAL = 11
    LEDGER = 12
    CUSTOM = 30


# ---------------------------------------------------------------------------
# 공통 외부 인터페이스 Enum (helper_hwp.constants 에서 re-export)
#
# 내부 파싱 코드(SpecialCharCode, BoxType 등)와 분리하여
# 외부 API는 포맷에 관계없이 동일한 ElementType / IterMode 를 사용합니다.
#
# v97 내부 태그 → 외부 ElementType 매핑 예시:
#   SpecialCharCode.BOX (10), BoxType.TABLE (0) -> ElementType.TABLE
#   SpecialCharCode.PICTURE (11)                -> ElementType.PICTURE
#   ParaFlag.PAGE_BREAK (0x02)                  -> ElementType.PAGE_BREAK
#   (일반 문단)                                  -> ElementType.PARAGRAPH
# ---------------------------------------------------------------------------
from helper_hwp.constants import ElementType, IterMode  # noqa: F401  (re-export)

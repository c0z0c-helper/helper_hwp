"""
HWP 97 (V3.00) 문자 및 문단 구조

이 모듈은 HWP 97 (V3.00) 파일의 문단 데이터를 처리합니다.
- 문단 정보 파싱 (앞문단 모양 여부, 글자 수, 줄 수 등)
- hchar 기반 글자 스트림 읽기
- 특수 문자 코드(0-31) 처리

참고: 한글문서파일형식97분석보고서, Section 4 (문단 자료 구조)
"""

import io
import struct
from dataclasses import dataclass, field
from enum import Enum
from typing import BinaryIO, Iterator, List, Optional, Tuple

from .constants import (
    CHAR_SHAPE_SIZE,
    LINE_INFO_SIZE,
    PARA_INFO_MAX_SIZE,
    PARA_INFO_MIN_SIZE,
    PARA_SHAPE_SIZE,
    SpecialCharCode,
)
from .models import CharShape, LineInfo


class HCharType(Enum):
    """HWP 97 (V3.00) hchar 문자 타입"""

    NORMAL = "normal"  # 일반 문자 (코드 > 31)
    PARA_END = "para_end"  # 문단 끝 (CR, 코드 13)
    TAB = "tab"  # 탭 (코드 9)
    SPECIAL = "special"  # 특수 제어 문자 (코드 0-31 중 BOX/PICTURE 등)
    CONTROL = "control"  # 기타 제어 (코드 0-31)


@dataclass
class HChar:
    """HWP 97 (V3.00) hchar 문자

    HWP 97 (V3.00)의 hchar는 2바이트 고정 길이.
    코드 0-31: 특수 제어 코드, 32 이상: 일반 글자(한글/영문/한자).
    특수 문자(코드 5,6,7,8,10,11,14~22,25,26,28,29)는 추가 데이터를 가짐.
    """

    char_type: HCharType
    code: int  # hchar 코드 (0-65535)
    extra_data: Optional[bytes] = None  # 특수 문자 부가 정보 (n바이트)

    def to_string(self) -> str:
        """hchar를 Python str로 변환.

        HWP 97 (V3.00)의 내부 문자 코드(hchar)는 Johab(상용조합형) 2바이트 인코딩입니다.
        빅엔디언으로 2바이트를 구성하여 Johab으로 디코딩합니다.
        ASCII(0x20-0x7E) 범위는 코드 직접 변환합니다.
        제어코드(0x00-0x1F)는 출력 불가 문자이므로 빈 문자열을 반환합니다.
        Johab 디코딩 실패(U+FFFD) 또는 디코딩 결과가 제어문자이면 빈 문자열을 반환합니다.
        유효한 Johab 2바이트 범위: 상위바이트 0x84~0xD3.
        """
        if self.char_type == HCharType.NORMAL:
            if self.code < 0x20:
                # NUL 및 제어코드 제거
                return ""
            if self.code < 0x80:
                return chr(self.code)
            # Johab 2바이트: 빅엔디언으로 패킹
            # 유효한 Johab 상위바이트 범위: 0x84~0xD3
            high_byte = (self.code >> 8) & 0xFF
            if high_byte < 0x84:
                # 유효하지 않은 Johab 범위 (렌더링 캐시 데이터 등)
                return ""
            raw = struct.pack(">H", self.code)
            try:
                ch = raw.decode("johab", errors="replace")
                # Johab 디코딩 실패(대체문자 U+FFFD) 제거
                if ch == "\ufffd":
                    return ""
                # 디코딩 결과가 제어문자이면 제거
                if len(ch) == 1 and ord(ch) < 0x20:
                    return ""
                # 멀티문자 결과에서 제어문자 포함시 제거
                if any(ord(c) < 0x20 for c in ch):
                    return ""
                return ch
            except Exception:
                return ""
        elif self.char_type == HCharType.PARA_END:
            return "\n"
        elif self.char_type == HCharType.TAB:
            return "\t"
        else:
            return ""


# ---------------------------------------------------------------------------
# 문단 정보 파싱
# ---------------------------------------------------------------------------


@dataclass
class ParaInfo:
    """HWP 97 (V3.00) 문단 정보 (가변 크기: 43 또는 230 bytes)

    스펙: Section 4.1
    """

    follow_prev_shape: bool  # offset 0, byte: 0=새 문단 모양, 이외=앞 따라감
    char_count: int  # offset 1, word: 글자 수 (0=빈 문단/리스트 끝)
    line_count: int  # offset 3, word: 줄 수
    has_char_shape: bool  # offset 5, byte: 글자 모양 포함 여부
    extra_flags: int  # offset 6, byte: 단나눔/페이지나눔/블록보호 등
    special_char_flags: int  # offset 7, dword: 특수 문자 존재 비트맵
    style_index: int  # offset 11, byte: 스타일 인덱스
    repr_char_shape: CharShape  # offset 12, 31 bytes: 대표 글자 모양
    para_shape_raw: Optional[bytes] = None  # 187 bytes (follow_prev_shape=0 일 때)

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> Optional["ParaInfo"]:
        """스트림에서 문단 정보 읽기. 빈 문단(글자 수 0) 포함."""
        header = stream.read(PARA_INFO_MIN_SIZE)
        if len(header) < PARA_INFO_MIN_SIZE:
            return None

        follow_prev = header[0]
        char_count = struct.unpack_from("<H", header, 1)[0]
        line_count = struct.unpack_from("<H", header, 3)[0]
        has_cs = header[5]
        extra_flags = header[6]
        special_flags = struct.unpack_from("<I", header, 7)[0]
        style_idx = header[11]
        repr_cs = CharShape.from_bytes(header[12:43])

        para_shape_raw = None
        if follow_prev == 0:
            # 문단 모양 187바이트 읽기
            raw = stream.read(PARA_SHAPE_SIZE)
            if len(raw) < PARA_SHAPE_SIZE:
                return None
            para_shape_raw = raw

        return cls(
            follow_prev_shape=bool(follow_prev),
            char_count=char_count,
            line_count=line_count,
            has_char_shape=bool(has_cs),
            extra_flags=extra_flags,
            special_char_flags=special_flags,
            style_index=style_idx,
            repr_char_shape=repr_cs,
            para_shape_raw=para_shape_raw,
        )

    @property
    def is_page_break(self) -> bool:
        return bool(self.extra_flags & 0x02)

    @property
    def is_column_break(self) -> bool:
        return bool(self.extra_flags & 0x01)


# ---------------------------------------------------------------------------
# 글자 모양 정보 스트림 파싱
# ---------------------------------------------------------------------------


def read_char_shapes(stream: BinaryIO, char_count: int) -> List[Tuple[int, Optional[CharShape]]]:
    """글자 모양 정보 읽기 (char_count 만큼 반복).

    각 글자에 대해:
      - flag=1 (1 byte): 앞 글자 모양 따라감 → CharShape 없음
      - flag≠1 (1 byte) + CharShape (31 bytes): 새 글자 모양

    Args:
        stream: 바이너리 스트림
        char_count: 문단 글자 수

    Returns:
        [(char_index, CharShape 또는 None), ...]
    """
    result: List[Tuple[int, Optional[CharShape]]] = []
    for i in range(char_count):
        flag_byte = stream.read(1)
        if not flag_byte:
            break
        flag = flag_byte[0]
        if flag == 1:
            result.append((i, None))
        else:
            cs_data = stream.read(CHAR_SHAPE_SIZE)
            if len(cs_data) < CHAR_SHAPE_SIZE:
                break
            result.append((i, CharShape.from_bytes(cs_data)))
    return result


# ---------------------------------------------------------------------------
# 글자 스트림 파싱
# ---------------------------------------------------------------------------


def read_hchars(stream: BinaryIO, char_count: int) -> Iterator[HChar]:
    """hchar 스트림에서 글자들을 읽어 HChar 이터레이터 반환.

    HWP 97 (V3.00)에서 특수 문자의 부가 데이터는 hchar 단위(2바이트씩)로
    char_count에 포함되어 있습니다. 즉 추가 바이트를 stream.read()로
    읽어오면 안 되고, 대신 read_count를 증가시키며 hchar 단위로 읽습니다.

    스펙: 한글문서파일형식97분석보고서, Section 10 (특수 문자 자료 구조)

    Args:
        stream: 바이너리 스트림
        char_count: 문단 글자 수 (hchar 단위)

    Yields:
        HChar 객체
    """
    # 각 특수 문자의 전체 구조 크기(바이트) - 첫 hchar(2) 포함
    # hchar 단위 추가 소비 = (total - 2) / 2
    _TOTAL_SIZE: dict = {
        6: 42,  # 책갈피: hchar(2)+dword(4)+hchar(2)+hchar[16](32)+word(2) = 42
        7: 84,  # 날짜형식: hchar(2)+hchar[40](80)+hchar(2) = 84
        8: 96,  # 날짜코드: hchar(2)+hchar[40](80)+word[4](8)+word[2](4)+hchar(2) = 96
        9: 8,  # 탭: hchar(2)+hunit(2)+word(2)+hchar(2) = 8
        18: 8,  # 번호코드: hchar(2)+word(2)+word(2)+hchar(2) = 8
        19: 8,  # 번호바꾸기: hchar(2)+word(2)+word(2)+hchar(2) = 8
        20: 8,  # 쪽번호달기: hchar(2)+word(2)+word(2)+hchar(2) = 8
        21: 8,  # 홀수쪽: hchar(2)+word(2)+word(2)+hchar(2) = 8
        22: 24,  # 메일머지: hchar(2)+kchar[20](20)+hchar(2) = 24
        23: 10,  # 글자겹침: hchar(2)+hchar[3](6)+hchar(2) = 10
        24: 6,  # 하이픈: hchar(2)+hunit(2)+hchar(2) = 6
        25: 6,  # 차례표시: hchar(2)+hunit(2)+hchar(2) = 6
        26: 246,  # 찾아보기: hchar(2)+hchar[60](120)+hchar[60](120)+word(2)+hchar(2) = 246
        28: 64,  # 개요모양/번호 전체 = 64
        30: 4,  # 묶음빈칸: hchar(2)+hchar(2) = 4
        31: 4,  # 고정폭빈칸: hchar(2)+hchar(2) = 4
    }
    # 문단 리스트를 포함하는 인라인 객체 코드.
    # 식별 정보: hchar(2)+dword(4)+hchar(2) = 8B = 4 hchar.
    # 식별 정보 소비 후 해당 객체의 추가 데이터(표 정보, 그림 정보 등)가
    # hchar 스트림 밖에 별도로 이어진다. 따라서 식별 정보만 읽고
    # read_count 를 char_count 로 강제 설정해 루프를 즉시 종료한다.
    # (스펙 오프셋과 실측이 2B 어긋나는 케이스가 있으므로, 초과 소비를 방지)
    _INLINE_OBJECT_CODES = {10, 11, 14, 15, 16, 17}
    _INLINE_IDENT_EXTRA = 3  # hchar(2)+dword(4)+hchar(2) 중 첫 hchar 제외 = 3 hchar

    # 가변 길이 코드 (hchar(2)+dword n +hchar(2)+byte[n] 구조)
    # 전체 소비 hchar = 1(첫hchar) + 2(dword=4바이트) + 1(반복hchar) + n/2
    _VAR_CODES = {5, 29}  # 필드코드, 상호참조

    read_count = 0
    while read_count < char_count:
        raw = stream.read(2)
        if len(raw) < 2:
            break
        code = struct.unpack_from("<H", raw)[0]
        read_count += 1

        if code > 31:
            yield HChar(char_type=HCharType.NORMAL, code=code)

        elif code == SpecialCharCode.PARA_END or code == 0:
            yield HChar(char_type=HCharType.PARA_END, code=code)

        elif code in _INLINE_OBJECT_CODES:
            # 식별 정보 나머지 (dword 4B + 반복 hchar 2B = 3 hchar) 소비
            extra = stream.read(_INLINE_IDENT_EXTRA * 2)
            read_count += _INLINE_IDENT_EXTRA
            yield HChar(char_type=HCharType.SPECIAL, code=code, extra_data=extra)
            # 객체 추가 데이터는 hchar 스트림 바깥에 있으므로 루프를 즉시 종료
            read_count = char_count

        elif code in _TOTAL_SIZE:
            # 나머지 (total - 2) 바이트 = (total/2 - 1) 개의 hchar 읽기
            extra_hchars = (_TOTAL_SIZE[code] - 2) // 2
            extra = stream.read(extra_hchars * 2)
            read_count += extra_hchars
            yield HChar(char_type=HCharType.SPECIAL, code=code, extra_data=extra)

        elif code in _VAR_CODES:
            # dword(4) + hchar(2) + byte[n]: 모두 hchar 단위로 읽음
            # dword = 2 hchar, 반복hchar = 1 hchar
            size_raw = stream.read(4)
            if len(size_raw) < 4:
                yield HChar(char_type=HCharType.SPECIAL, code=code)
                break
            extra_size = struct.unpack_from("<I", size_raw)[0]
            repeat_raw = stream.read(2)
            extra = stream.read(extra_size)
            # hchar 단위 추가 소비: 2(dword) + 1(반복hchar) + extra_size/2
            read_count += 3 + (extra_size // 2)
            yield HChar(
                char_type=HCharType.SPECIAL,
                code=code,
                extra_data=size_raw + repeat_raw + extra,
            )

        else:
            yield HChar(char_type=HCharType.CONTROL, code=code)


# ---------------------------------------------------------------------------
# 문단 클래스
# ---------------------------------------------------------------------------


@dataclass
class Paragraph:
    """HWP 97 (V3.00) 문단

    Attributes:
        info: 문단 정보
        line_infos: 줄 정보 리스트
        char_shape_map: 글자별 모양 [(char_index, CharShape)]
        chars: hchar 리스트
    """

    info: ParaInfo
    line_infos: List[LineInfo] = field(default_factory=list)
    char_shape_map: List[Tuple[int, Optional[CharShape]]] = field(default_factory=list)
    chars: List[HChar] = field(default_factory=list)

    def to_string(self) -> str:
        """문단 내용을 문자열로 변환"""
        parts = []
        for hc in self.chars:
            s = hc.to_string()
            if s:
                parts.append(s)
        return "".join(parts)

    @property
    def is_empty(self) -> bool:
        """문단 리스트 종료 마커 여부.

        스펙 4.1: char_count == 0 이면 빈 문단 (문단 리스트의 끝).
        line_count 값과 무관하게 char_count == 0 이면 종료 마커이다.
        """
        return self.info.char_count == 0

    @classmethod
    def read_from_stream(cls, stream: BinaryIO) -> Optional["Paragraph"]:
        """스트림에서 문단 1개 읽기.

        char_count=0 AND line_count=0 인 문단이 리스트 끝 종료 마커입니다.
        is_empty를 확인하여 종료 처리해야 합니다.
        """
        info = ParaInfo.from_stream(stream)
        if info is None:
            return None

        # char_count == 0 이면 리스트 종료 마커: 줄 정보/글자 모양/글자 없음
        if info.char_count == 0:
            return cls(info=info)

        # 줄 정보
        line_infos: List[LineInfo] = []
        for _ in range(info.line_count):
            li_raw = stream.read(LINE_INFO_SIZE)
            if len(li_raw) < LINE_INFO_SIZE:
                break
            line_infos.append(LineInfo.from_bytes(li_raw))

        # 글자 모양 정보 (has_char_shape != 0 일 때)
        char_shape_map: List[Tuple[int, Optional[CharShape]]] = []
        if info.has_char_shape:
            char_shape_map = read_char_shapes(stream, info.char_count)

        # 글자들
        chars = list(read_hchars(stream, info.char_count))

        return cls(
            info=info,
            line_infos=line_infos,
            char_shape_map=char_shape_map,
            chars=chars,
        )

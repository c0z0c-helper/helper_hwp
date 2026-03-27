"""
HWP 97 (V3.00) 파일 기본 데이터 모델

한글문서파일형식97분석보고서 참고
단위: hunit = 1/1800 inch (v50의 hwpunit = 1/7200 inch 와 다름)
"""

import struct
from dataclasses import dataclass, field
from typing import BinaryIO, List, Optional

from .constants import (
    CHAR_SHAPE_SIZE,
    DOCUMENT_INFO_SIZE,
    DOCUMENT_SUMMARY_SIZE,
    FILE_SIGNATURE,
    FILE_SIGNATURE_SIZE,
    PARA_SHAPE_SIZE,
    STYLE_ENTRY_SIZE,
    STYLE_NAME_SIZE,
)


# ---------------------------------------------------------------------------
# 파일 인식 정보 (30 bytes)
# ---------------------------------------------------------------------------


@dataclass
class FileHeader:
    """HWP 97 (V3.00) 파일 인식 정보 (30 bytes)

    파일 맨 앞 30바이트.
    서명: b"HWP Document File V3.00 \\x1a\\x01\\x02\\x03\\x04\\x05"
    """

    signature: bytes  # 30 bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> "FileHeader":
        if len(data) < FILE_SIGNATURE_SIZE:
            raise ValueError(f"파일 인식 정보 크기 부족: {len(data)} < {FILE_SIGNATURE_SIZE}")
        sig = data[:FILE_SIGNATURE_SIZE]
        if not sig.startswith(b"HWP Document File V3."):
            raise ValueError(f"HWP 97 (V3.00) 서명 불일치: {sig[:21]}")
        return cls(signature=sig)

    @classmethod
    def from_stream(cls, stream: BinaryIO) -> "FileHeader":
        return cls.from_bytes(stream.read(FILE_SIGNATURE_SIZE))

    @property
    def sub_revision(self) -> int:
        """서브 리비전 (signature[25] 값, 0=글3.0, 1=글3.0이후)"""
        if len(self.signature) > 25:
            return self.signature[25]
        return 0


# ---------------------------------------------------------------------------
# 문서 정보 (128 bytes)
# ---------------------------------------------------------------------------


@dataclass
class DocumentInfo:
    """HWP 97 (V3.00) 문서 정보 (128 bytes)

    스펙: 한글문서파일형식97분석보고서, Section 3.2
    """

    cursor_line: int  # offset 0, word: 커서 줄
    cursor_col: int  # offset 2, word: 커서 칸
    paper_type: int  # offset 4, byte: 용지 종류
    paper_orient: int  # offset 5, byte: 용지 방향 (0=보통, 1=넓게)
    paper_height: int  # offset 6, hunit: 용지 길이
    paper_width: int  # offset 8, hunit: 용지 너비
    margin_top: int  # offset 10, hunit: 위쪽 여백
    margin_bottom: int  # offset 12, hunit: 아래쪽 여백
    margin_left: int  # offset 14, hunit: 왼쪽 여백
    margin_right: int  # offset 16, hunit: 오른쪽 여백
    header_size: int  # offset 18, hunit: 머리말 길이
    footer_size: int  # offset 20, hunit: 꼬리말 길이
    binding_margin: int  # offset 22, hunit: 제본 여백
    doc_protect: int  # offset 24, dword: 문서 보호 (1=보호)
    reserved: int  # offset 28, word: 예약
    page_num_cont: int  # offset 30, byte: 쪽번호 연결
    footnote_cont: int  # offset 31, byte: 각주번호 연결
    linked_file: bytes  # offset 32, kchar[40]: 연결 인쇄 파일 이름
    extra_comment: bytes  # offset 72, kchar[24]: 덧붙이는 말
    password: int  # offset 96, word: 암호 여부
    start_page: int  # offset 98, word: 시작페이지 번호
    footnote_start: int  # offset 100, word: 각주 시작 번호
    footnote_reserved: int  # offset 102, word: 예약
    footnote_sep_gap: int  # offset 104, hunit: 각주 분리선↔본문 간격
    footnote_body_gap: int  # offset 106, hunit: 각주↔본문 간격
    footnote_gap: int  # offset 108, hunit: 각주↔각주 간격
    footnote_paren: int  # offset 110, echar: ')' 여부
    footnote_sep_type: int  # offset 111, byte: 분리선 너비 종류
    border_margins: bytes  # offset 112, hunit[4]: 테두리 간격 (좌우위아래)
    border_type: int  # offset 120, word: 테두리 종류
    hide_blank_line: int  # offset 122, byte: 빈줄감춤
    frame_move: int  # offset 123, byte: 틀옮김
    compressed: bool  # offset 124, byte: 압축 여부
    sub_revision: int  # offset 125, byte: sub revision (1=글3.0이후)
    info_block_size: int  # offset 126, word: 정보 블록 길이 (바이트)

    @classmethod
    def from_bytes(cls, data: bytes) -> "DocumentInfo":
        if len(data) < DOCUMENT_INFO_SIZE:
            raise ValueError(f"문서 정보 크기 부족: {len(data)} < {DOCUMENT_INFO_SIZE}")
        d = data
        return cls(
            cursor_line=struct.unpack_from("<H", d, 0)[0],
            cursor_col=struct.unpack_from("<H", d, 2)[0],
            paper_type=d[4],
            paper_orient=d[5],
            paper_height=struct.unpack_from("<H", d, 6)[0],
            paper_width=struct.unpack_from("<H", d, 8)[0],
            margin_top=struct.unpack_from("<H", d, 10)[0],
            margin_bottom=struct.unpack_from("<H", d, 12)[0],
            margin_left=struct.unpack_from("<H", d, 14)[0],
            margin_right=struct.unpack_from("<H", d, 16)[0],
            header_size=struct.unpack_from("<H", d, 18)[0],
            footer_size=struct.unpack_from("<H", d, 20)[0],
            binding_margin=struct.unpack_from("<H", d, 22)[0],
            doc_protect=struct.unpack_from("<I", d, 24)[0],
            reserved=struct.unpack_from("<H", d, 28)[0],
            page_num_cont=d[30],
            footnote_cont=d[31],
            linked_file=d[32:72],
            extra_comment=d[72:96],
            password=struct.unpack_from("<H", d, 96)[0],
            start_page=struct.unpack_from("<H", d, 98)[0],
            footnote_start=struct.unpack_from("<H", d, 100)[0],
            footnote_reserved=struct.unpack_from("<H", d, 102)[0],
            footnote_sep_gap=struct.unpack_from("<H", d, 104)[0],
            footnote_body_gap=struct.unpack_from("<H", d, 106)[0],
            footnote_gap=struct.unpack_from("<H", d, 108)[0],
            footnote_paren=d[110],
            footnote_sep_type=d[111],
            border_margins=d[112:120],
            border_type=struct.unpack_from("<H", d, 120)[0],
            hide_blank_line=d[122],
            frame_move=d[123],
            compressed=bool(d[124]),
            sub_revision=d[125],
            info_block_size=struct.unpack_from("<H", d, 126)[0],
        )


# ---------------------------------------------------------------------------
# 문서 요약 (1008 bytes)
# ---------------------------------------------------------------------------


@dataclass
class DocumentSummary:
    """HWP 97 (V3.00) 문서 요약 (1008 bytes)

    모든 문자열은 hchar(2바이트) 배열로 저장됨.
    스펙: Section 3.3
    """

    title: bytes  # offset 0,   hchar[56] = 112 bytes
    subject: bytes  # offset 112, hchar[56] = 112 bytes
    author: bytes  # offset 224, hchar[56] = 112 bytes
    date: bytes  # offset 336, hchar[56] = 112 bytes
    keywords: bytes  # offset 448, hchar[112] = 224 bytes
    extra: bytes  # offset 672, hchar[168] = 336 bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> "DocumentSummary":
        if len(data) < DOCUMENT_SUMMARY_SIZE:
            raise ValueError(f"문서 요약 크기 부족: {len(data)} < {DOCUMENT_SUMMARY_SIZE}")
        return cls(
            title=data[0:112],
            subject=data[112:224],
            author=data[224:336],
            date=data[336:448],
            keywords=data[448:672],
            extra=data[672:1008],
        )

    def _decode_hchar_bytes(self, raw: bytes) -> str:
        """hchar 배열을 문자열로 디코딩 (Johab 2바이트 조합형)"""
        result = []
        for i in range(0, len(raw) - 1, 2):
            val = struct.unpack_from("<H", raw, i)[0]
            if val == 0:
                break
            if val < 0x80:
                result.append(chr(val))
            else:
                try:
                    # HWP 97 (V3.00) hchar는 big-endian Johab으로 디코딩
                    result.append(struct.pack(">H", val).decode("johab", errors="replace"))
                except Exception:
                    result.append("?")
        return "".join(result)

    @property
    def title_str(self) -> str:
        return self._decode_hchar_bytes(self.title)

    @property
    def author_str(self) -> str:
        return self._decode_hchar_bytes(self.author)

    @property
    def date_str(self) -> str:
        return self._decode_hchar_bytes(self.date)


# ---------------------------------------------------------------------------
# 글자 모양 (31 bytes)
# ---------------------------------------------------------------------------


@dataclass
class CharShape:
    """HWP 97 (V3.00) 글자 모양 (31 bytes)

    스펙: Section 6 (글자 모양 자료 구조)
    """

    char_size: int  # offset 0,  hunit: 글자 크기
    font_ids: bytes  # offset 2,  byte[7]: 언어별 글꼴 인덱스
    expansion: bytes  # offset 9,  byte[7]: 언어별 장평 비율 (50~200)
    spacing: bytes  # offset 16, sbyte[7]: 언어별 자간 비율 (-50~50)
    shade_color: int  # offset 23, byte: 음영색 (0-7)
    char_color: int  # offset 24, byte: 글자색 (0-7)
    shade_ratio: int  # offset 25, byte: 음영 비율 (0-100)
    attr: int  # offset 26, byte: 속성 비트 플래그
    reserved: bytes  # offset 27, byte[4]: 예약

    @classmethod
    def from_bytes(cls, data: bytes) -> "CharShape":
        if len(data) < CHAR_SHAPE_SIZE:
            raise ValueError(f"글자 모양 크기 부족: {len(data)} < {CHAR_SHAPE_SIZE}")
        return cls(
            char_size=struct.unpack_from("<H", data, 0)[0],
            font_ids=data[2:9],
            expansion=data[9:16],
            spacing=data[16:23],
            shade_color=data[23],
            char_color=data[24],
            shade_ratio=data[25],
            attr=data[26],
            reserved=data[27:31],
        )

    @property
    def font_size_pt(self) -> float:
        """글자 크기를 포인트로 변환 (hunit → inch → pt)
        hunit: 1/1800 inch, 1 inch = 72 pt
        """
        return self.char_size / 1800 * 72

    @property
    def italic(self) -> bool:
        return bool(self.attr & 0x01)

    @property
    def bold(self) -> bool:
        return bool(self.attr & 0x02)

    @property
    def underline(self) -> bool:
        return bool(self.attr & 0x04)

    @property
    def font_id(self) -> int:
        """한글 글꼴 인덱스 (font_ids[0])"""
        return self.font_ids[0] if self.font_ids else 0


# ---------------------------------------------------------------------------
# 스타일 (238 bytes)
# ---------------------------------------------------------------------------


@dataclass
class StyleEntry:
    """HWP 97 (V3.00) 스타일 항목 (238 bytes)

    스펙: Section 6 (스타일 자료 구조)
    """

    name: bytes  # offset 0,  kchar[20]: 스타일 이름
    char_shape: CharShape  # offset 20, 31 bytes
    para_shape_raw: bytes  # offset 51, 187 bytes

    @classmethod
    def from_bytes(cls, data: bytes) -> "StyleEntry":
        if len(data) < STYLE_ENTRY_SIZE:
            raise ValueError(f"스타일 크기 부족: {len(data)} < {STYLE_ENTRY_SIZE}")
        name = data[0:STYLE_NAME_SIZE]
        char_shape = CharShape.from_bytes(data[STYLE_NAME_SIZE : STYLE_NAME_SIZE + CHAR_SHAPE_SIZE])
        para_shape_raw = data[STYLE_NAME_SIZE + CHAR_SHAPE_SIZE : STYLE_ENTRY_SIZE]
        return cls(name=name, char_shape=char_shape, para_shape_raw=para_shape_raw)

    @property
    def name_str(self) -> str:
        try:
            raw = self.name.split(b"\x00")[0]
            # HWP 97 (V3.00) 스타일 이름은 Johab(조합형) 인코딩
            return raw.decode("johab", errors="replace")
        except Exception:
            return ""


# ---------------------------------------------------------------------------
# 줄 정보 (14 bytes)
# ---------------------------------------------------------------------------


@dataclass
class LineInfo:
    """HWP 97 (V3.00) 줄 정보 (14 bytes)

    스펙: Section 4.2
    """

    start_pos: int  # offset 0, word: 줄 시작 위치 (hchar 단위 오프셋)
    space_adj: int  # offset 2, hunit: 공백 보정값
    line_height: int  # offset 4, hunit: 줄 높이
    reserved: bytes  # offset 6, byte[6]: 예약
    boundary: int  # offset 12, word: 단/페이지 구분 (bit0=페이지, bit1=단)

    @classmethod
    def from_bytes(cls, data: bytes) -> "LineInfo":
        if len(data) < 14:
            raise ValueError(f"줄 정보 크기 부족: {len(data)} < 14")
        return cls(
            start_pos=struct.unpack_from("<H", data, 0)[0],
            space_adj=struct.unpack_from("<H", data, 2)[0],
            line_height=struct.unpack_from("<H", data, 4)[0],
            reserved=data[6:12],
            boundary=struct.unpack_from("<H", data, 12)[0],
        )


# ---------------------------------------------------------------------------
# 정보 블록 항목
# ---------------------------------------------------------------------------


@dataclass
class InfoBlock:
    """HWP 97 (V3.00) 정보 블록 항목 (파일 앞부분 미압축)

    구조: ID(word, 2) + 길이(word, 2) + 내용(n)
    """

    block_id: int
    data: bytes

    @classmethod
    def read_from_stream(cls, stream: BinaryIO) -> Optional["InfoBlock"]:
        header = stream.read(4)
        if len(header) < 4:
            return None
        block_id, length = struct.unpack_from("<HH", header)
        if block_id == 0 and length == 0:
            return None
        data = stream.read(length)
        return cls(block_id=block_id, data=data)


# ---------------------------------------------------------------------------
# 추가 정보 블록 항목
# ---------------------------------------------------------------------------


@dataclass
class ExtraBlock:
    """HWP 97 (V3.00) 추가 정보 블록 항목 (파일 끝부분)

    구조: ID(dword, 4) + 길이(dword, 4) + 내용(n)
    """

    block_id: int
    data: bytes

    @classmethod
    def read_from_stream(cls, stream: BinaryIO) -> Optional["ExtraBlock"]:
        header = stream.read(8)
        if len(header) < 8:
            return None
        block_id, length = struct.unpack_from("<II", header)
        if block_id == 0x80000000 and length == 0:
            return None
        data = stream.read(length)
        return cls(block_id=block_id, data=data)


"""
HWP 97 (V3.00) 문서 구조 파싱

HWP 97 (V3.00) 파일은 CFB(Compound File Binary) 포맷이 아닌 단순 바이너리 파일입니다.
파일 구조:
  [파일 인식 정보 30] [문서 정보 128] [문서 요약 1008] [정보 블록 n]
  [--- 이하 압축 가능 ---]
  [글꼴 이름] [스타일] [문단 리스트] [추가 정보 블록 #1]
  [추가 정보 블록 #2 (미압축)]

참고: 한글문서파일형식97분석보고서, Section 3 (전체 구조)
"""

import io
import struct
import zlib
from dataclasses import dataclass, field
from typing import BinaryIO, List, Optional

from .char_paragraph import HChar, HCharType, Paragraph
from .constants import (
    DOCUMENT_INFO_SIZE,
    DOCUMENT_SUMMARY_SIZE,
    FILE_SIGNATURE_SIZE,
    FONT_LANG_COUNT,
    FONT_NAME_SIZE,
    INFO_BLOCK_HEADER_SIZE,
    STYLE_ENTRY_SIZE,
    SpecialCharCode,
)
from .models import (
    CharShape,
    DocumentInfo,
    DocumentSummary,
    ExtraBlock,
    FileHeader,
    InfoBlock,
    StyleEntry,
)
from .parsed_elements import ParsedParagraph, ParsedTable, TableCell


# ---------------------------------------------------------------------------
# 글꼴 이름 파싱
# ---------------------------------------------------------------------------


def _parse_font_names(stream: BinaryIO) -> List[List[str]]:
    """글꼴 이름 파싱 (7개 언어 반복).

    각 언어: word(개수) + kchar[40] × 개수
    반환: [[한글 글꼴들], [영문 글꼴들], ..., [사용자 글꼴들]]
    """
    all_fonts: List[List[str]] = []
    for _ in range(FONT_LANG_COUNT):
        count_raw = stream.read(2)
        if len(count_raw) < 2:
            break
        count = struct.unpack_from("<H", count_raw)[0]
        lang_fonts: List[str] = []
        for _ in range(count):
            name_raw = stream.read(FONT_NAME_SIZE)
            if len(name_raw) < FONT_NAME_SIZE:
                break
            null_pos = name_raw.find(b"\x00")
            name_bytes = name_raw[:null_pos] if null_pos >= 0 else name_raw
            # HWP 97 (V3.00) 글꼴 이름은 Johab(조합형) 인코딩 (EUC-KR 아님)
            lang_fonts.append(name_bytes.decode("johab", errors="replace"))
        all_fonts.append(lang_fonts)
    return all_fonts


# ---------------------------------------------------------------------------
# 스타일 파싱
# ---------------------------------------------------------------------------


def _parse_styles(stream: BinaryIO) -> List[StyleEntry]:
    """스타일 파싱 (개수 word + StyleEntry × 개수)"""
    count_raw = stream.read(2)
    if len(count_raw) < 2:
        return []
    count = struct.unpack_from("<H", count_raw)[0]
    styles: List[StyleEntry] = []
    for _ in range(count):
        entry_raw = stream.read(STYLE_ENTRY_SIZE)
        if len(entry_raw) < STYLE_ENTRY_SIZE:
            break
        styles.append(StyleEntry.from_bytes(entry_raw))
    return styles


# ---------------------------------------------------------------------------
# 표 정보 파싱 (특수 문자 코드 10의 extra_data)
# ---------------------------------------------------------------------------


def _parse_table_from_extra(extra_data: bytes) -> Optional[ParsedTable]:
    """특수 문자 코드 10 (BOX)의 extra_data에서 표 정보 파싱.

    스펙: Section 10.6
    표 정보 구조 (82 bytes 실측, 스펙은 84 bytes 기재):
      offset 8:  byte - 기준 위치
      offset 9:  byte - 그림 피함
      offset 10: shunit - 가로 위치
      offset 12: shunit - 세로 위치
      offset 14: word - 기타 옵션 (bit4: 하이퍼텍스트 여부)
      offset 76: word - 박스 종류 (0=표, 1=텍스트박스, 2=수식, 3=버튼)  [실측]
      offset 78: word - 셀 개수 (표일 때 셀의 개수, 이외는 늘 1)  [실측]
    """
    if len(extra_data) < 82:
        return None

    # extra_data는 size(4) + 실제 내용이므로 offset 4부터 표 정보
    info_offset = 4  # 앞 4바이트는 size_raw

    if len(extra_data) < info_offset + 82:
        return None

    d = extra_data[info_offset:]

    x = struct.unpack_from("<h", d, 10)[0] if len(d) >= 14 else 0
    y = struct.unpack_from("<h", d, 12)[0] if len(d) >= 14 else 0
    options = struct.unpack_from("<H", d, 14)[0] if len(d) >= 16 else 0
    box_type = struct.unpack_from("<H", d, 76)[0] if len(d) >= 78 else 0
    cell_count = struct.unpack_from("<H", d, 78)[0] if len(d) >= 80 else 0
    is_hyperlink = bool(options & 0x10)  # bit4 = 하이퍼텍스트

    return ParsedTable(
        box_type=box_type,
        rows=0,
        cols=cell_count,  # 실제 row/col 은 셀 파싱 후 재계산
        x=x,
        y=y,
        is_hyperlink=is_hyperlink,
    )


# ---------------------------------------------------------------------------
# 문단 리스트 파싱 (재귀 가능)
# ---------------------------------------------------------------------------


def _parse_box_after_ident(stream: BinaryIO) -> List[ParsedParagraph]:
    """코드 10 식별정보 이후의 표/텍스트박스 내용 파싱.

    표 정보 (84 bytes) → 셀 정보 (27 bytes × 셀수) → 각 셀 문단리스트 × 셀수 → 캡션 문단리스트
    박스 종류: 0=표, 1=텍스트박스, 2=수식, 3=버튼.
    스펙 Section 10.6: 스펙 offset 78=박스 종류, offset 80=셀 개수이나
    실측으로는 offset 76=박스 종류, offset 78=셀 개수 (스펙보다 2바이트 앞).
    cell_count가 0이면 (텍스트박스/수식 등) 문단리스트 1개만 파싱.

    box_type > 3 이거나 cell_count > 256이면 렌더링 캐시 데이터로 간주하여 skip.

    Args:
        stream: 식별정보(8바이트) 이후 스트림

    Returns:
        표 안의 모든 셀 문단 리스트 (순서대로)
    """
    pos_before = stream.tell()
    table_info = stream.read(84)
    if len(table_info) < 84:
        return []

    box_type = struct.unpack_from("<H", table_info, 78)[0]
    cell_count = struct.unpack_from("<H", table_info, 80)[0]

    # 비정상 값이면 렌더링 캐시로 간주 → 위치 복구 후 빈 목록 반환
    if box_type > 3 or cell_count > 256:
        stream.seek(pos_before)
        return []

    # 셀 정보 (27 bytes × 셀수) skip
    stream.read(27 * cell_count)

    # 셀 개수가 0이면 텍스트박스/수식 등: 문단리스트 1개만 존재
    actual_count = cell_count if cell_count > 0 else 1

    # 각 셀(또는 내부)의 문단리스트 파싱 (재귀)
    all_paras: List[ParsedParagraph] = []
    for _ in range(actual_count):
        cell_paras = _parse_paragraph_list(stream)
        all_paras.extend(cell_paras)

    # 캡션 문단리스트 (항상 존재, 빈 문단으로 끝남)
    _parse_paragraph_list(stream)  # 캡션은 수집하지 않음

    return all_paras


def _parse_picture_after_ident(stream: BinaryIO) -> None:
    """코드 11 식별정보 이후의 그림 내용 skip.

    스펙 Section 10.7:
    그림 정보 (348 + n bytes) → 캡션 문단리스트

    Args:
        stream: 식별정보(8바이트) 이후 스트림
    """
    pic_info = stream.read(348)
    if len(pic_info) < 348:
        return
    n = struct.unpack_from("<I", pic_info, 0)[0]  # 추가 정보 길이
    stream.read(n)
    # 캡션 문단리스트 skip
    _parse_paragraph_list(stream)


def _skip_para_list_special(stream: BinaryIO, code: int) -> None:
    """문단리스트 포함 특수 코드(15,16,17)의 식별정보 이후 내용 skip.

    스펙:
    - 15(숨은설명): 예약(8) + 문단리스트
    - 16(머리말/꼬리말): 헤더(10) + 문단리스트
    - 17(각주/미주): 헤더(14) + 문단리스트
    """
    header_sizes = {15: 8, 16: 10, 17: 14}
    header_size = header_sizes.get(code, 0)
    stream.read(header_size)
    _parse_paragraph_list(stream)


def _skip_line_after_ident(stream: BinaryIO) -> None:
    """코드 14(선) 식별정보 이후의 선 정보 skip.

    스펙 Section 10.8: 선 정보 (84 bytes), 문단리스트 없음.
    """
    stream.read(84)


def _parse_paragraph_list(
    stream: BinaryIO,
) -> List[ParsedParagraph]:
    """문단 리스트를 읽어 ParsedParagraph 리스트 반환.

    빈 문단(char_count=0)이 나오면 리스트 종료.
    char_count > _MAX_CC이면 렌더링 캐시 진입으로 판단하여 즉시 종료.
    특수 문자(코드 10/11/14/15/16/17) 발견 시 스트림 직후 위치에서
    추가 데이터를 읽어 태그 체인 방식으로 재귀 파싱합니다.
    """
    paragraphs: List[ParsedParagraph] = []

    while True:
        pos_before = stream.tell()
        para = Paragraph.read_from_stream(stream)
        if para is None:
            break
        if para.is_empty:
            break

        # 렌더링 캐시 진입 감지 (두 가지 조건)
        # 1) char_count가 비현실적으로 크면 중단
        # 2) line_count=0이면서 char_count>0 → 렌더링 캐시 para (정상 para는 반드시 lc>=1)
        if para.info.char_count > _MAX_CC:
            stream.seek(pos_before)  # 잘못 읽은 위치 복구
            break
        if para.info.char_count > 0 and para.info.line_count == 0:
            stream.seek(pos_before)  # 잘못 읽은 위치 복구
            break

        text = para.to_string()
        repr_cs = para.info.repr_char_shape

        # 글자 모양 정보 구성
        char_shapes: List[tuple] = []
        for idx, cs in para.char_shape_map:
            if cs is not None:
                char_shapes.append((idx, cs))

        paragraphs.append(
            ParsedParagraph(
                text=text,
                char_shape=repr_cs,
                char_shapes=char_shapes,
                is_page_break=para.info.is_page_break,
                is_column_break=para.info.is_column_break,
                style_index=para.info.style_index,
            )
        )

        # 특수 문자(코드 10/11/14/15/16/17) 처리:
        # read_hchars에서 식별 정보(8B)만 소비하고 종료했으므로
        # 스트림 현재 위치가 해당 객체의 추가 데이터 시작점.
        for hc in para.chars or []:
            if hc.char_type.value == "special":
                code = hc.code
                if code == 10:  # 표/텍스트박스/수식
                    inner = _parse_box_after_ident(stream)
                    paragraphs.extend(inner)
                elif code == 11:  # 그림
                    _parse_picture_after_ident(stream)
                elif code == 14:  # 선
                    _skip_line_after_ident(stream)
                elif code in (15, 16, 17):  # 숨은설명/머리말꼬리말/각주미주
                    _skip_para_list_special(stream, code)
                break  # 문단당 인라인 객체는 1개

    return paragraphs


# ---------------------------------------------------------------------------
# 렌더링 캐시 감지 임계값
# ---------------------------------------------------------------------------

_MAX_CC = 300  # 이 이상의 char_count는 렌더링 캐시 데이터로 간주

# para list 시작 마커: follow_prev_shape=0, char_count>=1 의 특정 패턴
# HWP97 para list 헤더의 앞 4바이트: 00 05 00 01 (follow=0, char_count=5, line_count=1)
# 더 일반적: 첫 바이트 0x00, 두번째 1~300 (char_count), 세번째+네번째 line_count
_PARA_LIST_MARKER = bytes([0x00, 0x05, 0x00, 0x01])


def _find_all_para_list_starts(body: bytes, from_offset: int) -> List[int]:
    """body[from_offset:] 에서 para list 시작 마커(00 05 00 01) 위치 모두 반환.

    렌더링 캐시 진입 이전 범위만 탐색 (마지막 유효 마커 이후는 제외).
    """
    offsets: List[int] = []
    pos = from_offset
    while pos < len(body) - 4:
        idx = body.find(_PARA_LIST_MARKER, pos)
        if idx == -1:
            break
        offsets.append(idx)
        pos = idx + 4
    return offsets


def _parse_all_body_lists(body_stream: BinaryIO) -> List[ParsedParagraph]:
    """body_stream의 현재 위치부터 root para list + 이후 모든 para list 파싱.

    HWP 97 (V3.00) body는:
      1. root para list (스타일 직후, 문서 1페이지 포함)
      2. 이후 연속 para list들 (나머지 페이지들)
    각 para list는 마커(00 05 00 01)로 시작하며, 순차적으로 위치함.
    """
    # body_stream의 현재 위치 기록 (스타일 파싱 직후 = root list 시작)
    root_start = body_stream.tell()
    body_bytes = body_stream.read()  # 나머지 전체

    all_paragraphs: List[ParsedParagraph] = []

    # root para list 파싱
    root_stream = io.BytesIO(body_bytes)
    root_paras = _parse_paragraph_list(root_stream)
    all_paragraphs.extend(root_paras)

    # root list 종료 후 스트림 위치 파악
    root_end_rel = root_stream.tell()  # body_bytes 내 상대 위치

    # body_bytes 내 모든 para list 마커 위치 수집
    para_starts = _find_all_para_list_starts(body_bytes, root_end_rel)

    # 각 para list 순차 파싱 (이미 root의 재귀 파싱에서 처리된 것들은 건너뜀)
    parsed_offsets: set = set()
    for i, start in enumerate(para_starts):
        if start in parsed_offsets:
            continue

        # 다음 마커까지를 최대 범위로 설정 (최대 64KB)
        if i + 1 < len(para_starts):
            max_size = min(para_starts[i + 1] - start, 65536)
        else:
            max_size = 65536

        seg_stream = io.BytesIO(body_bytes[start : start + max_size])
        seg_paras = _parse_paragraph_list(seg_stream)
        all_paragraphs.extend(seg_paras)
        parsed_offsets.add(start)

    return all_paragraphs


# ---------------------------------------------------------------------------
# HWP 97 (V3.00) 파일 최상위 구조
# ---------------------------------------------------------------------------


@dataclass
class Hwp97File:
    """HWP 97 (V3.00) 파일 파싱 결과

    Attributes:
        file_header: 파일 인식 정보
        doc_info: 문서 정보
        doc_summary: 문서 요약
        info_blocks: 정보 블록 리스트 (미압축)
        font_names: 글꼴 이름 (7개 언어)
        styles: 스타일 리스트
        paragraphs: 문서 본문 문단 리스트
        extra_blocks: 추가 정보 블록 #1 리스트
        extra_blocks2: 추가 정보 블록 #2 리스트
    """

    file_header: FileHeader
    doc_info: DocumentInfo
    doc_summary: DocumentSummary
    info_blocks: List[InfoBlock] = field(default_factory=list)
    font_names: List[List[str]] = field(default_factory=list)
    styles: List[StyleEntry] = field(default_factory=list)
    paragraphs: List[ParsedParagraph] = field(default_factory=list)
    extra_blocks: List[ExtraBlock] = field(default_factory=list)
    extra_blocks2: List[ExtraBlock] = field(default_factory=list)

    @classmethod
    def from_file(cls, file_path: str) -> "Hwp97File":
        with open(file_path, "rb") as f:
            return cls.from_bytes(f.read())

    @classmethod
    def from_bytes(cls, data: bytes) -> "Hwp97File":
        stream = io.BytesIO(data)

        # 1. 파일 인식 정보 (30 bytes)
        file_header = FileHeader.from_stream(stream)

        # 2. 문서 정보 (128 bytes)
        doc_info = DocumentInfo.from_bytes(stream.read(DOCUMENT_INFO_SIZE))

        # 3. 문서 요약 (1008 bytes)
        doc_summary = DocumentSummary.from_bytes(stream.read(DOCUMENT_SUMMARY_SIZE))

        # 4. 정보 블록 (미압축, info_block_size 바이트)
        info_blocks: List[InfoBlock] = []
        if doc_info.info_block_size > 0:
            ib_data = stream.read(doc_info.info_block_size)
            ib_stream = io.BytesIO(ib_data)
            while True:
                ib = InfoBlock.read_from_stream(ib_stream)
                if ib is None:
                    break
                info_blocks.append(ib)

        # 5. 압축 영역 처리 (글꼴 ~ 추가 정보 블록 #1)
        remaining = stream.read()
        if doc_info.compressed and remaining:
            # gzip(deflate) 압축 해제 (wbits=-15: raw deflate)
            decompressed = zlib.decompress(remaining, -zlib.MAX_WBITS)
            body_stream = io.BytesIO(decompressed)
        else:
            body_stream = io.BytesIO(remaining)

        # 6. 글꼴 이름
        font_names = _parse_font_names(body_stream)

        # 7. 스타일
        styles = _parse_styles(body_stream)

        # 8. 문단 리스트 (태그 체인 방식: 특수 코드 10/11/14/15/16/17 재귀 파싱)
        #    root para list 파싱 후 body 나머지 영역의 추가 para list들도 순차 파싱
        paragraphs = _parse_all_body_lists(body_stream)

        # 9. 추가 정보 블록 #1 (압축 영역 끝부분)
        extra_blocks: List[ExtraBlock] = []
        while True:
            eb = ExtraBlock.read_from_stream(body_stream)
            if eb is None:
                break
            extra_blocks.append(eb)

        # 10. 추가 정보 블록 #2 (미압축, 원본 스트림 끝부분)
        # 압축 파일이면 extra_blocks2는 없을 수도 있음 (글 96 이후 추가)
        extra_blocks2: List[ExtraBlock] = []

        return cls(
            file_header=file_header,
            doc_info=doc_info,
            doc_summary=doc_summary,
            info_blocks=info_blocks,
            font_names=font_names,
            styles=styles,
            paragraphs=paragraphs,
            extra_blocks=extra_blocks,
            extra_blocks2=extra_blocks2,
        )

    def get_font_name(self, lang_idx: int, font_idx: int) -> str:
        """글꼴 이름 조회 (lang_idx: 0=한글, 1=영문, ...)"""
        if lang_idx < len(self.font_names) and font_idx < len(self.font_names[lang_idx]):
            return self.font_names[lang_idx][font_idx]
        return ""

    def get_style_name(self, style_idx: int) -> str:
        """스타일 이름 조회"""
        if style_idx < len(self.styles):
            return self.styles[style_idx].name_str
        return ""

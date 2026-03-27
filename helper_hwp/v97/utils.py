"""
유틸리티 함수

HWP 97 (V3.00) 파일 형식 스펙 기반 단위 변환 및 인코딩 헬퍼.
참고: 한글문서파일형식97분석보고서 Section 2 (자료형 설명)

hunit (= HUNIT): 1/1800 inch (v50의 hwpunit = 1/7200 inch 와 다름)
"""

# ---------------------------------------------------------------------------
# hunit 단위 변환
# ---------------------------------------------------------------------------


def hunit_to_cm(hunit: int) -> float:
    """hunit을 cm로 변환.

    hunit: 1/1800 inch
    1 inch = 2.54 cm

    Args:
        hunit: 변환할 hunit 값

    Returns:
        센티미터 단위 값

    Examples:
        >>> hunit_to_cm(1800)  # 1 inch
        2.54
    """
    return hunit / 1800 * 2.54


def hunit_to_inch(hunit: int) -> float:
    """hunit을 inch로 변환.

    Args:
        hunit: 변환할 hunit 값

    Returns:
        인치 단위 값

    Examples:
        >>> hunit_to_inch(1800)  # 1 inch
        1.0
    """
    return hunit / 1800


def hunit_to_px(hunit: int, dpi: int = 96) -> int:
    """hunit을 pixel로 변환.

    Args:
        hunit: 변환할 hunit 값
        dpi: 화면 해상도 (기본값: 96 DPI)

    Returns:
        픽셀 단위 정수 값

    Examples:
        >>> hunit_to_px(1800)  # 1 inch at 96 DPI
        96
    """
    return int(hunit / 1800 * dpi)


def hunit_to_pt(hunit: int) -> float:
    """hunit을 포인트(pt)로 변환.

    1 inch = 72 pt

    Args:
        hunit: 변환할 hunit 값

    Returns:
        포인트 단위 값

    Examples:
        >>> hunit_to_pt(1800)  # 1 inch = 72 pt
        72.0
    """
    return hunit / 1800 * 72


# ---------------------------------------------------------------------------
# 문자열 인코딩 헬퍼
# ---------------------------------------------------------------------------


def decode_kchar(raw: bytes) -> str:
    """kchar 배열(EUC-KR/CP949)을 Python str로 디코딩.

    HWP 97 (V3.00)의 kchar는 상용조합형 한글까지 표현 가능하나,
    실제 저장은 EUC-KR(CP949)로 처리합니다.

    Args:
        raw: kchar 배열 바이트

    Returns:
        디코딩된 문자열 (null 종료 기준으로 잘림)
    """
    null_pos = raw.find(b"\x00")
    if null_pos >= 0:
        raw = raw[:null_pos]
    return raw.decode("euc-kr", errors="replace")


def decode_hchar_array(raw: bytes) -> str:
    """hchar 배열(2바이트 코드)을 Python str로 디코딩.

    hchar: 한글 내부 코드 (한글/영문/한자 포함, 2바이트 고정).
    0x0001~0x007F 는 ASCII, 그 외는 EUC-KR 2바이트로 처리합니다.

    Args:
        raw: hchar 배열 바이트 (짝수 길이)

    Returns:
        디코딩된 문자열
    """
    import struct

    result = []
    for i in range(0, len(raw) - 1, 2):
        val = struct.unpack_from("<H", raw, i)[0]
        if val == 0:
            break
        if val < 0x80:
            result.append(chr(val))
        else:
            try:
                result.append(raw[i : i + 2].decode("euc-kr", errors="replace"))
            except Exception:
                result.append("?")
    return "".join(result)


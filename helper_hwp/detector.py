"""
HWP/HWPX 파일 포맷 자동 감지

magic bytes와 확장자 기반으로 파일 포맷을 판별합니다.

HWP 5.0 (CFB):
    - magic: D0 CF 11 E0 A1 B1 1A E1 (OLE Compound File)
    - 확장자: .hwp

HWPX (OWPML/ZIP):
    - magic: 50 4B 03 04 (ZIP Local File Header)
    - 확장자: .hwpx

판별 우선순위:
    1. magic bytes (내용 기반, 신뢰도 높음)
    2. 파일 확장자 (fallback)
"""

from enum import Enum, auto
from pathlib import Path
from typing import Union

# OLE Compound File Binary magic
_OLE_MAGIC = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
# ZIP Local File Header magic
_ZIP_MAGIC = b"\x50\x4b\x03\x04"
# HWP 1.x 파일 시그니처 (첫 21바이트 고정, V3.00 서명 공유)
_HWP10_MAGIC = b"HWP Document File V3."
# 읽을 바이트 수 (최소 21바이트)
_MAGIC_READ_SIZE = 21


class HwpFormat(Enum):
    """감지된 HWP 파일 포맷"""

    HWP_V10 = auto()  # HWP 97 (V3.00, 단순 바이너리, Johab 인코딩)
    HWP_V5 = auto()  # HWP 5.0 (OLE Compound File Binary)
    HWPX = auto()  # HWPX (OWPML, ZIP 기반)
    UNKNOWN = auto()  # 알 수 없음


def detect_format(file_path: Union[str, Path]) -> HwpFormat:
    """
    파일 포맷을 magic bytes + 확장자로 판별합니다.

    Args:
        file_path: 검사할 파일 경로

    Returns:
        HwpFormat 열거값
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")

    # 1단계: magic bytes 검사
    with open(path, "rb") as f:
        header = f.read(_MAGIC_READ_SIZE)

    if header[:21] == _HWP10_MAGIC:
        return HwpFormat.HWP_V10
    if header[:8] == _OLE_MAGIC:
        return HwpFormat.HWP_V5
    if header[:4] == _ZIP_MAGIC:
        return HwpFormat.HWPX

    # 2단계: 확장자 fallback
    suffix = path.suffix.lower()
    if suffix == ".hwp":
        return HwpFormat.HWP_V5
    if suffix == ".hwpx":
        return HwpFormat.HWPX

    return HwpFormat.UNKNOWN

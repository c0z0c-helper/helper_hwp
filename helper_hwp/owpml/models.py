"""
HWPX/OWPML 기본 데이터 모델

OWPML 문서 구조에서 추출된 메타 정보, 버전, 헤더 등을 표현합니다.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class HwpxVersion:
    """HWPX 문서 버전 정보 (header.xml에서 추출)"""

    major: int = 5
    minor: int = 0
    micro: int = 0
    build: int = 0

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.micro}.{self.build}"

    @classmethod
    def from_string(cls, value: str) -> "HwpxVersion":
        """
        '5.0.3.0' 형식 문자열에서 버전 파싱.
        파싱 실패 시 기본값 반환.
        """
        parts = value.strip().split(".")

        def safe(idx: int) -> int:
            try:
                return int(parts[idx])
            except (IndexError, ValueError):
                return 0

        return cls(safe(0), safe(1), safe(2), safe(3))


@dataclass
class HwpxHeader:
    """
    HWPX 문서 헤더 (Contents/header.xml 파싱 결과)

    Attributes:
        version: 문서 버전
        compressed: 압축 여부 (HWPX는 ZIP 기반이므로 항상 True)
        encrypted: 암호화 여부 (manifest.xml 내 encryption-data 존재 여부)
        section_count: 본문 섹션 수
        bin_items: 이진 데이터 목록 {id: src_path}
    """

    version: HwpxVersion = field(default_factory=HwpxVersion)
    compressed: bool = True
    encrypted: bool = False
    section_count: int = 1
    bin_items: Dict[str, str] = field(default_factory=dict)  # id -> src 경로


@dataclass
class CharRunInfo:
    """
    OWPML 텍스트 런(run/<t>) 서식 정보

    HWPX의 charPr(문자 속성) 요소에서 추출.
    """

    font_size: int = 10  # 글자 크기 (pt 단위, HWPX: 1/100 pt)
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color: Optional[str] = None  # "#RRGGBB" 형식
    font_name: Optional[str] = None


@dataclass
class BinItem:
    """
    HWPX 이진 데이터 항목 (header.xml binItem)

    Attributes:
        item_id: binItem id 속성 값
        src: 파일 내 경로 (예: "BinData/image1.png")
        format: 이미지 포맷 (png, jpg 등)
    """

    item_id: str
    src: str
    format: Optional[str] = None

    @property
    def filename(self) -> str:
        """파일명만 반환"""
        return self.src.split("/")[-1] if "/" in self.src else self.src

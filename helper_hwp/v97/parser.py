"""
HWP 97 (V3.00) 문서 파서 (고수준 API)

이 모듈은 HWP 97 (V3.00) 파일을 Pythonic하게 접근할 수 있도록
래핑한 고수준 API를 제공합니다.

참고: 한글문서파일형식97분석보고서
"""

import contextlib
from contextlib import contextmanager
from typing import Generator, List, Tuple

from .converters import convert_to_markdown, convert_to_text
from .document_structure import Hwp97File
from .parsed_elements import ParsedParagraph, ParsedTable


class Hwp97Document:
    """HWP 97 (V3.00) 문서 - 고수준 Pythonic API

    주요 기능:
    - paragraphs: 문단 리스트 (ParsedParagraph)
    - to_text: 문서 전체 텍스트 추출
    - to_markdown: 마크다운 변환
    - doc_info, doc_summary: 문서 메타데이터 접근
    """

    def __init__(self, file_path: str) -> None:
        """HWP 97 (V3.00) 파일 로드.

        Args:
            file_path: HWP 파일 경로
        """
        self._hwp = Hwp97File.from_file(file_path)
        self.file_path = file_path

    @property
    def doc_info(self):
        """문서 정보 (DocumentInfo)"""
        return self._hwp.doc_info

    @property
    def doc_summary(self):
        """문서 요약 (DocumentSummary)"""
        return self._hwp.doc_summary

    @property
    def compressed(self) -> bool:
        """압축 여부"""
        return self._hwp.doc_info.compressed

    @property
    def paragraphs(self) -> List[ParsedParagraph]:
        """문서 본문 문단 리스트"""
        return self._hwp.paragraphs

    @property
    def font_names(self) -> List[List[str]]:
        """글꼴 이름 (7개 언어)"""
        return self._hwp.font_names

    @property
    def styles(self):
        """스타일 리스트"""
        return self._hwp.styles

    def to_text(self) -> str:
        """문서 전체 텍스트 반환.

        Returns:
            줄바꿈으로 문단 구분된 문자열
        """
        return convert_to_text(self._hwp)

    def to_markdown(self) -> str:
        """문서를 마크다운으로 변환.

        Returns:
            마크다운 문자열
        """
        return convert_to_markdown(self._hwp)

    def iter_paragraphs(self) -> Generator[ParsedParagraph, None, None]:
        """문단 이터레이터"""
        yield from self._hwp.paragraphs

    def __enter__(self) -> "Hwp97Document":
        return self

    def __exit__(self, *args) -> None:
        pass

    def __repr__(self) -> str:
        return f"Hwp97Document(file_path='{self.file_path}', paragraphs={len(self.paragraphs)})"


# ---------------------------------------------------------------------------
# 편의 함수
# ---------------------------------------------------------------------------


@contextmanager
def open_hwp97(file_path: str):
    """HWP 97 (V3.00) 파일을 컨텍스트 매니저로 열기.

    Args:
        file_path: HWP 파일 경로

    Yields:
        Hwp97Document 인스턴스

    Examples:
        >>> with open_hwp97("test10.hwp") as doc:
        ...     print(doc.to_text())
    """
    doc = Hwp97Document(file_path)
    yield doc


def hwp97_to_txt(file_path: str) -> str:
    """HWP 97 (V3.00) 파일을 텍스트로 변환.

    Args:
        file_path: HWP 파일 경로

    Returns:
        변환된 텍스트 문자열
    """
    doc = Hwp97Document(file_path)
    return doc.to_text()


def hwp97_to_markdown(file_path: str) -> str:
    """HWP 97 (V3.00) 파일을 마크다운으로 변환.

    Args:
        file_path: HWP 파일 경로

    Returns:
        변환된 마크다운 문자열
    """
    doc = Hwp97Document(file_path)
    return doc.to_markdown()


# hwp97_to_md 는 hwp97_to_markdown 의 별칭
hwp97_to_md = hwp97_to_markdown


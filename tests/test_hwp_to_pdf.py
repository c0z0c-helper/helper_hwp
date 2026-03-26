"""
test_hwp_to_pdf.py

hwp_to_pdf pytest 테스트.
playwright 미설치 시 skip.
"""

from __future__ import annotations

from pathlib import Path

import pytest

TESTS_DIR = Path(__file__).parent
HWP_TEST = TESTS_DIR / "test.hwp"


def _has_playwright() -> bool:
    try:
        import playwright  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
@pytest.mark.skipif(not _has_playwright(), reason="playwright 미설치")
def test_hwp_to_pdf_creates_file(tmp_path):
    """hwp_to_pdf: PDF 파일 생성 확인"""
    from helper_hwp import hwp_to_pdf

    pdf_path = tmp_path / "output.pdf"
    result = hwp_to_pdf(str(HWP_TEST), str(pdf_path))
    assert Path(result).exists()
    assert Path(result).stat().st_size >= 1


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
@pytest.mark.skipif(not _has_playwright(), reason="playwright 미설치")
def test_hwp_to_pdf_default_path(tmp_path):
    """hwp_to_pdf: output_pdf_path=None 이면 동일 이름으로 생성"""
    import shutil
    from helper_hwp import hwp_to_pdf

    # tmp_path에 hwp 복사
    tmp_hwp = tmp_path / "test.hwp"
    shutil.copy(str(HWP_TEST), str(tmp_hwp))

    result = hwp_to_pdf(str(tmp_hwp))
    expected = tmp_path / "test.pdf"
    assert Path(result) == expected
    assert expected.exists()

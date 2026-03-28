"""
test_hwp_to_markdown.py

hwp_to_markdown, hwpx_to_markdown, auto_to_markdown pytest 테스트.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from helper_hwp import auto_to_markdown, hwp_to_markdown, hwp97_to_markdown

TESTS_DIR = Path(__file__).parent
HWP_TEST = TESTS_DIR / "test.hwp"
HWP_TABLE = TESTS_DIR / "testTable.hwp"
HWP_97 = TESTS_DIR / "test97.hwp"
HWPX_TEST = TESTS_DIR / "test.hwpx"


# ---------------------------------------------------------------------------
# test.hwp
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
def test_hwp_to_markdown_returns_string():
    """hwp_to_markdown: str 반환"""
    result = hwp_to_markdown(str(HWP_TEST))
    assert isinstance(result, str)
    assert len(result) >= 1


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
def test_hwp_to_markdown_contains_table():
    """hwp_to_markdown: 표가 포함된 경우 마크다운 표 구문 포함"""
    result = hwp_to_markdown(str(HWP_TEST))
    # 표가 있으면 | 구분자가 등장해야 함
    assert "|" in result


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
def test_hwp_to_markdown_save_file(tmp_path):
    """hwp_to_markdown: 결과를 파일로 저장 가능"""
    result = hwp_to_markdown(str(HWP_TEST))
    out = tmp_path / "output.md"
    out.write_text(result, encoding="utf-8")
    assert out.stat().st_size >= 1


# ---------------------------------------------------------------------------
# testTable.hwp
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HWP_TABLE.exists(), reason=f"{HWP_TABLE.name} 없음")
def test_table_hwp_markdown_has_table_syntax():
    """testTable.hwp: 마크다운 표 구문 포함"""
    result = hwp_to_markdown(str(HWP_TABLE))
    assert "|" in result
    assert "---" in result


# ---------------------------------------------------------------------------
# auto_to_markdown (포맷 자동 감지)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
def test_auto_to_markdown_hwp():
    """auto_to_markdown: .hwp 파일 자동 감지 변환"""
    result = auto_to_markdown(str(HWP_TEST))
    assert isinstance(result, str)
    assert len(result) >= 1


@pytest.mark.skipif(not HWPX_TEST.exists(), reason=f"{HWPX_TEST.name} 없음")
def test_auto_to_markdown_hwpx():
    """auto_to_markdown: .hwpx 파일 자동 감지 변환"""
    result = auto_to_markdown(str(HWPX_TEST))
    assert isinstance(result, str)
    assert len(result) >= 1


# ---------------------------------------------------------------------------
# test97.hwp (HWP V3.00)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HWP_97.exists(), reason=f"{HWP_97.name} 없음")
def test_hwp97_to_markdown_returns_string():
    """hwp97_to_markdown: str 반환"""
    result = hwp97_to_markdown(str(HWP_97))
    assert isinstance(result, str)
    assert len(result) >= 1


@pytest.mark.skipif(not HWP_97.exists(), reason=f"{HWP_97.name} 없음")
def test_hwp97_to_markdown_no_garbage():
    """hwp97_to_markdown: U+FFFD 깨진 문자 미포함"""
    result = hwp97_to_markdown(str(HWP_97))
    assert "\ufffd" not in result


@pytest.mark.skipif(not HWP_97.exists(), reason=f"{HWP_97.name} 없음")
def test_hwp97_to_markdown_contains_korean():
    """hwp97_to_markdown: 한글 제안요청서 표지 내용 포함"""
    result = hwp97_to_markdown(str(HWP_97))
    assert any(word in result for word in ["안 요 청 서", "사 업 명", "정보", "시스템"])

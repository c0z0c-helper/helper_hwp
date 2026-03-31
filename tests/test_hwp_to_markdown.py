"""
test_hwp_to_markdown.py

hwp_to_md, hwp_to_txt pytest 테스트.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from helper_hwp import hwp_to_md

TESTS_DIR = Path(__file__).parent
HWP_TEST = TESTS_DIR / "test.hwp"
HWP_TABLE = TESTS_DIR / "testTable.hwp"
HWP_97 = TESTS_DIR / "test97.hwp"
HWPX_TEST = TESTS_DIR / "test.hwpx"
OWPML_TEST = TESTS_DIR / "test.owpml"


# ---------------------------------------------------------------------------
# test.hwp
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
def test_hwp_to_markdown_returns_string():
    """hwp_to_md (hwp): str 반환"""
    result = hwp_to_md(str(HWP_TEST))
    assert isinstance(result, str)
    assert len(result) >= 1


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
def test_hwp_to_markdown_contains_table():
    """hwp_to_md (hwp): 표가 포함된 경우 마크다운 표 구문 포함"""
    result = hwp_to_md(str(HWP_TEST))
    assert "|" in result


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
def test_hwp_to_markdown_save_file(tmp_path):
    """hwp_to_md (hwp): 결과를 파일로 저장 가능"""
    result = hwp_to_md(str(HWP_TEST))
    out = tmp_path / "output.md"
    out.write_text(result, encoding="utf-8")
    assert out.stat().st_size >= 1


# ---------------------------------------------------------------------------
# testTable.hwp
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HWP_TABLE.exists(), reason=f"{HWP_TABLE.name} 없음")
def test_table_hwp_markdown_has_table_syntax():
    """testTable.hwp: 마크다운 표 구문 포함"""
    result = hwp_to_md(str(HWP_TABLE))
    assert "|" in result
    assert "---" in result


# ---------------------------------------------------------------------------
# hwp_to_md (포맷 자동 감지)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
def test_auto_to_md_hwp():
    """hwp_to_md: .hwp 파일 자동 감지 변환"""
    result = hwp_to_md(str(HWP_TEST))
    assert isinstance(result, str)
    assert len(result) >= 1


@pytest.mark.skipif(not HWPX_TEST.exists(), reason=f"{HWPX_TEST.name} 없음")
def test_auto_to_md_hwpx():
    """hwp_to_md: .hwpx 파일 자동 감지 변환"""
    result = hwp_to_md(str(HWPX_TEST))
    assert isinstance(result, str)
    assert len(result) >= 1


# ---------------------------------------------------------------------------
# test97.hwp (HWP V3.00)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HWP_97.exists(), reason=f"{HWP_97.name} 없음")
def test_hwp97_to_markdown_returns_string():
    """hwp_to_md (hwp97): str 반환"""
    result = hwp_to_md(str(HWP_97))
    assert isinstance(result, str)
    assert len(result) >= 1


@pytest.mark.skipif(not HWP_97.exists(), reason=f"{HWP_97.name} 없음")
def test_hwp97_to_markdown_no_garbage():
    """hwp_to_md (hwp97): U+FFFD 깨진 문자 미포함"""
    result = hwp_to_md(str(HWP_97))
    assert "\ufffd" not in result


@pytest.mark.skipif(not HWP_97.exists(), reason=f"{HWP_97.name} 없음")
def test_hwp97_to_markdown_contains_korean():
    """hwp_to_md (hwp97): 한글 제안요청서 표지 내용 포함"""
    result = hwp_to_md(str(HWP_97))
    assert any(word in result for word in ["안 요 청 서", "사 업 명", "정보", "시스템"])


# ---------------------------------------------------------------------------
# HWPX 표 마크다운 형식
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HWPX_TEST.exists(), reason=f"{HWPX_TEST.name} 없음")
def test_hwpx_to_markdown_contains_table():
    """hwp_to_md (hwpx): 표가 마크다운 표 형식 (|, ---) 으로 포함"""
    result = hwp_to_md(str(HWPX_TEST))
    assert "|" in result
    assert "---" in result


# ---------------------------------------------------------------------------
# OWPML 표 마크다운 형식
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not OWPML_TEST.exists(), reason=f"{OWPML_TEST.name} 없음")
def test_owpml_to_markdown_contains_table():
    """hwp_to_md (owpml): 표가 마크다운 표 형식 (|, ---) 으로 포함"""
    result = hwp_to_md(str(OWPML_TEST))
    assert "|" in result
    assert "---" in result


@pytest.mark.skipif(not OWPML_TEST.exists(), reason=f"{OWPML_TEST.name} 없음")
def test_owpml_to_markdown_no_inline_table_marker():
    """hwp_to_md (owpml): '[표:' 인라인 마커가 없어야 함"""
    result = hwp_to_md(str(OWPML_TEST))
    assert "[표:" not in result

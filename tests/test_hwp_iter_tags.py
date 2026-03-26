"""
test_hwp_iter_tags.py

open_hwp() iter_tags 기반 순회 pytest 테스트.
test.hwp, testTable.hwp, test장평.hwp 대상.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from helper_hwp import ElementType, IterMode, open_hwp

TESTS_DIR = Path(__file__).parent
HWP_TEST = TESTS_DIR / "test.hwp"
HWP_TABLE = TESTS_DIR / "testTable.hwp"
HWP_JANGPYEONG = TESTS_DIR / "test장평.hwp"


# ---------------------------------------------------------------------------
# 보조 함수
# ---------------------------------------------------------------------------


def _collect_tags(hwp_path: Path, mode: IterMode = IterMode.SEQUENTIAL) -> dict:
    """iter_tags 결과를 ElementType별 카운트로 집계"""
    counts: dict = {}
    with open_hwp(str(hwp_path), mode) as doc:
        for etype, _ in doc.iter_tags():
            counts[etype] = counts.get(etype, 0) + 1
    return counts


# ---------------------------------------------------------------------------
# test.hwp — 기본 검증
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
def test_open_hwp_file_info():
    """HwpDocument 기본 속성 확인"""
    with open_hwp(str(HWP_TEST)) as doc:
        assert doc.version is not None
        assert isinstance(doc.compressed, bool)
        assert isinstance(doc.encrypted, bool)
        assert len(doc.sections) >= 1


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
def test_iter_tags_sequential_has_paragraphs():
    """SEQUENTIAL 모드: PARAGRAPH 요소 1개 이상 존재"""
    counts = _collect_tags(HWP_TEST, IterMode.SEQUENTIAL)
    assert counts.get(ElementType.PARAGRAPH, 0) >= 1


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
def test_iter_tags_sequential_paragraph_text():
    """SEQUENTIAL 모드: 첫 비어있지 않은 문단 텍스트 확인"""
    with open_hwp(str(HWP_TEST)) as doc:
        for etype, elem in doc.iter_tags():
            if etype == ElementType.PARAGRAPH and elem.text.strip():
                assert len(elem.text) >= 1
                return
    pytest.fail("비어있지 않은 PARAGRAPH 요소를 찾지 못함")


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
def test_iter_tags_structured_has_section():
    """STRUCTURED 모드: SECTION 요소 1개 이상 존재"""
    counts = _collect_tags(HWP_TEST, IterMode.STRUCTURED)
    assert counts.get(ElementType.SECTION, 0) >= 1


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
def test_iter_tags_structured_has_paragraphs():
    """STRUCTURED 모드: PARAGRAPH 요소 1개 이상 존재"""
    counts = _collect_tags(HWP_TEST, IterMode.STRUCTURED)
    assert counts.get(ElementType.PARAGRAPH, 0) >= 1


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
def test_iter_tags_table_metadata():
    """표가 있는 경우 TABLE 요소에 rows/cols 정보 존재"""
    with open_hwp(str(HWP_TEST)) as doc:
        for etype, elem in doc.iter_tags():
            if etype == ElementType.TABLE:
                assert elem.rows is not None
                assert elem.cols is not None
                assert elem.rows >= 1
                assert elem.cols >= 1
                return
    pytest.skip("표 요소 없음")


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
def test_char_shape_info():
    """문단 글자 모양 정보가 존재함"""
    with open_hwp(str(HWP_TEST)) as doc:
        for etype, elem in doc.iter_tags():
            if etype == ElementType.PARAGRAPH and elem.char_shape:
                assert elem.char_shape.font_size > 0
                return
    pytest.skip("char_shape 있는 PARAGRAPH 없음")


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
def test_to_text_not_empty():
    """to_text() 결과가 비어있지 않음"""
    with open_hwp(str(HWP_TEST)) as doc:
        text = doc.to_text()
    assert isinstance(text, str)
    assert len(text) >= 1


# ---------------------------------------------------------------------------
# testTable.hwp — 표 전용 검증
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HWP_TABLE.exists(), reason=f"{HWP_TABLE.name} 없음")
def test_table_hwp_has_table():
    """testTable.hwp: TABLE 요소 1개 이상"""
    counts = _collect_tags(HWP_TABLE)
    assert counts.get(ElementType.TABLE, 0) >= 1


@pytest.mark.skipif(not HWP_TABLE.exists(), reason=f"{HWP_TABLE.name} 없음")
def test_table_hwp_cell_para_counts():
    """testTable.hwp: cell_para_counts 배열 존재"""
    with open_hwp(str(HWP_TABLE)) as doc:
        for etype, elem in doc.iter_tags():
            if etype == ElementType.TABLE:
                assert elem.cell_para_counts is not None
                assert len(elem.cell_para_counts) >= 1
                return
    pytest.fail("TABLE 요소 없음")


# ---------------------------------------------------------------------------
# test장평.hwp — 장평(expansion) 속성 검증
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HWP_JANGPYEONG.exists(), reason=f"{HWP_JANGPYEONG.name} 없음")
def test_jangpyeong_hwp_paragraphs():
    """test장평.hwp: PARAGRAPH 요소 존재"""
    counts = _collect_tags(HWP_JANGPYEONG)
    assert counts.get(ElementType.PARAGRAPH, 0) >= 1

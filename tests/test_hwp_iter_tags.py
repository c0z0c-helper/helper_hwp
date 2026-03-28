"""
test_hwp_iter_tags.py

open_hwp() iter_tags 기반 순회 pytest 테스트.
test.hwp, testTable.hwp, test장평.hwp 대상.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from helper_hwp import ElementType, IterMode, open_hwp, hwp97_to_txt

TESTS_DIR = Path(__file__).parent
HWP_TEST = TESTS_DIR / "test.hwp"
HWP_TABLE = TESTS_DIR / "testTable.hwp"
HWP_JANGPYEONG = TESTS_DIR / "test장평.hwp"
HWP_97 = TESTS_DIR / "test97.hwp"


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


# ---------------------------------------------------------------------------
# test97.hwp — HWP V3.00 (hwp97_to_txt 기반)
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HWP_97.exists(), reason=f"{HWP_97.name} 없음")
def test_hwp97_to_txt_returns_string():
    """hwp97_to_txt: str 반환"""
    result = hwp97_to_txt(str(HWP_97))
    assert isinstance(result, str)
    assert len(result) >= 1


@pytest.mark.skipif(not HWP_97.exists(), reason=f"{HWP_97.name} 없음")
def test_hwp97_to_txt_no_garbage():
    """hwp97_to_txt: U+FFFD 깨진 문자 미포함"""
    result = hwp97_to_txt(str(HWP_97))
    assert "\ufffd" not in result


@pytest.mark.skipif(not HWP_97.exists(), reason=f"{HWP_97.name} 없음")
def test_hwp97_to_txt_paragraph_count():
    """hwp97_to_txt: 최소 100개 이상 줄 포함 (636 non-empty 기준)"""
    result = hwp97_to_txt(str(HWP_97))
    lines = [ln for ln in result.splitlines() if ln.strip()]
    assert len(lines) >= 100


@pytest.mark.skipif(not HWP_97.exists(), reason=f"{HWP_97.name} 없음")
def test_hwp97_to_txt_contains_cover_text():
    """hwp97_to_txt: 표지 핵심 텍스트 포함"""
    result = hwp97_to_txt(str(HWP_97))
    assert "제 안 요 청 서" in result

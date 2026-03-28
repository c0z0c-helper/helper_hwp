"""
test_convert_outputs.py

hwp / hwpx / owpml 파일을 md, txt 로 변환하여 tests/output/ 에 저장하는 테스트.

저장 경로 규칙:
    tests/output/<원본파일명>.<변환포맷>
    예) test.hwp  → tests/output/test.hwp.md
                  → tests/output/test.hwp.txt
        test.hwpx → tests/output/test.hwpx.md
                  → tests/output/test.hwpx.txt
"""

from __future__ import annotations

from pathlib import Path

import pytest

from helper_hwp import (
    auto_to_markdown,
    auto_to_txt,
    hwp_to_markdown,
    hwp_to_txt,
    hwp97_to_markdown,
    hwp97_to_txt,
    hwpx_to_markdown,
    hwpx_to_txt,
)

TESTS_DIR = Path(__file__).parent
OUTPUT_DIR = TESTS_DIR / "output"

# 테스트 대상 파일
HWP_TEST = TESTS_DIR / "test.hwp"
HWP_TABLE = TESTS_DIR / "testTable.hwp"
HWP_97 = TESTS_DIR / "test97.hwp"
HWP_JANGPYEONG = TESTS_DIR / "test장평.hwp"
HWPX_TEST = TESTS_DIR / "test.hwpx"
OWPML_TEST = TESTS_DIR / "test.owpml"


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------


def _save(src: Path, ext: str, content: str) -> Path:
    """OUTPUT_DIR/<원본파일명>.<ext> 로 저장 후 경로 반환"""
    OUTPUT_DIR.mkdir(exist_ok=True)
    out = OUTPUT_DIR / f"{src.name}.{ext}"
    out.write_text(content, encoding="utf-8")
    return out


# ---------------------------------------------------------------------------
# HWP 5.0 — txt
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
def test_save_test_hwp_txt():
    """test.hwp → txt 변환 저장"""
    txt = hwp_to_txt(str(HWP_TEST))
    assert isinstance(txt, str) and len(txt) >= 1
    out = _save(HWP_TEST, "txt", txt)
    assert out.stat().st_size >= 1


@pytest.mark.skipif(not HWP_TABLE.exists(), reason=f"{HWP_TABLE.name} 없음")
def test_save_testTable_hwp_txt():
    """testTable.hwp → txt 변환 저장"""
    txt = hwp_to_txt(str(HWP_TABLE))
    assert isinstance(txt, str) and len(txt) >= 1
    out = _save(HWP_TABLE, "txt", txt)
    assert out.stat().st_size >= 1


@pytest.mark.skipif(not HWP_97.exists(), reason=f"{HWP_97.name} 없음")
def test_save_test97_hwp_txt():
    """test97.hwp → txt 변환 저장 (한글 텍스트 포함 확인)"""
    txt = hwp97_to_txt(str(HWP_97))
    assert isinstance(txt, str) and len(txt) >= 1
    # 기본 표지 텍스트 포함 확인
    assert any(word in txt for word in ["안", "사트", "정보", "구축"])
    # 깨진 문자(�) 미포함 확인
    assert "\ufffd" not in txt
    out = _save(HWP_97, "txt", txt)
    assert out.stat().st_size >= 1


@pytest.mark.skipif(not HWP_JANGPYEONG.exists(), reason=f"{HWP_JANGPYEONG.name} 없음")
def test_save_jangpyeong_hwp_txt():
    """test장평.hwp → txt 변환 저장"""
    txt = hwp_to_txt(str(HWP_JANGPYEONG))
    assert isinstance(txt, str) and len(txt) >= 1
    out = _save(HWP_JANGPYEONG, "txt", txt)
    assert out.stat().st_size >= 1


# ---------------------------------------------------------------------------
# HWP 5.0 — md
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HWP_TEST.exists(), reason=f"{HWP_TEST.name} 없음")
def test_save_test_hwp_md():
    """test.hwp → md 변환 저장"""
    md = hwp_to_markdown(str(HWP_TEST))
    assert isinstance(md, str) and len(md) >= 1
    out = _save(HWP_TEST, "md", md)
    assert out.stat().st_size >= 1


@pytest.mark.skipif(not HWP_TABLE.exists(), reason=f"{HWP_TABLE.name} 없음")
def test_save_testTable_hwp_md():
    """testTable.hwp → md 변환 저장 (표 구문 포함 확인)"""
    md = hwp_to_markdown(str(HWP_TABLE))
    assert "|" in md and "---" in md
    out = _save(HWP_TABLE, "md", md)
    assert out.stat().st_size >= 1


@pytest.mark.skipif(not HWP_97.exists(), reason=f"{HWP_97.name} 없음")
def test_save_test97_hwp_md():
    """test97.hwp → md 변환 저장 (한글 텍스트 포함 확인)"""
    md = hwp97_to_markdown(str(HWP_97))
    assert isinstance(md, str) and len(md) >= 1
    # 기본 표지 텍스트 포함 확인
    assert any(word in md for word in ["안", "사트", "정보", "구축"])
    # 깨진 문자(�) 미포함 확인
    assert "\ufffd" not in md
    out = _save(HWP_97, "md", md)
    assert out.stat().st_size >= 1


@pytest.mark.skipif(not HWP_JANGPYEONG.exists(), reason=f"{HWP_JANGPYEONG.name} 없음")
def test_save_jangpyeong_hwp_md():
    """test장평.hwp → md 변환 저장"""
    md = hwp_to_markdown(str(HWP_JANGPYEONG))
    assert isinstance(md, str) and len(md) >= 1
    out = _save(HWP_JANGPYEONG, "md", md)
    assert out.stat().st_size >= 1


# ---------------------------------------------------------------------------
# HWPX — txt
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HWPX_TEST.exists(), reason=f"{HWPX_TEST.name} 없음")
def test_save_test_hwpx_txt():
    """test.hwpx → txt 변환 저장"""
    txt = hwpx_to_txt(str(HWPX_TEST))
    assert isinstance(txt, str) and len(txt) >= 1
    out = _save(HWPX_TEST, "txt", txt)
    assert out.stat().st_size >= 1


# ---------------------------------------------------------------------------
# HWPX — md
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HWPX_TEST.exists(), reason=f"{HWPX_TEST.name} 없음")
def test_save_test_hwpx_md():
    """test.hwpx → md 변환 저장"""
    md = hwpx_to_markdown(str(HWPX_TEST))
    assert isinstance(md, str) and len(md) >= 1
    out = _save(HWPX_TEST, "md", md)
    assert out.stat().st_size >= 1


# ---------------------------------------------------------------------------
# OWPML (.owpml) — auto 감지 → txt, md
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not OWPML_TEST.exists(), reason=f"{OWPML_TEST.name} 없음")
def test_save_test_owpml_txt():
    """test.owpml → auto_to_txt 변환 저장"""
    txt = auto_to_txt(str(OWPML_TEST))
    assert isinstance(txt, str) and len(txt) >= 1
    out = _save(OWPML_TEST, "txt", txt)
    assert out.stat().st_size >= 1


@pytest.mark.skipif(not OWPML_TEST.exists(), reason=f"{OWPML_TEST.name} 없음")
def test_save_test_owpml_md():
    """test.owpml → auto_to_markdown 변환 저장"""
    md = auto_to_markdown(str(OWPML_TEST))
    assert isinstance(md, str) and len(md) >= 1
    out = _save(OWPML_TEST, "md", md)
    assert out.stat().st_size >= 1

"""빈 문단(글자 수 0, 문단 리스트 끝)은 43바이트로 끝나야 한다 (문단 모양 187바이트 없음)."""
import io

from helper_hwp.v97.char_paragraph import ParaInfo


def test_empty_paragraph_does_not_consume_para_shape():
    data = bytes(43) + b"NEXT" * 100
    stream = io.BytesIO(data)
    info = ParaInfo.from_stream(stream)
    assert info is not None
    assert info.char_count == 0
    assert info.para_shape_raw is None
    assert stream.tell() == 43


def test_table_2x2_all_cells_read():
    """이슈 #1: 빈 문단을 230바이트로 읽어 둘째 셀부터 비던 문제."""
    from pathlib import Path

    from helper_hwp.constants import ElementType
    from helper_hwp.v97.parser import open_hwp97

    path = Path(__file__).parent / "hwp3-table-2x2.hwp"
    with open_hwp97(str(path)) as doc:
        tables = [e for et, e in doc.iter_tags() if et == ElementType.TABLE]
    assert len(tables) == 1
    assert [c.text.strip() for c in tables[0].cells] == ["CELL-A1", "CELL-B1", "CELL-A2", "CELL-B2"]

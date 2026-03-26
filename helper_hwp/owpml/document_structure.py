"""
HWPX 문서 구조 파싱 (ZIP + XML 기반)

HWPX 파일의 ZIP 패키지를 열고 Contents/header.xml, Contents/section*.xml을
파싱하여 문서 구조 객체로 반환합니다.

OWPML 파일 구조:
    META-INF/manifest.xml       - 파일 목록 및 암호화 여부
    Contents/header.xml         - 문서 헤더 (버전, binItem, 스타일 등)
    Contents/section0.xml       - 본문 섹션 0
    Contents/section1.xml       - 본문 섹션 1 (있을 경우)
    BinData/                    - 이미지 등 이진 데이터
"""

import logging
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .constants import OwpmlTag, SectionPath
from .models import BinItem, HwpxHeader, HwpxVersion

logger = logging.getLogger(__name__)


def _local(tag: str) -> str:
    """'{namespace}localname' → 'localname'"""
    return tag.split("}")[1] if "}" in tag else tag


# ---------------------------------------------------------------------------
# 저수준 XML 데이터 클래스
# ---------------------------------------------------------------------------


@dataclass
class RawRun:
    """단일 텍스트 런 (<t> 요소 1개)"""

    text: str
    char_pr_id: Optional[str] = None  # charPr id 참조 (서식 연결용)


@dataclass
class RawParagraph:
    """섹션 내 원시 문단 (<p> 요소)"""

    runs: List[RawRun] = field(default_factory=list)
    para_pr_id: Optional[str] = None  # paraPr id 참조
    is_page_break: bool = False  # 쪽 나누기 여부

    @property
    def text(self) -> str:
        return "".join(r.text for r in self.runs)


@dataclass
class RawTableCell:
    """표 셀 (<tc> 요소)"""

    row: int
    col: int
    rowspan: int = 1
    colspan: int = 1
    paragraphs: List[RawParagraph] = field(default_factory=list)

    @property
    def text(self) -> str:
        lines = [p.text for p in self.paragraphs if p.text]
        return "\n".join(lines)


@dataclass
class RawTable:
    """표 (<tbl> 요소)"""

    rows: int = 0
    cols: int = 0
    cells: List[RawTableCell] = field(default_factory=list)

    def to_markdown(self) -> str:
        if not self.cells:
            return ""
        grid: Dict[Tuple[int, int], str] = {
            (c.row, c.col): c.text.replace("\n", " ").replace("|", "\\|") for c in self.cells
        }
        row_count = max(c.row for c in self.cells) + 1
        col_count = max(c.col for c in self.cells) + 1
        lines = []
        for r in range(row_count):
            cells_text = [grid.get((r, c), "") for c in range(col_count)]
            lines.append("| " + " | ".join(cells_text) + " |")
            if r == 0:
                lines.append("| " + " | ".join(["---"] * col_count) + " |")
        return "\n".join(lines)

    def to_text(self) -> str:
        if not self.cells:
            return ""
        grid: Dict[Tuple[int, int], str] = {
            (c.row, c.col): c.text.replace("\n", " ") for c in self.cells
        }
        row_count = max(c.row for c in self.cells) + 1
        col_count = max(c.col for c in self.cells) + 1
        lines = []
        for r in range(row_count):
            lines.append("\t".join(grid.get((r, c), "") for c in range(col_count)))
        return "\n".join(lines)


@dataclass
class RawSection:
    """본문 섹션 (section*.xml 1개에 대응)"""

    index: int
    paragraphs: List[RawParagraph] = field(default_factory=list)
    tables: List[RawTable] = field(default_factory=list)


# ---------------------------------------------------------------------------
# XML 파서 헬퍼
# ---------------------------------------------------------------------------


class _SectionParser:
    """section*.xml을 파싱하여 RawSection 반환"""

    def parse(self, xml_bytes: bytes, index: int) -> RawSection:
        root = ET.fromstring(xml_bytes)
        section = RawSection(index=index)
        self._walk(root, section)
        return section

    def _walk(self, elem: ET.Element, section: RawSection) -> None:
        tag = _local(elem.tag)
        if tag == OwpmlTag.P:
            para = self._parse_paragraph(elem)
            section.paragraphs.append(para)
        elif tag == OwpmlTag.TBL:
            tbl = self._parse_table(elem)
            section.tables.append(tbl)
            # 표도 문단 리스트에 sentinel로 추가 (순서 보존)
            section.paragraphs.append(RawParagraph())  # 빈 문단 placeholder
        else:
            for child in elem:
                self._walk(child, section)

    def _parse_paragraph(self, p_elem: ET.Element) -> RawParagraph:
        para = RawParagraph()
        para_pr = p_elem.get("paraPrIDRef") or p_elem.get("paraPrId")
        if para_pr:
            para.para_pr_id = para_pr
        self._collect_runs(p_elem, para)
        return para

    def _collect_runs(self, elem: ET.Element, para: RawParagraph) -> None:
        tag = _local(elem.tag)
        if tag == OwpmlTag.T and elem.text:
            run = RawRun(text=elem.text)
            # 부모 run 요소의 charPrIDRef 접근은 재귀 한 단계 위에서 처리
            para.runs.append(run)
        elif tag == OwpmlTag.TBL:
            # 문단 내 중첩 표: 텍스트로 인라인 처리
            tbl = self._parse_table(elem)
            if tbl.cells:
                inline = " ".join(c.text.replace("\n", " ") for c in tbl.cells if c.text)
                para.runs.append(RawRun(text=f"[표: {inline}]"))
        elif tag in (OwpmlTag.FOOT_NOTE, OwpmlTag.END_NOTE):
            # 각주/미주 내용은 별도로 수집하지 않고 표시자만 추가
            pass
        else:
            for child in elem:
                self._collect_runs(child, para)

    def _parse_table(self, tbl_elem: ET.Element) -> RawTable:
        tbl = RawTable()
        row_idx = 0
        for child in tbl_elem:
            tag = _local(child.tag)
            if tag == OwpmlTag.TR:
                cells = self._parse_row(child, row_idx)
                tbl.cells.extend(cells)
                row_idx += 1
            else:
                # tbl 속성 요소 (tblPr 등) 건너뜀
                for sub in child:
                    if _local(sub.tag) == OwpmlTag.TR:
                        cells = self._parse_row(sub, row_idx)
                        tbl.cells.extend(cells)
                        row_idx += 1
        if tbl.cells:
            tbl.rows = max(c.row for c in tbl.cells) + 1
            tbl.cols = max(c.col for c in tbl.cells) + 1
        return tbl

    def _parse_row(self, tr_elem: ET.Element, row_idx: int) -> List[RawTableCell]:
        cells = []
        col_idx = 0
        for child in tr_elem:
            tag = _local(child.tag)
            if tag == OwpmlTag.TC:
                cell = RawTableCell(row=row_idx, col=col_idx)
                # colspan / rowspan
                cell.colspan = int(child.get("colSpan", child.get("colspan", 1)))
                cell.rowspan = int(child.get("rowSpan", child.get("rowspan", 1)))
                # 셀 내 문단 수집
                for sub in child:
                    if _local(sub.tag) == OwpmlTag.P:
                        para = self._parse_paragraph(sub)
                        cell.paragraphs.append(para)
                    else:
                        for ssub in sub:
                            if _local(ssub.tag) == OwpmlTag.P:
                                cell.paragraphs.append(self._parse_paragraph(ssub))
                cells.append(cell)
                col_idx += 1
        return cells


# ---------------------------------------------------------------------------
# 헤더 파서
# ---------------------------------------------------------------------------


class _HeaderParser:
    """Contents/header.xml 파싱"""

    def parse(self, xml_bytes: bytes) -> HwpxHeader:
        header = HwpxHeader()
        root = ET.fromstring(xml_bytes)
        for elem in root.iter():
            tag = _local(elem.tag)
            if tag == "version":
                ver_str = elem.get("value") or elem.get("version") or elem.text or ""
                if ver_str:
                    header.version = HwpxVersion.from_string(ver_str)
            elif tag == OwpmlTag.BIN_ITEM:
                item_id = elem.get("id", "")
                src = elem.get("src", "")
                if item_id and src:
                    header.bin_items[item_id] = src
        return header


# ---------------------------------------------------------------------------
# HwpxFile: 최상위 진입점
# ---------------------------------------------------------------------------


class HwpxFile:
    """
    HWPX 파일 핸들러

    ZIP 패키지를 열고 header, section 들을 파싱하여 보관합니다.
    v50의 HwpFile에 대응하는 클래스입니다.

    사용법:
        hwpx = HwpxFile.from_file("doc.hwpx")
        for section in hwpx.sections:
            for para in section.paragraphs:
                print(para.text)
    """

    def __init__(self, header: HwpxHeader, sections: List[RawSection]):
        self.header = header
        self.sections = sections

    @classmethod
    def from_file(cls, file_path: str) -> "HwpxFile":
        """
        HWPX 파일을 파싱하여 HwpxFile 반환.

        Args:
            file_path: HWPX 파일 경로
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {file_path}")
        if not zipfile.is_zipfile(str(path)):
            raise ValueError(f"유효하지 않은 HWPX 파일입니다: {file_path}")

        with zipfile.ZipFile(str(path), "r") as zf:
            names = set(zf.namelist())

            # 암호화 확인
            encrypted = False
            if SectionPath.MANIFEST in names:
                manifest_bytes = zf.read(SectionPath.MANIFEST)
                encrypted = b"encryption-data" in manifest_bytes.lower()

            # 헤더 파싱
            header = HwpxHeader()
            header.encrypted = encrypted
            if SectionPath.HEADER in names:
                header_bytes = zf.read(SectionPath.HEADER)
                header = _HeaderParser().parse(header_bytes)
                header.encrypted = encrypted

            if encrypted:
                raise ValueError("암호화된 HWPX 파일은 지원하지 않습니다.")

            # 섹션 파일 목록 수집
            section_files = sorted(
                name
                for name in names
                if name.startswith(SectionPath.SECTION_PREFIX)
                and name.endswith(SectionPath.SECTION_EXT)
            )
            header.section_count = len(section_files)

            # 섹션 파싱
            parser = _SectionParser()
            sections: List[RawSection] = []
            for idx, sec_path in enumerate(section_files):
                xml_bytes = zf.read(sec_path)
                section = parser.parse(xml_bytes, idx)
                sections.append(section)

        return cls(header=header, sections=sections)

    @property
    def version(self) -> HwpxVersion:
        return self.header.version

    @property
    def encrypted(self) -> bool:
        return self.header.encrypted

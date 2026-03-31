# 사용자 가이드

helper_hwp 라이브러리 사용 방법을 안내합니다.

## 목차

- [1. 시작하기](#1-시작하기)
- [2. 기본 사용법](#2-기본-사용법)
- [3. 고급 기능](#3-고급-기능)
- [4. CLI 사용법](#4-cli-사용법)
- [5. API 레퍼런스](#5-api-레퍼런스)
- [6. 예제](#6-예제)
- [7. 문제 해결](#7-문제-해결)

---

## 1. 시작하기

### 1.1. 설치

```bash
pip install helper-hwp
```

선택적 의존성 설치:

```bash
# HTML/DOCX 변환 기능
pip install "helper-hwp[doc]"

# PDF 변환 기능
pip install "helper-hwp[pdf]"
```

### 1.2. 지원 포맷

| 포맷 | 확장자 | 설명 |
| --- | --- | --- |
| HWP 5.x | `.hwp` | OLE Compound File Binary 기반 |
| HWP 97 | `.hwp` | V3.00 단순 바이너리 (Johab 인코딩) |
| HWPX | `.hwpx` | OWPML/ZIP 기반 XML 포맷 |

`hwp_open()` 는 파일 내용(magic bytes)을 읽어 세 포맷을 자동 감지합니다.

### 1.3. 첫 번째 프로그램

```python
from helper_hwp import hwp_to_txt, hwp_to_md

# 텍스트 추출 (포맷 자동 감지)
text = hwp_to_txt('example.hwp')
print(text)

# 마크다운 변환
md = hwp_to_md('example.hwpx')
print(md)
```

---

## 2. 기본 사용법

### 2.1. 텍스트 추출

```python
from helper_hwp import hwp_to_txt

text = hwp_to_txt('document.hwp')
print(text)
```

### 2.2. 마크다운 변환

헤더, 볼드, 표 구조를 마크다운으로 변환합니다.

```python
from helper_hwp import hwp_to_md

markdown = hwp_to_md('document.hwp')

with open('output.md', 'w', encoding='utf-8') as f:
    f.write(markdown)
```

**출력 예시:**
```markdown
# 제목

## 부제목

본문 텍스트입니다.

**굵은 글씨**

| 열1 | 열2 | 열3 |
| --- | --- | --- |
| A | B | C |
| D | E | F |
```

### 2.3. 문서 열기 (Hwp50Document)

포맷 자동 감지로 문서 객체를 반환합니다. context manager 사용을 권장합니다.

```python
from helper_hwp import hwp_open

with hwp_open('document.hwp') as doc:
    print(f"버전: {doc.version}")          # HWP 5.x
    print(f"섹션 수: {len(doc.sections)}")
    print(f"압축 여부: {doc.compressed}")
```

HWP 97 파일도 동일하게 사용합니다:

```python
with hwp_open('document_old.hwp') as doc:
    print(f"압축 여부: {doc.compressed}")
    print(f"문단 수: {len(doc.paragraphs)}")
```

HWPX 파일도 동일합니다:

```python
with hwp_open('document.hwpx') as doc:
    for etype, elem in doc.iter_tags():
        print(etype, elem)
```

---

## 3. 고급 기능

### 3.1. 포맷 감지

```python
from helper_hwp import detect_format, HwpFormat

fmt = detect_format('document.hwp')

if fmt == HwpFormat.HWP_V5:
    print("HWP 5.x 포맷")
elif fmt == HwpFormat.HWP_V10:
    print("HWP 97 포맷")
elif fmt == HwpFormat.HWPX:
    print("HWPX 포맷")
```

### 3.2. 요소 순회 (iter_tags)

세 포맷 모두 동일한 인터페이스를 사용합니다.

```python
from helper_hwp import hwp_open, ElementType

with hwp_open('document.hwp') as doc:
    for element_type, element in doc.iter_tags():
        if element_type == ElementType.PARAGRAPH:
            print(f"문단: {element.text}")
        elif element_type == ElementType.TABLE:
            print(f"표: {element.rows}행 x {element.cols}열")
        elif element_type == ElementType.PAGE_BREAK:
            print("--- 페이지 구분 ---")
```

### 3.3. ElementType 전체 목록

| ElementType | v50 | v97 | owpml | 설명 |
| --- | :---: | :---: | :---: | --- |
| PARAGRAPH | O | O | O | 문단 |
| TABLE | O | O | O | 표 |
| PAGE_BREAK | O | O | O | 페이지 구분 |
| SECTION | - | - | O | 섹션 (STRUCTURED 모드) |
| PICTURE | O | O | - | 그림 |
| EQUATION | O | O | - | 수식 |
| FOOTNOTE | O | - | O | 각주 |
| ENDNOTE | O | - | O | 미주 |
| HYPERLINK | O | O | O | 하이퍼링크 |
| FIELD | O | - | O | 필드 |
| SHAPE | O | - | - | 도형 |
| SHAPE_COMPONENT | O | - | - | 도형 컴포넌트 |
| COMMENT | O | - | - | 메모 |
| OLE | O | - | O | OLE 객체 |
| HEADER | O | - | - | 머리글 |
| FOOTER | O | - | - | 바닥글 |
| CAPTION | O | - | - | 캡션 |
| CTRL_HEADER | O | - | - | 컨트롤 헤더 |
| CTRL_DATA | O | - | - | 컨트롤 데이터 |
| LIST_HEADER | O | - | - | 목록 헤더 |
| PAGE_DEF | O | - | - | 페이지 정의 |
| AUTO_NUMBER | O | - | - | 자동 번호 |
| NEW_NUMBER | O | - | - | 새 번호 |
| PAGE_NUM_POS | O | - | - | 페이지 번호 위치 |
| BOOKMARK | O | O | O | 책갈피 |

### 3.4. 글자 모양 정보

HWP 5.x 문단에서 글자 모양 정보를 읽습니다.

```python
from helper_hwp import hwp_open, ElementType

with hwp_open('document.hwp') as doc:
    for element_type, element in doc.iter_tags():
        if element_type == ElementType.PARAGRAPH:
            if element.char_shape:
                print(f"폰트 크기: {element.char_shape.font_size}")
                print(f"굵기: {element.char_shape.bold}")
                print(f"이태릭: {element.char_shape.italic}")
```

### 3.5. 표 데이터 추출

```python
from helper_hwp import hwp_open, ElementType

with hwp_open('document.hwp') as doc:
    for element_type, element in doc.iter_tags():
        if element_type == ElementType.TABLE:
            print(f"표 {element.table_index}")
            print(f"  크기: {element.rows}행 x {element.cols}열")
            print(f"  셀 수: {element.cell_count}")
            print(f"  셀별 문단 수: {element.cell_para_counts}")
```

### 3.6. 페이지 단위 처리 (HWP 5.x)

```python
from helper_hwp import open_hwp50

with open_hwp50('document.hwp') as doc:
    for page in doc.pages:
        print(f"\n=== 페이지 {page.page_number} ===")
        for paragraph in page.paragraphs:
            if paragraph.text:
                print(paragraph.text)
```

### 3.7. 순회 모드 (IterMode)

#### SEQUENTIAL 모드 (기본)

문서 출현 순서대로 빠르게 순회합니다.

```python
from helper_hwp import hwp_open, IterMode

with hwp_open('document.hwp', IterMode.SEQUENTIAL) as doc:
    for element_type, element in doc.iter_tags():
        print(element_type, element)
```

#### STRUCTURED 모드

계층 구조(Section → Paragraph → Char)를 유지하며 순회합니다.

```python
from helper_hwp import hwp_open, IterMode

with hwp_open('document.hwp', IterMode.STRUCTURED) as doc:
    for element_type, element in doc.iter_tags():
        print(element_type, element)
```

### 3.8. HWPUNIT 단위 변환

```python
from helper_hwp import hwp50_unit_to_cm, hwp50_unit_to_inch, hwp50_unit_to_px

hwpunit = 1000

print(f"{hwpunit} HWPUNIT = {hwp50_unit_to_cm(hwpunit)} cm")
print(f"{hwpunit} HWPUNIT = {hwp50_unit_to_inch(hwpunit)} inch")
print(f"{hwpunit} HWPUNIT = {hwp50_unit_to_px(hwpunit)} px (96 DPI)")
print(f"{hwpunit} HWPUNIT = {hwp50_unit_to_px(hwpunit, dpi=300)} px (300 DPI)")
```

### 3.9. HWP 97 전용 API

포맷을 명시적으로 지정할 경우 사용합니다.

```python
from helper_hwp import open_hwp97, Hwp97Document

with open_hwp97('document_old.hwp') as doc:
    print(f"문단 수: {len(doc.paragraphs)}")
    print(f"문서 제목: {doc.doc_summary}")

    for etype, elem in doc.iter_tags():
        if etype.value == 'paragraph':
            print(elem.text)
```

### 3.10. HWPX 전용 API

```python
from helper_hwp import open_hwpx, HwpxDocument

with open_hwpx('document.hwpx') as doc:
    for etype, elem in doc.iter_tags():
        print(etype, elem)
```

---

## 4. CLI 사용법

설치 후 다음 명령어를 터미널에서 사용할 수 있습니다.

### 4.1. hwp2txt

HWP/HWPX 파일을 텍스트로 변환합니다.

```bash
hwp2txt document.hwp
hwp2txt document.hwp -o output.txt
```

### 4.2. hwp2md

HWP/HWPX 파일을 마크다운으로 변환합니다.

```bash
hwp2md document.hwp
hwp2md document.hwpx -o output.md
```

### 4.3. hwp2html

HWP 파일을 HTML로 변환합니다 (`helper-md-doc` 패키지 필요).

```bash
pip install "helper-hwp[doc]"
hwp2html document.hwp -o output.html
```

### 4.4. hwp2doc

HWP 파일을 DOCX로 변환합니다 (`helper-md-doc` 패키지 필요).

```bash
hwp2doc document.hwp -o output.docx
```

### 4.5. hwp2pdf

HWP 파일을 PDF로 변환합니다 (`helper-md-doc` + `playwright` 필요).

```bash
pip install "helper-hwp[pdf]"
hwp2pdf document.hwp -o output.pdf
```

---

## 5. API 레퍼런스

### 5.1. 통합 API (포맷 자동 감지, 권장)

#### `hwp_open(file_path, iter_mode=IterMode.SEQUENTIAL)`

파일 포맷을 자동 감지하여 Document 객체를 반환합니다.

- `file_path` (str): HWP/HWPX 파일 경로
- `iter_mode` (IterMode): 순회 모드
- 반환: `Hwp50Document` / `Hwp97Document` / `HwpxDocument`

#### `hwp_to_txt(file_path)`

텍스트를 추출합니다. 반환: `str`

#### `hwp_to_md(file_path)`

마크다운으로 변환합니다. 반환: `str`

#### `hwp_to_pdf(file_path, output_path)`

PDF로 변환합니다 (`playwright` 필요). 반환: `str` (출력 파일 경로)

#### `detect_format(file_path)`

파일 포맷을 감지합니다. 반환: `HwpFormat`

### 5.2. Hwp50Document (HWP 5.x)

#### 속성

| 속성 | 타입 | 설명 |
| --- | --- | --- |
| `version` | `Hwp50Version` | 문서 버전 |
| `compressed` | `bool` | 압축 여부 |
| `encrypted` | `bool` | 암호화 여부 |
| `sections` | `List` | 섹션 리스트 |
| `pages` | `List[Hwp50Page]` | 페이지 리스트 |

#### 메서드

##### `iter_tags(mode=None)`

`(ElementType, element)` 튜플을 yield하는 제너레이터입니다.

```python
for element_type, element in doc.iter_tags():
    if element_type == ElementType.PARAGRAPH:
        print(element.text)
```

##### `get_elements_by_type(element_type)`

특정 타입 요소를 검색합니다.

```python
paragraphs = doc.get_elements_by_type(ElementType.PARAGRAPH)
tables = doc.get_elements_by_type(ElementType.TABLE)
```

##### `to_text()`

전체 텍스트를 추출합니다. 반환: `str`

### 5.3. Hwp97Document (HWP 97)

#### 속성

| 속성 | 타입 | 설명 |
| --- | --- | --- |
| `compressed` | `bool` | 압축 여부 |
| `paragraphs` | `List[Hwp97Paragraph]` | 문단 리스트 |
| `doc_info` | `Hwp97DocumentInfo` | 문서 정보 |
| `doc_summary` | `DocumentSummary` | 문서 요약 |

#### 메서드

`iter_tags()`, `to_text()`, `to_markdown()` 은 HwpDocument와 동일한 인터페이스입니다.

### 5.4. HwpxDocument (HWPX)

`iter_tags()`, `to_text()`, `to_markdown()` 은 HwpDocument와 동일한 인터페이스입니다.

### 5.5. Hwp50Paragraph / Hwp97Paragraph / HwpxParagraph

| 속성 | 타입 | 설명 |
| --- | --- | --- |
| `text` | `str` | 문단 텍스트 |
| `paragraph` | `Paragraph` | 원본 문단 객체 |
| `char_shape` | `CharShapeInfo` | 글자 모양 (폰트 크기, 굵기, 이탤릭) |
| `char_shapes` | `List` | 위치별 글자 모양 |

### 5.6. Hwp50Table / Hwp97Table / HwpxTable

| 속성 | 타입 | 설명 |
| --- | --- | --- |
| `table_index` | `int` | 표 인덱스 |
| `rows` | `int` | 행 수 |
| `cols` | `int` | 열 수 |
| `cell_count` | `int` | 셀 개수 |
| `cell_para_counts` | `List[int]` | 셀별 문단 수 |
| `cell_widths` | `List[int]` | 셀 너비 (HWPUNIT) |
| `cell_heights` | `List[int]` | 셀 높이 (HWPUNIT) |
| `cell_colspans` | `List[int]` | 셀 병합 (가로) |
| `cell_rowspans` | `List[int]` | 셀 병합 (세로) |

### 5.7. Hwp50Page / HwpxPage (HWP 5.x / HWPX)

| 속성 | 타입 | 설명 |
| --- | --- | --- |
| `page_number` | `int` | 페이지 번호 |
| `paragraphs` | `List[ParsedParagraph]` | 문단 리스트 |

### 5.8. HwpFormat (감지 결과)

| 값 | 설명 |
| --- | --- |
| `HwpFormat.HWP_V5` | HWP 5.x (OLE CFB) |
| `HwpFormat.HWP_V10` | HWP 97 (V3.00, 단순 바이너리) |
| `HwpFormat.HWPX` | HWPX (OWPML, ZIP) |
| `HwpFormat.UNKNOWN` | 알 수 없음 |

---

## 6. 예제

### 예제 1: 텍스트 추출 및 파일 저장

```python
from helper_hwp import hwp_to_txt
from pathlib import Path

text = hwp_to_txt('example.hwp')
Path('output.txt').write_text(text, encoding='utf-8')
print("변환 완료: output.txt")
```

### 예제 2: 마크다운 변환 및 파일 저장

```python
from helper_hwp import hwp_to_md
from pathlib import Path

markdown = hwp_to_md('example.hwp')
Path('output.md').write_text(markdown, encoding='utf-8')
print("변환 완료: output.md")
```

### 예제 3: 표 데이터 추출

```python
from helper_hwp import hwp_open, ElementType

with hwp_open('document.hwp') as doc:
    for etype, elem in doc.iter_tags():
        if etype == ElementType.TABLE:
            print(f"\n표 {elem.table_index}: {elem.rows}행 x {elem.cols}열")
            print(f"셀별 문단 수: {elem.cell_para_counts}")
```

### 예제 4: 문서 정보 추출

```python
from helper_hwp import hwp_open, ElementType, detect_format

fmt = detect_format('document.hwp')
print(f"포맷: {fmt}")

with hwp_open('document.hwp') as doc:
    print(f"압축: {doc.compressed}")
    print(f"문단 수: {len(doc.get_elements_by_type(ElementType.PARAGRAPH))}")
    print(f"표 수: {len(doc.get_elements_by_type(ElementType.TABLE))}")
```

### 예제 5: JSON으로 변환

```python
from helper_hwp import hwp_open, ElementType
import json

with hwp_open('document.hwp') as doc:
    data = {'paragraphs': [], 'tables': []}

    for etype, elem in doc.iter_tags():
        if etype == ElementType.PARAGRAPH:
            data['paragraphs'].append({
                'text': elem.text,
                'font_size': elem.char_shape.font_size if elem.char_shape else None,
                'bold': elem.char_shape.bold if elem.char_shape else None,
            })
        elif etype == ElementType.TABLE:
            data['tables'].append({
                'index': elem.table_index,
                'rows': elem.rows,
                'cols': elem.cols,
            })

with open('output.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

### 예제 6: HWP 97 문서 처리

```python
from helper_hwp import open_hwp, ElementType, HwpFormat, detect_format

fmt = detect_format('old_document.hwp')
print(f"포맷: {fmt}")  # HwpFormat.HWP_V10

with open_hwp('old_document.hwp') as doc:
    for etype, elem in doc.iter_tags():
        if etype == ElementType.PARAGRAPH:
            print(elem.text)
```

### 예제 7: HWPX 문서 처리

```python
from helper_hwp import hwp_open, ElementType

with hwp_open('document.hwpx') as doc:
    for etype, elem in doc.iter_tags():
        if etype == ElementType.PARAGRAPH and elem.text:
            print(elem.text)
        elif etype == ElementType.TABLE:
            print(f"표: {elem.rows}x{elem.cols}")
```

### 예제 8: 대용량 파일 처리

```python
from helper_hwp import hwp_open, ElementType

with hwp_open('large_document.hwp') as doc:
    count = 0
    for etype, elem in doc.iter_tags():
        if etype == ElementType.PARAGRAPH:
            count += 1
            if '중요' in elem.text:
                print(f"[{count}] {elem.text}")
```

---

## 7. 문제 해결

### Q1: 파일을 찾을 수 없습니다

```
FileNotFoundError: [Errno 2] No such file or directory: 'example.hwp'
```

절대 경로 또는 올바른 상대 경로를 사용하세요.

```python
from pathlib import Path

hwp_file = Path('example.hwp')
if not hwp_file.exists():
    raise FileNotFoundError(f"파일 없음: {hwp_file}")
text = to_txt(str(hwp_file))
```

### Q2: 암호화된 파일은 지원하나요?

현재 버전에서는 암호화된 HWP 5.x 파일의 복호화를 지원하지 않습니다. 한글에서 암호화를 해제한 후 사용하세요.

```python
from helper_hwp import hwp_open

with hwp_open('document.hwp') as doc:
    if doc.encrypted:
        print("암호화된 파일입니다. 한글에서 암호화를 해제해 주세요.")
```

### Q3: 표가 제대로 추출되지 않습니다

`cell_para_counts`를 확인하여 셀 구조를 파악하세요.

```python
from helper_hwp import hwp_open, ElementType

with hwp_open('document.hwp') as doc:
    for etype, elem in doc.iter_tags():
        if etype == ElementType.TABLE:
            print(f"행/열: {elem.rows} x {elem.cols}")
            print(f"셀 문단 수: {elem.cell_para_counts}")
```

### Q4: 특정 문자가 깨집니다

파일 저장 시 UTF-8 인코딩을 명시하세요.

```python
text = hwp_to_txt('document.hwp')
with open('output.txt', 'w', encoding='utf-8') as f:
    f.write(text)
```

HWP 97 파일의 경우 Johab(cp949) 인코딩을 사용하며, 라이브러리가 내부적으로 UTF-8로 변환합니다.

### Q5: 지원 버전은 어떻게 되나요?

| 포맷 | 지원 여부 |
| --- | --- |
| HWP 5.x (CFB 기반, `.hwp`) | 지원 |
| HWP 97 (V3.00, `.hwp`) | 지원 |
| HWPX (OWPML, `.hwpx`) | 지원 |
| HWP 3.0 이하 | 미지원 |

### Q6: `open_hwp`과 `open_hwp_v50`의 차이는?

| 함수 | 설명 |
| --- | --- |
| `hwp_open` | 포맷 자동 감지 후 적절한 Document 반환 (권장) |
| `open_hwp50` | HWP 5.x 전용 파서 직접 호출 |
| `open_hwp97` | HWP 97 전용 파서 직접 호출 |
| `open_hwpx` | HWPX 전용 파서 직접 호출 |

---

## 추가 리소스

- [GitHub 저장소](https://github.com/c0z0c-helper/helper_hwp)
- [개발자 문서](DEVELOPER.md)
- [예제 코드](../examples/)

## 라이센스

Apache License 2.0

출처: [https://github.com/c0z0c-helper/helper_hwp](https://github.com/c0z0c-helper/helper_hwp)

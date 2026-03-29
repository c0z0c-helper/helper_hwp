# 개발자 문서

helper_hwp 프로젝트 개발에 참여하기 위한 가이드입니다.

## 목차

- [1. 프로젝트 구조](#1-프로젝트-구조)
- [2. 아키텍처](#2-아키텍처)
- [3. 개발 환경 설정](#3-개발-환경-설정)
- [4. 코드 스타일](#4-코드-스타일)
- [5. 테스트](#5-테스트)
- [6. 기여 방법](#6-기여-방법)
- [7. 릴리스 프로세스](#7-릴리스-프로세스)

---

## 1. 프로젝트 구조

```
helper_hwp/
├── helper_hwp/                  # 메인 패키지
│   ├── __init__.py              # 패키지 초기화 및 공개 API
│   ├── constants.py             # 공통 Enum (ElementType, IterMode) - 3포맷 공유
│   ├── detector.py              # 파일 포맷 자동 감지 (magic bytes + 확장자)
│   ├── converters.py            # 통합 변환 API (open_hwp, to_txt, to_md, to_pdf)
│   ├── cli.py                   # CLI 진입점 (hwp2txt, hwp2md, hwp2html 등)
│   │
│   ├── v50/                     # HWP 5.x (OLE Compound File Binary) 파서
│   │   ├── __init__.py
│   │   ├── document_structure.py  # CFB 스토리지 파싱, HwpFile, Section
│   │   ├── char_paragraph.py      # 문단 및 문자 처리
│   │   ├── parsed_elements.py     # ParsedParagraph, ParsedTable, ParsedPage
│   │   ├── parser.py              # HwpDocument (고수준 API)
│   │   ├── models.py              # Version, Header 데이터 모델
│   │   ├── constants.py           # v50 내부 상수 (RecordTag, ControlID 등)
│   │   ├── converters.py          # v50 전용 변환 헬퍼
│   │   ├── iterators.py           # SEQUENTIAL/STRUCTURED 순회 구현
│   │   ├── record_stream.py       # 레코드 스트림 처리
│   │   ├── requirements_rnac.py   # 의존성 검사
│   │   └── utils.py               # HWPUNIT 단위 변환
│   │
│   ├── v97/                     # HWP 97 (V3.00, 단순 바이너리) 파서
│   │   ├── __init__.py
│   │   ├── document_structure.py  # Hwp97File (Johab 인코딩 바이너리 파싱)
│   │   ├── char_paragraph.py      # 문단 및 문자 처리
│   │   ├── parsed_elements.py     # ParsedParagraph, ParsedTable
│   │   ├── parser.py              # Hwp97Document (고수준 API)
│   │   ├── models.py              # DocumentInfo, DocumentSummary
│   │   ├── constants.py           # v97 내부 상수 (SpecialCharCode, BoxType 등)
│   │   ├── converters.py          # v97 전용 변환 헬퍼
│   │   └── utils.py               # v97 유틸리티
│   │
│   └── owpml/                   # HWPX (OWPML, ZIP/XML) 파서
│       ├── __init__.py
│       ├── document_structure.py  # HwpxFile (ZIP 압축 해제 + XML 파싱)
│       ├── parsed_elements.py     # ParsedParagraph, ParsedTable, ParsedPage
│       ├── parser.py              # HwpxDocument (고수준 API)
│       ├── models.py              # HwpxVersion, HwpxHeader
│       └── constants.py           # owpml 내부 상수 (OwpmlTag 등)
│
├── tests/                       # 테스트 코드
│   ├── conftest.py
│   ├── test_hwp_iter_tags.py
│   ├── test_hwp_to_markdown.py
│   ├── test_hwp_to_pdf.py
│   ├── test_convert_outputs.py
│   ├── test.hwp                  # HWP 5.x 테스트 파일
│   ├── test97.hwp                # HWP 97 테스트 파일
│   ├── test.hwpx                 # HWPX 테스트 파일
│   └── testTable.hwp             # 표 테스트 파일
│
├── examples/                    # 사용 예제
│   ├── example_hwp_to_txt.py
│   ├── example_hwp_to_markdown.py
│   ├── example_iter_tags.py
│   └── example_iter_tags_to_json.py
│
├── docs/                        # 문서
│   ├── USER_GUIDE.md
│   ├── DEVELOPER.md
│   ├── 한글문서파일형식5.0분석보고서.md
│   ├── 한글문서파일형식97분석보고서.md
│   ├── hwp_format_spec.md
│   ├── 한글문서파일형식_5.0_revision1.3.txt
│   └── 한글문서파일형식3.0_HWPML_revision1.2.txt
│
├── pyproject.toml               # 프로젝트 설정 (버전, 의존성, CLI 진입점)
├── README.md
├── CHANGELOG.md
└── LICENSE
```

---

## 2. 아키텍처

### 2.1. 포맷 자동 감지 흐름

```
파일
  ↓ detector.detect_format()
    magic bytes(D0CF... / 504B... / "HWP Document File V3.") 우선 판별
    → HwpFormat.HWP_V5 / HWP_V10 / HWPX / UNKNOWN
  ↓ converters.open_hwp()
    HWP_V5  → open_hwp_v50() → HwpDocument
    HWP_V10 → open_hwp97()   → Hwp97Document
    HWPX    → open_hwpx()    → HwpxDocument
```

### 2.2. 파서 계층 (공통 구조)

세 포맷 모두 동일한 계층 구조를 따릅니다.

```
파일
  ↓ (v50: olefile / v97: 직접 바이너리 / owpml: zipfile + xml.etree)
XxxFile  (document_structure.py - 저수준 파싱)
  ↓
XxxDocument  (parser.py - 고수준 API, context manager 지원)
  ↓
iter_tags()  →  (ElementType, ParsedXxx) 튜플
  ↓
to_txt() / to_md()  (converters.py - 최상위 통합 변환)
```

### 2.3. 통합 외부 인터페이스 Enum

`helper_hwp/constants.py` 에서 단일 정의하며, 세 포맷이 공유합니다.

| Enum | 역할 |
| --- | --- |
| `ElementType` | 파싱 요소 타입 (PARAGRAPH, TABLE, PAGE_BREAK 등 26종) |
| `IterMode` | 순회 모드 (SEQUENTIAL, STRUCTURED) |

각 포맷의 `constants.py` 는 이 파일에서 재내보내기(re-export)하여 하위 호환을 유지합니다.

```python
# helper_hwp/v50/constants.py (하위 호환 예시)
from helper_hwp.constants import ElementType, IterMode
```

### 2.4. HWP 5.x 내부 구조

HWP 5.x 파일은 OLE CFB(Compound File Binary) 포맷입니다.

```
CFB 스토리지
├── FileHeader           (버전, 플래그)
├── DocInfo              (글꼴, 스타일, 레이아웃 등)
└── BodyText/
    ├── Section0         (레코드 스트림)
    ├── Section1
    └── ...
```

레코드 스트림은 가변 길이 레코드의 연속입니다. 각 레코드는 태그 ID(`RecordTag`)와 페이로드로 구성됩니다.

```
Section 레코드 스트림
  → HWPTAG_PARA_HEADER (각 문단 시작)
  → HWPTAG_PARA_TEXT  (문단 텍스트)
  → HWPTAG_CTRL_HEADER (컨트롤 헤더: 표, 그림, 필드 등)
  → HWPTAG_TABLE (표 메타데이터)
  → ...
```

### 2.5. HWP 97 내부 구조

HWP 97 파일(V3.00)은 단순 바이너리 포맷으로, Johab(cp949) 인코딩을 사용합니다.

```
파일 헤더 (0x20 bytes)
  "HWP Document File V3.00 \r\n\x1a" 시그니처
DocumentInfo (문서 정보 블록)
DocumentSummary (문서 요약 블록)
BodyText (문단 스트림 - SpecialCharCode 기반)
```

문단 내 특수 문자 코드(`SpecialCharCode`)로 표, 그림 등을 구분합니다:
- `SpecialCharCode.BOX(10)` + `BoxType.TABLE(0)` → `ElementType.TABLE`
- `SpecialCharCode.PICTURE(11)` → `ElementType.PICTURE`

### 2.6. HWPX 내부 구조

HWPX 파일은 ZIP 패키지로, OWPML XML 파일들의 묶음입니다.

```
ZIP 패키지
├── META-INF/container.xml
├── Contents/
│   ├── header.xml        (글꼴, 스타일 등)
│   ├── section0.xml      (본문 섹션)
│   ├── section1.xml
│   └── ...
└── mimetype
```

파싱은 `xml.etree.ElementTree` 기반으로 `OwpmlTag` 열거값과 매핑합니다.

### 2.7. converters.py 역할

최상위 통합 변환 함수를 정의합니다. 각 서브모듈 변환 함수에 직접 의존하지 않고, `detect_format()` → `open_hwp()` → `iter_tags()` 패턴으로 포맷에 무관하게 변환합니다.

```python
# to_txt 내부 흐름 (단순화)
def to_txt(file_path: str) -> str:
    with open_hwp(file_path) as doc:
        lines = []
        for etype, elem in doc.iter_tags():
            if etype == ElementType.PARAGRAPH:
                lines.append(elem.text)
        return "\n".join(lines)
```

---

## 3. 개발 환경 설정

### 3.1. 저장소 클론

```bash
git clone https://github.com/c0z0c-helper/helper_hwp.git
cd helper_hwp
```

### 3.2. Conda 환경 (권장)

프로젝트는 `py311_helper` conda 환경을 기준으로 개발합니다.

```bash
conda create -n py311_helper python=3.11
conda activate py311_helper
```

또는 venv 사용:

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate
```

### 3.3. 의존성 설치

```bash
# 런타임 의존성 + 패키지 편집 가능 설치
pip install -e .

# 개발 의존성 포함
pip install -e ".[dev]"
```

또는:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 3.4. Pre-commit 설정

```bash
pre-commit install
```

---

## 4. 코드 스타일

사용 도구:

| 도구 | 역할 |
| --- | --- |
| Black | 코드 포맷팅 |
| Ruff | 린팅 |
| mypy | 타입 체크 |

```bash
# 포맷팅
black helper_hwp tests examples

# 린팅
ruff check helper_hwp tests examples

# 타입 체크
mypy helper_hwp
```

### 4.1. 코딩 규칙

- 라인 길이: 100자
- Python 버전: 3.8 이상
- 타입 힌트: 모든 공개 API 필수
- Docstring: Google 스타일

```python
def to_txt(file_path: str) -> str:
    """HWP/HWPX 파일에서 텍스트를 추출합니다.

    Args:
        file_path: HWP/HWPX 파일 경로

    Returns:
        추출된 텍스트 문자열

    Raises:
        FileNotFoundError: 파일을 찾을 수 없는 경우
        ValueError: 지원하지 않는 파일 포맷인 경우
    """
```

### 4.2. 설계 원칙

- `try/except` 남용 금지 - 오류는 호출자에게 전파
- `print` 최소화 - 로깅(`logging`) 우선
- 함수/메서드/클래스 단위로 코드 제안
- MVP 우선: 재현성(reproducibility)을 최우선으로

---

## 5. 테스트

### 5.1. 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 커버리지 포함
pytest --cov=helper_hwp --cov-report=html

# 특정 테스트만
pytest tests/test_hwp_iter_tags.py
pytest tests/test_hwp_to_markdown.py
```

HTML 커버리지 리포트는 `htmlcov/index.html` 에 생성됩니다.

### 5.2. 테스트 파일 구조

| 파일 | 설명 |
| --- | --- |
| `tests/test.hwp` | HWP 5.x 기본 테스트 |
| `tests/test97.hwp` | HWP 97 테스트 |
| `tests/test.hwpx` | HWPX 테스트 |
| `tests/testTable.hwp` | 표 처리 테스트 |
| `tests/test장평.hwp` | 장평(자간) 처리 테스트 |
| `tests/test.owpml` | OWPML 직접 파싱 테스트 |

### 5.3. 테스트 작성 가이드

- 테스트 파일명: `test_*.py`
- 테스트 함수명: `test_*`
- 모든 새 기능은 테스트 필수

```python
def test_to_txt_hwp5():
    """HWP 5.x 텍스트 추출 테스트"""
    result = to_txt('tests/test.hwp')
    assert isinstance(result, str)
    assert len(result) > 0


def test_to_txt_hwp97():
    """HWP 97 텍스트 추출 테스트"""
    result = to_txt('tests/test97.hwp')
    assert isinstance(result, str)
    assert len(result) > 0


def test_to_txt_hwpx():
    """HWPX 텍스트 추출 테스트"""
    result = to_txt('tests/test.hwpx')
    assert isinstance(result, str)
    assert len(result) > 0
```

---

## 6. 기여 방법

### 6.1. 이슈 생성

버그 리포트나 기능 요청은 [GitHub Issues](https://github.com/c0z0c-helper/helper_hwp/issues) 에 등록해 주세요.

### 6.2. 브랜치 전략

| 브랜치 | 설명 |
| --- | --- |
| `master` | 안정 버전 |
| `feature/*` | 새 기능 |
| `bugfix/*` | 버그 수정 |

### 6.3. Pull Request 절차

1. Fork 후 브랜치 생성
```bash
git checkout -b feature/my-feature
```

2. 코드 작성 및 테스트
```bash
pytest
black helper_hwp
ruff check helper_hwp
```

3. 커밋
```bash
git commit -m "feat: HWP 97 equation parsing 추가"
```

4. Push 및 PR 생성
```bash
git push origin feature/my-feature
```

PR 설명에 포함할 내용:
- 변경 사항 요약
- 관련 이슈 번호
- 테스트 결과

### 6.4. 커밋 메시지 컨벤션

```
<타입>: <제목>
```

| 타입 | 설명 |
| --- | --- |
| `feat` | 새 기능 |
| `fix` | 버그 수정 |
| `docs` | 문서 수정 |
| `style` | 코드 포맷팅 |
| `refactor` | 리팩토링 |
| `test` | 테스트 추가/수정 |
| `chore` | 빌드/설정 변경 |

---

## 7. 릴리스 프로세스

### 7.1. 버전 관리

Semantic Versioning (MAJOR.MINOR.PATCH):

| 변경 종류 | 버전 증가 |
| --- | --- |
| 호환되지 않는 API 변경 | MAJOR |
| 하위 호환 기능 추가 | MINOR |
| 버그 수정 | PATCH |

현재 버전: `0.5.6`

### 7.2. 버전 변경 파일

버전 변경 시 두 파일을 동시에 수정합니다:

- `pyproject.toml` → `[project] version = "X.Y.Z"`
- `helper_hwp/__init__.py` → `__version__ = "X.Y.Z"`

### 7.3. 릴리스 체크리스트

1. `CHANGELOG.md` 업데이트
2. 버전 번호 업데이트 (`pyproject.toml`, `__init__.py`)
3. 테스트 실행
```bash
pytest
```
4. 빌드
```bash
python -m build
```
5. PyPI 배포
```bash
python -m twine upload dist/*
```

자세한 업로드 절차는 `PYPI_UPLOAD_GUIDE.md` 를 참고하세요.

---

## 참고 자료

- `docs/한글문서파일형식5.0분석보고서.md` - HWP 5.x 포맷 분석
- `docs/한글문서파일형식97분석보고서.md` - HWP 97 포맷 분석
- `docs/한글문서파일형식_5.0_revision1.3.txt` - HWP 5.0 공식 스펙
- `docs/한글문서파일형식3.0_HWPML_revision1.2.txt` - HWPML 스펙
- [olefile 문서](https://olefile.readthedocs.io/) - CFB 파싱 라이브러리
- [pycryptodome 문서](https://pycryptodome.readthedocs.io/) - AES 암호화 해제

## 라이센스

Apache License 2.0

출처: [https://github.com/c0z0c-helper/helper_hwp](https://github.com/c0z0c-helper/helper_hwp)

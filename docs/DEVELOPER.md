# 개발자 문서

helper_hwp 프로젝트 개발에 참여하기 위한 가이드입니다.

## 목차

- [프로젝트 구조](#프로젝트-구조)
- [개발 환경 설정](#개발-환경-설정)
- [코드 스타일](#코드-스타일)
- [테스트](#테스트)
- [기여 방법](#기여-방법)
- [릴리스 프로세스](#릴리스-프로세스)

## 프로젝트 구조

```
helper_hwp/
├── helper_hwp/              # 메인 패키지
│   ├── __init__.py          # 패키지 초기화 및 공개 API
│   ├── parser.py            # HWP 문서 파서 (고수준 API)
│   ├── document_structure.py  # HWP 파일 구조 (CFB 스토리지)
│   ├── char_paragraph.py    # 문단 및 문자 처리
│   ├── parsed_elements.py   # 파싱된 요소 (문단, 표, 페이지)
│   ├── models.py            # 데이터 모델 (Version, Header 등)
│   ├── constants.py         # 상수 정의
│   ├── record_stream.py     # 레코드 스트림 처리
│   └── utils.py             # 유틸리티 함수
├── tests/                   # 테스트 코드
│   ├── test_hwp_to_txt.py
│   ├── test_hwp_to_markdown.py
│   └── test.hwp             # 샘플 HWP 파일
├── examples/                # 사용 예제
│   ├── example_hwp_to_txt.py
│   ├── example_hwp_to_markdown.py
│   └── example_iter_tags.py
├── docs/                    # 문서
│   ├── DEVELOPER.md         # 개발자 문서 (이 파일)
│   └── USER_GUIDE.md        # 사용자 가이드
├── pyproject.toml           # 프로젝트 설정
├── README.md                # 프로젝트 소개
├── LICENSE                  # 라이센스
└── CHANGELOG.md             # 변경 이력
```

## 개발 환경 설정

### 1. 저장소 클론

```bash
git clone https://github.com/c0z0c/helper_hwp.git
cd helper_hwp
```

### 2. 가상환경 생성

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치

```bash
# 런타임 의존성
pip install -e .

# 개발 의존성
pip install -e ".[dev]"
```

또는:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. Pre-commit 설정

```bash
pre-commit install
```

## 코드 스타일

이 프로젝트는 다음 도구를 사용합니다:

- **Black**: 코드 포맷팅
- **Ruff**: 린팅
- **mypy**: 타입 체크

### 코드 포맷팅

```bash
# Black으로 포맷팅
black helper_hwp tests examples

# Ruff로 린팅
ruff check helper_hwp tests examples

# mypy로 타입 체크
mypy helper_hwp
```

### 코딩 컨벤션

- 라인 길이: 100자
- Python 버전: 3.8 이상
- 타입 힌트 권장 (모든 공개 API)
- 문서화 스타일: Google docstring

예시:

```python
def hwp_to_txt(hwp_path: str) -> str:
    """
    HWP 파일에서 텍스트를 추출합니다.

    Args:
        hwp_path: HWP 파일 경로

    Returns:
        추출된 텍스트 문자열

    Raises:
        FileNotFoundError: 파일을 찾을 수 없는 경우
    """
    pass
```

## 테스트

### 테스트 실행

```bash
# 모든 테스트 실행
pytest

# 커버리지 포함
pytest --cov=helper_hwp --cov-report=html

# 특정 테스트만 실행
pytest tests/test_hwp_to_txt.py
```

### 테스트 작성 가이드

- 모든 새로운 기능은 테스트 코드 필수
- 테스트 파일명: `test_*.py`
- 테스트 함수명: `test_*`
- 샘플 HWP 파일은 [tests/](../tests/) 디렉토리에 위치

예시:

```python
def test_hwp_to_txt():
    """텍스트 추출 테스트"""
    result = hwp_to_txt('tests/test.hwp')
    assert len(result) > 0
    assert isinstance(result, str)
```

## 아키텍처

### HWP 파일 구조

HWP 5.x 파일은 CFB (Compound File Binary) 포맷 기반으로 되어 있습니다:

1. **FileHeader**: 파일 시그니처, 버전, 압축/암호화 플래그
2. **DocInfo**: 문서 정보 (글꼴, 스타일, 레이아웃 등)
3. **BodyText**: 본문 (섹션 → 문단 → 문자)

### 주요 클래스

#### HwpFile

CFB 스토리지를 읽어 HWP 파일 구조를 파싱합니다.

```python
# document_structure.py
class HwpFile:
    @classmethod
    def from_file(cls, file_path: str) -> 'HwpFile':
        """HWP 파일 로드"""
```

#### HwpDocument

고수준 API로 문서 요소를 쉽게 순회합니다.

```python
# parser.py
class HwpDocument:
    def iter_tags(self, mode: Optional[IterMode] = None):
        """문서 요소 순회"""

    def get_elements_by_type(self, element_type: ElementType) -> List:
        """특정 타입 요소 검색"""
```

#### 파싱된 요소

- **ParsedParagraph**: 문단 (텍스트, 글자 모양)
- **ParsedTable**: 표 (행/열, 셀 정보)
- **ParsedPage**: 페이지 (페이지 번호, 문단 목록)

### 데이터 흐름

```
HWP 파일
  ↓ (olefile로 CFB 읽기)
HwpFile
  ↓ (레코드 스트림 파싱)
Section → Paragraph → Char
  ↓ (고수준 API)
HwpDocument
  ↓ (iter_tags, get_elements_by_type)
ParsedParagraph, ParsedTable, ParsedPage
  ↓
hwp_to_txt(), hwp_to_markdown()
```

## 기여 방법

### 1. 이슈 생성

버그 리포트나 기능 요청은 [GitHub Issues](https://github.com/c0z0c/helper_hwp/issues)에 등록해 주세요.

### 2. 브랜치 전략

- `master`: 안정 버전
- `develop`: 개발 브랜치 (선택사항)
- `feature/*`: 새 기능
- `bugfix/*`: 버그 수정

### 3. Pull Request

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

3. 커밋 (명확한 메시지 작성)
```bash
git commit -m "Add feature: HWP equation parsing"
```

4. Push 및 PR 생성
```bash
git push origin feature/my-feature
```

5. PR 설명에 다음 내용 포함:
   - 변경 사항 요약
   - 관련 이슈 번호
   - 테스트 결과

### 커밋 메시지 컨벤션

```
<타입>: <제목>

<본문>

<푸터>
```

타입:
- `feat`: 새 기능
- `fix`: 버그 수정
- `docs`: 문서 수정
- `style`: 코드 포맷팅
- `refactor`: 리팩토링
- `test`: 테스트 추가/수정
- `chore`: 빌드/설정 변경

## 릴리스 프로세스

### 버전 관리

Semantic Versioning (MAJOR.MINOR.PATCH) 사용:

- MAJOR: 호환되지 않는 API 변경
- MINOR: 하위 호환 가능한 기능 추가
- PATCH: 하위 호환 가능한 버그 수정

### 릴리스 체크리스트

1. [CHANGELOG.md](../CHANGELOG.md) 업데이트
2. 버전 번호 업데이트
   - [pyproject.toml](../pyproject.toml)
   - [helper_hwp/__init__.py](../helper_hwp/__init__.py)
3. 테스트 실행
```bash
pytest
```
4. 빌드 및 배포
```bash
python -m build
python -m twine upload dist/*
```

## 참고 자료

- [HWP 5.0 파일 형식 스펙](https://www.hancom.com/)
- [olefile 문서](https://olefile.readthedocs.io/)
- [pycryptodome 문서](https://pycryptodome.readthedocs.io/)

## 라이센스

이 프로젝트는 Apache License 2.0 하에 배포됩니다.

출처: https://github.com/c0z0c/helper_hwp

## 문의

- GitHub Issues: https://github.com/c0z0c/helper_hwp/issues

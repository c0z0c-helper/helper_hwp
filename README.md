# helper_hwp

Python으로 작성된 HWP (한글 문서) 파일 파서 및 텍스트 추출 라이브러리입니다.

## 특징

- HWP 5.x 포맷 지원 (CFB 기반)
- HWP 97 (V3.00) 포맷 지원
- HWPX / OWPML 포맷 지원
- 파일 포맷 자동 감지 (`open_hwp`)
- 텍스트 추출 및 마크다운 변환
- PDF 변환 지원 (`to_pdf`, playwright 필요)
- CLI 명령어 제공: `hwp2txt`, `hwp2md`, `hwp2html`, `hwp2doc`, `hwp2pdf`
- 표, 페이지 단위 파싱 지원
- 단위 변환 유틸리티 제공 (HWPUNIT ↔ cm/inch/px)

## 설치

```bash
pip install helper-hwp
```

또는 소스에서 설치:

```bash
git clone https://github.com/c0z0c-helper/helper_hwp.git
cd helper_hwp
pip install -e .
```

## 빠른 시작

### 텍스트 추출

```python
from helper_hwp import to_txt

# HWP / HWP97 / HWPX 포맷 자동 감지
text = to_txt('example.hwp')
print(text)
```

### 마크다운 변환

```python
from helper_hwp import to_md

# HWP / HWP97 / HWPX 포맷 자동 감지
markdown = to_md('example.hwp')
print(markdown)
```

### PDF 변환

```python
from helper_hwp import to_pdf

# playwright 설치 필요: pip install playwright && playwright install chromium
to_pdf('example.hwp', 'output.pdf')
```

### 문서 객체 사용

```python
from helper_hwp import open_hwp, ElementType

# HWP 문서 열기 (포맷 자동 감지)
with open_hwp('example.hwp') as doc:
    for etype, elem in doc.iter_tags():
        if etype == ElementType.PARAGRAPH:
            print(elem.text)
```

### CLI 사용

```bash
hwp2txt example.hwp
hwp2md  example.hwp
hwp2pdf example.hwp
```

## Examples

다음 예제를 참고하세요:

- [HWP → 텍스트 변환](https://github.com/c0z0c-helper/helper_hwp/blob/master/examples/example_hwp_to_txt.py)
- [HWP → Markdown 변환](https://github.com/c0z0c-helper/helper_hwp/blob/master/examples/example_hwp_to_markdown.py)
- [태그 순회 → JSON](https://github.com/c0z0c-helper/helper_hwp/blob/master/examples/example_iter_tags_to_json.py)

또는 소스 배포판(sdist)을 다운로드하여 확인:

```bash
pip download --no-deps helper-hwp
tar -xzf helper_hwp-*.tar.gz
```

## 문서

- [사용자 가이드](https://github.com/c0z0c-helper/helper_hwp/blob/master/docs/USER_GUIDE.md) - 기본 사용법 및 예제
- [개발자 문서](https://github.com/c0z0c-helper/helper_hwp/blob/master/docs/DEVELOPER.md) - 프로젝트 구조 및 개발 가이드

## 요구사항

- Python 3.8 이상
- olefile >= 0.46
- pycryptodome >= 3.15.0

## 라이센스

이 프로젝트는 Apache License 2.0 라이센스 하에 배포됩니다.

누구나 자유롭게 사용하고 수정할 수 있으며, 사용 시 출처를 표기해 주세요.

출처: [https://github.com/c0z0c-helper/helper_hwp](https://github.com/c0z0c-helper/helper_hwp)

자세한 내용은 [LICENSE](https://github.com/c0z0c-helper/helper_hwp/blob/master/LICENSE) 파일을 참조하세요.

## 기여

프로젝트에 대한 기여를 환영합니다! 기여 방법은 [개발자 문서](https://github.com/c0z0c-helper/helper_hwp/blob/master/docs/DEVELOPER.md)를 참조하세요.

## 변경 이력

변경 이력은 [CHANGELOG.md](https://github.com/c0z0c-helper/helper_hwp/blob/master/CHANGELOG.md)를 참조하세요.


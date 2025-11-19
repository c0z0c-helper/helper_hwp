# PyPI 업로드 가이드

이 문서는 `helper_hwp` 라이브러리를 PyPI에 업로드하는 방법을 설명합니다.

## 사전 준비

### 1. 필요한 도구 설치

```bash
pip install -r requirements-dev.txt
```

이 명령어는 다음 도구들을 설치합니다:
- `build`: 패키지 빌드 도구
- `twine`: PyPI 업로드 도구
- 기타 개발 도구 (pytest, black, ruff, mypy)

### 2. PyPI 계정 및 API 토큰

#### Test PyPI (테스트용)
- URL: https://test.pypi.org/
- 계정: 가입 필요 (https://test.pypi.org/account/register/)
- API 토큰: 계정 생성 후 발급 (https://test.pypi.org/manage/account/token/)

#### Production PyPI (실제 배포)
- URL: https://pypi.org/
- 계정: 가입 필요 (https://pypi.org/account/register/)
- API 토큰: 계정 생성 후 발급 (https://pypi.org/manage/account/token/)

### 3. .pypirc 설정 파일 생성

홈 디렉토리에 `.pypirc` 파일을 생성합니다:

**Windows:**
```bash
# C:\Users\<사용자명>\.pypirc
notepad %USERPROFILE%\.pypirc
```

**Linux/Mac:**
```bash
# ~/.pypirc
nano ~/.pypirc
```

파일 내용 (`.pypirc.example` 참고):

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR_PRODUCTION_TOKEN_HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-XXXX.XXXX
```

**⚠️ 중요:** `.pypirc` 파일은 절대로 Git에 커밋하지 마세요! (이미 `.gitignore`에 추가되어 있음)

## 업로드 방법

### 방법 1: 자동 스크립트 사용 (권장)

#### Test PyPI에 업로드

```bash
python upload_to_pypi.py --test
```

#### Production PyPI에 업로드

```bash
python upload_to_pypi.py
```

스크립트는 자동으로:
1. 이전 빌드 파일 정리
2. 패키지 빌드
3. 패키지 검증
4. 업로드 (사용자 확인 후)

### 방법 2: 수동 업로드

#### 1단계: 이전 빌드 정리

```bash
# Windows
rmdir /s /q dist build
del /s /q *.egg-info

# Linux/Mac
rm -rf dist build *.egg-info
```

#### 2단계: 패키지 빌드

```bash
python -m build
```

빌드 후 `dist/` 디렉토리에 다음 파일들이 생성됩니다:
- `helper_hwp-0.5.0.tar.gz` (소스 배포)
- `helper_hwp-0.5.0-py3-none-any.whl` (휠 배포)

#### 3단계: 패키지 검증

```bash
python -m twine check dist/*
```

#### 4단계: 업로드

**Test PyPI에 업로드:**
```bash
python -m twine upload --repository testpypi dist/*
```

**Production PyPI에 업로드:**
```bash
python -m twine upload dist/*
```

## 업로드 후 확인

### Test PyPI에서 확인

- 패키지 페이지: https://test.pypi.org/project/helper-hwp/
- 설치 테스트:
  ```bash
  pip install --index-url https://test.pypi.org/simple/ helper-hwp
  ```

### Production PyPI에서 확인

- 패키지 페이지: https://pypi.org/project/helper-hwp/
- 설치:
  ```bash
  pip install helper-hwp
  ```

## 버전 관리

새 버전을 업로드하기 전에 `pyproject.toml`의 버전을 업데이트하세요:

```toml
[project]
name = "helper-hwp"
version = "0.5.1"  # 버전 번호 증가
```

버전 번호 규칙 (Semantic Versioning):
- `0.5.0` → `0.5.1`: 버그 수정
- `0.5.0` → `0.6.0`: 새 기능 추가 (하위 호환)
- `0.5.0` → `1.0.0`: 주요 변경 (하위 호환 불가)

## 트러블슈팅

### 오류: "File already exists"

PyPI는 같은 버전을 두 번 업로드할 수 없습니다. `pyproject.toml`에서 버전을 증가시키세요.

### 오류: "Invalid or non-existent authentication"

`.pypirc` 파일의 API 토큰이 올바른지 확인하세요.

### 오류: "The user '<username>' isn't allowed to upload"

Production PyPI 토큰을 아직 생성하지 않았거나, 토큰이 잘못되었습니다.

## 참고 자료

- [PyPI 공식 문서](https://packaging.python.org/en/latest/tutorials/packaging-projects/)
- [Test PyPI](https://test.pypi.org/)
- [Production PyPI](https://pypi.org/)
- [Semantic Versioning](https://semver.org/)

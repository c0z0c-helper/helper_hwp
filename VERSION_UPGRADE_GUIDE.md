# 버전 업그레이드 가이드

이 문서는 `helper_hwp` 패키지의 버전을 업그레이드하고 PyPI에 배포하는 전체 프로세스를 설명합니다.

## 목차
1. [버전 번호 결정](#버전-번호-결정)
2. [버전 업그레이드 절차](#버전-업그레이드-절차)
3. [PyPI 업로드](#pypi-업로드)
4. [자동화 스크립트](#자동화-스크립트)

---

## 버전 번호 결정

**Semantic Versioning (SemVer)** 규칙을 따릅니다: `MAJOR.MINOR.PATCH`

### 예시: 현재 버전 0.5.0

| 변경 유형 | 새 버전 | 사용 시기 |
|---------|--------|---------|
| **Patch** | 0.5.1 | 버그 수정, 작은 개선 |
| **Minor** | 0.6.0 | 새 기능 추가 (하위 호환 유지) |
| **Major** | 1.0.0 | 주요 변경 (하위 호환 불가) |

### 결정 기준

```
0.5.0 → 0.5.1  # 버그 수정
- 텍스트 추출 오류 수정
- 성능 개선
- 문서 오타 수정

0.5.0 → 0.6.0  # 새 기능 추가
- HTML 변환 기능 추가
- 새로운 유틸리티 함수 추가
- 기존 기능은 그대로 유지

0.5.0 → 1.0.0  # 주요 변경
- API 인터페이스 변경
- 기존 함수명 변경 또는 제거
- 하위 호환성 깨짐
```

---

## 버전 업그레이드 절차

### 1단계: 코드 수정 및 테스트

```bash
# 코드 수정
# ... (기능 추가 또는 버그 수정)

# 테스트 실행
pytest tests/

# Git 커밋
git add .
git commit -m "기능 추가: XXX 구현"
git push
```

### 2단계: 버전 번호 업데이트

다음 3개 파일을 수정해야 합니다:

#### 2-1. `helper_hwp/__init__.py`

```python
__version__ = '0.5.3'
```

#### 2-2. `pyproject.toml`

```toml
[project]
name = "helper-hwp"
version = "0.5.1"  # 이 줄만 수정
description = "Python HWP 파일 파서 및 텍스트 추출 라이브러리"
```

#### 2-3. `CHANGELOG.md`

파일 **상단**에 새 버전 섹션을 추가:

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [0.5.1] - 2025-11-20

### Fixed
- 텍스트 추출 시 특수문자 처리 오류 수정
- 표 파싱 버그 수정

### Added
- 예제 코드 추가

## [0.5.0] - 2025-11-19
...기존 내용...
```

변경 유형:
- **Added**: 새 기능
- **Changed**: 기존 기능 변경
- **Deprecated**: 곧 제거될 기능
- **Removed**: 제거된 기능
- **Fixed**: 버그 수정
- **Security**: 보안 수정

### 3단계: 버전 업데이트 커밋

```bash
git add helper_hwp/__init__.py pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.5.1"
git push
```

### 4단계: Git 태그 생성 (선택사항, 권장)

```bash
# 태그 생성
git tag v0.5.1

# 태그 푸시
git push origin v0.5.1

# 태그 확인
git tag -l
```

---

## PyPI 업로드

### 방법 1: 단계별 수동 업로드

#### 1. 이전 빌드 파일 삭제

```bash
# Windows (Git Bash)
rm -rf dist/ build/ *.egg-info

# Windows (CMD)
rmdir /s /q dist build
del /s /q *.egg-info
```

#### 2. 패키지 빌드

```bash
python -m build
```

빌드 후 `dist/` 디렉토리 확인:
```
dist/
├── helper_hwp-0.5.1.tar.gz
└── helper_hwp-0.5.1-py3-none-any.whl
```

#### 3. 패키지 검증

```bash
python -m twine check dist/*
```

출력 예시:
```
Checking dist/helper_hwp-0.5.1-py3-none-any.whl: PASSED
Checking dist/helper_hwp-0.5.1.tar.gz: PASSED
```

#### 4. Test PyPI에 업로드 (테스트)

```bash
python -m twine upload --repository testpypi --disable-progress-bar dist/*
```

Test PyPI 확인: https://test.pypi.org/project/helper-hwp/

#### 5. Test PyPI에서 설치 테스트

```bash
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ helper-hwp
```

#### 6. Production PyPI에 업로드

문제가 없으면 실제 PyPI에 업로드:

```bash
python -m twine upload --disable-progress-bar dist/*
```

확인: https://pypi.org/project/helper-hwp/

### 방법 2: 자동화 스크립트 사용

#### Test PyPI 업로드

```bash
python upload_to_pypi.py --test
```

스크립트가 자동으로:
1. 이전 빌드 파일 정리
2. 패키지 빌드
3. 패키지 검증
4. Test PyPI 업로드 (확인 후)

#### Production PyPI 업로드

```bash
python upload_to_pypi.py
```

---

## 자동화 스크립트

### 버전 업그레이드 자동화 (선택사항)

`bump_version.py` 스크립트를 만들어 자동화할 수 있습니다:

```python
# 사용법
python bump_version.py 0.5.1 patch "버그 수정"
python bump_version.py 0.6.0 minor "새 기능 추가"
python bump_version.py 1.0.0 major "주요 변경"
```

자동으로:
1. `__init__.py`, `pyproject.toml` 버전 업데이트
2. `CHANGELOG.md`에 새 섹션 추가
3. Git 커밋 및 태그 생성
4. (선택) PyPI 빌드 및 업로드

---

## 전체 프로세스 요약

### 버전 업그레이드 체크리스트

- [ ] 1. 코드 수정 및 테스트
- [ ] 2. 버전 번호 결정 (Patch/Minor/Major)
- [ ] 3. 파일 업데이트:
  - [ ] `helper_hwp/__init__.py` - `__version__`
  - [ ] `pyproject.toml` - `version`
  - [ ] `CHANGELOG.md` - 새 버전 섹션 추가
- [ ] 4. Git 커밋: `git commit -m "Bump version to X.Y.Z"`
- [ ] 5. Git 태그: `git tag vX.Y.Z`
- [ ] 6. Git 푸시: `git push && git push origin vX.Y.Z`
- [ ] 7. 빌드: `python -m build`
- [ ] 8. 검증: `python -m twine check dist/*`
- [ ] 9. Test PyPI 업로드 및 테스트
- [ ] 10. Production PyPI 업로드

### 빠른 명령어 모음

```bash
# 버전 업데이트 후
git add helper_hwp/__init__.py pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.5.1"
git tag v0.5.1
git push && git push origin v0.5.1

# 빌드 및 업로드
rm -rf dist/ build/ *.egg-info
python -m build
python -m twine check dist/*
python -m twine upload --repository testpypi --disable-progress-bar dist/*
python -m twine upload --disable-progress-bar dist/*
```

---

## 주의사항

### 중요 규칙

1. **버전은 되돌릴 수 없습니다**
   - PyPI에 업로드한 버전은 삭제할 수 없습니다
   - 같은 버전 번호로 다시 업로드할 수 없습니다
   - 실수 시 버전을 증가시켜 새로 업로드해야 합니다

2. **항상 Test PyPI에서 먼저 테스트**
   - Production PyPI 업로드 전 Test PyPI에서 검증
   - 설치 및 기본 기능 테스트 수행

3. **CHANGELOG.md는 사용자를 위한 문서**
   - 기술적인 세부사항보다는 **변경사항의 영향**에 집중
   - 사용자가 업그레이드 시 알아야 할 내용 작성
   - Breaking Changes는 명확하게 표시

4. **Git 태그는 일관성 유지**
   - 버전 번호 앞에 `v` 접두사 사용: `v0.5.1`
   - PyPI 버전과 Git 태그가 일치하도록 관리

### 문제 해결

#### "File already exists" 오류
```
같은 버전을 두 번 업로드할 수 없습니다.
→ 버전 번호를 증가시켜 다시 업로드하세요.
```

#### 업로드 인증 오류
```
~/.pypirc 파일의 API 토큰 확인
또는 --username __token__ --password pypi-XXX 옵션 사용
```

#### 빌드 경고
```
License classifiers deprecated 경고는 무시해도 됩니다.
패키지 기능에는 영향이 없습니다.
```

---

## 참고 자료

- [Semantic Versioning](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [PyPI 공식 가이드](https://packaging.python.org/)
- [프로젝트 CHANGELOG.md](CHANGELOG.md)
- [PyPI 업로드 가이드](PYPI_UPLOAD_GUIDE.md)

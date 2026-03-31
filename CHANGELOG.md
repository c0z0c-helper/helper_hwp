# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.7] - 2026-03-31

### Changed
- 최상위 공개 API 명칭 통일
  - `open_hwp` → `hwp_open`
  - `to_txt` → `hwp_to_txt`
  - `to_md` → `hwp_to_md`
  - `to_pdf` → `hwp_to_pdf`
  - `auto_to_txt`, `auto_to_markdown` 제거 (포맷 자동 감지는 `hwp_to_txt`, `hwp_to_md`로 통합)
- `helper_hwp.v50.__init__`: 공개 심볼에 `Hwp50*` 접두사 alias 추가, 기존 심볼 정리
- `helper_hwp.v97.__init__`: 공개 심볼에 `Hwp97*` 접두사 alias 추가, 기존 심볼 정리

### Fixed
- 테스트 전면 갱신 — 변경된 API명 반영, 44개 테스트 전부 PASS
  - `test_convert_outputs.py`: `hwp_to_txt`, `hwp_to_md`, `hwp_to_pdf` 사용
  - `test_hwp_iter_tags.py`: `hwp_open`, `hwp_to_txt` 사용
  - `test_hwp_to_markdown.py`: `hwp_to_md` 사용 (`auto_to_markdown` 제거)
  - `test_hwp_to_pdf.py`: `hwp_to_pdf` alias 사용

## [0.5.6] - 2026-03-29

### Added
- HWP 97 (V3.00) 포맷 파서 추가 (`v97` 모듈)
  - 파일 인식 정보, 문서 정보, 문단 리스트, 표(BOX) 파싱
  - 텍스트 추출 (`to_txt`), 마크다운 변환 (`to_md`) 통합 지원
  - `open_hwp97`, `Hwp97Document` API
  - 단위 변환 (`hunit_to_cm`, `hunit_to_inch`, `hunit_to_px`)
- HWPX (`.hwpx`) 및 OWPML (`.owpml`) 파일 지원 (`owpml` 모듈)
- 포맷 자동 감지 (`detect_format`) — `.hwp` / `.hwp97` / `.hwpx` / `.owpml`
- CLI 명령어 추가: `hwp2txt`, `hwp2md`, `hwp2html`, `hwp2doc`, `hwp2pdf`
- 최상위 통합 변환 API: `open_hwp`, `to_txt`, `to_md`, `to_pdf`
- PDF 변환 지원 (`to_pdf`, playwright 기반)
- 테스트 전면 재작성 — pytest 기반, 44개 테스트 전부 PASS
  - `test_convert_outputs.py`: 변환 결과 파일 저장 검증
  - `test_hwp_iter_tags.py`: `iter_tags` 순회 검증
  - `test_hwp_to_markdown.py`: 마크다운 변환 검증
  - `test_hwp_to_pdf.py`: PDF 변환 검증
- 테스트 파일 추가: `test.hwpx`, `test.owpml`, `test97.hwp`, `testTable.hwp`, `test장평.hwp`

### Changed
- `open_hwp` 포맷 자동 감지 dispatch 방식으로 전환 (v50 / v97 / owpml 통합)
- 공통 외부 인터페이스 Enum (`ElementType`, `IterMode`) 세 포맷 공유
- `upload_to_pypi.py` → `upload_helper_hwp.py` 파일명 변경

## [0.5.5] - 2025-12-15
### Fixed
- hwp2txt
- hwp2md
- hwp2html
- hwp2doc
- hwp2pdf

## [0.5.4] - 2025-11-23

### Fixed
- README 오타 수정
- PyPI 설치 후 import 오류 해결
- hwp_to_txt hwp_to_text
- hwp_to_md hwp_to_markdown

## [0.5.1] - 2025-11-19

### Fixed
- 패키지 구조 설정 수정: `py-modules`에서 `packages`로 변경
- PyPI 설치 후 import 오류 해결

## [0.5.0] - 2025-11-19

### Added - 초기 릴리즈

#### 핵심 기능
- CFB (Compound File Binary) 기반 HWP 5.x 파일 파싱
- 레코드 스트림 리더 및 태그 처리
- 텍스트 추출 (`hwp_to_txt`)
- 마크다운 변환 (`hwp_to_markdown`)
- 문서 객체 API (`open_hwp`, `HwpDocument`)

#### 파싱 기능
- 문단 파싱 (텍스트, 스타일, 레이아웃)
  - 문단 헤더 (HWPTAG_PARA_HEADER)
  - 문단 텍스트 (HWPTAG_PARA_TEXT)
  - 글자 모양 (HWPTAG_PARA_CHAR_SHAPE)
  - 레이아웃 정보 (HWPTAG_PARA_LINE_SEG)
  - 페이지 구분 감지 (page_break_type)
- 표 파싱 (HWPTAG_TABLE)
  - 행/열 구조 및 셀 병합 정보
  - 셀 너비/높이, 여백, 간격
  - 표 내부 문단 텍스트 추출
- 도형/개체 파싱
  - 그림 (HWPTAG_SHAPE_COMPONENT_PICTURE)
  - 수식 (HWPTAG_EQEDIT)
  - 도형 요소 (HWPTAG_SHAPE_COMPONENT)
- 글자 모양 (CharShape) 파싱
  - 폰트 크기, ID, 스타일 (굵게, 기울임, 밑줄)
  - 자간, 장평, 색상
  - 문단별 글자 모양 매핑

#### 문서 순회 모드
- `SEQUENTIAL`: 문서 출현 순서대로 순회 (속도 우선)
- `STRUCTURED`: Section → Paragraph → Char 계층 구조로 순회

#### 요소 타입
- `PARAGRAPH`: 문단
- `TABLE`: 표
- `PICTURE`: 그림
- `EQUATION`: 수식
- `SHAPE_COMPONENT`: 도형 요소
- `CTRL_HEADER`, `LIST_HEADER`, `PAGE_DEF` 등

#### 유틸리티
- 단위 변환 함수
  - `hwpunit_to_cm`: HWPUNIT → cm
  - `hwpunit_to_inch`: HWPUNIT → inch
  - `hwpunit_to_px`: HWPUNIT → px

#### 예제 및 문서
- 텍스트 추출 예제 (`example_hwp_to_txt.py`)
- 마크다운 변환 예제 (`example_hwp_to_markdown.py`)
- 태그 순회 예제 (`example_iter_tags.py`)
- JSON 변환 예제 (`example_iter_tags_to_json.py`)
- 사용자 가이드 (`docs/USER_GUIDE.md`)
- 개발자 문서 (`docs/DEVELOPER.md`)

#### 테스트
- 텍스트 추출 테스트 (`test_hwp_to_txt.py`)
- 마크다운 변환 테스트 (`test_hwp_to_markdown.py`)
- PDF 변환 테스트 (`test_hwp_to_markdown_pdf.py`)
- 태그 순회 테스트 (`test_hwp_iter_tags.py`)

### Known Limitations
- 페이지 경계 정확도: `is_page_first_line` 플래그 기반 페이지 구분은 근사치이며, 정확한 페이지 경계는 HWP 스펙 문서에서 명확히 정의되지 않음
- 그림/도형 처리: 현재는 바이너리 데이터만 추출하며, 이미지는 Base64 인코딩되지 않음
- 하이퍼링크: 파싱 구현 미완료

## [Unreleased]

### TODO - 향후 개발 계획

#### High Priority
1. **페이지 구분 개선**
   - 정확한 페이지 경계 감지 (현재는 `is_page_first_line` 근사치 사용)
   - HWP 스펙 문서 재검토 및 추가 분석 필요

2. **마크다운 이미지 지원**
   - 그림 객체를 Base64로 인코딩하여 마크다운에 임베드
   - `![alt](data:image/png;base64,...)` 형식 지원

3. **도형 Mermaid 변환**
   - 도형 객체를 Mermaid 다이어그램으로 변환
   - 변환 불가능한 경우 Base64 이미지로 폴백

4. **하이퍼링크 지원**
   - URL 링크 추출 및 마크다운 변환
   - `[텍스트](URL)` 형식 지원

#### Medium Priority
5. **각주/미주 파싱**
   - FOOTNOTE, ENDNOTE 요소 처리

6. **머리말/꼬리말 지원**
   - HEADER, FOOTER 요소 처리

7. **메모/주석 파싱**
   - COMMENT 요소 처리

8. **OLE 객체 지원**
   - OLE 객체 정보 추출

9. **북마크/필드 지원**
   - BOOKMARK, FIELD 요소 처리

#### Low Priority
10. **성능 최적화**
    - 대용량 문서 처리 최적화
    - 메모리 사용량 개선

11. **추가 출력 형식**
    - HTML 변환
    - JSON 구조화 출력 개선

12. **문서 작성 기능**
    - HWP 파일 생성 (장기 계획)

### Notes
- 일부 기능은 HWP 스펙 문서의 제한으로 인해 구현이 어려울 수 있음
- 개발 일정은 미정

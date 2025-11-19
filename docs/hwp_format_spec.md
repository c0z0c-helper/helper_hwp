# HWP 파일 포맷 명세

HWP 파일은 Microsoft의 CFB (Compound File Binary) 포맷을 기반으로 합니다.

## 구조 개요

```
HWP File (CFB Container)
├── FileHeader
├── DocInfo/
│   ├── BinData
│   ├── BorderFill
│   ├── CharShape
│   ├── FaceName
│   ├── ParaShape
│   └── ...
├── BodyText/
│   ├── Section0
│   ├── Section1
│   └── ...
└── BinData/
    ├── BIN0001.png
    ├── BIN0002.jpg
    └── ...
```

## CFB (Compound File Binary)

- MS Office에서 사용하는 파일 시스템 형식
- 디렉토리와 스트림으로 구성
- Python에서는 `olefile` 라이브러리로 파싱 가능

## 레코드 구조

모든 데이터는 레코드 단위로 저장됩니다.

### 레코드 헤더 (4바이트)

```
+----------+----------+----------+
| Tag ID   | Level    | Size     |
| (10bit)  | (10bit)  | (12bit)  |
+----------+----------+----------+
```

- **Tag ID**: 레코드 타입 식별자 (0-1023)
- **Level**: 계층 레벨 (0-1023)
- **Size**: 데이터 크기 (바이트)
  - 0xFFF인 경우 다음 4바이트가 실제 크기

### 주요 태그

- `HWPTAG_PARA_HEADER` (66): 문단 헤더
- `HWPTAG_PARA_TEXT` (67): 문단 텍스트
- `HWPTAG_PARA_CHAR_SHAPE` (68): 글자 모양
- `HWPTAG_PARA_LINE_SEG` (69): 줄 정보
- `HWPTAG_TABLE` (71): 표
- `HWPTAG_SHAPE_COMPONENT` (72): 도형 요소

## 문단 구조

```
Paragraph
├── ParagraphHeader
├── ParagraphText (CharList)
├── CharShapes
├── LineSeg
└── Controls (optional)
    ├── Table
    ├── Picture
    ├── Equation
    └── ...
```

### 문자 리스트 (CharList)

- UTF-16 인코딩 (2바이트)
- 일반 문자: 1개 카운트
- 컨트롤 문자: 8개 카운트

**특수 문자:**
- `0x0000-0x001F`: 컨트롤 문자
- `0x0002`: 섹션/단 구분
- `0x000D`: 문단 끝
- `0x0009`: 탭
- `0x000A`: 줄 바꿈

## 암호화

- AES-128/256 지원
- 파일 헤더의 플래그로 암호화 여부 확인
- 복호화 후 Deflate 압축 해제 필요

## 압축

- Deflate (zlib) 알고리즘 사용
- 파일 헤더의 플래그로 압축 여부 확인
- Python의 `zlib` 모듈로 처리 가능

## 참고 자료

- [hwp-rs](https://github.com/hahnlee/hwp-rs): Rust로 구현된 HWP 파서
- [pyhwp](https://github.com/mete0r/pyhwp): Python HWP 파서 (레거시)
- MS CFB 명세: [Microsoft Documentation](https://docs.microsoft.com/en-us/openspecs/windows_protocols/ms-cfb/)
- 한컴: [HWP/OWPML형식] https://www.hancom.com/support/downloadCenter/hwpOwpml
